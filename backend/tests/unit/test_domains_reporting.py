import pytest

from domains.reporting.service import generate_report, generate_investigation_report
from domains.reporting.sections import (
    _executive_summary,
    _investigation_findings,
    _detected_entities,
    _evidence_summary_section,
    _technical_analysis,
    _business_analysis,
    _risk_summary,
    _recommended_actions_section,
    _user_guidance,
)


class TestReportService:
    def test_generate_report_returns_dict(self):
        analysis = {
            "prediction": "scam",
            "confidence": 0.85,
            "rule_label": "high",
            "rule_score": 75,
            "scam_category": "Phishing",
            "risk_level": "HIGH",
            "detected_indicators": ["Suspicious URL"],
            "entities": [{"type": "url", "value": "http://evil.com", "risk": "HIGH"}],
            "supporting_evidence": [{"description": "test", "severity": "HIGH", "source": "rules"}],
            "decision_score": 75,
            "decision_level": "SCAM",
            "assessment_score": 75,
            "assessment_band": "High risk",
            "assessment_confidence": "HIGH",
            "assessment_summary": "test",
            "business_reason": "test",
            "technical_reason": "test",
            "recommended_action": "Block",
            "risk_breakdown": {"phishing": 50},
            "reasons": ["Suspicious URL detected"],
            "_original_text": "test message",
            "threats": ["financial fraud"],
        }
        result = generate_report(analysis)
        assert isinstance(result, dict)
        assert "report_id" in result
        assert "executive_summary" in result
        assert "investigation_findings" in result
        assert "recommended_actions" in result

    def test_generate_report_safe_message(self):
        analysis = {
            "prediction": "safe",
            "confidence": 0.05,
            "rule_label": "low",
            "rule_score": 10,
            "scam_category": "",
            "risk_level": "VERY_LOW",
            "detected_indicators": [],
            "entities": [],
            "supporting_evidence": [],
            "decision_score": 10,
            "decision_level": "SAFE",
            "assessment_score": 10,
            "assessment_band": "Suitable for normal communication",
            "assessment_confidence": "HIGH",
            "assessment_summary": "safe",
            "business_reason": "",
            "technical_reason": "",
            "recommended_action": "Ignore",
            "risk_breakdown": {},
            "reasons": [],
            "_original_text": "hello",
        }
        result = generate_report(analysis)
        assert result is not None
        assert result["assessment"]["score"] == 10


class TestReportSections:
    def test_executive_summary_returns_string(self):
        result = _executive_summary("Phishing", 80, "HIGH", ["Suspicious URL"])
        assert isinstance(result, str)
        assert len(result) > 0

    def test_executive_summary_low_risk(self):
        result = _executive_summary("", 10, "LOW", [])
        assert isinstance(result, str)

    def test_investigation_findings_returns_list(self):
        result = _investigation_findings(["Suspicious URL"], ["test"], [])
        assert isinstance(result, list)

    def test_investigation_findings_no_indicators(self):
        result = _investigation_findings([], [], [])
        assert isinstance(result, list)

    def test_detected_entities_returns_dict(self):
        entities = [{"type": "url", "value": "http://evil.com", "risk": "HIGH"}]
        result = _detected_entities(entities)
        assert isinstance(result, dict)
        assert result["total"] == 1

    def test_detected_entities_empty(self):
        result = _detected_entities([])
        assert result["total"] == 0

    def test_evidence_summary_section_returns_dict(self):
        evidence = [{"description": "test", "severity": "HIGH", "source": "rules"}]
        result = _evidence_summary_section(evidence)
        assert isinstance(result, dict)
        assert result["high_severity"] == 1

    def test_technical_analysis_returns_dict(self):
        result = _technical_analysis(0.85, 75, 75, [], [])
        assert isinstance(result, dict)
        assert "ml_confidence" in result

    def test_business_analysis_returns_dict(self):
        result = _business_analysis("Phishing", [], {}, "test")
        assert isinstance(result, dict)
        assert "likely_attacker_objective" in result

    def test_risk_summary_returns_dict(self):
        result = _risk_summary({"phishing": 50}, "HIGH")
        assert isinstance(result, dict)
        assert result["overall_severity"] == "HIGH"

    def test_recommended_actions_critical(self):
        actions = _recommended_actions_section("Block", 95)
        assert isinstance(actions, list)
        assert len(actions) > 0

    def test_recommended_actions_safe(self):
        actions = _recommended_actions_section("Ignore", 10)
        assert isinstance(actions, list)

    def test_user_guidance_returns_dict(self):
        result = _user_guidance(80, "Phishing")
        assert isinstance(result, dict)
        assert "immediate_actions" in result
        assert "long_term_safety_tips" in result

    def test_user_guidance_low_score(self):
        result = _user_guidance(10, "")
        assert result["immediate_actions"] == ["No immediate action required."]
