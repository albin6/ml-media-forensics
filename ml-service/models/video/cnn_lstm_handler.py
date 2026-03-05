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
        cnn = models.resnet50(weights=None)
        cnn.fc = nn.Identity()
        cnn = nn.Sequential(cnn, nn.Linear(2048, self.FEATURE_DIM))

        lstm = nn.LSTM(
            input_size=self.FEATURE_DIM,
            hidden_size=self.LSTM_HIDDEN,
            num_layers=self.LSTM_LAYERS,
            batch_first=True,
            dropout=0.3,
        )

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
            feat = self.cnn(tensor)
        return feat.squeeze(0)

    def infer(self, video_bytes: bytes) -> Dict[str, Any]:
        frames = extract_frames(video_bytes, sample_rate=5, max_frames=120)
        if not frames:
            return {"error": "No frames extracted from video"}

        features = []
        for frame_no, frame_bytes in frames:
            feat = self._frame_to_feature(frame_bytes)
            features.append(feat)

        seq = torch.stack(features, dim=0).unsqueeze(0)

        with torch.no_grad():
            lstm_out, _ = self.lstm(seq)
            frame_logits = self.classifier(lstm_out)
            frame_probs  = torch.softmax(frame_logits, dim=2)

        frame_results: List[Dict] = []
        for i, (frame_no, _) in enumerate(frames):
            conf = frame_probs[0, i, 1].item()
            frame_results.append({
                "frame_no":    frame_no,
                "is_tampered": conf >= 0.5,
                "confidence":  round(conf, 4),
            })

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
