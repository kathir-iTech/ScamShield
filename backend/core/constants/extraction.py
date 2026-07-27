__all__ = [
    "SUSPICIOUS_TLDS", "KNOWN_SHORTENERS", "INDIAN_BANKS", "GOVERNMENT_ENTITIES",
    "UPI_HANDLES", "SCAM_KEYWORDS", "URGENCY_WORDS", "PAYMENT_APPS",
    "INDIA_BANKS_SHORT", "GOVT_REFS", "SUSPICIOUS_URL_KEYWORDS", "OTP_PATTERNS",
    "MONEY_PHRASES", "TRACKING_KEYWORDS", "TRANSACTION_KEYWORDS",
    "ENTITY_RISK_MAP", "ENTITY_INDICATOR_MAP", "INTELLIGENCE_INDICATOR_MAP",
    "PHONE_PATTERNS", "TRACKING_PATTERNS", "TRANSACTION_PATTERNS",
    "CURRENCY_PATTERNS", "OTP_EXTRACT_PATTERNS", "SOCIAL_HANDLE_PATTERNS", "URL_PATTERNS",
]

import re
from typing import Dict, FrozenSet, List, Tuple

SUSPICIOUS_TLDS: FrozenSet[str] = frozenset({
    ".xyz", ".top", ".club", ".gq", ".ml", ".cf", ".tk", ".ga",
    ".men", ".loan", ".win", ".bid", ".download",
})

KNOWN_SHORTENERS: FrozenSet[str] = frozenset({
    "bit.ly", "tinyurl.com", "tiny.cc", "t.co", "ow.ly", "is.gd",
    "buff.ly", "shorturl.at", "cutt.ly", "rb.gy", "bl.ink", "short.link",
})

INDIAN_BANKS: Tuple[str, ...] = (
    "sbi", "state bank of india", "hdfc", "icici", "axis", "kotak mahindra",
    "pnb", "punjab national bank", "canara bank", "bank of baroda", "bob",
    "indusind", "yes bank", "union bank", "idbi", "rbi", "sebi",
    "bandhan bank", "south indian bank", "federal bank", "idfc first",
)

GOVERNMENT_ENTITIES: Tuple[str, ...] = (
    "pm", "modi", "sarkari", "government of india", "central govt",
    "nrega", "ayushman", "income tax", "itr", "gst", "aadhaar",
    "passport seva", "epfo", "esic", "nsdl", "csc",
)

UPI_HANDLES: FrozenSet[str] = frozenset({
    "paytm", "gpay", "phonepe", "axisbank", "hdfcbank", "icici", "sbi",
    "okicici", "okaxis", "ybl", "ibl", "apl", "upi", "fam", "airtel",
    "jio", "freecharge", "mobikwik",
})

SCAM_KEYWORDS: Dict[str, int] = {
    "upi": 15, "kyc": 20, "aadhaar": 15, "aadhar": 15, "otp": 15,
    "deactivate": 20, "blocked": 15, "suspended": 15, "freeze": 20, "limited": 10,
    "disconnected": 20, "disconnection": 20, "penalty": 15, "fine": 10,
    "lottery": 25, "won": 20, "cashback": 15, "refund": 10, "prize": 20,
    "work from home": 15, "part-time": 10, "data entry": 10, "registration fee": 20,
    "customs": 20, "clearance": 15, "release fee": 25, "illegal": 20,
    "subsidy": 15, "scheme": 10, "installment": 10, "pension": 10,
    "tneb": 15, "electricity": 5, "bill": 5,
    "urgent": 10, "immediately": 10, "expires": 10, "expiring": 10,
    "account will be": 15, "suspended": 15, "limited": 10,
    "click here": 10, "verify now": 15, "update now": 10,
    "free": 5, "guaranteed": 10, "earn": 10, "income": 5,
    "processing fee": 20, "registration fee": 20, "exam fee": 20,
}

URGENCY_WORDS: Tuple[str, ...] = (
    "urgent", "immediately", "asap", "right away", "now", "hurry",
    "limited time", "expires", "expiring", "today only", "final notice",
    "last warning",
)

PAYMENT_APPS: Tuple[str, ...] = (
    "gpay", "phonepe", "paytm", "bhim", "upi", "amazon pay",
)

INDIA_BANKS_SHORT: Tuple[str, ...] = (
    "sbi", "hdfc", "icici", "axis", "kotak", "pnb", "canara",
    "bob", "indusind", "rbi", "sebi",
)

GOVT_REFS: Tuple[str, ...] = (
    "pm", "modi", "sarkari", "government of india", "central govt",
    "nrega", "ayushman",
)

SUSPICIOUS_URL_KEYWORDS: FrozenSet[str] = frozenset({
    "kyc", "update", "verify", "secure", "login", "account",
    "bank", "upi", "aadhaar", "aadhar", "otp", "confirm", "reset",
})

OTP_PATTERNS: Tuple[str, ...] = (
    r"\botp\b",
    r"one[\s-]*time[\s-]*password",
    r"verification code",
    r"(?:otp|code)\s*[:\-]\s*\d{4,8}",
)

MONEY_PHRASES: Tuple[Tuple[str, str], ...] = (
    (r"(?:rs|inr|₹)\s*[\d,]+", "Mentions a monetary amount"),
    (r"pay(?:\s*now|\s*immediately|\s*the)", "Payment demand detected"),
    (r"transfer\s*(?:money|funds|amount)", "Money transfer request"),
    (r"(?:fee|fine|penalty|payment)\s*(?:of\s*)?(?:rs|inr|₹)?\s*[\d,]+", "Specific monetary demand"),
    (r"credit\s*(?:card|score|limit)", "Credit-related mention"),
    (r"(?:loan|emi)", "Loan or EMI mentioned"),
)

TRACKING_KEYWORDS: Tuple[str, ...] = (
    "track", "shipment", "courier", "parcel", "tracking", "order", "dispatch",
)

TRANSACTION_KEYWORDS: Tuple[str, ...] = (
    "txn", "transaction", "ref", "reference", "payment id", "utr", "rrn",
)

ENTITY_RISK_MAP: Dict[str, Dict[str, str]] = {
    "shortened_url": {"risk": "HIGH", "reason": "Destination hidden behind URL shortener"},
    "suspicious_tld": {"risk": "HIGH", "reason": "Common phishing infrastructure"},
    "otp_code": {"risk": "HIGH", "reason": "Active authentication credential"},
    "upi_id": {"risk": "MEDIUM", "reason": "Direct payment request possible"},
    "email": {"risk": "MEDIUM", "reason": "Potential phishing or impersonation"},
    "phone": {"risk": "MEDIUM", "reason": "Potential contact for scam operations"},
    "ip_address": {"risk": "MEDIUM", "reason": "Direct network identifier"},
    "ifsc_code": {"risk": "MEDIUM", "reason": "Bank account targeting"},
    "bank_account": {"risk": "HIGH", "reason": "Direct financial instrument"},
    "url": {"risk": "LOW", "reason": "May lead to phishing site"},
    "domain": {"risk": "LOW", "reason": "May host malicious content"},
    "currency_amount": {"risk": "LOW", "reason": "Financial transaction mention"},
    "bank_name": {"risk": "LOW", "reason": "Institutional reference"},
    "government_entity": {"risk": "LOW", "reason": "Government impersonation possible"},
    "qr_keyword": {"risk": "MEDIUM", "reason": "QR-based payment request"},
    "tracking_id": {"risk": "LOW", "reason": "Courier reference identifier"},
    "social_handle": {"risk": "LOW", "reason": "Potential social media vector"},
    "transaction_id": {"risk": "LOW", "reason": "Transaction reference identifier"},
    "phone_indian": {"risk": "MEDIUM", "reason": "Indian telecom contact point"},
    "phone_international": {"risk": "MEDIUM", "reason": "International contact point"},
    "email_raw": {"risk": "MEDIUM", "reason": "Potential phishing or impersonation"},
}

ENTITY_INDICATOR_MAP: Dict[str, str] = {
    "bank_name": "Bank Impersonation",
    "upi_id": "UPI ID",
    "shortened_url": "Shortened URL",
    "email": "Email Address",
    "phone_indian": "Phone Number",
    "phone_international": "Phone Number",
    "url": "Suspicious URL",
    "suspicious_tld": "Suspicious URL",
}

INTELLIGENCE_INDICATOR_MAP: Dict[str, str] = {
    "shortened_url": "Shortened URL",
    "suspicious_tld": "Suspicious TLD",
    "otp_code": "OTP Code",
    "upi_id": "UPI ID",
    "email": "Email Address",
    "bank_name": "Bank Name",
    "currency_amount": "Currency Amount",
    "qr_keyword": "QR Payment Request",
    "phone_indian": "Indian Phone Number",
    "phone_international": "International Phone Number",
    "ifsc_code": "IFSC Code",
    "bank_account": "Bank Account Number",
    "ip_address": "IP Address",
}

PHONE_PATTERNS: Tuple[Tuple[str, str, float], ...] = (
    (r"(?:\+91[-.\s]?|0)?[6789]\d{9}\b", "phone_indian", 0.95),
    (r"\+\d{1,3}[-.\s]?\d{6,14}\b", "phone_international", 0.90),
    (r"1[8-9]00[-.\s]?\d{3}[-.\s]?\d{4}\b", "phone_indian", 0.90),
    (r"0\d{2,4}[-.\s]?\d{6,8}\b", "phone_indian", 0.85),
)

TRACKING_PATTERNS: Tuple[Tuple[str, str, float], ...] = (
    (r"\b[A-Z]{2}\d{9}[A-Z]{2}\b", "tracking_id", 0.95),
    (r"\b1Z[A-Z0-9]{14,18}\b", "tracking_id", 0.95),
    (r"\b\d{12,16}\b", "tracking_id", 0.55),
)

TRANSACTION_PATTERNS: Tuple[Tuple[str, float], ...] = (
    (r"\b(?:txn|trn|ref)[:\s]*[a-z0-9]{8,20}\b", 0.90),
    (r"\b\d{12}\b", 0.60),
)

CURRENCY_PATTERNS: Tuple[str, ...] = (
    r"(?:rs|inr|₹)\s*[\d,]+(?:\s*(?:lakh|crore|k|thousand))?",
    r"\b\d[\d,]*(?:\s*(?:lakh|crore|k|thousand))?\s*(?:rs|inr|₹)",
    r"(?:\$|usd|eur|gbp)\s*[\d,]+(?:\.\d{2})?",
)

OTP_EXTRACT_PATTERNS: Tuple[Tuple[str, float, bool], ...] = (
    (r"\botp\s*(?::|-|is)?\s*(\d{4,8})\b", 0.92, True),
    (r"(?:code|pin)\s*(?::|-|is)?\s*(\d{4,8})\b", 0.80, True),
    (r"\b\d{4,8}\b", 0.60, False),
)

SOCIAL_HANDLE_PATTERNS: Tuple[Tuple[str, str, float], ...] = (
    (r"@[a-z0-9_]{3,30}\b", "social_handle", 0.85),
    (r"(?:t\.me|telegram)\s*(?:/|:)?\s*@?[a-z0-9_]+", "social_handle", 0.90),
)

URL_PATTERNS: Tuple[str, ...] = (
    r"https?://(?:[-\w.]|%[\da-fA-F]{2})+(?::\d+)?(?:/[^\s]*)?",
    r"(?<!//)\bwww\.[-\w.]+(?:\.[a-z]{2,})(?:/[^\s]*)?",
)
