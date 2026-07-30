import re
from typing import Dict, List, Tuple


_URLS_RE: re.Pattern = re.compile(r"https?://(?:[-\w.]|%[\da-fA-F]{2})+(?:/[^\s]*)?", re.IGNORECASE)
_EMAILS_RE: re.Pattern = re.compile(r"[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}\b", re.IGNORECASE)
_PHONES_RE: re.Pattern = re.compile(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")
_UPI_RE: re.Pattern = re.compile(r"[a-z0-9._-]+@[a-z]{3,}\b", re.IGNORECASE)

_VALID_UPI_HANDLES: frozenset = frozenset({
    "paytm", "gpay", "phonepe", "amazonpay", "bhim", "upi",
    "ybl", "ibl", "apl", "axl", "payu", "icici", "hdfc", "sbi", "kotak",
})


def extract_entities(text: str) -> Dict[str, List[str]]:
    entities: Dict[str, List[str]] = {"urls": [], "emails": [], "phones": [], "upis": []}
    for m in _URLS_RE.finditer(text):
        entities["urls"].append(m.group(0))
    for m in _EMAILS_RE.finditer(text):
        entities["emails"].append(m.group(0).lower())
    for m in _PHONES_RE.finditer(text):
        entities["phones"].append(m.group(0))
    for m in _UPI_RE.finditer(text):
        handle = m.group(0).split("@")[1].lower() if "@" in m.group(0) else ""
        if handle in _VALID_UPI_HANDLES:
            entities["upis"].append(m.group(0).lower())
    return entities


def preserve_placeholders(text: str) -> Tuple[str, Dict[str, str]]:
    placeholders: Dict[str, str] = {}
    for m in _URLS_RE.finditer(text):
        key = f"__url_{len(placeholders)}__"
        placeholders[key] = m.group(0)
        text = text.replace(m.group(0), key, 1)
    for m in _EMAILS_RE.finditer(text):
        key = f"__email_{len(placeholders)}__"
        placeholders[key] = m.group(0)
        text = text.replace(m.group(0), key, 1)
    for m in _PHONES_RE.finditer(text):
        key = f"__phone_{len(placeholders)}__"
        placeholders[key] = m.group(0)
        text = text.replace(m.group(0), key, 1)
    for m in _UPI_RE.finditer(text):
        handle = m.group(0).split("@")[1].lower() if "@" in m.group(0) else ""
        if handle in _VALID_UPI_HANDLES:
            key = f"__upi_{len(placeholders)}__"
            placeholders[key] = m.group(0)
            text = text.replace(m.group(0), key, 1)
    return text, placeholders


def restore_placeholders(text: str, placeholders: Dict[str, str]) -> str:
    for key, value in placeholders.items():
        text = text.replace(key, value)
    return text


def clean_text(text: str) -> str:
    text_with_ph, placeholders = preserve_placeholders(text)
    t = text_with_ph.lower()
    t = re.sub(r"[^a-z0-9\s_]", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    t = restore_placeholders(t, placeholders)
    return t
