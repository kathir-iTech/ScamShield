import pytest

from domains.assessment.explanation import (
    calculate_severity,
    detect_category,
    detect_indicators,
    extract_recommendations,
    extract_threats,
    generate_explanation,
)


def test_unknown_category_returns_no_score():
    cat, conf = detect_category("", [])
    assert cat == "Unknown Scam"
    assert conf == 0.0


def test_bank_kyc_category_detected():
    text = "Update your KYC immediately or your SBI account will be deactivated"
    cat, conf = detect_category(text, [])
    assert cat == "Bank KYC Scam"
    assert conf > 0


def test_lottery_category_detected():
    text = "Congratulations! You won 50 lakh lottery"
    cat, conf = detect_category(text, [])
    assert cat == "Lottery Scam"
    assert conf > 0


def test_job_scam_category_detected():
    text = "Work from home job. Registration fee 500 required"
    cat, conf = detect_category(text, [])
    assert cat == "Job Scam"
    assert conf > 0


def test_reasons_boost_category_score():
    text = "random text"
    reasons = ["kyc update required", "aadhaar verification"]
    cat, conf = detect_category(text, reasons)
    assert cat == "Bank KYC Scam"
    assert conf > 0


@pytest.mark.parametrize("ml_label,conf,rule_score,rule_label,indicators,expected", [
    ("scam", 0.9, 60, "high", ["OTP Request", "Suspicious URL"], "CRITICAL"),
    ("scam", 0.95, 30, "medium", ["Urgency Language"], "HIGH"),
    ("safe", 0.6, 25, "low", ["Urgency Language"], "MEDIUM"),
    ("safe", 0.6, 5, "low", [], "LOW"),
    ("safe", 0.6, 0, "low", [], "VERY LOW"),
])
def test_calculate_severity(ml_label, conf, rule_score, rule_label, indicators, expected):
    sev = calculate_severity(ml_label, conf, rule_score, rule_label, indicators)
    assert sev == expected


def test_detect_indicators_from_text():
    inds = detect_indicators("URGENT: Share your OTP 123456 immediately! Click https://evil.com now!", [])
    assert "OTP Request" in inds
    assert "Suspicious URL" in inds
    assert "Urgency Language" in inds


def test_detect_indicators_from_text_no_otp_sharing():
    inds = detect_indicators("URGENT: Your OTP is 123456. Click https://evil.com immediately!", [])
    assert "OTP Request" not in inds
    assert "Suspicious URL" in inds
    assert "Urgency Language" in inds


def test_detect_indicators_from_reasons():
    inds = detect_indicators("hello", ["otp share detected"])
    assert "OTP Request" in inds


def test_threats_for_known_category():
    threats = extract_threats("UPI Scam")
    assert threats["primary"] == "Financial Theft"
    assert threats["secondary"] == "Credential Harvesting"


def test_threats_for_unknown_category():
    threats = extract_threats("Nonexistent")
    assert threats["primary"] == "Unsolicited Message"


def test_recommendations_for_known_category():
    recs = extract_recommendations("Bank KYC Scam")
    assert len(recs) >= 4
    assert any("KYC" in r for r in recs)


def test_recommendations_for_unknown_category():
    recs = extract_recommendations("Nonexistent")
    assert len(recs) >= 4


def test_generate_explanation_structure():
    result = generate_explanation("test", {
        "prediction": "safe", "confidence": 0.3,
        "rule_score": 5, "rule_label": "low", "reasons": [],
    })
    assert "summary" in result
    assert "risk_level" in result
    assert "scam_category" in result
    assert "detected_indicators" in result
    assert "threats" in result
    assert "recommended_actions" in result
    assert "confidence_reason" in result


def test_generate_explanation_high_conf_scam():
    result = generate_explanation("URGENT: Your SBI KYC will expire", {
        "prediction": "scam", "confidence": 0.95,
        "rule_score": 60, "rule_label": "high",
        "reasons": ["kyc update", "sbi account"],
    })
    assert result["risk_level"] in ("CRITICAL", "HIGH")
    assert "scam" in result["summary"].lower()
