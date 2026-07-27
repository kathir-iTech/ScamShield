from typing import Any, Dict, List

from core.constants import UNKNOWN_CATEGORY

from .models import CampaignIndicators, InvestigationArtefact


def _detect_campaign(artefacts: List[InvestigationArtefact], merged: Dict[str, List[Dict]]) -> Dict:
    if len(artefacts) < 2:
        return {
            "campaign_detected": False,
            "confidence": 0.0,
            "indicators": CampaignIndicators().__dict__,
            "summary": "Single artefact - campaign detection requires 2+ messages",
        }

    indicators = CampaignIndicators()
    shared_entity_count = 0

    phones = merged.get("phone", [])
    for p in phones:
        if p["occurrences"] >= 2:
            indicators.shared_phones.append(p["value"])
            shared_entity_count += 1

    domains = [e for e_type in ("url", "domain") for e in merged.get(e_type, [])]
    for d in domains:
        if d["occurrences"] >= 2:
            indicators.shared_domains.append(d["value"])
            shared_entity_count += 1

    upis = merged.get("upi_id", [])
    for u in upis:
        if u["occurrences"] >= 2:
            indicators.shared_upi.append(u["value"])
            shared_entity_count += 1

    emails = merged.get("email", [])
    for e in emails:
        if e["occurrences"] >= 2:
            indicators.shared_emails.append(e["value"])
            shared_entity_count += 1

    banks = merged.get("bank_name", [])
    banks += merged.get("ifsc_code", [])
    banks += merged.get("bank_account", [])
    seen_banks = set()
    for b in banks:
        if isinstance(b, dict):
            val = b.get("value", "")
            if val and val not in seen_banks:
                seen_banks.add(val)
                if b.get("occurrences", 0) >= 2:
                    indicators.shared_banks.append(val)
                    shared_entity_count += 1

    total_indicators = merged.get("indicator", [])
    for ind in merged.get("indicator", []):
        if ind.get("occurrences", 0) >= 2:
            indicators.shared_indicators.append(ind.get("value", ""))

    families = set()
    categories = set()
    for art in artefacts:
        families.add(art.analysis.get("reasoning_family", ""))
        categories.add(art.analysis.get("scam_category", UNKNOWN_CATEGORY))
    indicators.same_scam_family = len(families) == 1 and "" not in families

    if len(artefacts) >= 2:
        first_text = artefacts[0].text.lower() if artefacts else ""
        word_overlaps = 0
        for art in artefacts[1:]:
            words = set(art.text.lower().split())
            common = words & set(first_text.split())
            overlap_ratio = len(common) / max(len(words), 1)
            if overlap_ratio > 0.3:
                word_overlaps += 1
        indicators.repeated_wording = word_overlaps > 0

    campaign_score = 0.0
    if indicators.same_scam_family:
        campaign_score += 0.25
    if indicators.repeated_wording:
        campaign_score += 0.15
    if indicators.shared_phones:
        campaign_score += 0.2
    if indicators.shared_domains:
        campaign_score += 0.15
    if indicators.shared_upi:
        campaign_score += 0.2
    if indicators.shared_emails:
        campaign_score += 0.1
    if indicators.shared_banks:
        campaign_score += 0.15
    campaign_score += min(shared_entity_count * 0.05, 0.2)

    campaign_detected = campaign_score >= 0.3

    summary_parts = []
    if campaign_detected:
        summary_parts.append("Coordinated campaign detected")
    else:
        summary_parts.append("No coordinated campaign detected")
    if indicators.shared_phones:
        summary_parts.append(f"shared phone: {', '.join(indicators.shared_phones[:2])}")
    if indicators.shared_domains:
        summary_parts.append(f"shared domain: {', '.join(indicators.shared_domains[:2])}")
    if indicators.shared_upi:
        summary_parts.append(f"shared UPI: {', '.join(indicators.shared_upi[:2])}")
    if indicators.same_scam_family:
        summary_parts.append(f"consistent scam family across messages")

    return {
        "campaign_detected": campaign_detected,
        "confidence": round(min(campaign_score, 1.0), 3),
        "indicators": {
            "shared_phones": indicators.shared_phones,
            "shared_domains": indicators.shared_domains,
            "shared_upi": indicators.shared_upi,
            "shared_emails": indicators.shared_emails,
            "shared_banks": indicators.shared_banks,
            "shared_indicators": indicators.shared_indicators[:5],
            "repeated_wording": indicators.repeated_wording,
            "same_scam_family": indicators.same_scam_family,
        },
        "summary": ". ".join(summary_parts) + ".",
    }


def _build_investigation_summary(
    artefacts: List[InvestigationArtefact],
    merged: Dict[str, List[Dict]],
    repeated: Dict[str, int],
    campaign: Dict,
    global_risk: Dict,
) -> str:
    total = len(artefacts)
    scam_count = sum(1 for a in artefacts if a.analysis.get("prediction") == "scam")
    safe_count = total - scam_count
    merged_count = sum(len(v) for v in merged.values())
    repeated_indicator_count = sum(repeated.values())

    parts = [
        f"Investigation analysed {total} artefact(s): {scam_count} classified as scam, {safe_count} as safe."
    ]
    parts.append(f"Merged {merged_count} unique entities across artefacts.")
    if repeated:
        parts.append(f"Detected {repeated_indicator_count} repeated indicator(s) across {len(repeated)} type(s).")
    if campaign.get("campaign_detected"):
        parts.append(f"Coordinated campaign detected (confidence: {campaign['confidence']:.1%}).")
    parts.append(f"Overall risk: {global_risk.get('overall_risk', 'UNKNOWN')} (score: {global_risk.get('overall_score', 0)}).")
    return " ".join(parts)
