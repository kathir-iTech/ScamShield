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
    (r"\b(?:share|send|forward|whatsapp)\s+(?:this|your|the|me|it|now)\s*(?:otp|code|password)|\b(?:otp|code)\s*(?:share|send|forward)\b|one\s*time\s*password\s+(?:share|send|forward)", "OTP Request"),
    (r"\burgent\b|immediately|asap|hurry|expir(?:es|ing)\b|act now|limited time|right away", "Urgency Language"),
    (r"https?://\S+", "Suspicious URL"),
    (r"\b(?:block|suspend|freeze|deactiv|disconnect)\w*\s*(?:ed|ing)?\s+(?:within|in|after|your)", "Account Threat"),
    (r"\bpay\s+(?:now|immediately|the|this|here)\b|\btransfer\s+(?:money|funds|amount)\b|\b(?:fee|fine|penalty)\s+(?:of\s+)?(?:rs|inr|₹)\s*\d+", "Payment Request"),
    (r"\b(?:sbi|hdfc|icici|axis|kotak|pnb|bank\s+of|rbi|sebi)\b.*\b(?:block|suspend|freeze|urgent|verify|update|share|send)\b|\b(?:block|suspend|freeze|urgent|verify|update|share|send)\b.*\b(?:sbi|hdfc|icici|axis|kotak|pnb|bank\s+of|rbi|sebi)\b", "Bank Impersonation"),
    (r"\bkyc\s+(?:update|verify|expire|pending|urgent)\b|\bverify\s+(?:your\s+)?(?:account|kyc|aadhaar|pan)\b|\bupdate\s+(?:your\s+)?(?:kyc|aadhaar|pan|bank)\b", "KYC Update Request"),
    (r"\b(?:lottery|won|winner|prize|jackpot)\b.*\b(?:claim|collect|transfer|pay|fee|register)\b|\bclaim\s+(?:your\s+)?(?:prize|lottery|reward|cashback)\b", "Prize/Lottery Mention"),
    (r"\bupi\s+(?:pin|password|otp)\b|\b(?:gpay|phonepe|paytm|bhim)\s+(?:pin|password|otp)\b", "Payment App Mention"),
    (r"\bloan\s+(?:approved|guaranteed|instant|apply|register)\b|\bemi\s+(?:pay|transfer|send)\b|\bcredit\s+card\s+(?:verify|update|share)", "Loan/EMI Mention"),
    (r"\bjob\s+(?:offer|guaranteed|apply|register|fee)\b|\bwork\s+from\s+home\s+(?:guaranteed|earn|income)\b", "Job Offer"),
    (r"\binvestment\s+(?:guaranteed|return|profit|earn)\b|\bguaranteed\s+(?:return|profit|income)\b", "Investment Offer"),
    (r"\b(?:customs|clearance)\s+(?:fee|pay|charge|release)\b|\bcourier\s+(?:fee|pay|charge|stuck|held)\b", "Courier/Customs Mention"),
    (r"\belectricity\s+(?:bill|disconnect|cut|suspend)\b|\b(?:tneb|disconnection)\s+(?:notice|fee|pay)\b", "Utility Bill Mention"),
    (r"\bpm\b|\bmodi\b|\bsarkari\b|\bgovernment\s+of\b|\bcentral\s+govt\b|\bnrega\b|\bayushman\b", "Government Impersonation"),
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
