import re
import urllib.parse
from typing import Dict, List, Tuple

from core.constants import (
    CURRENCY_PATTERNS,
    ENTITY_RISK_MAP,
    ENTITY_SOURCE_INFERENCE,
    ENTITY_SOURCE_KEYWORD,
    ENTITY_SOURCE_REGEX,
    GOVERNMENT_ENTITIES,
    INDIAN_BANKS,
    INTELLIGENCE_INDICATOR_MAP,
    KNOWN_SHORTENERS,
    OTP_EXTRACT_PATTERNS,
    PHONE_PATTERNS,
    RISK_LOW,
    SOCIAL_HANDLE_PATTERNS,
    SUSPICIOUS_TLDS,
    TRACKING_KEYWORDS,
    TRACKING_PATTERNS,
    TRANSACTION_KEYWORDS,
    TRANSACTION_PATTERNS,
    UPI_HANDLES,
    URL_PATTERNS,
)

_URL_REGEXES: List[re.Pattern] = [re.compile(p, re.IGNORECASE) for p in URL_PATTERNS]
_DOMAIN_PATTERN: re.Pattern = re.compile(r"\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}\b", re.IGNORECASE)
_EMAIL_PATTERN: re.Pattern = re.compile(r"\b[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}\b", re.IGNORECASE)
_UPI_PATTERN: re.Pattern = re.compile(r"\b[a-z0-9._-]+@[a-z]{3,}\b", re.IGNORECASE)
_QR_PATTERN: re.Pattern = re.compile(r"\bqr\s*code\b|\bscan\s*(?:the\s*)?(?:qr\s*)?code\b", re.IGNORECASE)
_IFSC_PATTERN: re.Pattern = re.compile(r"\b[A-Z]{4}0[A-Z0-9]{6}\b")
_BANK_ACCT_PATTERN: re.Pattern = re.compile(r"\b\d{9,18}\b")
_IPV4_PATTERN: re.Pattern = re.compile(r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b")
_IPV6_PATTERN: re.Pattern = re.compile(r"\b(?:[a-fA-F0-9]{1,4}:){7}[a-fA-F0-9]{1,4}\b")
_OTP_TRIGGER: re.Pattern = re.compile(r"\botp\b", re.IGNORECASE)
_OTP_NUMERIC: re.Pattern = re.compile(r"\b\d{4,8}\b")
_PHONE_REGEXES: List[Tuple[re.Pattern, str, float]] = [
    (re.compile(p), t, c) for p, t, c in PHONE_PATTERNS
]
_SOCIAL_REGEXES: List[Tuple[re.Pattern, str, float]] = [
    (re.compile(p, re.IGNORECASE), t, c) for p, t, c in SOCIAL_HANDLE_PATTERNS
]
_CURRENCY_REGEXES: List[re.Pattern] = [re.compile(p, re.IGNORECASE) for p in CURRENCY_PATTERNS]
_OTP_EXTRACT_REGEXES: List[Tuple[re.Pattern, float, bool]] = [
    (re.compile(p, re.IGNORECASE), c, g) for p, c, g in OTP_EXTRACT_PATTERNS
]
_TRACKING_REGEXES: List[Tuple[re.Pattern, str, float]] = [
    (re.compile(p), t, c) for p, t, c in TRACKING_PATTERNS
]
_TRANSACTION_REGEXES: List[Tuple[re.Pattern, float]] = [
    (re.compile(p, re.IGNORECASE), c) for p, c in TRANSACTION_PATTERNS
]
_SHORTENER_REGEXES: Dict[str, re.Pattern] = {
    s: re.compile(rf"https?://{re.escape(s)}/\S+", re.IGNORECASE)
    for s in KNOWN_SHORTENERS
}
_TLD_REGEXES: Dict[str, re.Pattern] = {
    tld: re.compile(rf"https?://(?:[-\w.]+?)({re.escape(tld)})(?:/[^\s]*)?", re.IGNORECASE)
    for tld in SUSPICIOUS_TLDS
}
_BANK_PATTERNS: List[Tuple[re.Pattern, str]] = [
    (re.compile(r"\b" + re.escape(b) + r"\b" if " " not in b else re.escape(b), re.IGNORECASE), b)
    for b in INDIAN_BANKS
]
_GOVT_PATTERNS: List[Tuple[re.Pattern, str]] = [
    (re.compile(r"\b" + re.escape(e) + r"\b" if " " not in e else re.escape(e), re.IGNORECASE), e)
    for e in GOVERNMENT_ENTITIES
]


def extract_urls(text: str) -> List[Dict]:
    found: List[Dict] = []
    seen = set()
    for pat in _URL_REGEXES:
        for match in pat.finditer(text):
            raw = match.group(0).rstrip(".,;:!?)")
            if raw not in seen:
                seen.add(raw)
                entity: Dict = {"value": raw, "type": "url", "confidence": 0.99, "source": ENTITY_SOURCE_REGEX}
                try:
                    parsed = urllib.parse.urlparse(raw if "://" in raw else "http://" + raw)
                    domain = parsed.netloc.lower()
                    if any(s in domain for s in KNOWN_SHORTENERS):
                        entity["type"] = "shortened_url"
                    else:
                        for tld in SUSPICIOUS_TLDS:
                            if domain.endswith(tld):
                                entity["type"] = "suspicious_tld"
                                break
                except (ValueError, AttributeError):
                    pass
                found.append(entity)
    return found


def extract_domains(text: str) -> List[Dict]:
    found: List[Dict] = []
    seen = set()
    for match in _DOMAIN_PATTERN.finditer(text):
        raw = match.group(0).lower()
        if raw not in seen:
            seen.add(raw)
            if "https://" + raw not in text and "http://" + raw not in text:
                found.append({"value": raw, "type": "domain", "confidence": 0.95, "source": ENTITY_SOURCE_REGEX})
    return found


def extract_emails(text: str) -> List[Dict]:
    found: List[Dict] = []
    seen = set()
    for match in _EMAIL_PATTERN.finditer(text):
        raw = match.group(0).lower()
        if raw not in seen:
            seen.add(raw)
            found.append({"value": raw, "type": "email", "confidence": 0.98, "source": ENTITY_SOURCE_REGEX})
    return found


def extract_phones(text: str) -> List[Dict]:
    found: List[Dict] = []
    seen = set()
    for pat, ptype, conf in _PHONE_REGEXES:
        for match in pat.finditer(text):
            raw = match.group(0).strip("-.,;:!?)")
            if raw not in seen:
                seen.add(raw)
                found.append({"value": raw, "type": ptype, "confidence": conf, "source": ENTITY_SOURCE_REGEX})
    return found


def extract_upi_ids(text: str) -> List[Dict]:
    found: List[Dict] = []
    seen = set()
    for match in _UPI_PATTERN.finditer(text):
        raw = match.group(0).lower()
        handle = raw.split("@")[1] if "@" in raw else ""
        if handle in UPI_HANDLES:
            if raw not in seen:
                seen.add(raw)
                found.append({"value": raw, "type": "upi_id", "confidence": 0.97, "source": ENTITY_SOURCE_REGEX})
    return found


def extract_qr_keywords(text: str) -> List[Dict]:
    found: List[Dict] = []
    for match in _QR_PATTERN.finditer(text):
        found.append({"value": match.group(0), "type": "qr_keyword", "confidence": 0.95, "source": ENTITY_SOURCE_REGEX})
    return found


def extract_bank_names(text: str) -> List[Dict]:
    found: List[Dict] = []
    seen = set()
    t = text.lower()
    for pattern, bank in _BANK_PATTERNS:
        if pattern.search(t):
            if bank not in seen:
                seen.add(bank)
                found.append({"value": bank.title(), "type": "bank_name", "confidence": 0.90, "source": ENTITY_SOURCE_KEYWORD})
    return found


def extract_government_entities(text: str) -> List[Dict]:
    found: List[Dict] = []
    seen = set()
    t = text.lower()
    for pattern, entity in _GOVT_PATTERNS:
        if pattern.search(t):
            if entity not in seen:
                seen.add(entity)
                found.append({"value": entity.title(), "type": "government_entity", "confidence": 0.85, "source": ENTITY_SOURCE_KEYWORD})
    return found


def extract_currency_amounts(text: str) -> List[Dict]:
    found: List[Dict] = []
    seen = set()
    for pat in _CURRENCY_REGEXES:
        for match in pat.finditer(text):
            raw = match.group(0).strip().lower()
            if raw not in seen:
                seen.add(raw)
                found.append({"value": match.group(0), "type": "currency_amount", "confidence": 0.88, "source": ENTITY_SOURCE_REGEX})
    return found


def extract_otp_codes(text: str) -> List[Dict]:
    found: List[Dict] = []
    seen = set()
    if not _OTP_TRIGGER.search(text):
        return found
    for pat, conf, has_group in _OTP_EXTRACT_REGEXES:
        if found:
            break
        for match in pat.finditer(text):
            raw = match.group(0)
            if raw not in seen:
                seen.add(raw)
                val = match.group(1) if has_group and match.lastindex and match.lastindex >= 1 else raw
                found.append({"value": val.strip(), "type": "otp_code", "confidence": conf, "source": ENTITY_SOURCE_REGEX})
    if not found:
        codes = _OTP_NUMERIC.findall(text)
        if codes:
            found.append({"value": codes[0], "type": "otp_code", "confidence": 0.70, "source": ENTITY_SOURCE_INFERENCE})
    return found


def extract_shortened_urls(text: str) -> List[Dict]:
    found: List[Dict] = []
    seen = set()
    for shortener, pattern in _SHORTENER_REGEXES.items():
        for match in pattern.finditer(text):
            raw = match.group(0).rstrip(".,;:!?)")
            if raw not in seen:
                seen.add(raw)
                found.append({"value": raw, "type": "shortened_url", "confidence": 0.99, "source": ENTITY_SOURCE_REGEX})
    return found


def extract_suspicious_tlds(text: str) -> List[Dict]:
    found: List[Dict] = []
    seen = set()
    for tld, pattern in _TLD_REGEXES.items():
        for match in pattern.finditer(text):
            domain = match.group(0)
            if domain not in seen:
                seen.add(domain)
                found.append({"value": domain, "type": "suspicious_tld", "confidence": 0.95, "source": ENTITY_SOURCE_REGEX})
    return found


def extract_ip_addresses(text: str) -> List[Dict]:
    found: List[Dict] = []
    seen = set()
    for match in _IPV4_PATTERN.finditer(text):
        raw = match.group(0)
        if raw not in seen:
            seen.add(raw)
            found.append({"value": raw, "type": "ip_address", "confidence": 0.99, "source": ENTITY_SOURCE_REGEX})
    for match in _IPV6_PATTERN.finditer(text):
        raw = match.group(0)
        if raw not in seen:
            seen.add(raw)
            found.append({"value": raw, "type": "ip_address", "confidence": 0.98, "source": ENTITY_SOURCE_REGEX})
    return found


def extract_social_handles(text: str) -> List[Dict]:
    found: List[Dict] = []
    seen = set()
    for pat, etype, conf in _SOCIAL_REGEXES:
        for match in pat.finditer(text):
            raw = match.group(0)
            pos = match.start()
            key = raw.lower()
            if key in seen:
                continue
            if pos > 0 and re.match(r"[a-z0-9]", text[pos - 1], re.IGNORECASE):
                continue
            at_parts = raw.split("@")
            if len(at_parts) == 2 and at_parts[1].lower() in UPI_HANDLES:
                continue
            seen.add(key)
            found.append({"value": raw, "type": etype, "confidence": conf, "source": ENTITY_SOURCE_REGEX})
    return found


def extract_ifsc_codes(text: str) -> List[Dict]:
    found: List[Dict] = []
    seen = set()
    for match in _IFSC_PATTERN.finditer(text):
        raw = match.group(0)
        if raw not in seen:
            seen.add(raw)
            found.append({"value": raw, "type": "ifsc_code", "confidence": 0.99, "source": ENTITY_SOURCE_REGEX})
    return found


def extract_bank_accounts(text: str) -> List[Dict]:
    found: List[Dict] = []
    seen = set()
    for match in _BANK_ACCT_PATTERN.finditer(text):
        raw = match.group(0)
        if raw not in seen:
            seen.add(raw)
            if re.match(r"^\d{4,8}$", raw):
                continue
            if re.match(r"^[6789]\d{9}$", raw):
                continue
            found.append({"value": raw, "type": "bank_account", "confidence": 0.55, "source": ENTITY_SOURCE_REGEX})
    return found


def extract_tracking_ids(text: str) -> List[Dict]:
    found: List[Dict] = []
    seen = set()
    t = text.upper()
    has_keyword = any(kw in t.lower() for kw in TRACKING_KEYWORDS)
    for pat, etype, conf in _TRACKING_REGEXES:
        for match in pat.finditer(t):
            raw = match.group(0)
            cleaned = re.sub(r"\s+", "", raw)
            if cleaned not in seen and has_keyword:
                seen.add(cleaned)
                found.append({"value": cleaned, "type": etype, "confidence": conf, "source": ENTITY_SOURCE_REGEX})
    return found


def extract_transaction_ids(text: str) -> List[Dict]:
    found: List[Dict] = []
    seen = set()
    has_keyword = any(kw in text.lower() for kw in TRANSACTION_KEYWORDS)
    for pat, conf in _TRANSACTION_REGEXES:
        for match in pat.finditer(text):
            raw = match.group(0)
            if raw not in seen and has_keyword:
                seen.add(raw)
                found.append({"value": raw, "type": "transaction_id", "confidence": conf, "source": ENTITY_SOURCE_REGEX})
    return found
