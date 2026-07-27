import uuid
from datetime import datetime, timezone
from typing import Dict, List

from config.settings import (
    REPORT_ENTITIES_PER_TYPE,
    REPORT_KEY_FINDINGS,
    REPORT_MAX_FINDINGS,
    REPORT_MAX_HIGH_RISK_ENTITIES,
    REPORT_TOP_RISKS,
)
from core.constants import (
    ATTACKER_GOALS,
    ML_LABEL_SAFE,
    ML_LABEL_SCAM,
    VICTIM_IMPACTS,
    INVESTIGATION_RISK_CRITICAL,
    INVESTIGATION_RISK_HIGH,
    INVESTIGATION_RISK_MEDIUM,
)


def _executive_summary(category: str, score: int, band: str, indicators: List[str]) -> str:
    if score >= 76:
        return (
            f"This investigation identified a {category.lower()} with high confidence. "
            f"The message exhibits {len(indicators)} distinct scam indicators "
            f"and is assessed as \"{band.lower()}\". "
            f"Immediate action is recommended to prevent potential financial or data loss."
        )
    if score >= 51:
        return (
            f"This message was flagged as a potential {category.lower()} during automated analysis. "
            f"Multiple suspicious indicators were detected, and the overall risk "
            f"assessment is \"{band.lower()}\". "
            f"Verification before responding is advised."
        )
    if score >= 21:
        return (
            f"Some suspicious signals were detected in this message, "
            f"but the evidence is not conclusive. "
            f"The message is assessed as \"{band.lower()}\". "
            f"Further review is recommended for certainty."
        )
    return (
        f"This message was analysed and no significant scam indicators were found. "
        f"The message is assessed as \"{band.lower()}\" and appears to be legitimate communication."
    )


def _investigation_findings(indicators: List[str], reasons: List[str], evidence: List[Dict]) -> List[str]:
    findings: List[str] = []
    seen = set()

    for ind in indicators:
        key = ind.lower()
        if key not in seen:
            seen.add(key)
            findings.append(f"{ind} detected in message content.")

    for reason in reasons:
        clean = reason[0].upper() + reason[1:] if reason else reason
        key = clean.lower()
        if key not in seen:
            seen.add(key)
            findings.append(f"{clean}.")

    for ev in evidence:
        desc = ev.get("description", "")
        if desc:
            key = desc.lower()[:60]
            if key not in seen:
                seen.add(key)
                findings.append(f"{desc[0].upper()}{desc[1:]}.")

    if not findings:
        findings.append("No suspicious indicators detected.")

    return findings[:REPORT_MAX_FINDINGS]


def _detected_entities(entities: List[Dict]) -> Dict:
    by_type: Dict[str, List[str]] = {}
    high_risk: List[str] = []
    for ent in entities:
        etype = ent.get("type", "unknown")
        value = ent.get("value", "")
        risk = ent.get("risk", "")
        if etype not in by_type:
            by_type[etype] = []
        by_type[etype].append(value)
        if risk == "HIGH":
            high_risk.append(f"{value} ({etype})")
    return {
        "total": len(entities),
        "by_type": {k: {"count": len(v), "values": v[:REPORT_ENTITIES_PER_TYPE]} for k, v in by_type.items()},
        "high_risk_entities": high_risk[:REPORT_MAX_HIGH_RISK_ENTITIES],
    }


def _evidence_summary_section(evidence: List[Dict]) -> Dict:
    high = [e for e in evidence if e.get("severity") == "HIGH"]
    medium = [e for e in evidence if e.get("severity") == "MEDIUM"]
    sources = {}
    for e in evidence:
        src = e.get("source", "unknown")
        sources[src] = sources.get(src, 0) + 1
    return {
        "total_items": len(evidence),
        "high_severity": len(high),
        "medium_severity": len(medium),
        "by_source": sources,
        "key_findings": [e["description"] for e in high[:REPORT_KEY_FINDINGS]],
    }


def _technical_analysis(
    confidence: float, decision_score: int, assessment_score: int,
    evidence: List[Dict], entities: List[Dict],
) -> Dict:
    return {
        "ml_confidence": round(confidence, 3),
        "ml_classification": ML_LABEL_SCAM if confidence > 0.5 else ML_LABEL_SAFE,
        "decision_score": decision_score,
        "assessment_score": assessment_score,
        "evidence_count": len(evidence),
        "entity_count": len(entities),
        "methodology": "Multi-layer analysis combining ML classification, rule-based heuristics, entity extraction, evidence correlation, and unified risk assessment.",
    }


def _business_analysis(category: str, threats: List[str], risk_breakdown: Dict, business_reason: str) -> Dict:
    risk_items = {k: v for k, v in risk_breakdown.items() if v > 0}
    top_risks = sorted(risk_items.items(), key=lambda x: -x[1])[:REPORT_TOP_RISKS]
    attacker_goal = _attacker_goal(category)
    victim_impact = _victim_impact(category, threats)
    return {
        "category": category,
        "likely_attacker_objective": attacker_goal,
        "potential_victim_impact": victim_impact,
        "top_risk_factors": [{"risk": k.replace("_", " ").title(), "score": v} for k, v in top_risks],
        "business_impact_summary": business_reason,
    }


def _attacker_goal(category: str) -> str:
    return ATTACKER_GOALS.get(category, "Deceive the victim into sharing sensitive information or transferring money.")


def _victim_impact(category: str, threats: List[str]) -> str:
    return VICTIM_IMPACTS.get(category, "Potential financial loss, data compromise, or identity theft.")


def _risk_summary(risk_breakdown: Dict, severity: str) -> Dict:
    return {
        "overall_severity": severity,
        "risk_scores": risk_breakdown,
        "primary_risk": max(risk_breakdown, key=risk_breakdown.get) if risk_breakdown else "none",
    }


def _recommended_actions_section(action: str, score: int) -> List[str]:
    if score >= 91:
        return [
            "Block the sender immediately.",
            "Report the message to cybercrime.gov.in or forward to 1930.",
            "Do not click any links or download any attachments.",
            "If any credentials were shared, change passwords immediately.",
            "Monitor bank accounts for unauthorized transactions.",
        ]
    if score >= 76:
        return [
            "Do not reply to or engage with this message.",
            "Do not click any links or call any phone numbers in the message.",
            "Verify any claims independently through official channels.",
            "Report suspicious messages to the Cyber Crime portal.",
        ]
    if score >= 51:
        return [
            "Do not share any personal or financial information.",
            "Verify the sender through an independent official channel.",
            "Report the message if it appears to impersonate a known organization.",
        ]
    if score >= 21:
        return [
            "Exercise caution when responding to unsolicited messages.",
            "Verify the sender independently if the message appears unusual.",
            "Do not share OTPs, passwords, or banking details via message.",
        ]
    return [
        "No action required. This message appears to be legitimate.",
        "Always remain vigilant against unsolicited communications.",
    ]


def _user_guidance(score: int, category: str) -> Dict:
    if score >= 76:
        immediate = [
            "Do not interact with the message sender.",
            "Do not click any links or open attachments.",
            "Do not share OTP, PIN, password, or banking details.",
        ]
        short_term = [
            f"If you engaged with this {category.lower()}, contact your bank immediately.",
            f"Report the incident to cybercrime.gov.in or call 1930.",
            "Change passwords for any accounts that may have been compromised.",
        ]
        long_term = [
            "Enable two-factor authentication on all financial accounts.",
            "Never share sensitive information in response to unsolicited messages.",
            "Verify sender identity through official channels before taking action.",
        ]
    elif score >= 51:
        immediate = [
            "Do not share personal or financial information.",
            "Do not click any links in the message.",
            "Verify the sender independently.",
        ]
        short_term = [
            f"Monitor accounts for any unusual activity related to {category.lower()}.",
            "Report the message if it impersonates a known organization.",
        ]
        long_term = [
            "Stay informed about common scam tactics.",
            "Use official apps and websites for financial transactions.",
        ]
    elif score >= 21:
        immediate = [
            "Exercise caution before responding.",
            "Do not share sensitive information.",
        ]
        short_term = [
            "Verify the message content independently.",
            "Be alert for follow-up messages that may escalate the scam.",
        ]
        long_term = [
            "Never share OTP or banking details via SMS or phone calls.",
            "Register on the Do Not Disturb list to reduce spam messages.",
        ]
    else:
        immediate = ["No immediate action required."]
        short_term = ["Continue to exercise caution with unsolicited messages."]
        long_term = ["Stay vigilant against evolving scam techniques."]

    return {
        "immediate_actions": immediate,
        "short_term_actions": short_term,
        "long_term_safety_tips": long_term,
    }


def generate_investigation_report(result: "InvestigationResult") -> Dict:
    merged = result.merged_entities
    repeated = result.repeated_indicators
    campaign = result.campaign
    timeline = result.timeline
    global_risk = result.global_risk
    artefacts = result.artefact_summaries

    report_id = str(uuid.uuid4())
    generated_at = datetime.now(timezone.utc).isoformat()

    total = len(artefacts)
    scam_count = sum(1 for a in artefacts if a.get("prediction") == "scam")
    safe_count = total - scam_count
    merged_count = sum(len(v) for v in merged.values())
    repeated_count = sum(repeated.values())

    exec_summary = (
        f"Investigation analysed {total} artefact(s): {scam_count} scam, {safe_count} safe. "
        f"Merged {merged_count} unique entities, detected {repeated_count} repeated indicators. "
        f"Overall risk: {global_risk.get('overall_risk', 'UNKNOWN')} "
        f"(score: {global_risk.get('overall_score', 0)})."
    )
    if campaign.get("campaign_detected"):
        exec_summary += f" Coordinated campaign detected (confidence: {campaign['confidence']:.1%})."

    entity_section = merged if isinstance(merged, dict) else {}
    current_timeline = timeline if isinstance(timeline, list) else []

    global_score = global_risk.get("overall_score", 0)
    if global_score >= INVESTIGATION_RISK_CRITICAL:
        actions = [
            "Block all identified senders and numbers immediately.",
            "Report coordinated campaign to cybercrime.gov.in or 1930.",
            "Notify all potential victims identified in the campaign.",
            "Preserve all artefacts as evidence.",
        ]
    elif global_score >= INVESTIGATION_RISK_HIGH:
        actions = [
            "Do not engage with any of the identified senders.",
            "Do not click shared links or call shared numbers.",
            "Verify independently through official channels.",
            "Report coordinated activity to law enforcement.",
        ]
    elif global_score >= INVESTIGATION_RISK_MEDIUM:
        actions = [
            "Exercise caution with all related messages.",
            "Verify sender identities independently.",
            "Monitor for additional related messages.",
        ]
    else:
        actions = [
            "No immediate action required for these messages.",
            "Continue to remain vigilant against related messages.",
        ]

    return {
        "report_id": report_id,
        "generated_at": generated_at,
        "report_type": "investigation",
        "executive_summary": exec_summary,
        "global_risk": {
            "overall_risk": global_risk.get("overall_risk", "UNKNOWN"),
            "overall_score": global_score,
            "confidence": global_risk.get("confidence", 0.0),
            "dominant_family": global_risk.get("dominant_family", ""),
        },
        "arte facts": [
            {
                "index": a.get("index", 0),
                "type": a.get("type", ""),
                "prediction": a.get("prediction", ""),
                "assessment_score": a.get("assessment_score", 0),
                "scam_category": a.get("scam_category", ""),
                "reasoning_family": a.get("reasoning_family", ""),
            }
            for a in artefacts
        ],
        "campaign_analysis": {
            "detected": campaign.get("campaign_detected", False),
            "confidence": campaign.get("confidence", 0.0),
            "indicators": campaign.get("indicators", {}),
            "summary": campaign.get("summary", ""),
        },
        "merged_entities": entity_section,
        "repeated_indicators": repeated,
        "timeline": current_timeline,
        "strongest_evidence": global_risk.get("strongest_evidence", []),
        "weakest_signals": global_risk.get("weakest_signals", []),
        "open_questions": global_risk.get("open_questions", []),
        "recommended_actions": actions,
    }
