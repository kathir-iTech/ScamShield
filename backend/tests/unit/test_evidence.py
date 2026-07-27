import pytest

from domains.assessment.evidence import (
    build_confidence_breakdown,
    build_evidence,
    build_risk_breakdown,
    calculate_decision_score,
    correlate_evidence,
    detect_conflicts,
    get_decision_level,
    get_priority,
)


def test_build_evidence_minimal():
    result = build_evidence({
        "prediction": "safe", "confidence": 0.1,
        "rule_score": 0, "rule_label": "low", "reasons": [],
        "detected_indicators": [], "scam_category": "Unknown Scam",
        "entities": [], "entity_summary": {"total_entities": 0, "threat_indicators": [], "by_type": {}},
        "entity_risk": {"high": [], "medium": [], "low": []},
    })
    assert "decision_score" in result
    assert "decision_level" in result
    assert "decision_reasoning" in result
    assert "recommended_priority" in result


@pytest.mark.parametrize("score,expected_level", [
    (0, "SAFE"),
    (14, "SAFE"),
    (15, "LOW RISK"),
    (34, "LOW RISK"),
    (35, "SUSPICIOUS"),
    (59, "SUSPICIOUS"),
    (60, "HIGH RISK"),
    (79, "HIGH RISK"),
    (80, "CRITICAL"),
    (100, "CRITICAL"),
])
def test_decision_level(score, expected_level):
    assert get_decision_level(score) == expected_level


@pytest.mark.parametrize("score,level,expected_priority", [
    (0, "SAFE", "LOW"),
    (24, "LOW RISK", "LOW"),
    (25, "SUSPICIOUS", "NORMAL"),
    (49, "SUSPICIOUS", "NORMAL"),
    (50, "HIGH RISK", "HIGH"),
    (69, "HIGH RISK", "HIGH"),
    (70, "CRITICAL", "URGENT"),
    (100, "CRITICAL", "URGENT"),
])
def test_priority(score, level, expected_priority):
    assert get_priority(score, level) == expected_priority


def test_calculate_decision_score_empty():
    assert calculate_decision_score([]) == 0


@pytest.mark.parametrize("indicators,entities,expected_label", [
    (["OTP Request", "KYC Update Request", "Suspicious URL"], [], "Credential Theft"),
    (["Payment Request", "Suspicious URL"], [], "Payment Fraud"),
    (["Courier/Customs Mention", "Payment Request"], [], "Delivery Scam"),
])
def test_correlate_evidence(indicators, entities, expected_label):
    result = correlate_evidence(indicators, entities)
    labels = [c["label"] for c in result]
    assert expected_label in labels


def test_detect_conflicts_ml_safe_rules_high():
    result = detect_conflicts(
        prediction="safe", confidence=0.5, rule_label="high",
        rule_score=60, indicators=["OTP Request"], entities=[],
    )
    assert any(c["type"] == "ml_vs_rules" for c in result)


def test_detect_conflicts_ml_safe_high_risk_entities():
    entities = [{"type": "shortened_url", "value": "https://bit.ly/x", "risk": "HIGH"}]
    result = detect_conflicts(
        prediction="safe", confidence=0.8, rule_label="low",
        rule_score=10, indicators=[], entities=entities,
    )
    assert any(c["type"] == "ml_vs_entities" for c in result)


def test_build_confidence_breakdown():
    result = build_confidence_breakdown(
        prediction="scam", confidence=0.95, rule_label="high",
        rule_score=60, indicators=["OTP Request", "Suspicious URL"],
        entities=[{"type": "url", "value": "x", "risk": "LOW"}],
    )
    assert "ml" in result
    assert "rules" in result
    assert "entities" in result
    assert "explanation" in result
    assert "overall" in result
    assert 0 <= result["overall"] <= 100


def test_build_risk_breakdown():
    result = build_risk_breakdown(
        indicators=["OTP Request", "Payment Request"],
        entities=[{"type": "upi_id", "value": "x", "risk": "MEDIUM"}],
        category="UPI Scam",
        correlations=[{"label": "Payment Fraud"}],
    )
    for k in ("credential_theft", "financial_loss", "identity_theft", "malware", "social_engineering"):
        assert k in result
        assert 0 <= result[k] <= 100
    assert result["financial_loss"] > 0


def test_build_evidence_with_high_risk_entities():
    result = build_evidence({
        "prediction": "scam", "confidence": 0.9,
        "rule_score": 60, "rule_label": "high",
        "reasons": ["otp share detected"],
        "detected_indicators": ["OTP Request", "Suspicious URL"],
        "scam_category": "Bank KYC Scam",
        "entities": [{"type": "url", "value": "https://evil.xyz", "risk": "LOW"}],
        "entity_summary": {
            "total_entities": 3,
            "by_type": {"url": 1},
            "threat_indicators": ["Suspicious URL"],
        },
        "entity_risk": {
            "high": [{"type": "shortened_url", "value": "https://bit.ly/x"}],
            "medium": [{"type": "phone_indian", "value": "+91-9876543210"}],
            "low": [{"type": "url", "value": "https://evil.xyz"}],
        },
    })
    assert result["decision_score"] >= 20
    assert result["decision_level"] in ("CRITICAL", "HIGH RISK", "SUSPICIOUS")
    assert len(result["supporting_evidence"]) >= 5
