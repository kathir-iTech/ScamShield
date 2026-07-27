import re
from typing import Dict, List, Optional, Tuple

TAMIL_UNICODE_RANGE: Tuple[int, int] = (0x0B80, 0x0BFF)

TAMIL_STOP_WORDS: frozenset = frozenset({
    "and", "or", "but", "not", "the", "a", "an", "is", "are", "was", "were",
    "be", "been", "being", "have", "has", "had", "do", "does", "did",
    "will", "would", "can", "could", "shall", "should", "may", "might",
    "this", "that", "these", "those", "i", "you", "he", "she", "it", "we", "they",
    "me", "him", "her", "us", "them", "my", "your", "his", "its", "our", "their",
    "in", "on", "at", "to", "for", "with", "by", "from", "of", "about",
    "up", "out", "off", "over", "under", "again", "further", "then", "once",
    "here", "there", "when", "where", "why", "how", "all", "each", "every",
    "both", "few", "more", "most", "other", "some", "such", "no", "nor", "not",
    "only", "own", "same", "so", "than", "too", "very", "just", "because",
    "as", "until", "while", "if", "else",
})

TANGLISH_NORM_MAP: Dict[str, str] = {
    "unga": "your",
    "ungal": "your",
    "naan": "i",
    "namba": "our",
    "avan": "he",
    "aval": "she",
    "athu": "it",
    "ivanga": "they",
    "pannu": "do",
    "panni": "done",
    "pannunga": "please do",
    "panniko": "claim",
    "pannirukkom": "have done",
    "pannittu": "having done",
    "vaanga": "come",
    "ponga": "go",
    "solunga": "tell",
    "kudunga": "give",
    "vanga": "come",
    "irukku": "is there",
    "irukinga": "are",
    "aagum": "will happen",
    "aagirukku": "has happened",
    "aaga": "to become",
    "venum": "want",
    "venuma": "do you want",
    "vendum": "needed",
    "mudiyum": "possible",
    "mattum": "only",
    "maatrum": "only",
    "kuduthu": "given",
    "vangikunga": "get/receive",
    "sollunga": "tell",
    "paakunga": "see",
    "pannungo": "please do",
    "potu": "put",
    "eduthu": "taken",
    "vecha": "kept",
    "iruntha": "if was",
    "irunthalum": "even if",
    "illati": "otherwise",
    "illanna": "if not",
    "kudaathu": "should not",
    "mudiyathu": "not possible",
    "theriyum": "know",
    "theriyathu": "dont know",
    "sari": "okay",
    "sariya": "correctly",
    "nalla": "good",
    "nallathu": "good thing",
    "romba": "very",
    "konjam": "little",
    "sitha": "small",
    "periya": "big",
    "neraya": "many",
    "niraya": "many",
    "sila": "some",
    "ella": "all",
    "ellam": "everything",
    "epdi": "how",
    "eppadi": "how",
    "enga": "where",
    "enakku": "to me",
    "unakku": "to you",
    "avanukku": "to him",
    "namakku": "to us",
    "ennoda": "mine",
    "unnoda": "yours",
    "yaaru": "who",
    "edhu": "which",
    "enanna": "what",
    "yaen": "why",
    "yen": "why",
    "eppov": "when",
    "eppo": "when",
}

HINDI_NORM_MAP: Dict[str, str] = {
    "aap": "you",
    "hum": "we",
    "mera": "my",
    "tumhara": "your",
    "yojna": "scheme",
    "sarkari": "government",
    "sarkar": "government",
    "karein": "do",
    "kijiye": "please do",
    "paaye": "get",
    "mila": "got",
    "diya": "given",
    "liya": "taken",
    "rahe": "remaining",
    "ho": "are",
    "hai": "is",
    "hain": "are",
    "mein": "in",
    "ka": "of",
    "ki": "of",
    "ke": "of",
    "se": "from",
    "ko": "to",
    "par": "on",
    "nahi": "no",
    "aur": "and",
    "yeh": "this",
    "woh": "that",
    "bahut": "very",
    "thoda": "little",
    "abhi": "now",
    "aaj": "today",
    "kal": "yesterday/tomorrow",
    "rashi": "amount",
    "paisa": "money",
    "rupya": "rupees",
}


def detect_language(text: str) -> str:
    has_tamil = any(TAMIL_UNICODE_RANGE[0] <= ord(c) <= TAMIL_UNICODE_RANGE[1] for c in text)
    has_tanglish_words = any(w in TANGLISH_NORM_MAP for w in text.lower().split())
    has_hindi_words = any(w in HINDI_NORM_MAP for w in text.lower().split())

    if has_tamil:
        tamil_chars = sum(1 for c in text if TAMIL_UNICODE_RANGE[0] <= ord(c) <= TAMIL_UNICODE_RANGE[1])
        if tamil_chars > 3 or (tamil_chars / max(len(text), 1)) > 0.1:
            return "ta"
    if has_tanglish_words:
        return "tangling"
    if has_hindi_words:
        return "hi-en"
    return "en"


def normalize_tanglish(text: str) -> str:
    words = text.lower().split()
    normalized = []
    for word in words:
        clean = word.strip(".,!?;:'\"()[]{}/\\@#$%^&*+-=<>")
        if clean in TANGLISH_NORM_MAP:
            normalized.append(TANGLISH_NORM_MAP[clean])
        else:
            normalized.append(word)
    return " ".join(normalized)


def normalize_hindi_english(text: str) -> str:
    words = text.lower().split()
    normalized = []
    for word in words:
        clean = word.strip(".,!?;:'\"()[]{}/\\@#$%^&*+-=<>")
        if clean in HINDI_NORM_MAP:
            normalized.append(HINDI_NORM_MAP[clean])
        else:
            normalized.append(word)
    return " ".join(normalized)


def normalize_unicode(text: str) -> str:
    import unicodedata
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"[\u200c\u200d\u200e\u200f\ufeff]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def preprocess_multilingual(text: str) -> Tuple[str, str]:
    text = normalize_unicode(text)
    lang = detect_language(text)

    if lang == "ta":
        processed = text
    elif lang == "tangling":
        processed = normalize_tanglish(text)
    elif lang == "hi-en":
        processed = normalize_hindi_english(text)
    else:
        processed = text

    return processed, lang


def expand_scam_keywords_for_tamil() -> List[str]:
    return [
        # UPI/Payment related Tanglish
        "gpay", "phonepe", "paytm", "upi", "bhim",
        # Urgency/suspicious Tanglish
        "urgent", "immediately", "block", "suspend", "freeze", "deactivate",
        # KYC related Tanglish
        "kyc", "aadhaar", "aadhar", "update", "verify", "verification",
        # Threat language Tanglish
        "account", "bank", "sbi", "hdfc", "icici", "axis", "pnb",
        # Prize/lottery Tanglish
        "lottery", "winner", "prize", "cashback", "won",
        # Investment Tanglish
        "investment", "profit", "return", "earn", "income",
        # Job Tanglish
        "job", "salary", "work from home", "data entry", "part time",
        # Customs/delivery Tanglish
        "customs", "parcel", "courier", "delivery", "shipment",
        # Government Tanglish
        "subsidy", "scheme", "government", "pension",
        # OTP related Tanglish
        "otp", "share otp", "send otp",
    ]


def build_multilingual_indicator_patterns() -> List[Tuple[str, str, str]]:
    return [
        (r"\buk\b|bill\s+amount|payment\s+pending", "Utility Bill Mention", "ta"),
        (r"\btneb\b|current\s+bill|electricity\s+connection", "Utility Bill Mention", "ta"),
        (r"\bgas\s+(?:connection|subsidy|cylinder)\b|lpg\s+subsidy", "Government Scheme Scam", "ta"),
        (r"\bpmay\b|housing\s+scheme|house\s+subsidy", "Government Scheme Scam", "ta"),
        (r"\bmodi\b|pm\s+scheme\b|pradhan\s+mantri", "Government Scheme Scam", "ta"),
        (r"\bdisconnection\b|connection\s+(?:cut|removed)", "Utility Bill Mention", "ta"),
        (r"\bpension\b|old\s+age\s+(?:benefit|scheme)", "Government Scheme Scam", "ta"),
    ]
