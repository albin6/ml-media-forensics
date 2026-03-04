import io
import tempfile
from typing import Generator, List, Tuple
import cv2
import numpy as np
from PIL import Image


def extract_frames(
    video_bytes: bytes,
    sample_rate: int = 5,
    max_frames: int = 120,
) -> List[Tuple[int, bytes]]:
    """
    Extract sampled frames from a video.

    Args:
        video_bytes: Raw video file bytes.
        sample_rate: Extract every Nth frame (e.g., 5 = every 5th frame).
        max_frames:  Maximum number of frames to extract.

    Returns:
        List of (frame_number, jpeg_bytes) tuples.
    """
    frames = []

    # Write to a temp file since OpenCV VideoCapture cannot read from bytes
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=True) as tmp:
        tmp.write(video_bytes)
        tmp.flush()

        cap = cv2.VideoCapture(tmp.name)
        if not cap.isOpened():
            raise ValueError("Cannot open video file")

        frame_no = 0
        extracted = 0
        while extracted < max_frames:
            ret, frame = cap.read()
            if not ret:
                break
            if frame_no % sample_rate == 0:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil = Image.fromarray(rgb)
                buf = io.BytesIO()
                pil.save(buf, format="JPEG", quality=95)
                frames.append((frame_no, buf.getvalue()))
                extracted += 1
            frame_no += 1

        cap.release()

    return frames
