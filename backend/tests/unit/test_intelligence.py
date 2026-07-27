import pytest

from domains.intelligence.public import (
    analyze,
    extract_bank_accounts,
    extract_bank_names,
    extract_currency_amounts,
    extract_domains,
    extract_emails,
    extract_government_entities,
    extract_ifsc_codes,
    extract_ip_addresses,
    extract_otp_codes,
    extract_phones,
    extract_qr_keywords,
    extract_shortened_urls,
    extract_social_handles,
    extract_suspicious_tlds,
    extract_tracking_ids,
    extract_transaction_ids,
    extract_upi_ids,
    extract_urls,
)


@pytest.mark.parametrize("func,text,expected_type", [
    (extract_urls, "Visit https://example.com/path now!", "url"),
    (extract_urls, "Click https://bit.ly/abc123", "shortened_url"),
    (extract_urls, "Visit https://evil-site.xyz/page", "suspicious_tld"),
    (extract_domains, "Visit example.com for info", "domain"),
    (extract_emails, "Contact us at support@company.com", "email"),
    (extract_phones, "Call +91-9876543210 now", "phone_indian"),
    (extract_phones, "Call +14445556666", "phone_international"),
    (extract_upi_ids, "Send money to user@paytm", "upi_id"),
    (extract_qr_keywords, "Scan the QR code to pay", "qr_keyword"),
    (extract_bank_names, "Your SBI account is blocked", "bank_name"),
    (extract_government_entities, "PM Modi scheme announced", "government_entity"),
    (extract_currency_amounts, "Pay Rs 50,000 now", "currency_amount"),
    (extract_otp_codes, "Your OTP is 482916", "otp_code"),
    (extract_ip_addresses, "Server at 192.168.1.1", "ip_address"),
    (extract_social_handles, "Join @trading_king", "social_handle"),
    (extract_ifsc_codes, "IFSC: ICIC0001234", "ifsc_code"),
    (extract_bank_accounts, "Account: 123456789012", "bank_account"),
    (extract_tracking_ids, "Tracking ID EA123456789IN for courier", "tracking_id"),
    (extract_transaction_ids, "Txn ref: TXN20260725123456", "transaction_id"),
])
def test_entity_extractors(func, text, expected_type):
    result = func(text)
    assert any(e["type"] == expected_type for e in result), f"Expected {expected_type} in {result}"


@pytest.mark.parametrize("func,text", [
    (extract_shortened_urls, "Visit https://tinyurl.com/abc123"),
    (extract_suspicious_tlds, "Visit https://evil-site.top/page"),
])
def test_extract_url_specialized(func, text):
    result = func(text)
    assert len(result) >= 1


def test_analyze_returns_correct_structure():
    result = analyze("Test message with https://example.com")
    assert "entities" in result
    assert "entity_summary" in result
    assert "entity_risk" in result
    assert result["entity_summary"]["total_entities"] >= 1


def test_analyze_threat_indicators():
    result = analyze("Your OTP is 482916. Visit https://sbi-kyc.xyz")
    assert len(result["entity_summary"]["threat_indicators"]) >= 1


def test_entity_risk_categorization():
    result = analyze("Visit https://bit.ly/abc and call +91-9876543210")
    high_risk = result["entity_risk"]["high"]
    assert any(e["type"] == "shortened_url" for e in high_risk)


def test_deduplication():
    result = analyze("https://example.com https://example.com")
    entities = result["entities"]
    urls = [e for e in entities if e["type"] == "url"]
    assert len(urls) == 1


def test_otp_not_extracted_without_otp_keyword():
    result = extract_otp_codes("Your code is 1234")
    otp = [e for e in result if e["type"] == "otp_code"]
    assert len(otp) == 0
