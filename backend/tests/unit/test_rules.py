from rules import analyze_message, check_otp, check_service_keywords, check_suspicious_links, check_urgent_money


def test_analyze_safe():
    result = analyze_message("Hello, how are you?")
    assert result["risk_label"] == "low"
    assert result["risk_score"] == 0


def test_analyze_high_risk():
    result = analyze_message("URGENT: Your SBI account KYC will be deactivated. Click https://sbi-kyc.xyz to update OTP now!")
    assert result["risk_score"] >= 35
    assert result["risk_label"] in ("high", "medium")


def test_otp_share_detected():
    score, reasons = check_otp("Share your OTP with us on WhatsApp")
    assert score >= 20
    assert any("share" in r.lower() for r in reasons)


def test_otp_mention():
    score, reasons = check_otp("Your OTP is 123456")
    assert score >= 5
    assert any("otp" in r.lower() for r in reasons)


def test_urgent_money_detected():
    score, reasons = check_urgent_money("URGENT: Pay Rs 5000 immediately")
    assert score >= 5
    assert any("urgent" in r.lower() for r in reasons)


def test_suspicious_links():
    score, reasons = check_suspicious_links("Visit https://evil.xyz")
    assert score >= 15
    assert any("suspicious" in r.lower() or "tld" in r.lower() for r in reasons)


def test_shortened_url():
    score, reasons = check_suspicious_links("Click https://bit.ly/abc123")
    assert score >= 15
    assert any("shortener" in r.lower() for r in reasons)


def test_service_keywords():
    score, reasons = check_service_keywords("Your SBI account is blocked. Lottery won!")
    assert score >= 3
    assert any("sbi" in r.lower() for r in reasons)


def test_risk_score_capped():
    text = " ".join([
        "URGENT: Your SBI KYC and Aadhaar will be deactivated.",
        "Update immediately or account frozen.",
        "Click https://sbi-kyc.xyz to verify OTP now!",
        "Lottery won! Pay Rs 50000 processing fee.",
        "Your parcel at customs clearance.",
        "PM Modi scheme subsidy pension.",
        "Work from home job registration fee.",
    ])
    result = analyze_message(text)
    assert result["risk_score"] <= 100


def test_get_suggested_action():
    from rules import get_suggested_action
    assert "click" in get_suggested_action("high").lower()
    assert "verify" in get_suggested_action("medium").lower()
    assert "safe" in get_suggested_action("low").lower()


def test_multiple_urls_bonus():
    score, reasons = check_suspicious_links("Visit https://example.com and https://test.org")
    assert score >= 5
    assert any("multiple" in r.lower() for r in reasons)
