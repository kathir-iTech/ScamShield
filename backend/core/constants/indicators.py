__all__ = [
    "INDICATOR_PATTERNS", "HIGH_WEIGHT_KEYWORDS", "MEDIUM_WEIGHT_KEYWORDS",
    "INDICATOR_OTP_REQUEST", "INDICATOR_PAYMENT_REQUEST", "INDICATOR_ACCOUNT_THREAT",
    "INDICATOR_QR_CODE_REQUEST", "INDICATOR_BANK_IMPERSONATION", "INDICATOR_KYC_UPDATE",
    "INDICATOR_INVESTMENT_OFFER", "INDICATOR_COURIER_CUSTOMS", "INDICATOR_SUSPICIOUS_URL",
    "INDICATOR_SHORTENED_URL", "INDICATOR_URGENCY_LANGUAGE", "INDICATOR_PAYMENT_APP",
    "INDICATOR_LOAN_EMI", "INDICATOR_JOB_OFFER", "INDICATOR_PRIZE_LOTTERY",
    "INDICATOR_GOVT_IMPERSONATION", "INDICATOR_UTILITY_BILL", "INDICATOR_CRYPTO",
    "INDICATOR_CUSTOMER_CARE", "INDICATOR_EMAIL_ADDRESS", "INDICATOR_PHONE_NUMBER", "INDICATOR_UPI_ID",
    "CRITICAL_INDICATORS", "HIGH_RISK_INDICATORS", "HIGH_RISK_REASON_KEYWORDS",
]

from typing import FrozenSet, Tuple

INDICATOR_PATTERNS: Tuple[Tuple[str, str], ...] = (
    (r"\botp\b|one\s*time\s*password|verification\s*code", "OTP Request"),
    (r"\burgent\b|immediately|asap|hurry|expir(?:es|ing)\b|act now|limited time|right away", "Urgency Language"),
    (r"https?://\S+", "Suspicious URL"),
    (r"\b(?:block|suspend|freeze|deactiv|disconnect)\w*\s*(?:ed|ing)?", "Account Threat"),
    (r"\brs\b|inr|₹|money|payment|transfer|pay\s*(?:now|the|this)", "Payment Request"),
    (r"\b(?:sbi|hdfc|icici|axis|kotak|pnb|bank\s+of|rbi|sebi)\b", "Bank Impersonation"),
    (r"\bkyc\b|update.*kyc|verify.*account|confirm.*details|aadhaar", "KYC Update Request"),
    (r"\blottery|won\b|winner|prize|jackpot|cashback", "Prize/Lottery Mention"),
    (r"\bupi|gpay|phonepe|paytm|bhim\b|amazon\s*pay", "Payment App Mention"),
    (r"\bloan\b|emi\b|credit\s*(?:card|limit|score)", "Loan/EMI Mention"),
    (r"\bjob\b|work\s*(?:from\s*)?home|data\s*entry|part[- ]time|salary", "Job Offer"),
    (r"\binvestment|profit|guaranteed\s*return|earn\s*income", "Investment Offer"),
    (r"\bcustoms|clearance|release\s*fee|courier|parcel|shipment|import", "Courier/Customs Mention"),
    (r"\belectricity|bill\s*(?:due|pending|pay)|tneb|disconnection", "Utility Bill Mention"),
    (r"\bpm\b|modi|sarkari|government\s+of|central\s*govt|scheme|subsidy", "Government Impersonation"),
    (r"qr\s*code|scan\s*(?:the\s*)?(?:qr\s*)?code", "QR Code Request"),
    (r"\bbitcoin|crypto|cryptocurrency|blockchain|btc\b|eth\b", "Cryptocurrency Mention"),
    (r"customer\s*(?:care|support|service)|help\s*(?:desk|line)|toll\s*free|helpline", "Customer Care Impersonation"),
)

HIGH_WEIGHT_KEYWORDS: FrozenSet[str] = frozenset({
    "kyc", "aadhaar", "aadhar", "upi", "otp",
})

MEDIUM_WEIGHT_KEYWORDS: FrozenSet[str] = frozenset({
    "lottery", "won", "prize", "customs", "clearance",
})

INDICATOR_OTP_REQUEST: str = "OTP Request"
INDICATOR_PAYMENT_REQUEST: str = "Payment Request"
INDICATOR_ACCOUNT_THREAT: str = "Account Threat"
INDICATOR_QR_CODE_REQUEST: str = "QR Code Request"
INDICATOR_BANK_IMPERSONATION: str = "Bank Impersonation"
INDICATOR_KYC_UPDATE: str = "KYC Update Request"
INDICATOR_INVESTMENT_OFFER: str = "Investment Offer"
INDICATOR_COURIER_CUSTOMS: str = "Courier/Customs Mention"
INDICATOR_SUSPICIOUS_URL: str = "Suspicious URL"
INDICATOR_SHORTENED_URL: str = "Shortened URL"
INDICATOR_URGENCY_LANGUAGE: str = "Urgency Language"
INDICATOR_PAYMENT_APP: str = "Payment App Mention"
INDICATOR_LOAN_EMI: str = "Loan/EMI Mention"
INDICATOR_JOB_OFFER: str = "Job Offer"
INDICATOR_PRIZE_LOTTERY: str = "Prize/Lottery Mention"
INDICATOR_GOVT_IMPERSONATION: str = "Government Impersonation"
INDICATOR_UTILITY_BILL: str = "Utility Bill Mention"
INDICATOR_CRYPTO: str = "Cryptocurrency Mention"
INDICATOR_CUSTOMER_CARE: str = "Customer Care Impersonation"
INDICATOR_EMAIL_ADDRESS: str = "Email Address"
INDICATOR_PHONE_NUMBER: str = "Phone Number"
INDICATOR_UPI_ID: str = "UPI ID"

CRITICAL_INDICATORS: FrozenSet[str] = frozenset({
    INDICATOR_OTP_REQUEST,
    INDICATOR_PAYMENT_REQUEST,
    INDICATOR_ACCOUNT_THREAT,
    INDICATOR_QR_CODE_REQUEST,
})

HIGH_RISK_INDICATORS: FrozenSet[str] = frozenset({
    INDICATOR_BANK_IMPERSONATION,
    INDICATOR_KYC_UPDATE,
    INDICATOR_INVESTMENT_OFFER,
    INDICATOR_COURIER_CUSTOMS,
})

HIGH_RISK_REASON_KEYWORDS: FrozenSet[str] = frozenset({
    "otp", "share", "suspicious", "threat", "block", "suspend",
})
