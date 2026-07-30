import asyncio
import re
import concurrent.futures
from typing import Dict, List, Optional

from PIL import Image
import pytesseract

from utils.text import clean_text
from core.exceptions import ImageCorruptedError, ImageDecompressionBombError, ImageDimensionError

PHONE_REGEX = re.compile(r"(?:\+91[-\s]?)?[6-9]\d{9}")
OTP_REGEX = re.compile(r"(?<!\w)(\d{4,8})(?!\w)")
URL_REGEX = re.compile(r"https?://(?:[-\w.]|%[\da-fA-F]{2})+[^\s]*")
EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")

_MAX_IMAGE_PIXELS: int = 50_000_000
_MAX_IMAGE_DIMENSION: int = 10_000

_thread_pool: Optional[concurrent.futures.ThreadPoolExecutor] = None


def _get_thread_pool() -> concurrent.futures.ThreadPoolExecutor:
    global _thread_pool
    if _thread_pool is None:
        _thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=2, thread_name_prefix="ocr")
    return _thread_pool


def _validate_image(img: Image.Image) -> None:
    width, height = img.size
    if width > _MAX_IMAGE_DIMENSION or height > _MAX_IMAGE_DIMENSION:
        raise ImageDimensionError(
            f"Image dimensions {width}x{height} exceed limit "
            f"({_MAX_IMAGE_DIMENSION}x{_MAX_IMAGE_DIMENSION})"
        )
    pixels = width * height
    if pixels > _MAX_IMAGE_PIXELS:
        raise ImageDecompressionBombError(
            f"Image has {pixels} pixels, exceeding limit of {_MAX_IMAGE_PIXELS}"
        )


def _run_ocr(image_path: str) -> str:
    try:
        img = Image.open(image_path)
    except Exception as exc:
        raise ImageCorruptedError(f"Cannot open image: {exc}") from exc
    try:
        img.verify()
    except Exception as exc:
        raise ImageCorruptedError(f"Image verification failed: {exc}") from exc
    img = Image.open(image_path)
    if img.mode not in ("L", "RGB", "RGBA"):
        img = img.convert("RGB")
    try:
        img.load()
    except Exception as exc:
        raise ImageCorruptedError(f"Image data loading failed: {exc}") from exc
    _validate_image(img)
    text = pytesseract.image_to_string(img)
    return text.strip()


def extract_text(image_path: str) -> str:
    return _run_ocr(image_path)


async def extract_text_async(image_path: str) -> str:
    """Run OCR in a thread pool to avoid blocking the async event loop."""
    pool = _get_thread_pool()
    loop = asyncio.get_running_loop()
    text = await loop.run_in_executor(pool, _run_ocr, image_path)
    return text


def extract_metadata(text: str) -> Dict[str, List[str]]:
    phones = list(set(PHONE_REGEX.findall(text)))
    otps = [m for m in OTP_REGEX.findall(text) if len(m) >= 4]
    urls = URL_REGEX.findall(text)
    emails = EMAIL_REGEX.findall(text)
    return {
        "phone_numbers": phones,
        "otps": otps,
        "urls": urls,
        "emails": emails,
    }
