from typing import Any, Dict, List

from core.constants import UNKNOWN_CATEGORY

from .models import InvestigationArtefact


def _compute_global_risk(
    artefacts: List[InvestigationArtefact],
    merged: Dict[str, List[Dict]],
    repeated: Dict[str, int],
    campaign: Dict,
) -> Dict:
    if not artefacts:
        return {
            "overall_risk": "UNKNOWN",
            "overall_score": 0,
            "confidence": 0.0,
            "dominant_family": "",
            "strongest_evidence": [],
            "weakest_signals": [],
            "open_questions": [],
        }

    scores = [a.analysis.get("assessment_score", 0) for a in artefacts]
    confidences = [a.analysis.get("confidence", 0.0) for a in artefacts]
    predictions = [a.analysis.get("prediction", "safe") for a in artefacts]
    families = [a.analysis.get("reasoning_family", "") for a in artefacts]

    max_score = max(scores) if scores else 0
    avg_score = sum(scores) / len(scores) if scores else 0
    has_scam = "scam" in predictions

    if has_scam:
        scam_scores = [s for s, p in zip(scores, predictions) if p == "scam"]
        peak_score = max(scam_scores) if scam_scores else max_score
    else:
        peak_score = max_score

    high_risk_entities = sum(
        1 for entity_list in merged.values()
        for e in entity_list if e.get("max_risk") == "HIGH"
    )
    repeated_count = sum(repeated.values())
    campaign_boost = 0.15 if campaign.get("campaign_detected") else 0.0

    overall_score = min(int(peak_score * 0.6 + avg_score * 0.4 + campaign_boost * 100), 100)
    if repeated_count >= 3:
        overall_score = min(overall_score + 5, 100)
    if high_risk_entities >= 3:
        overall_score = min(overall_score + 5, 100)

    if overall_score >= 76:
        overall_risk = "CRITICAL"
    elif overall_score >= 51:
        overall_risk = "HIGH"
    elif overall_score >= 21:
        overall_risk = "MEDIUM"
    else:
        overall_risk = "LOW"

    confidence = max(confidences) if confidences else 0.0
    confidence = min(confidence + campaign_boost, 1.0)
    if len(artefacts) == 1:
        confidence *= 0.9

    dominant_family = max(set(families), key=families.count) if families else ""

    strongest = []
    for art in artefacts:
        if art.analysis.get("assessment_score", 0) >= 51:
            cat = art.analysis.get("scam_category", UNKNOWN_CATEGORY)
            strongest.append(f"Artefact #{art.index + 1}: {cat} (score: {art.analysis.get('assessment_score', 0)})")
    if campaign.get("campaign_detected"):
        strongest.append(f"Campaign detected across {len(artefacts)} artefacts")

    weakest = []
    for art in artefacts:
        if art.analysis.get("prediction") == "safe" and art.analysis.get("assessment_score", 0) < 21:
            weakest.append(f"Artefact #{art.index + 1}: appears benign (score: {art.analysis.get('assessment_score', 0)})")

    questions = []
    if campaign.get("campaign_detected"):
        questions.append("Verify if the shared entities belong to the same threat actor")
    high_risk_phones = [
        e["value"] for e in merged.get("phone", []) if e.get("max_risk") == "HIGH"
    ]
    if high_risk_phones:
        questions.append(f"Investigate phone number{'s' if len(high_risk_phones) > 1 else ''}: {', '.join(high_risk_phones[:2])}")

    return {
        "overall_risk": overall_risk,
        "overall_score": overall_score,
        "confidence": round(confidence, 3),
        "dominant_family": dominant_family,
        "peak_single_score": max_score,
        "average_score": round(avg_score, 1),
        "highest_risk_artefact": max(range(len(artefacts)), key=lambda i: artefacts[i].analysis.get("assessment_score", 0)) if artefacts else -1,
        "strongest_evidence": strongest[:5],
        "weakest_signals": weakest[:5],
        "open_questions": questions[:5],
    }
