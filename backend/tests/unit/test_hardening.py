"""Tests for production hardening features — input defence, validation, sanitisation, resilience."""

import pytest
from core.exceptions import (
    EmptyTextError,
    ImageCorruptedError,
    ImageDecompressionBombError,
    TextTooLargeError,
)
from utils.validate import normalise_text, sanitise_text, validate_text_length


class TestInputValidation:
    def test_empty_text_raises(self):
        with pytest.raises(EmptyTextError):
            sanitise_text("")

    def test_whitespace_only_raises(self):
        with pytest.raises(EmptyTextError):
            sanitise_text("   \n\t  ")

    def test_text_too_long_raises(self):
        long_text = "x" * 10001
        with pytest.raises(TextTooLargeError):
            sanitise_text(long_text)

    def test_max_length_accepted(self):
        text = "x" * 10000
        result = sanitise_text(text)
        assert len(result) == 10000

    def test_control_characters_removed(self):
        text = "hello\x00world\x1f"
        result = normalise_text(text)
        assert "\x00" not in result
        assert "\x1f" not in result

    def test_zero_width_chars_removed(self):
        text = "hello\u200bworld\u200c"
        result = normalise_text(text)
        assert "\u200b" not in result
        assert "\u200c" not in result

    def test_unicode_normalisation_nfc(self):
        text = "\u0041\u030a"  # A + combining ring above
        result = normalise_text(text)
        assert result == "\u00c5"  # NFC-normalised Å

    def test_unassigned_unicode_removed(self):
        text = "hello\ufff0world"
        result = normalise_text(text)
        assert "\ufff0" not in result

    def test_multiple_newlines_collapsed(self):
        text = "line1\n\n\n\nline2"
        result = normalise_text(text)
        assert "\n\n\n" not in result

    def test_valid_text_passes(self):
        result = sanitise_text("Hello, this is a normal message.")
        assert result == "Hello, this is a normal message."

    def test_leading_trailing_whitespace_stripped(self):
        result = sanitise_text("  hello world  ")
        assert result == "hello world"


class TestImageValidation:
    def test_decompression_bomb_detected(self):
        from ocr import _validate_image
        from PIL import Image
        large = Image.new("RGB", (8000, 8000))
        with pytest.raises(ImageDecompressionBombError):
            _validate_image(large)

    def test_dimension_limit_respected(self):
        from ocr import _validate_image
        from PIL import Image
        small = Image.new("RGB", (100, 100))
        _validate_image(small)

    def test_corrupted_image_raises(self):
        from ocr import extract_text
        import tempfile
        import os
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as f:
            f.write(b"not a real image")
            path = f.name
        try:
            with pytest.raises(ImageCorruptedError):
                extract_text(path)
        finally:
            os.unlink(path)


class TestPipelineResilience:
    def test_pipeline_handles_unicode_input(self):
        from services.orchestrator import analyze_text
        texts = [
            "Hello\u200bWorld",  # zero-width
            "Caf\u00e9",  # accented
            "\u041f\u0440\u0438\u0432\u0435\u0442",  # Cyrillic
            "\u0041\u030a\u0041\u030a",  # decomposed
            "a" * 5000,  # long but valid
        ]
        for t in texts:
            try:
                result = analyze_text(t)
                assert "prediction" in result
            except Exception as exc:
                pytest.fail(f"Pipeline failed on '{t[:30]}': {exc}")

    def test_pipeline_handles_adversarial_input(self):
        from services.orchestrator import analyze_text
        texts = [
            "\x00\x01\x02" * 10,
            "\xff\xfe\x00" * 10,
            "\u0000\u0001\u0002" * 10,
            "\ufff0\ufff1\ufff2" * 10,
        ]
        for t in texts:
            try:
                result = analyze_text(t)
                assert "prediction" in result
            except Exception as exc:
                pytest.fail(f"Pipeline failed on adversarial input: {exc}")

    def test_pipeline_returns_required_fields_on_safe_text(self):
        from services.orchestrator import analyze_text
        result = analyze_text("Hello, this is a test message.")
        for key in ("prediction", "confidence", "rule_score", "assessment_score",
                     "decision_score", "risk_level", "scam_category"):
            assert key in result, f"Missing key: {key}"


class TestConcurrency:
    def test_ml_model_thread_safety(self):
        import concurrent.futures
        from predict import predict
        test_text = "Test message for concurrent access"
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
            futures = [ex.submit(predict, test_text) for _ in range(20)]
            for f in concurrent.futures.as_completed(futures):
                label, conf = f.result(timeout=10)
                assert label in ("scam", "safe")
                assert 0.0 <= conf <= 1.0

    def test_pipeline_thread_safety(self):
        import concurrent.futures
        from services.orchestrator import analyze_text
        test_text = "Test message for concurrent pipeline access"
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
            futures = [ex.submit(analyze_text, test_text) for _ in range(20)]
            for f in concurrent.futures.as_completed(futures):
                result = f.result(timeout=30)
                assert "prediction" in result
                assert "confidence" in result


class TestLogSanitisation:
    def test_mask_pii_numbers(self):
        from main import _mask_pii
        msg = "Phone: +919876543210"
        result = _mask_pii(msg)
        assert "+919876543210" not in result

    def test_mask_pii_emails(self):
        from main import _mask_pii
        msg = "Email: test@example.com"
        result = _mask_pii(msg)
        assert "test@example.com" not in result

    def test_mask_pii_otp(self):
        from main import _mask_pii
        msg = "Your OTP is 482916"
        result = _mask_pii(msg)
        assert "<OTP>" in result or "OTP" not in result

    def test_regex_timeout_large_input(self):
        from domains.intelligence.public import extract_urls
        large = "x" * 10000 + " https://example.com " + "y" * 10000
        result = extract_urls(large)
        assert len(result) >= 1
