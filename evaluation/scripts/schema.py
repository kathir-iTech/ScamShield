from typing import Any, Dict, List, Optional, Tuple


SAMPLE_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": [
        "id", "text", "expected_prediction", "expected_category",
        "expected_risk_level", "expected_decision_level",
        "expected_assessment_band", "difficulty", "language", "source_type",
    ],
    "properties": {
        "id": {"type": "string", "pattern": r"^[a-z0-9_-]+$"},
        "text": {"type": "string", "minLength": 1},
        "expected_prediction": {"type": "string", "enum": ["scam", "safe"]},
        "expected_category": {"type": "string"},
        "expected_risk_level": {
            "type": "string",
            "enum": ["CRITICAL", "HIGH", "MEDIUM", "LOW", "VERY LOW"],
        },
        "expected_decision_level": {
            "type": "string",
            "enum": ["CRITICAL", "HIGH RISK", "SUSPICIOUS", "LOW RISK", "SAFE"],
        },
        "expected_assessment_band": {"type": "string"},
        "expected_entities": {
            "type": "array",
            "items": {"type": "string"},
        },
        "expected_confidence_min": {"type": "number", "minimum": 0, "maximum": 1},
        "expected_confidence_max": {"type": "number", "minimum": 0, "maximum": 1},
        "difficulty": {
            "type": "string",
            "enum": ["easy", "medium", "hard"],
        },
        "language": {"type": "string", "enum": ["en", "ta", "tangling"]},
        "source_type": {
            "type": "string",
            "enum": ["sms", "whatsapp", "email", "telegram", "social"],
        },
        "ground_truth_reason": {"type": "string"},
        "notes": {"type": "string"},
        "expected_action": {"type": "string"},
        "expected_priority": {"type": "string"},
    },
}

VALID_CATEGORIES: set = {
    "Bank KYC Scam", "UPI Scam", "Lottery Scam", "Investment Scam",
    "Courier Scam", "Job Scam", "Government Scheme Scam",
    "Electricity Bill Scam", "Customs Scam", "Loan Scam",
    "Fake Customer Care", "QR Code Scam", "Crypto Scam",
    "Phishing", "Account Suspension", "Subscription Scam",
    "OTP Scam", "Fake Support", "Legitimate", "Mixed",
}

FAMILY_CATEGORY_MAP: Dict[str, str] = {
    "Bank KYC Scam": "Financial Fraud",
    "UPI Scam": "Financial Fraud",
    "Loan Scam": "Financial Fraud",
    "Investment Scam": "Financial Fraud",
    "Crypto Scam": "Financial Fraud",
    "QR Code Scam": "Financial Fraud",
    "Account Suspension": "Financial Fraud",
    "OTP Scam": "Credential Theft",
    "Phishing": "Credential Theft",
    "Job Scam": "Credential Theft",
    "Government Scheme Scam": "Credential Theft",
    "Fake Customer Care": "Social Engineering",
    "Fake Support": "Social Engineering",
    "Courier Scam": "Social Engineering",
    "Customs Scam": "Social Engineering",
    "Lottery Scam": "Consumer Fraud",
    "Subscription Scam": "Consumer Fraud",
    "Electricity Bill Scam": "Consumer Fraud",
    "Legitimate": "Legitimate",
    "Mixed": "Financial Fraud",
}

SUBFAMILY_CATEGORY_MAP: Dict[str, str] = {
    "Bank KYC Scam": "Banking",
    "Account Suspension": "Banking",
    "OTP Scam": "OTP",
    "UPI Scam": "UPI",
    "QR Code Scam": "UPI",
    "Loan Scam": "Loan",
    "Investment Scam": "Investment",
    "Crypto Scam": "Crypto",
    "Phishing": "Fake Login",
    "Job Scam": "Identity Theft",
    "Government Scheme Scam": "Identity Theft",
    "Fake Customer Care": "Fake Support",
    "Fake Support": "Fake Support",
    "Courier Scam": "Delivery",
    "Customs Scam": "Customs",
    "Lottery Scam": "Lottery",
    "Subscription Scam": "Subscription",
    "Electricity Bill Scam": "Subscription",
    "Legitimate": "Safe",
    "Mixed": "General",
}

VALID_PREDICTIONS = {"scam", "safe"}
VALID_RISK_LEVELS = {"CRITICAL", "HIGH", "MEDIUM", "LOW", "VERY LOW"}
VALID_DECISION_LEVELS = {"CRITICAL", "HIGH RISK", "SUSPICIOUS", "LOW RISK", "SAFE"}
VALID_DIFFICULTIES = {"easy", "medium", "hard"}
VALID_LANGUAGES = {"en", "ta", "tangling"}
VALID_SOURCES = {"sms", "whatsapp", "email", "telegram", "social"}


INVESTIGATION_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": ["id", "artefacts", "expected_campaign", "expected_overall_risk", "expected_overall_score"],
    "properties": {
        "id": {"type": "string", "pattern": r"^[a-z0-9_-]+$"},
        "artefacts": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["text", "type"],
                "properties": {
                    "text": {"type": "string"},
                    "type": {"type": "string", "enum": ["sms", "screenshot", "whatsapp", "email", "telegram", "chat", "text"]},
                },
            },
            "minItems": 1,
        },
        "expected_campaign": {"type": "boolean"},
        "expected_overall_risk": {"type": "string", "enum": ["CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN"]},
        "expected_overall_score": {"type": "integer", "minimum": 0, "maximum": 100},
        "expected_timeline_events": {"type": "integer", "minimum": 0},
        "expected_merged_entities": {"type": "integer", "minimum": 0},
        "expected_cross_message_entities": {"type": "integer", "minimum": 0},
        "notes": {"type": "string"},
    },
}


def validate_investigation_sample(sample: Dict[str, Any]) -> List[str]:
    errors = []

    if not isinstance(sample.get("id"), str) or not sample["id"]:
        errors.append("Missing or invalid 'id'")

    artefacts = sample.get("artefacts", [])
    if not artefacts:
        errors.append(f"'{sample.get('id')}': investigation sample must have at least 1 artefact")
    for i, art in enumerate(artefacts):
        if not art.get("text", "").strip():
            errors.append(f"'{sample.get('id')}': artefact {i} has empty text")
        art_type = art.get("type", "text")
        if art_type not in {"sms", "screenshot", "whatsapp", "email", "telegram", "chat", "text"}:
            errors.append(f"'{sample.get('id')}': artefact {i} has invalid type '{art_type}'")

    campaign = sample.get("expected_campaign")
    if not isinstance(campaign, bool):
        errors.append(f"'{sample.get('id')}': expected_campaign must be boolean")

    risk = sample.get("expected_overall_risk")
    if risk not in {"CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN"}:
        errors.append(f"'{sample.get('id')}': expected_overall_risk must be one of CRITICAL/HIGH/MEDIUM/LOW/UNKNOWN")

    score = sample.get("expected_overall_score")
    if not isinstance(score, int) or not (0 <= score <= 100):
        errors.append(f"'{sample.get('id')}': expected_overall_score must be int 0-100")

    return errors


def validate_sample(sample: Dict[str, Any]) -> List[str]:
    errors = []

    if not isinstance(sample.get("id"), str) or not sample["id"]:
        errors.append("Missing or invalid 'id'")

    if not isinstance(sample.get("text"), str) or not sample["text"].strip():
        errors.append(f"Missing or empty 'text' in sample {sample.get('id', '?')}")

    pred = sample.get("expected_prediction")
    if pred not in VALID_PREDICTIONS:
        errors.append(f"'{sample.get('id')}': expected_prediction must be scame/safe, got '{pred}'")

    cat = sample.get("expected_category", "")
    if cat not in VALID_CATEGORIES:
        errors.append(f"'{sample.get('id')}': unknown category '{cat}'")

    risk = sample.get("expected_risk_level")
    if risk not in VALID_RISK_LEVELS:
        errors.append(f"'{sample.get('id')}': invalid risk level '{risk}'")

    dec = sample.get("expected_decision_level")
    if dec not in VALID_DECISION_LEVELS:
        errors.append(f"'{sample.get('id')}': invalid decision level '{dec}'")

    diff = sample.get("difficulty")
    if diff not in VALID_DIFFICULTIES:
        errors.append(f"'{sample.get('id')}': invalid difficulty '{diff}'")

    lang = sample.get("language")
    if lang not in VALID_LANGUAGES:
        errors.append(f"'{sample.get('id')}': invalid language '{lang}'")

    src = sample.get("source_type")
    if src not in VALID_SOURCES:
        errors.append(f"'{sample.get('id')}': invalid source_type '{src}'")

    conf_min = sample.get("expected_confidence_min")
    conf_max = sample.get("expected_confidence_max")
    if conf_min is not None and conf_max is not None:
        if not (0 <= conf_min <= conf_max <= 1):
            errors.append(f"'{sample.get('id')}': confidence range invalid ({conf_min}-{conf_max})")

    return errors


def validate_dataset(samples: List[Dict[str, Any]]) -> Tuple[bool, List[str], Dict[str, List[str]]]:
    all_errors = []
    per_sample: Dict[str, List[str]] = {}
    ids: set = set()
    duplicates: List[str] = []

    for sample in samples:
        sid = sample.get("id", "?")
        if sid in ids:
            duplicates.append(sid)
        ids.add(sid)

        errs = validate_sample(sample)
        if errs:
            per_sample[sid] = errs
            all_errors.extend(errs)

    if duplicates:
        all_errors.append(f"Duplicate IDs: {duplicates}")

    return len(all_errors) == 0, all_errors, per_sample
