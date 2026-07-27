__all__ = [
    "MAX_TEXT_LENGTH", "MAX_FILE_SIZE_MB", "SUPPORTED_IMAGE_TYPES",
]

from typing import List

MAX_TEXT_LENGTH: int = 10000
MAX_FILE_SIZE_MB: int = 10
SUPPORTED_IMAGE_TYPES: List[str] = ["image/jpeg", "image/png", "image/webp", "image/bmp"]
