import io
import numpy as np
from PIL import Image

def compute_ela(image_bytes: bytes, quality: int = 95, amplifier: int = 20) -> Image.Image:
    """
    Error Level Analysis (ELA): detect regions with different compression levels.

    Algorithm:
    1. Save the image at a fixed JPEG quality to a buffer (re-compress).
    2. Compute the absolute pixel difference: |original - re-compressed|.
    3. Amplify the difference for visual contrast.

    Args:
        image_bytes: Raw bytes of the original image.
        quality:     JPEG re-compression quality (95 is standard for ELA).
        amplifier:   Multiplier to enhance the difference map.

    Returns:
        PIL Image representing the ELA heatmap.
    """
    original = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    recompressed_buffer = io.BytesIO()
    original.save(recompressed_buffer, format="JPEG", quality=quality)
    recompressed_buffer.seek(0)
    recompressed = Image.open(recompressed_buffer).convert("RGB")

    if original.size != recompressed.size:
        recompressed = recompressed.resize(original.size, Image.LANCZOS)

    orig_array  = np.array(original,     dtype=np.int16)
    reco_array  = np.array(recompressed, dtype=np.int16)
    diff        = np.abs(orig_array - reco_array) * amplifier
    diff        = np.clip(diff, 0, 255).astype(np.uint8)

    return Image.fromarray(diff, mode="RGB")

def ela_to_tensor(image_bytes: bytes, size: tuple = (299, 299)):
    """
    Full ELA preprocessing pipeline for CNN input.

    Returns:
        ela_pil:   The ELA heatmap as a PIL image (for visualization).
        tensor:    Normalized torch.Tensor of shape (1, 3, H, W).
    """
    import torch
    from torchvision import transforms

    ela_pil = compute_ela(image_bytes)

    transform = transforms.Compose([
        transforms.Resize(size),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5]),
    ])
    tensor = transform(ela_pil).unsqueeze(0)
    return ela_pil, tensor
