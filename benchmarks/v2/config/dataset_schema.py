import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple, Set

VALID_CATEGORIES: Set[str] = {
    "UPI_FRAUD", "BANKING_FRAUD", "KYC_SCAM", "AADHAAR_SCAM", "PAN_SCAM",
    "FAKE_CUSTOMER_CARE", "COURIER_SCAM", "ELECTRICITY_BILL_SCAM", "QR_SCAM",
    "LOTTERY_SCAM", "INVESTMENT_SCAM", "CRYPTO_SCAM", "LOAN_SCAM", "JOB_SCAM",
    "ROMANCE_SCAM", "GOVERNMENT_IMPERSONATION", "DIGITAL_ARREST",
    "INCOME_TAX_SCAM", "TELECOM_SCAM",
    "LEGITIMATE_BANKING", "LEGITIMATE_UPI", "LEGITIMATE_OTP",
    "LEGITIMATE_COURIER", "LEGITIMATE_GOVERNMENT", "LEGITIMATE_OTHER"
}

SCAM_CATEGORIES: Set[str] = {
    "UPI_FRAUD", "BANKING_FRAUD", "KYC_SCAM", "AADHAAR_SCAM", "PAN_SCAM",
    "FAKE_CUSTOMER_CARE", "COURIER_SCAM", "ELECTRICITY_BILL_SCAM", "QR_SCAM",
    "LOTTERY_SCAM", "INVESTMENT_SCAM", "CRYPTO_SCAM", "LOAN_SCAM", "JOB_SCAM",
    "ROMANCE_SCAM", "GOVERNMENT_IMPERSONATION", "DIGITAL_ARREST",
    "INCOME_TAX_SCAM", "TELECOM_SCAM"
}

LEGIT_CATEGORIES: Set[str] = {
    "LEGITIMATE_BANKING", "LEGITIMATE_UPI", "LEGITIMATE_OTP",
    "LEGITIMATE_COURIER", "LEGITIMATE_GOVERNMENT", "LEGITIMATE_OTHER"
}

VALID_LANGUAGES: Set[str] = {
    "en", "hi", "ta", "te", "kn", "ml", "bn", "mr", "gu", "hi-en", "tangling"
}

VALID_RISK_LEVELS: Set[str] = {"CRITICAL", "HIGH", "MEDIUM", "LOW", "NONE"}

VALID_SOURCES: Set[str] = {
    "synthetic", "manual", "cert-in", "rbi", "ncpc", "public_dataset", "academic"
}

SAMPLE_SCHEMA: Dict[str, Dict[str, Any]] = {
    "id": {"type": str, "required": True, "description": "Unique sample identifier"},
    "text": {"type": str, "required": True, "description": "Original message text"},
    "text_clean": {"type": str, "required": True, "description": "Cleaned/normalized text"},
    "language": {"type": str, "required": True, "description": "Language code from VALID_LANGUAGES"},
    "category": {"type": str, "required": True, "description": "Category from VALID_CATEGORIES"},
    "is_scam": {"type": bool, "required": True, "description": "Whether the message is a scam"},
    "risk_level": {"type": str, "required": True, "description": "Risk level from VALID_RISK_LEVELS"},
    "extracted_entities": {
        "type": dict, "required": True,
        "description": "Extracted entities from the message",
        "fields": {
            "urls": {"type": list, "description": "List of URLs found"},
            "phones": {"type": list, "description": "List of phone numbers"},
            "upi_ids": {"type": list, "description": "List of UPI IDs"},
            "banks": {"type": list, "description": "List of bank names mentioned"},
            "emails": {"type": list, "description": "List of email addresses"},
            "aadhaar": {"type": list, "description": "List of Aadhaar numbers"},
            "pan": {"type": list, "description": "List of PAN numbers"}
        }
    },
    "ground_truth_label": {"type": str, "required": True, "description": "Ground truth: scam or legitimate"},
    "source": {"type": str, "required": True, "description": "Data source from VALID_SOURCES"},
    "annotation_notes": {"type": str, "required": True, "description": "Notes about the annotation"},
    "annotator_id": {"type": str, "required": False, "description": "Annotator identifier"},
    "version": {"type": str, "required": True, "description": "Dataset schema version"},
    "created_at": {"type": str, "required": True, "description": "ISO datetime of creation"},
    "updated_at": {"type": str, "required": True, "description": "ISO datetime of last update"}
}


def _check_type(value: Any, expected_type: type, field_name: str) -> List[str]:
    errors: List[str] = []
    if not isinstance(value, expected_type):
        errors.append(f"{field_name}: expected {expected_type.__name__}, got {type(value).__name__}")
    return errors


def validate_sample(sample: Dict[str, Any]) -> List[str]:
    errors: List[str] = []

    for field_name, schema in SAMPLE_SCHEMA.items():
        present = field_name in sample
        is_required = schema.get("required", False)

        if is_required and not present:
            errors.append(f"{field_name}: missing required field")
            continue

        if not present:
            continue

        value = sample[field_name]
        expected_type = schema["type"]

        type_errors = _check_type(value, expected_type, field_name)
        errors.extend(type_errors)

        if type_errors:
            continue

        if field_name == "language" and value not in VALID_LANGUAGES:
            errors.append(f"language: '{value}' not in VALID_LANGUAGES")
        elif field_name == "category" and value not in VALID_CATEGORIES:
            errors.append(f"category: '{value}' not in VALID_CATEGORIES")
        elif field_name == "risk_level" and value not in VALID_RISK_LEVELS:
            errors.append(f"risk_level: '{value}' not in VALID_RISK_LEVELS")
        elif field_name == "source" and value not in VALID_SOURCES:
            errors.append(f"source: '{value}' not in VALID_SOURCES")
        elif field_name == "ground_truth_label" and value not in ("scam", "legitimate"):
            errors.append(f"ground_truth_label: '{value}' not in ('scam', 'legitimate')")
        elif field_name == "is_scam" and not isinstance(value, bool):
            errors.append(f"is_scam: expected bool, got {type(value).__name__}")
        elif field_name == "extracted_entities":
            if not isinstance(value, dict):
                errors.append("extracted_entities: expected dict")
            else:
                expected_entity_fields = {"urls", "phones", "upi_ids", "banks", "emails", "aadhaar", "pan"}
                for ef in expected_entity_fields:
                    if ef not in value:
                        errors.append(f"extracted_entities.{ef}: missing field")
                    elif not isinstance(value[ef], list):
                        errors.append(f"extracted_entities.{ef}: expected list")

    return errors


def validate_dataset(samples: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
    all_errors: List[str] = []

    if not samples:
        return False, ["dataset is empty"]

    for i, sample in enumerate(samples):
        sample_errors = validate_sample(sample)
        for err in sample_errors:
            all_errors.append(f"[sample {i}] {err}")

    return len(all_errors) == 0, all_errors


def generate_sample_id(category: str, index: int) -> str:
    prefix = category.lower()[:4].replace("_", "")
    ts = datetime.now(timezone.utc).strftime("%y%m%d%H%M%S")
    uid = uuid.uuid4().hex[:6]
    return f"{prefix}_{ts}_{index:06d}_{uid}"
