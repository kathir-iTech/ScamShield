__all__ = [
    "analyze",
    "extract_urls", "extract_shortened_urls", "extract_suspicious_tlds",
    "extract_domains", "extract_emails", "extract_phones", "extract_upi_ids",
    "extract_qr_keywords", "extract_bank_names", "extract_government_entities",
    "extract_currency_amounts", "extract_otp_codes", "extract_ip_addresses",
    "extract_social_handles", "extract_ifsc_codes", "extract_bank_accounts",
    "extract_tracking_ids", "extract_transaction_ids",
]


def __getattr__(name):
    import importlib
    return getattr(importlib.import_module("domains.intelligence.public"), name)
