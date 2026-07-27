from domains.reporting.public import generate_report
from domains.reporting.sections import _executive_summary, _user_guidance


def test_generate_report_minimal():
    result = generate_report({
        "prediction": "safe", "confidence": 0.1,
        "rule_label": "low", "rule_score": 0,
        "scam_category": "Unknown Scam", "risk_level": "VERY LOW",
        "detected_indicators": [], "threats": [],
        "entities": [], "entity_summary": {},
        "supporting_evidence": [],
        "decision_score": 0, "decision_level": "SAFE",
        "assessment_score": 0, "assessment_band": "Suitable for normal communication",
        "assessment_confidence": "LOW", "assessment_summary": "",
        "business_reason": "", "technical_reason": "",
        "recommended_action": "Ignore",
        "risk_breakdown": {"credential_theft": 0, "financial_loss": 0, "identity_theft": 0, "malware": 0, "social_engineering": 0},
        "reasons": [], "_original_text": "",
    })
    assert "report_id" in result
    assert len(result["report_id"]) == 36
    assert "generated_at" in result
    assert "executive_summary" in result
    assert "assessment" in result
    assert "scam_category" in result
    assert "severity" in result
    assert "investigation_findings" in result
    assert "detected_entities" in result
    assert "evidence_summary" in result
    assert "technical_analysis" in result
    assert "business_analysis" in result
    assert "risk_summary" in result
    assert "recommended_actions" in result
    assert "incident_timeline" in result
    assert "user_guidance" in result


def test_timeline_six_stages():
    result = generate_report({
        "prediction": "safe", "confidence": 0.1,
        "rule_label": "low", "rule_score": 0,
        "scam_category": "Unknown Scam", "risk_level": "VERY LOW",
        "detected_indicators": [], "threats": [],
        "entities": [], "entity_summary": {},
        "supporting_evidence": [],
        "decision_score": 0, "decision_level": "SAFE",
        "assessment_score": 0, "assessment_band": "Suitable for normal communication",
        "assessment_confidence": "LOW", "assessment_summary": "",
        "business_reason": "", "technical_reason": "",
        "recommended_action": "Ignore",
        "risk_breakdown": {"credential_theft": 0, "financial_loss": 0, "identity_theft": 0, "malware": 0, "social_engineering": 0},
        "reasons": [], "_original_text": "",
    })
    assert len(result["incident_timeline"]) == 6
    for stage in result["incident_timeline"]:
        assert "stage" in stage
        assert "event" in stage
        assert "description" in stage


def test_user_guidance_three_sections():
    guidance = _user_guidance(0, "Unknown Scam")
    assert "immediate_actions" in guidance
    assert "short_term_actions" in guidance
    assert "long_term_safety_tips" in guidance


def test_user_guidance_high_risk():
    guidance = _user_guidance(80, "Bank KYC Scam")
    assert len(guidance["immediate_actions"]) >= 3
    assert len(guidance["short_term_actions"]) >= 2
    assert len(guidance["long_term_safety_tips"]) >= 2


def test_executive_summary_critical():
    summary = _executive_summary("Bank KYC Scam", 80, "Suitable for immediate action", ["OTP Request", "Suspicious URL"])
    assert "immediate action" in summary.lower()


def test_executive_summary_investigation():
    summary = _executive_summary("UPI Scam", 60, "Suitable for security investigation", ["Payment Request"])
    assert "verification" in summary.lower() or "flagged" in summary.lower()


def test_executive_summary_low():
    summary = _executive_summary("Unknown Scam", 10, "Suitable for normal communication", [])
    assert "legitimate" in summary.lower() or "no significant" in summary.lower()


def test_report_with_entities():
    result = generate_report({
        "prediction": "scam", "confidence": 0.95,
        "rule_label": "high", "rule_score": 70,
        "scam_category": "Bank KYC Scam", "risk_level": "CRITICAL",
        "detected_indicators": ["OTP Request", "Suspicious URL", "KYC Update Request"],
        "threats": ["Financial Theft", "Identity Theft"],
        "entities": [
            {"type": "url", "value": "https://evil.xyz", "risk": "HIGH"},
            {"type": "email", "value": "spam@evil.com", "risk": "MEDIUM"},
        ],
        "entity_summary": {"total_entities": 2, "by_type": {"url": 1, "email": 1}, "threat_indicators": ["Suspicious URL"]},
        "supporting_evidence": [
            {"description": "ML model classifies as scam", "severity": "HIGH", "source": "ml"},
            {"description": "Rule score 70/100", "severity": "HIGH", "source": "rules"},
        ],
        "decision_score": 70, "decision_level": "HIGH RISK",
        "assessment_score": 80, "assessment_band": "Suitable for immediate action",
        "assessment_confidence": "HIGH", "assessment_summary": "Urgent: Bank KYC Scam.",
        "business_reason": "Bank KYC Scam threat", "technical_reason": "ML and rules confirm",
        "recommended_action": "Do not interact",
        "risk_breakdown": {"credential_theft": 80, "financial_loss": 30, "identity_theft": 50, "malware": 15, "social_engineering": 40},
        "reasons": ["otp share", "sbi kyc update"], "_original_text": "",
    })
    assert len(result["investigation_findings"]) >= 2
    assert result["detected_entities"]["total"] == 2
    assert len(result["detected_entities"]["high_risk_entities"]) >= 1
