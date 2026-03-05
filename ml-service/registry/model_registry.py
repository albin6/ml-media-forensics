import json
import os
from pathlib import Path

_MANIFEST_PATH = Path(__file__).parent.parent / "model_store" / "manifest.json"

class ModelRegistry:
    """
    Loads and caches ML model handlers by name from the model manifest.
    Supports hot-swapping active models by re-reading the manifest.
    """

    def __init__(self):
        self._cache: dict = {}

    def _manifest(self) -> dict:
        with open(_MANIFEST_PATH) as f:
            return json.load(f)

    def get_image_model(self):
        manifest = self._manifest()
        active   = manifest["active_image_model"]
        if active not in self._cache:
            version_info = manifest["versions"][active]
            model_path   = str(Path(__file__).parent.parent / "model_store" / version_info["file"])
            architecture = version_info.get("architecture", "resnet50").lower().replace("+", "").replace(" ", "")

            from models.image.cnn_handler import CNNImageHandler
            arch = "xception" if "xception" in architecture else "resnet50"
            self._cache[active] = CNNImageHandler(model_path=model_path, architecture=arch)

        return self._cache[active], active

    def get_video_model(self):
        manifest = self._manifest()
        active   = manifest["active_video_model"]
        if active not in self._cache:
            version_info = manifest["versions"][active]
            model_path   = str(Path(__file__).parent.parent / "model_store" / version_info["file"])

            from models.video.cnn_lstm_handler import CNNLSTMVideoHandler
            self._cache[active] = CNNLSTMVideoHandler(model_path=model_path)

        return self._cache[active], active

registry = ModelRegistry()
