"""Regression tests for entity preservation in clean_text."""

from utils.text import clean_text, extract_entities, preserve_placeholders, restore_placeholders


class TestExtractEntities:
    def test_extract_urls(self):
        entities = extract_entities("Visit https://flipkart.com/track for tracking")
        assert "https://flipkart.com/track" in entities["urls"]

    def test_extract_emails(self):
        entities = extract_entities("Email support@example.com for help")
        assert "support@example.com" in entities["emails"]

    def test_extract_phones(self):
        entities = extract_entities("Call +91-9876543210 now")
        assert any("9876543210" in p for p in entities["phones"])

    def test_extract_upi(self):
        entities = extract_entities("Pay to user@paytm")
        assert "user@paytm" in entities["upis"]

    def test_extract_no_entities(self):
        entities = extract_entities("Hello world")
        assert all(len(v) == 0 for v in entities.values())

    def test_extract_multiple_urls(self):
        entities = extract_entities("A https://a.com B https://b.com C")
        assert len(entities["urls"]) == 2

    def test_extract_mixed_entities(self):
        entities = extract_entities("Email a@b.com and call +1-234-567-8900")
        assert len(entities["emails"]) == 1
        assert len(entities["phones"]) >= 1


class TestPreservePlaceholders:
    def test_preserve_url(self):
        text, ph = preserve_placeholders("Check https://example.com")
        assert "__url_0__" in text
        assert ph["__url_0__"] == "https://example.com"

    def test_preserve_email(self):
        text, ph = preserve_placeholders("Contact a@b.com")
        assert "__email_0__" in text
        assert ph["__email_0__"] == "a@b.com"

    def test_no_entities(self):
        text, ph = preserve_placeholders("Hello world")
        assert text == "Hello world"
        assert len(ph) == 0

    def test_preserve_multiple_types(self):
        text, ph = preserve_placeholders("Email a@b.com and call +1-234-567-8900")
        assert "__email_0__" in text
        assert "__phone_1__" in text

    def test_preserve_only_known_upi_handles(self):
        text, ph = preserve_placeholders("Pay user@paytm or user@paypal")
        assert "__upi_0__" in text
        assert "user@paypal" not in str(ph)


class TestRestorePlaceholders:
    def test_restore_url(self):
        text, ph = preserve_placeholders("https://example.com")
        restored = restore_placeholders("before __url_0__ after", ph)
        assert restored == "before https://example.com after"

    def test_restore_no_placeholders(self):
        restored = restore_placeholders("hello", {})
        assert restored == "hello"

    def test_roundtrip(self):
        original = "Contact support@company.com or visit https://company.com"
        text, ph = preserve_placeholders(original)
        restored = restore_placeholders(text, ph)
        assert restored == original


class TestCleanText:
    def test_preserves_url(self):
        result = clean_text("Visit https://example.com/page")
        assert "https://example.com/page" in result

    def test_preserves_email(self):
        result = clean_text("Email test@example.com")
        assert "test@example.com" in result

    def test_preserves_phone(self):
        result = clean_text("Call +91-9876543210")
        assert "+91-9876543210" in result

    def test_lowercases(self):
        result = clean_text("HELLO World")
        assert result == "hello world"

    def test_strips_punctuation(self):
        result = clean_text("Hello!!! How are you?")
        assert "!!!" not in result
        assert "?" not in result
        assert result == "hello how are you"

    def test_collapses_whitespace(self):
        result = clean_text("hello    world\n\n  test")
        assert result == "hello world test"

    def test_empty_string(self):
        assert clean_text("") == ""

    def test_only_punctuation(self):
        assert clean_text("!!! ???") == ""

    def test_url_with_punctuation(self):
        result = clean_text("Check https://example.com/page?q=1!")
        assert "https://example.com/page?q=1" in result

    def test_email_in_text(self):
        result = clean_text("My email is user@domain.com")
        assert "user@domain.com" in result

    def test_unicode_text(self):
        result = clean_text("Check your OTP: 123456. Do not share!")
        assert "123456" in result
        assert "otp" in result

    def test_tamil_text(self):
        result = clean_text("உங்கள் OTP 123456. இதை யாருடனும் பகிர வேண்டாம்")
        assert "otp" in result
        assert "123456" in result

    def test_bengali_text(self):
        result = clean_text("আপনার OTP হল 123456")
        assert "otp" in result
        assert "123456" in result

    def test_tanglish_text(self):
        result = clean_text("Unga OTP 123456. Yaarudanum share pannathinga")
        assert "otp" in result
        assert "123456" in result

    def test_multiple_entities(self):
        result = clean_text("Email a@b.com or call +1-234-567-8900. Visit https://site.com")
        assert "a@b.com" in result
        assert "+1-234-567-8900" in result
        assert "https://site.com" in result

    def test_entity_at_start(self):
        result = clean_text("https://site.com is the link")
        assert result.startswith("https://site.com")

    def test_entity_at_end(self):
        result = clean_text("The link is https://site.com")
        assert result.endswith("https://site.com")

    def test_upi_preserved(self):
        result = clean_text("Pay to user@paytm")
        assert "user@paytm" in result

    def test_mixed_case_preserved_for_urls(self):
        result = clean_text("HTTP://EXAMPLE.COM/Path")
        assert "http://example.com/path" in result.lower() or "HTTP://EXAMPLE.COM/Path" in result

    def test_special_chars_around_entities(self):
        result = clean_text("Visit: https://site.com! (click now)")
        assert "https://site.com" in result
        assert "!" not in result

    def test_phone_with_country_code(self):
        result = clean_text("Call +1 (800) 123-4567 for support")
        assert "+1 (800) 123-4567" in result or "+1 800 123 4567" in result.replace("-", " ").replace("(", "").replace(")", "")

    def test_no_false_positive_digit_stripping(self):
        result = clean_text("Order #12345 has tracking ID ABC-789")
        assert "12345" in result
        assert "abc-789" in result or "abc789" in result
