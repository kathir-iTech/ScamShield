import pytest

from domains.reasoning.refinement import (
    _fp_legitimate_banking_notification,
    _fp_government_alert,
    _fp_delivery_notification,
    _fp_legitimate_otp,
    _fp_transaction_receipt,
    _fp_low_indicator_high_confidence,
    _fp_subscription_reminder,
    _fn_obfuscated_url,
    _fn_unicode_spoofing,
    _fn_urgency_with_payment,
    _fn_credential_harvesting,
    _fn_social_engineering,
    _fn_fake_support,
    _fn_qr_payment_scam,
    _fn_investment_scam,
    _fn_obfuscated_contact,
    _compute_fp_adjustment,
    _compute_fn_adjustment,
    ALL_RULES,
    FP_RULES,
    FN_RULES,
)


def _make_analysis(**overrides):
    base = {
        "prediction": "scam",
        "confidence": 0.85,
        "_original_text": "",
        "detected_indicators": [],
        "entities": [],
        "rule_score": 0.0,
        "reasons": [],
    }
    base.update(overrides)
    return base


class TestFPRules:
    def test_fp_banking_notification_matches(self):
        analysis = _make_analysis(
            _original_text="Your SBI account has been credited with Rs 15000. Available balance: Rs 45200.",
        )
        assert _fp_legitimate_banking_notification(analysis) is True

    def test_fp_banking_notification_skipped_safe(self):
        analysis = _make_analysis(prediction="safe")
        assert _fp_legitimate_banking_notification(analysis) is False

    def test_fp_banking_notification_with_url_skipped(self):
        analysis = _make_analysis(
            _original_text="Your SBI account has been credited. Click http://evil.xyz",
            entities=[{"type": "url", "value": "http://evil.xyz"}],
            detected_indicators=["Suspicious URL"],
        )
        assert _fp_legitimate_banking_notification(analysis) is False

    def test_fp_government_alert_matches(self):
        analysis = _make_analysis(
            _original_text="PM Modi scheme: Your pension is approved.",
        )
        assert _fp_government_alert(analysis) is True

    def test_fp_government_alert_with_url_skipped(self):
        analysis = _make_analysis(
            _original_text="PM Modi scheme: Click http://evil.xyz",
            entities=[{"type": "url", "value": "http://evil.xyz"}],
            detected_indicators=["Suspicious URL"],
        )
        assert _fp_government_alert(analysis) is False

    def test_fp_delivery_notification_matches(self):
        analysis = _make_analysis(
            _original_text="Your Amazon order has been shipped. Track here.",
        )
        assert _fp_delivery_notification(analysis) is True

    def test_fp_delivery_notification_with_url_skipped(self):
        analysis = _make_analysis(
            _original_text="Your order has been shipped. Click http://evil.xyz",
            entities=[{"type": "url", "value": "http://evil.xyz"}],
            detected_indicators=["Suspicious URL"],
        )
        assert _fp_delivery_notification(analysis) is False

    def test_fp_legitimate_otp_matches(self):
        analysis = _make_analysis(
            _original_text="Your OTP for transaction is 784512. Valid for 10 minutes.",
            detected_indicators=["OTP Request"],
        )
        assert _fp_legitimate_otp(analysis) is True

    def test_fp_legitimate_otp_with_share_skipped(self):
        analysis = _make_analysis(
            _original_text="Share your OTP 784512 with us.",
            detected_indicators=["OTP Request"],
        )
        assert _fp_legitimate_otp(analysis) is False

    def test_fp_transaction_receipt_matches(self):
        analysis = _make_analysis(
            _original_text="Your transaction of Rs 15000 has been processed. Ref No: TXN7845.",
        )
        assert _fp_transaction_receipt(analysis) is True

    def test_fp_transaction_receipt_with_threat_skipped(self):
        analysis = _make_analysis(
            _original_text="Your account will be blocked. Transaction failed.",
            detected_indicators=["Account Threat"],
        )
        assert _fp_transaction_receipt(analysis) is False

    def test_fp_low_indicator_high_confidence_matches(self):
        analysis = _make_analysis(
            confidence=0.75,
            detected_indicators=["Urgency Language"],
            entities=[],
            rule_score=20,
        )
        assert _fp_low_indicator_high_confidence(analysis) is True

    def test_fp_low_indicator_high_confidence_many_indicators_skipped(self):
        analysis = _make_analysis(
            confidence=0.75,
            detected_indicators=["Urgency Language", "Suspicious URL"],
        )
        assert _fp_low_indicator_high_confidence(analysis) is False

    def test_fp_subscription_reminder_matches(self):
        analysis = _make_analysis(
            _original_text="Your Netflix subscription renewal is due.",
        )
        assert _fp_subscription_reminder(analysis) is True

    def test_fp_subscription_reminder_with_url_skipped(self):
        analysis = _make_analysis(
            _original_text="Your subscription renewal is due. Click http://evil.xyz",
            entities=[{"type": "url", "value": "http://evil.xyz"}],
            detected_indicators=["Suspicious URL"],
        )
        assert _fp_subscription_reminder(analysis) is False


class TestFNRules:
    def test_fn_obfuscated_url_matches(self):
        analysis = _make_analysis(prediction="safe", _original_text="Click bit[dot]ly/abc123")
        assert _fn_obfuscated_url(analysis) is True

    def test_fn_obfuscated_url_hxxp_matches(self):
        analysis = _make_analysis(prediction="safe", _original_text="Visit hxxp://evil.xyz")
        assert _fn_obfuscated_url(analysis) is True

    def test_fn_obfuscated_url_click_here(self):
        analysis = _make_analysis(prediction="safe", _original_text="Click here to claim your prize")
        assert _fn_obfuscated_url(analysis) is True

    def test_fn_obfuscated_url_hxxp(self):
        analysis = _make_analysis(prediction="safe", _original_text="Visit hxxp://evil.xyz")
        assert _fn_obfuscated_url(analysis) is True

    def test_fn_unicode_spoofing_matches(self):
        analysis = _make_analysis(prediction="safe", _original_text="Click https://sérvicë.com")
        assert _fn_unicode_spoofing(analysis) is True

    def test_fn_unicode_spoofing_plain_text_skipped(self):
        analysis = _make_analysis(prediction="scam", _original_text="Hello world")
        assert _fn_unicode_spoofing(analysis) is False

    def test_fn_urgency_with_payment_matches(self):
        analysis = _make_analysis(
            prediction="safe",
            _original_text="URGENT: Pay Rs 5000 now or your account will be blocked.",
            detected_indicators=["Urgency Language", "Payment Request"],
        )
        assert _fn_urgency_with_payment(analysis) is True

    def test_fn_credential_harvesting_matches(self):
        analysis = _make_analysis(
            prediction="safe",
            _original_text="Share your OTP and bank details to verify your account.",
        )
        assert _fn_credential_harvesting(analysis) is True

    def test_fn_social_engineering_matches(self):
        analysis = _make_analysis(
            prediction="safe",
            _original_text="Congratulations! You won a prize. Click to claim your free gift now!",
        )
        assert _fn_social_engineering(analysis) is True

    def test_fn_social_engineering_low_score(self):
        analysis = _make_analysis(prediction="safe", _original_text="Hello, how are you?")
        assert _fn_social_engineering(analysis) is False

    def test_fn_fake_support_matches(self):
        analysis = _make_analysis(
            prediction="safe",
            _original_text="Call our customer care on 18001234567 for refund.",
        )
        assert _fn_fake_support(analysis) is True

    def test_fn_fake_support_without_phone_skipped(self):
        analysis = _make_analysis(
            prediction="safe",
            _original_text="Contact customer care for help.",
        )
        assert _fn_fake_support(analysis) is False

    def test_fn_qr_payment_scam_matches(self):
        analysis = _make_analysis(
            prediction="safe",
            detected_indicators=["QR Code Request", "Payment Request"],
        )
        assert _fn_qr_payment_scam(analysis) is True

    def test_fn_investment_scam_matches(self):
        analysis = _make_analysis(
            prediction="safe",
            _original_text="Guaranteed 100% profit on crypto investment. Limited offer!",
        )
        assert _fn_investment_scam(analysis) is True

    def test_fn_obfuscated_contact_matches(self):
        analysis = _make_analysis(
            _original_text="Contact us at support (at) example (dot) com",
        )
        assert _fn_obfuscated_contact(analysis) is True


class TestAdjustments:
    def test_fp_adjustment_banking(self):
        analysis = _make_analysis(
            _original_text="Your SBI account has been credited with Rs 15000. Available balance: Rs 45200.",
        )
        impact, applied = _compute_fp_adjustment(analysis)
        assert impact > 0
        assert any(r["rule_id"] == "FP-001" for r in applied)

    def test_fn_adjustment_obfuscated(self):
        analysis = _make_analysis(
            prediction="safe",
            _original_text="Click bit[dot]ly/abc123",
        )
        impact, applied = _compute_fn_adjustment(analysis)
        assert impact > 0
        assert any(r["rule_id"] == "FN-001" for r in applied)

    def test_fp_adjustment_capped(self):
        analysis = _make_analysis(
            _original_text="Your SBI account has been credited. Track order. OTP is 784512. Subscription due.",
            detected_indicators=["OTP Request"],
        )
        impact, applied = _compute_fp_adjustment(analysis)
        assert impact <= 40

    def test_fn_adjustment_capped(self):
        analysis = _make_analysis(
            prediction="safe",
            _original_text="URGENT: Pay now. Share your OTP. Call customer care 18001234567. Invest in crypto guaranteed profit. Click bit.ly/xyz",
            detected_indicators=["QR Code Request", "Payment Request", "Urgency Language"],
        )
        impact, applied = _compute_fn_adjustment(analysis)
        assert impact <= 40


class TestAllRules:
    def test_all_rules_count(self):
        assert len(FP_RULES) == 14
        assert len(FN_RULES) == 12
        assert len(ALL_RULES) == 26

    def test_all_rules_have_unique_ids(self):
        ids = [r.rule_id for r in ALL_RULES]
        assert len(ids) == len(set(ids))

    def test_all_rules_have_reasons(self):
        for r in ALL_RULES:
            assert r.reason

    def test_fp_rules_are_fp_reduction(self):
        for r in FP_RULES:
            assert r.category == "fp_reduction"
            assert r.confidence_impact < 0

    def test_fn_rules_are_fn_reduction(self):
        for r in FN_RULES:
            assert r.category == "fn_reduction"
            assert r.confidence_impact > 0
