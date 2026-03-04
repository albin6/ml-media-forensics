import torch
import torch.nn as nn
from torchvision import models
from typing import Dict, Any, List

from preprocessing.ela import ela_to_tensor
from preprocessing.frame_extractor import extract_frames


class CNNLSTMVideoHandler:
    """
    Dual-stream CNN+LSTM detector for video tampering.

    Pipeline:
    1. Extract frames from video via OpenCV.
    2. Apply ELA to each frame.
    3. CNN encodes each ELA frame into a feature vector.
    4. LSTM processes the sequence of frame features for temporal analysis.
    5. Output: per-frame tampering scores + overall video verdict.
    """

    FEATURE_DIM = 512
    LSTM_HIDDEN  = 256
    LSTM_LAYERS  = 2

    def __init__(self, model_path: str, device: str = "cpu"):
        self.device = torch.device("cuda" if torch.cuda.is_available() else device)
        self.cnn, self.lstm, self.classifier = self._build_model()
        self._load_weights(model_path)
        self.cnn.eval()
        self.lstm.eval()
        self.classifier.eval()

    def _build_model(self):
        # CNN feature extractor (ResNet-50 backbone, remove FC)
        cnn = models.resnet50(weights=None)
        cnn.fc = nn.Identity()  # Output: (batch, 2048)
        cnn = nn.Sequential(cnn, nn.Linear(2048, self.FEATURE_DIM))

        # LSTM for temporal reasoning
        lstm = nn.LSTM(
            input_size=self.FEATURE_DIM,
            hidden_size=self.LSTM_HIDDEN,
            num_layers=self.LSTM_LAYERS,
            batch_first=True,
            dropout=0.3,
        )

        # Binary classifier: tampered / authentic
        classifier = nn.Sequential(
            nn.Linear(self.LSTM_HIDDEN, 64),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(64, 2),
        )

        return (
            cnn.to(self.device),
            lstm.to(self.device),
            classifier.to(self.device),
        )

    def _load_weights(self, path: str):
        import os
        if os.path.exists(path):
            state = torch.load(path, map_location=self.device)
            if "cnn" in state:
                self.cnn.load_state_dict(state["cnn"], strict=False)
            if "lstm" in state:
                self.lstm.load_state_dict(state["lstm"], strict=False)
            if "classifier" in state:
                self.classifier.load_state_dict(state["classifier"], strict=False)

    def _frame_to_feature(self, frame_bytes: bytes) -> torch.Tensor:
        """ELA → CNN → feature vector for a single frame. Returns shape (FEATURE_DIM,)."""
        _, tensor = ela_to_tensor(frame_bytes, size=(224, 224))
        tensor = tensor.to(self.device)
        with torch.no_grad():
            feat = self.cnn(tensor)  # (1, FEATURE_DIM)
        return feat.squeeze(0)       # → (FEATURE_DIM,)

    def infer(self, video_bytes: bytes) -> Dict[str, Any]:
        # 1. Extract sampled frames
        frames = extract_frames(video_bytes, sample_rate=5, max_frames=120)
        if not frames:
            return {"error": "No frames extracted from video"}

        # 2. ELA + CNN per-frame feature extraction  →  list of (FEATURE_DIM,) tensors
        features = []
        for frame_no, frame_bytes in frames:
            feat = self._frame_to_feature(frame_bytes)
            features.append(feat)

        # 3. Stack into sequence: (1, T, FEATURE_DIM) for LSTM batch_first
        seq = torch.stack(features, dim=0).unsqueeze(0)  # (T, FEATURE_DIM) → (1, T, FEATURE_DIM)

        # 4. LSTM temporal analysis
        with torch.no_grad():
            lstm_out, _ = self.lstm(seq)             # (1, T, HIDDEN)
            frame_logits = self.classifier(lstm_out)  # (1, T, 2)
            frame_probs  = torch.softmax(frame_logits, dim=2)  # (1, T, 2)

        # 5. Build per-frame results
        frame_results: List[Dict] = []
        for i, (frame_no, _) in enumerate(frames):
            conf = frame_probs[0, i, 1].item()
            frame_results.append({
                "frame_no":    frame_no,
                "is_tampered": conf >= 0.5,
                "confidence":  round(conf, 4),
            })

        # 6. Overall video verdict: tampered if >25% of frames are flagged
        tampered_count = sum(1 for f in frame_results if f["is_tampered"])
        overall_conf   = frame_probs[0, :, 1].mean().item()
        is_tampered    = tampered_count / len(frame_results) > 0.25

        return {
            "is_tampered":          is_tampered,
            "confidence":           round(overall_conf, 4),
            "frame_results":        frame_results,
            "tampered_frame_count": tampered_count,
            "total_frames_analysed": len(frame_results),
            "metadata": {
                "architecture":   "CNN+LSTM",
                "sample_rate":    5,
                "tamper_threshold": 0.25,
                "device":         str(self.device),
            },
        }
