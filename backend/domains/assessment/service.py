from typing import Dict

from core.constants import (
    ACTION_BLOCK_REPORT,
    ACTION_DO_NOT_INTERACT,
    ACTION_IGNORE,
    ACTION_MONITOR,
    ACTION_VERIFY,
    ASSESSMENT_IMMEDIATE_ACTION,
    ASSESSMENT_INVESTIGATION,
    ASSESSMENT_NORMAL,
    ASSESSMENT_REVIEW,
    CONFIDENCE_HIGH,
    CONFIDENCE_LOW,
    CONFIDENCE_MEDIUM,
    DECISION_SAFE,
    ML_LABEL_SAFE,
    ML_LABEL_SCAM,
    RISK_LOW,
    UNKNOWN_CATEGORY,
)
from config.settings import (
    ASSESSMENT_CONFLICT_PENALTY,
    ASSESSMENT_DECISION_WEIGHT,
    ASSESSMENT_ENTITY_WEIGHT,
    ASSESSMENT_EVIDENCE_HIGH_CAP,
    ASSESSMENT_EVIDENCE_HIGH_POINTS,
    ASSESSMENT_EVIDENCE_MED_CAP,
    ASSESSMENT_EVIDENCE_MED_POINTS,
    ASSESSMENT_EVIDENCE_WEIGHT,
    ASSESSMENT_INDICATOR_WEIGHT,
    ASSESSMENT_MANUAL_REVIEW_CONFIDENCE_THRESHOLD,
    ASSESSMENT_MAX_CONFLICT_PENALTY,
    ASSESSMENT_MAX_DECISION_POINTS,
    ASSESSMENT_MAX_ENTITY_POINTS,
    ASSESSMENT_MAX_EVIDENCE_POINTS,
    ASSESSMENT_MAX_INDICATOR_POINTS,
    ASSESSMENT_MAX_ML_POINTS,
    ASSESSMENT_MAX_SCORE,
    ASSESSMENT_ML_WEIGHT,
    HIGH_CONFIDENCE_THRESHOLD,
    MEDIUM_CONFIDENCE_THRESHOLD,
)


def assess(analysis: dict) -> Dict:
    prediction = analysis.get("prediction", ML_LABEL_SAFE)
    confidence = analysis.get("confidence", 0.0)
    decision_score = analysis.get("decision_score", 0)
    decision_level = analysis.get("decision_level", DECISION_SAFE)
    rule_label = analysis.get("rule_label", "low")
    rule_score = analysis.get("rule_score", 0)
    indicators = analysis.get("detected_indicators", [])
    category = analysis.get("scam_category", UNKNOWN_CATEGORY)
    entity_risk = analysis.get("entity_risk", {})
    entity_summary = analysis.get("entity_summary", {})
    supporting_evidence = analysis.get("supporting_evidence", [])
    conflicting_evidence = analysis.get("conflicting_evidence", [])
    evidence_conf_breakdown = analysis.get("confidence_breakdown", {})

    if prediction == ML_LABEL_SCAM:
        ml_points = round(ASSESSMENT_MAX_ML_POINTS * confidence)
    else:
        ml_points = round(ASSESSMENT_MAX_ML_POINTS * (1 - confidence))
    ml_points = min(ml_points, ASSESSMENT_MAX_ML_POINTS)

    if prediction == ML_LABEL_SCAM and confidence < MEDIUM_CONFIDENCE_THRESHOLD:
        if not indicators and rule_label == RISK_LOW and not entity_risk.get("high"):
            ml_points = round(ml_points * 0.3)

    decision_points = round(ASSESSMENT_MAX_DECISION_POINTS * (decision_score / 100))

    high_count = sum(1 for e in supporting_evidence if e.get("severity") == "HIGH")
    med_count = sum(1 for e in supporting_evidence if e.get("severity") == "MEDIUM")
    evidence_points = min(high_count * ASSESSMENT_EVIDENCE_HIGH_POINTS, ASSESSMENT_EVIDENCE_HIGH_CAP) + min(med_count * ASSESSMENT_EVIDENCE_MED_POINTS, ASSESSMENT_EVIDENCE_MED_CAP)
    evidence_points = min(evidence_points, ASSESSMENT_MAX_EVIDENCE_POINTS)

    indicator_count = len(indicators)
    if indicator_count >= 4:
        indicator_points = ASSESSMENT_MAX_INDICATOR_POINTS
    elif indicator_count == 3:
        indicator_points = 9
    elif indicator_count == 2:
        indicator_points = 7
    elif indicator_count == 1:
        indicator_points = 4
    else:
        indicator_points = 0

    high_entities = entity_risk.get("high", [])
    med_entities = entity_risk.get("medium", [])
    entity_points = min(len(high_entities) * 3, 6) + min(len(med_entities) * 2, 4)
    entity_points = min(entity_points, ASSESSMENT_MAX_ENTITY_POINTS)

    conflict_count = len(conflicting_evidence)
    conflict_penalty = min(conflict_count * 3, ASSESSMENT_MAX_CONFLICT_PENALTY)

    assessment_score = ml_points + decision_points + evidence_points + indicator_points + entity_points - conflict_penalty
    assessment_score = max(0, min(assessment_score, ASSESSMENT_MAX_SCORE))

    if assessment_score >= 76:
        assessment_band = ASSESSMENT_IMMEDIATE_ACTION
    elif assessment_score >= 51:
        assessment_band = ASSESSMENT_INVESTIGATION
    elif assessment_score >= 21:
        assessment_band = ASSESSMENT_REVIEW
    else:
        assessment_band = ASSESSMENT_NORMAL

    overall_conf = evidence_conf_breakdown.get("overall", 50)
    has_conflict = conflict_count > 0

    if confidence > HIGH_CONFIDENCE_THRESHOLD and overall_conf >= 60 and not has_conflict:
        assessment_confidence = CONFIDENCE_HIGH
    elif confidence > MEDIUM_CONFIDENCE_THRESHOLD or overall_conf >= 40:
        assessment_confidence = CONFIDENCE_MEDIUM
    else:
        assessment_confidence = CONFIDENCE_LOW

    review_required = False
    manual_review_reason = ""

    if has_conflict and confidence > ASSESSMENT_MANUAL_REVIEW_CONFIDENCE_THRESHOLD:
        review_required = True
        manual_review_reason = "High ML confidence but conflicting evidence from rules or entity analysis."
    elif category == UNKNOWN_CATEGORY and assessment_score >= 21:
        review_required = True
        manual_review_reason = "Message flagged but could not be categorized into a known scam type."
    elif assessment_confidence == CONFIDENCE_LOW and assessment_score >= 21:
        review_required = True
        manual_review_reason = "Low assessment confidence despite elevated risk score."
    elif prediction == ML_LABEL_SCAM and rule_label == RISK_LOW and confidence < MEDIUM_CONFIDENCE_THRESHOLD:
        review_required = True
        manual_review_reason = "ML classification lacks confidence and rule engine found no corroborating evidence."

    business_reason = _business_reason(assessment_band, category, prediction, assessment_score)
    technical_reason = _technical_reason(
        ml_points, decision_points, evidence_points, indicator_points,
        entity_points, conflict_penalty, high_count, indicator_count,
    )
    recommended_action = _recommended_action(assessment_score, prediction, rule_label)

    if assessment_score >= 76:
        summary = f"Urgent: {category}. Immediate action required to prevent potential harm."
    elif assessment_score >= 51:
        summary = f"Investigate: {category}. Strong indicators warrant security investigation."
    elif assessment_score >= 21:
        summary = f"Review: {category}. Some suspicious signals detected."
    else:
        summary = f"Clear: Message appears benign. No action needed."

    return {
        "assessment_score": assessment_score,
        "assessment_band": assessment_band,
        "assessment_confidence": assessment_confidence,
        "assessment_summary": summary,
        "business_reason": business_reason,
        "technical_reason": technical_reason,
        "recommended_action": recommended_action,
        "review_required": review_required,
        "manual_review_reason": manual_review_reason,
    }


def _business_reason(band: str, category: str, prediction: str, score: int) -> str:
    if score >= 76:
        return f"This message is part of a {category.lower()} and poses an immediate threat to your security or finances."
    if score >= 51:
        return f"Multiple scam indicators suggest this message may be a {category.lower()} targeting you."
    if score >= 21:
        return f"Some suspicious elements were detected that may indicate a {category.lower()}, but the evidence is not conclusive."
    return "This message appears to be legitimate communication with no signs of fraud."


def _technical_reason(
    ml_pts: int, decision_pts: int, evidence_pts: int,
    indicator_pts: int, entity_pts: int, conflict_penalty: int,
    high_evidence: int, indicator_count: int,
) -> str:
    parts = []
    if ml_pts > 15:
        parts.append(f"ML model identifies scam patterns (contributed {ml_pts}/{ASSESSMENT_MAX_ML_POINTS})")
    if decision_pts > 15:
        parts.append(f"evidence correlation score is elevated ({decision_pts}/{ASSESSMENT_MAX_DECISION_POINTS})")
    if evidence_pts > 10:
        parts.append(f"{high_evidence} high-severity evidence items detected ({evidence_pts}/{ASSESSMENT_MAX_EVIDENCE_POINTS})")
    if indicator_count >= 3:
        parts.append(f"{indicator_count} distinct threat categories identified ({indicator_pts}/{ASSESSMENT_MAX_INDICATOR_POINTS})")
    if entity_pts > 5:
        parts.append(f"concrete risk entities extracted from message ({entity_pts}/{ASSESSMENT_MAX_ENTITY_POINTS})")
    if conflict_penalty > 0:
        parts.append(f"conflicting signals reduced score by {conflict_penalty} points")

    if parts:
        return "Assessment based on " + "; ".join(parts) + "."
    return "No significant technical indicators detected."


def _recommended_action(score: int, prediction: str, rule_label: str) -> str:
    if score >= 91:
        return ACTION_BLOCK_REPORT
    if score >= 76:
        return ACTION_DO_NOT_INTERACT
    if score >= 51:
        return ACTION_VERIFY
    if score >= 21:
        return ACTION_MONITOR
    return ACTION_IGNORE
