from domains.assessment.public import assess


def test_assess_minimal():
    result = assess({
        "prediction": "safe", "confidence": 0.1,
        "decision_score": 0, "decision_level": "SAFE",
        "rule_label": "low", "rule_score": 0,
        "detected_indicators": [],
        "scam_category": "Unknown Scam",
        "entity_risk": {"high": [], "medium": [], "low": []},
        "entity_summary": {},
        "supporting_evidence": [],
        "conflicting_evidence": [],
        "confidence_breakdown": {"overall": 10},
    })
    assert 0 <= result["assessment_score"] <= 100
    assert result["assessment_confidence"] == "LOW"


def test_assess_scam_high_conf():
    result = assess({
        "prediction": "scam", "confidence": 0.95,
        "decision_score": 85, "decision_level": "CRITICAL",
        "rule_label": "high", "rule_score": 70,
        "detected_indicators": ["OTP Request", "Suspicious URL", "Bank Impersonation", "KYC Update Request"],
        "scam_category": "Bank KYC Scam",
        "entity_risk": {"high": [{"type": "url", "value": "x", "risk": "HIGH"}], "medium": [], "low": []},
        "entity_summary": {"total_entities": 3, "threat_indicators": ["Suspicious URL"]},
        "supporting_evidence": [
            {"severity": "HIGH", "source": "ml", "type": "ml_prediction"},
            {"severity": "HIGH", "source": "rules", "type": "rule_score"},
            {"severity": "HIGH", "source": "intel", "type": "entity_high"},
        ],
        "conflicting_evidence": [],
        "confidence_breakdown": {"overall": 80},
    })
    assert result["assessment_score"] >= 76
    assert result["assessment_band"] == "Suitable for immediate action"
    assert result["assessment_confidence"] == "HIGH"


def test_assess_with_conflict():
    result = assess({
        "prediction": "safe", "confidence": 0.8,
        "decision_score": 30, "decision_level": "SUSPICIOUS",
        "rule_label": "high", "rule_score": 50,
        "detected_indicators": ["OTP Request"],
        "scam_category": "Unknown Scam",
        "entity_risk": {"high": [{"type": "url", "value": "x", "risk": "HIGH"}], "medium": [], "low": []},
        "entity_summary": {"total_entities": 2, "threat_indicators": []},
        "supporting_evidence": [
            {"severity": "MEDIUM", "source": "ml", "type": "ml_prediction"},
            {"severity": "HIGH", "source": "rules", "type": "rule_score"},
        ],
        "conflicting_evidence": [
            {"type": "ml_vs_rules", "description": "conflict"},
        ],
        "confidence_breakdown": {"overall": 50},
    })
    assert result["review_required"] is True


def test_assess_score_bounds():
    result = assess({
        "prediction": "scam", "confidence": 0.99,
        "decision_score": 100, "decision_level": "CRITICAL",
        "rule_label": "high", "rule_score": 100,
        "detected_indicators": ["OTP Request", "Suspicious URL", "Payment Request", "Account Threat"],
        "scam_category": "Bank KYC Scam",
        "entity_risk": {"high": [{"type": "url", "value": "x", "risk": "HIGH"}] * 3, "medium": [{"type": "phone", "value": "y", "risk": "MEDIUM"}] * 3, "low": []},
        "entity_summary": {"total_entities": 6, "threat_indicators": ["Suspicious URL"]},
        "supporting_evidence": [
            {"severity": "HIGH", "source": "ml", "type": "ml_prediction"},
            {"severity": "HIGH", "source": "rules", "type": "rule_score"},
            {"severity": "HIGH", "source": "intel", "type": "entity_high"},
            {"severity": "HIGH", "source": "intel", "type": "entity_high"},
            {"severity": "MEDIUM", "source": "intel", "type": "entity_medium"},
        ],
        "conflicting_evidence": [],
        "confidence_breakdown": {"overall": 90},
    })
    assert 0 <= result["assessment_score"] <= 100
    assert result["assessment_confidence"] == "HIGH"


def test_assess_band_normal():
    result = assess({
        "prediction": "safe", "confidence": 0.99,
        "decision_score": 0, "decision_level": "SAFE",
        "rule_label": "low", "rule_score": 0,
        "detected_indicators": [],
        "scam_category": "Unknown Scam",
        "entity_risk": {"high": [], "medium": [], "low": []},
        "entity_summary": {},
        "supporting_evidence": [],
        "conflicting_evidence": [],
        "confidence_breakdown": {"overall": 10},
    })
    assert result["assessment_band"] == "Suitable for normal communication"
    assert result["recommended_action"] == "Ignore"


def test_assess_review_required_unknown_category():
    result = assess({
        "prediction": "scam", "confidence": 0.5,
        "decision_score": 30, "decision_level": "SUSPICIOUS",
        "rule_label": "low", "rule_score": 15,
        "detected_indicators": ["Urgency Language"],
        "scam_category": "Unknown Scam",
        "entity_risk": {"high": [], "medium": [], "low": []},
        "entity_summary": {},
        "supporting_evidence": [{"severity": "MEDIUM", "source": "rules", "type": "rule_indicator"}],
        "conflicting_evidence": [],
        "confidence_breakdown": {"overall": 30},
    })
    assert result["review_required"] is True


def test_assess_summary_text():
    result = assess({
        "prediction": "scam", "confidence": 0.99,
        "decision_score": 100, "decision_level": "CRITICAL",
        "rule_label": "high", "rule_score": 100,
        "detected_indicators": ["OTP Request", "Suspicious URL", "Bank Impersonation", "KYC Update Request"],
        "scam_category": "Bank KYC Scam",
        "entity_risk": {
            "high": [{"type": "url", "value": "x", "risk": "HIGH"}, {"type": "url", "value": "y", "risk": "HIGH"}],
            "medium": [{"type": "phone", "value": "z", "risk": "MEDIUM"}],
            "low": [],
        },
        "entity_summary": {},
        "supporting_evidence": [
            {"severity": "HIGH", "source": "ml", "type": "ml_prediction"},
            {"severity": "HIGH", "source": "rules", "type": "rule_score"},
            {"severity": "HIGH", "source": "intel", "type": "entity_high"},
        ],
        "conflicting_evidence": [],
        "confidence_breakdown": {"overall": 80},
    })
    assert "Urgent" in result["assessment_summary"]
