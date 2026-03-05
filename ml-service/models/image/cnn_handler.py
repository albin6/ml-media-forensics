import io
import base64
import torch
import torch.nn as nn
from torchvision import models
from typing import Dict, Any
from PIL import Image

from preprocessing.ela import ela_to_tensor

class CNNImageHandler:
    """
    Forensic image tampering detector using XceptionNet / ResNet backbone
    fine-tuned on FaceForensics++ or CASIA dataset.

    Returns: { is_tampered, confidence, ela_heatmap_bytes }
    """

    def __init__(self, model_path: str, architecture: str = "xception", device: str = "cpu"):
        self.device       = torch.device("cuda" if torch.cuda.is_available() else device)
        self.architecture = architecture
        self.model        = self._build_model(architecture)
        self._load_weights(model_path)
        self.model.eval()

    def _build_model(self, arch: str) -> nn.Module:
        if arch == "xception":
            model = models.inception_v3(weights=None, num_classes=2, aux_logits=False)
        elif arch == "resnet50":
            model = models.resnet50(weights=None)
            model.fc = nn.Linear(model.fc.in_features, 2)
        else:
            raise ValueError(f"Unknown architecture: {arch}")
        return model.to(self.device)

    def _load_weights(self, path: str):
        """Load model weights — skip if weights file doesn't exist yet (first run)."""
        import os
        if os.path.exists(path):
            state = torch.load(path, map_location=self.device)
            self.model.load_state_dict(state, strict=False)

    def infer(self, image_bytes: bytes) -> Dict[str, Any]:
        ela_pil, tensor = ela_to_tensor(image_bytes, size=(299, 299))
        tensor = tensor.to(self.device)

        with torch.no_grad():
            logits = self.model(tensor)
            probs  = torch.softmax(logits, dim=1)
            tampered_prob = probs[0, 1].item()
            is_tampered   = tampered_prob >= 0.5

        buf = io.BytesIO()
        ela_pil.save(buf, format="PNG")
        ela_b64 = base64.b64encode(buf.getvalue()).decode()

        return {
            "is_tampered":     is_tampered,
            "confidence":      round(tampered_prob, 4),
            "ela_heatmap_bytes": ela_b64,
            "metadata": {
                "architecture": self.architecture,
                "device":       str(self.device),
                "ela_quality":  95,
            },
        }
