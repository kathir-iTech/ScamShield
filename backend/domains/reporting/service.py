import uuid
from datetime import datetime, timezone
from typing import Dict

from core.constants import (
    ML_LABEL_SAFE,
    RISK_LOW,
    SEVERITY_VERY_LOW,
    TIMELINE_STAGES,
    UNKNOWN_CATEGORY,
)

from .sections import (
    _executive_summary,
    _investigation_findings,
    _detected_entities,
    _evidence_summary_section,
    _technical_analysis,
    _business_analysis,
    _attacker_goal,
    _victim_impact,
    _risk_summary,
    _recommended_actions_section,
    _user_guidance,
    generate_investigation_report,
)


def generate_report(analysis: dict) -> Dict:
    prediction = analysis.get("prediction", ML_LABEL_SAFE)
    confidence = analysis.get("confidence", 0.0)
    rule_label = analysis.get("rule_label", RISK_LOW)
    rule_score = analysis.get("rule_score", 0)
    category = analysis.get("scam_category", UNKNOWN_CATEGORY)
    risk_level = analysis.get("risk_level", SEVERITY_VERY_LOW)
    indicators = analysis.get("detected_indicators", [])
    threats = analysis.get("threats", [])
    entities = analysis.get("entities", [])
    entity_summary = analysis.get("entity_summary", {})
    evidence = analysis.get("supporting_evidence", [])
    decision_score = analysis.get("decision_score", 0)
    decision_level = analysis.get("decision_level", "SAFE")
    assessment_score = analysis.get("assessment_score", 0)
    assessment_band = analysis.get("assessment_band", "Suitable for normal communication")
    assessment_confidence = analysis.get("assessment_confidence", "LOW")
    assessment_summary = analysis.get("assessment_summary", "")
    business_reason = analysis.get("business_reason", "")
    technical_reason = analysis.get("technical_reason", "")
    recommended_action = analysis.get("recommended_action", "Ignore")
    risk_breakdown = analysis.get("risk_breakdown", {})
    reasons = analysis.get("reasons", [])
    text = analysis.get("_original_text", "")

    report_id = str(uuid.uuid4())
    generated_at = datetime.now(timezone.utc).isoformat()

    executive_summary = _executive_summary(category, assessment_score, assessment_band, indicators)
    findings = _investigation_findings(indicators, reasons, evidence)
    detected = _detected_entities(entities)
    evidence_summary = _evidence_summary_section(evidence)
    tech_analysis = _technical_analysis(confidence, decision_score, assessment_score, evidence, entities)
    business_analysis = _business_analysis(category, threats, risk_breakdown, business_reason)
    risk_summary = _risk_summary(risk_breakdown, risk_level)
    actions = _recommended_actions_section(recommended_action, assessment_score)
    timeline = list(TIMELINE_STAGES)
    guidance = _user_guidance(assessment_score, category)

    reasoning_family = analysis.get("reasoning_family", "")
    reasoning_subfamily = analysis.get("reasoning_subfamily", "")
    reasoning_family_confidence = analysis.get("reasoning_family_confidence", 0.0)
    reasoning_primary = analysis.get("reasoning_primary_evidence", [])
    reasoning_supporting = analysis.get("reasoning_supporting_evidence", [])
    reasoning_dominant_chain = analysis.get("reasoning_dominant_evidence_chain", [])

    reasoning_section = None
    if reasoning_family:
        reasoning_section = {
            "family_classification": {
                "family": reasoning_family,
                "subfamily": reasoning_subfamily,
                "confidence": reasoning_family_confidence,
            },
            "dominant_evidence_chain": reasoning_dominant_chain[:5],
            "primary_evidence_count": len(reasoning_primary),
            "supporting_evidence_count": len(reasoning_supporting),
        }

    assessment_section = {
        "score": assessment_score,
        "band": assessment_band,
        "confidence": assessment_confidence,
        "summary": assessment_summary,
    }
    if reasoning_section:
        assessment_section["reasoning"] = reasoning_section

    return {
        "report_id": report_id,
        "generated_at": generated_at,
        "executive_summary": executive_summary,
        "assessment": assessment_section,
        "scam_category": category,
        "severity": risk_level,
        "investigation_findings": findings,
        "detected_entities": detected,
        "evidence_summary": evidence_summary,
        "technical_analysis": tech_analysis,
        "business_analysis": business_analysis,
        "risk_summary": risk_summary,
        "recommended_actions": actions,
        "incident_timeline": timeline,
        "user_guidance": guidance,
    }


__all__ = ["generate_report", "generate_investigation_report"]
