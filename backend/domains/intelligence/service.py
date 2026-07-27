from typing import Any, Dict, List

from core.constants import ENTITY_RISK_MAP, INTELLIGENCE_INDICATOR_MAP, RISK_LOW, UNKNOWN_CATEGORY

from .extractors import (
    extract_bank_accounts,
    extract_bank_names,
    extract_currency_amounts,
    extract_domains,
    extract_emails,
    extract_government_entities,
    extract_ifsc_codes,
    extract_ip_addresses,
    extract_otp_codes,
    extract_phones,
    extract_qr_keywords,
    extract_shortened_urls,
    extract_social_handles,
    extract_suspicious_tlds,
    extract_tracking_ids,
    extract_transaction_ids,
    extract_upi_ids,
    extract_urls,
)


def analyze(text: str, ocr_metadata: dict = None) -> Dict:
    all_entities: List[Dict] = []
    all_entities.extend(extract_urls(text))
    all_entities.extend(extract_domains(text))
    all_entities.extend(extract_emails(text))
    all_entities.extend(extract_phones(text))
    all_entities.extend(extract_upi_ids(text))
    all_entities.extend(extract_qr_keywords(text))
    all_entities.extend(extract_bank_names(text))
    all_entities.extend(extract_government_entities(text))
    all_entities.extend(extract_currency_amounts(text))
    all_entities.extend(extract_otp_codes(text))
    all_entities.extend(extract_ip_addresses(text))
    all_entities.extend(extract_social_handles(text))
    all_entities.extend(extract_ifsc_codes(text))
    all_entities.extend(extract_bank_accounts(text))
    all_entities.extend(extract_tracking_ids(text))
    all_entities.extend(extract_transaction_ids(text))

    seen_values = set()
    deduped: List[Dict] = []
    for e in all_entities:
        key = e["value"].lower() + "|" + e["type"]
        if key not in seen_values:
            seen_values.add(key)
            if "risk" not in e:
                risk_info = ENTITY_RISK_MAP.get(e["type"], {"risk": RISK_LOW.upper(), "reason": "Unknown entity type"})
                e["risk"] = risk_info["risk"]
                e["risk_reason"] = risk_info["reason"]
            deduped.append(e)

    by_type: Dict[str, int] = {}
    threat_indicators: List[str] = []
    risk_entities: Dict[str, List[Dict]] = {}

    for e in deduped:
        etype = e["type"]
        by_type[etype] = by_type.get(etype, 0) + 1
        risk = e.get("risk", RISK_LOW.upper())
        risk_entities.setdefault(risk.lower(), []).append(e)

    for e in deduped:
        label = INTELLIGENCE_INDICATOR_MAP.get(e["type"])
        if label and label not in threat_indicators and e.get("risk") in ("HIGH", "MEDIUM"):
            threat_indicators.append(label)

    return {
        "entities": deduped,
        "entity_summary": {
            "total_entities": len(deduped),
            "by_type": by_type,
            "threat_indicators": threat_indicators,
        },
        "entity_risk": {
            "high": risk_entities.get("high", []),
            "medium": risk_entities.get("medium", []),
            "low": risk_entities.get("low", []),
        },
    }
