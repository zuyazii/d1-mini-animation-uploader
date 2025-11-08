"""Wrappers around the existing image-to-bitmap tooling."""

from __future__ import annotations

import io
from typing import Tuple, List

from PIL import Image

from tools.image_to_ssd1306 import image_to_bitmap
from .config import OLED_WIDTH, OLED_HEIGHT


class ImageValidationError(ValueError):
    """Raised when an uploaded image does not satisfy OLED requirements."""


def png_bytes_to_bitmap(blob: bytes, *, invert: bool = False) -> Tuple[List[int], List[str]]:
    """Convert raw PNG bytes into bitmap data + ASCII preview."""
    try:
        img = Image.open(io.BytesIO(blob)).convert("L")
    except Exception as exc:  # pragma: no cover - Pillow-specific errors
        raise ImageValidationError(f"Failed to decode PNG: {exc}") from exc

    if img.size != (OLED_WIDTH, OLED_HEIGHT):
        raise ImageValidationError(
            f"Image must be exactly {OLED_WIDTH}x{OLED_HEIGHT} pixels (got {img.size[0]}x{img.size[1]})."
        )

    bitmap, ascii_rows = image_to_bitmap(
        img,
        threshold=128,
        invert=invert,
        lsb_first=False,
    )
    return bitmap, ascii_rows
