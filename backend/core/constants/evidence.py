__all__ = [
    "EVIDENCE_CORRELATIONS",
    "EVIDENCE_TYPE_ML", "EVIDENCE_TYPE_RULE", "EVIDENCE_TYPE_RULE_INDICATOR",
    "EVIDENCE_TYPE_INDICATOR", "EVIDENCE_TYPE_ENTITY_HIGH", "EVIDENCE_TYPE_ENTITY_MEDIUM",
    "EVIDENCE_TYPE_ENTITY_VOLUME", "EVIDENCE_TYPE_THREAT_INDICATOR", "EVIDENCE_TYPE_CORRELATION",
    "EVIDENCE_TYPE_CONFLICT",
    "EVIDENCE_SOURCE_ML", "EVIDENCE_SOURCE_RULES", "EVIDENCE_SOURCE_EXPLANATION",
    "EVIDENCE_SOURCE_INTEL", "EVIDENCE_SOURCE_EVIDENCE",
    "RISK_TYPES", "RISK_DIMENSION_LABELS",
]

from typing import Dict, FrozenSet

EVIDENCE_CORRELATIONS: Dict[str, Dict] = {
    "credential_theft": {
        "label": "Credential Theft",
        "required": {"OTP Request", "KYC Update Request"},
        "optional": {"Bank Impersonation", "Suspicious URL", "Shortened URL", "Account Threat"},
        "min_optional": 1,
        "description": "Message targets banking credentials through OTP and KYC manipulation",
    },
    "payment_fraud": {
        "label": "Payment Fraud",
        "required": {"Payment Request"},
        "optional": {"UPI ID", "Shortened URL", "Suspicious URL", "Payment App Mention", "QR Code Request"},
        "min_optional": 1,
        "description": "Message directs victim to make payments through fraudulent channels",
    },
    "delivery_scam": {
        "label": "Delivery Scam",
        "required": {"Courier/Customs Mention"},
        "optional": {"Payment Request", "Suspicious URL", "Urgency Language", "Phone Number"},
        "min_optional": 1,
        "description": "Message impersonates courier or customs to extract advance fees",
    },
    "phishing": {
        "label": "Phishing",
        "required": {"Suspicious URL"},
        "optional": {"Government Impersonation", "Bank Impersonation", "KYC Update Request", "Urgency Language"},
        "min_optional": 1,
        "description": "Message uses a deceptive link to steal credentials or personal data",
    },
    "financial_scam": {
        "label": "Financial Scam",
        "required": {"Investment Offer"},
        "optional": {"Cryptocurrency Mention", "Urgency Language", "Social Handle", "Email Address"},
        "min_optional": 1,
        "description": "Message promotes fraudulent investment or cryptocurrency schemes",
    },
    "employment_fraud": {
        "label": "Employment Fraud",
        "required": {"Job Offer"},
        "optional": {"Payment Request", "Email Address", "Phone Number", "Urgency Language"},
        "min_optional": 1,
        "description": "Message offers fake employment opportunities to collect fees or data",
    },
    "identity_theft": {
        "label": "Identity Theft",
        "required": {"KYC Update Request"},
        "optional": {"Suspicious URL", "Account Threat", "Government Impersonation", "OTP Request"},
        "min_optional": 1,
        "description": "Message attempts to collect Aadhaar, PAN or other identity documents",
    },
    "advance_fee_fraud": {
        "label": "Advance Fee Fraud",
        "required": {"Prize/Lottery Mention", "Payment Request"},
        "optional": {"Phone Number", "Urgency Language", "Email Address"},
        "min_optional": 0,
        "description": "Message promises a prize or reward in exchange for an upfront payment",
    },
    "utility_fraud": {
        "label": "Utility Fraud",
        "required": {"Utility Bill Mention"},
        "optional": {"Payment Request", "Account Threat", "Suspicious URL", "Urgency Language"},
        "min_optional": 1,
        "description": "Message impersonates a utility provider demanding immediate payment",
    },
    "tech_support_fraud": {
        "label": "Tech Support Fraud",
        "required": {"Customer Care Impersonation"},
        "optional": {"Account Threat", "Phone Number", "Urgency Language"},
        "min_optional": 0,
        "description": "Message impersonates customer support to gain remote access or credentials",
    },
}

EVIDENCE_TYPE_ML: str = "ml_prediction"
EVIDENCE_TYPE_RULE: str = "rule_score"
EVIDENCE_TYPE_RULE_INDICATOR: str = "rule_indicator"
EVIDENCE_TYPE_INDICATOR: str = "indicator"
EVIDENCE_TYPE_ENTITY_HIGH: str = "entity_high"
EVIDENCE_TYPE_ENTITY_MEDIUM: str = "entity_medium"
EVIDENCE_TYPE_ENTITY_VOLUME: str = "entity_volume"
EVIDENCE_TYPE_THREAT_INDICATOR: str = "threat_indicator"
EVIDENCE_TYPE_CORRELATION: str = "correlation"
EVIDENCE_TYPE_CONFLICT: str = "conflict"

EVIDENCE_SOURCE_ML: str = "ml"
EVIDENCE_SOURCE_RULES: str = "rules"
EVIDENCE_SOURCE_EXPLANATION: str = "explanation"
EVIDENCE_SOURCE_INTEL: str = "intel"
EVIDENCE_SOURCE_EVIDENCE: str = "evidence"

RISK_TYPES: tuple = (
    "credential_theft",
    "financial_loss",
    "identity_theft",
    "malware",
    "social_engineering",
)

RISK_DIMENSION_LABELS: Dict[str, str] = {
    "credential_theft": "Credential Theft",
    "financial_loss": "Financial Theft",
    "identity_theft": "Identity Theft",
    "malware": "Malware",
    "social_engineering": "Social Engineering",
}
