import re
import unicodedata

from config.settings import MAX_TEXT_LENGTH
from core.exceptions import EmptyTextError, TextTooLargeError


_CONTROL_CHARS: re.Pattern = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_ZERO_WIDTH_CHARS: re.Pattern = re.compile(r"[\u200b\u200c\u200d\u2060\u2061\u2062\u2063\u2064\ufeff]")
_UNASSIGNED_UNICODE: re.Pattern = re.compile(r"[\ufff0-\uffff\U000e0000-\U0010ffff]")
_MULTI_NEWLINE: re.Pattern = re.compile(r"\n{3,}")


def normalise_text(text: str) -> str:
    t = unicodedata.normalize("NFKC", text)
    t = _CONTROL_CHARS.sub("", t)
    t = _ZERO_WIDTH_CHARS.sub("", t)
    t = _UNASSIGNED_UNICODE.sub("", t)
    t = _MULTI_NEWLINE.sub("\n\n", t)
    return t.strip()


def validate_text_length(text: str) -> str:
    if len(text) > MAX_TEXT_LENGTH:
        raise TextTooLargeError(
            f"Text exceeds maximum length of {MAX_TEXT_LENGTH} characters "
            f"(got {len(text)})"
        )
    return text


def sanitise_text(text: str) -> str:
    text = normalise_text(text)
    text = validate_text_length(text)
    if not text:
        raise EmptyTextError("Text must not be empty")
    return text


def truncate_text_for_log(text: str, max_len: int = 60) -> str:
    if len(text) <= max_len:
        return text
    return text[:max_len] + "..."
