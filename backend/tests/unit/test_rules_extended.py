import pytest
from rules import analyze_message, check_otp, check_urgent_money, check_suspicious_links, check_service_keywords


class TestAnalyzeMessage:
    def test_empty_text(self):
        result = analyze_message("")
        assert result["risk_label"] == "low"
        assert result["risk_score"] == 0

    def test_short_safe(self):
        result = analyze_message("Hi")
        assert result["risk_label"] == "low"

    def test_max_score_capped(self):
        text = "URGENT: " + " ".join([
            "https://evil.xyz", "https://bit.ly/abc",
            "SBI", "KYC", "OTP", "lottery", "deactivate",
            "Rs 50000", "pay now", "customer care 18001234567",
            "PM Modi", "customs clearance", "work from home",
            "registration fee Rs 999",
        ])
        result = analyze_message(text)
        assert result["risk_score"] <= 100

    def test_reasons_list_limited(self):
        text = "URGENT SBI KYC OTP https://evil.xyz https://bit.ly/abc lottery Rs 50000 deactivate"
        result = analyze_message(text)
        assert len(result["reasons"]) <= 5

    def test_high_risk_threshold(self):
        text = "URGENT: Your SBI KYC account will be deactivated immediately. Pay Rs 50000 processing fee now. Your parcel at customs release fee. Lottery won! https://sbi-kyc.xyz https://bit.ly/scam"
        result = analyze_message(text)
        assert result["risk_label"] == "high"
        assert result["risk_score"] >= 70


class TestCheckOtpEdgeCases:
    def test_no_otp(self):
        score, reasons = check_otp("Hello world")
        assert score == 0
        assert reasons == []

    def test_otp_code_pattern(self):
        score, reasons = check_otp("Your OTP: 784512 is valid")
        assert score == 0

    def test_otp_code_with_scam_context(self):
        score, reasons = check_otp("URGENT: Send OTP 784512 to verify your account immediately")
        assert score > 0

    def test_otp_forward_request(self):
        score, reasons = check_otp("Forward this OTP to 9988776655")
        assert score >= 20


class TestCheckUrgentMoneyEdgeCases:
    def test_no_urgency(self):
        score, reasons = check_urgent_money("Hello")
        assert reasons == []

    def test_multiple_urgency_words(self):
        score, reasons = check_urgent_money("URGENT: Act NOW immediately!")
        assert score >= 5

    def test_suspension_threat(self):
        score, reasons = check_urgent_money("Your account will be blocked in 24 hours")
        assert score >= 15

    def test_loan_mention(self):
        score, reasons = check_urgent_money("Get a loan with low EMI")
        assert score == 0

    def test_loan_mention_with_scam_context(self):
        score, reasons = check_urgent_money("URGENT: Apply now for guaranteed loan approval, low EMI!")
        assert score >= 8

    def test_credit_card(self):
        score, reasons = check_urgent_money("Your credit card limit increased")
        assert score == 0

    def test_credit_card_with_scam_context(self):
        score, reasons = check_urgent_money("URGENT: Verify your credit card now or it will be blocked!")
        assert score >= 8


class TestCheckSuspiciousLinksEdgeCases:
    def test_no_url(self):
        score, reasons = check_suspicious_links("Hello world")
        assert score == 0

    def test_legitimate_url_zero_score(self):
        score, reasons = check_suspicious_links("Visit https://google.com")
        assert score == 0

    def test_unknown_url_low_score(self):
        score, reasons = check_suspicious_links("Visit https://my-personal-site.io")
        assert score >= 5

    def test_shortened_url_high_score(self):
        score, reasons = check_suspicious_links("Click https://tinyurl.com/abc123")
        assert score >= 15

    def test_suspicious_tld(self):
        score, reasons = check_suspicious_links("Visit https://evil.xyz")
        assert score >= 15

    def test_url_with_kyc_in_domain(self):
        score, reasons = check_suspicious_links("Visit https://sbi-kyc.com")
        assert score >= 10

    def test_multiple_urls(self):
        score, reasons = check_suspicious_links("Visit https://evil.xyz and https://bad.top")
        assert score > 5

    def test_multiple_shorteners(self):
        score, reasons = check_suspicious_links("https://bit.ly/a https://tiny.cc/b")
        assert score >= 15


class TestCheckServiceKeywordsEdgeCases:
    def test_no_keywords(self):
        score, reasons = check_service_keywords("Hello world")
        assert score == 0

    def test_multiple_banks(self):
        score, reasons = check_service_keywords("URGENT: SBI HDFC ICICI Axis Kotak accounts suspended! Verify now!")
        assert score >= 3
        matches = [r for r in reasons if "bank" in r.lower()]
        assert len(matches) >= 1

    def test_multiple_banks_no_context(self):
        score, reasons = check_service_keywords("SBI HDFC ICICI Axis Kotak")
        assert score == 0

    def test_payment_apps(self):
        score, reasons = check_service_keywords("URGENT: Use GPay or PhonePe to pay now!")
        assert score >= 3

    def test_payment_apps_no_context(self):
        score, reasons = check_service_keywords("Use GPay or PhonePe")
        assert score == 0

    def test_government_reference(self):
        score, reasons = check_service_keywords("URGENT: PM Modi scheme subsidy, apply now!")
        assert score >= 5

    def test_government_reference_no_context(self):
        score, reasons = check_service_keywords("PM Modi scheme")
        assert score == 0

    def test_scam_keywords(self):
        score, reasons = check_service_keywords("URGENT: This is a lottery win, claim now!")
        assert score > 0
        assert any("keyword" in r.lower() for r in reasons)

    def test_scam_keywords_no_context(self):
        score, reasons = check_service_keywords("This is a lottery win")
        assert score == 0

    def test_yes_bank(self):
        score, reasons = check_service_keywords("URGENT: Yes Bank account suspended, verify now!")
        assert score >= 3

    def test_yes_bank_no_context(self):
        score, reasons = check_service_keywords("Yes Bank account")
        assert score == 0
