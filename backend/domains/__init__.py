__all__ = [
    "analyze",
    "extract_urls", "extract_shortened_urls", "extract_suspicious_tlds",
    "extract_domains", "extract_emails", "extract_phones", "extract_upi_ids",
    "extract_qr_keywords", "extract_bank_names", "extract_government_entities",
    "extract_currency_amounts", "extract_otp_codes", "extract_ip_addresses",
    "extract_social_handles", "extract_ifsc_codes", "extract_bank_accounts",
    "extract_tracking_ids", "extract_transaction_ids",
    "reason", "refine", "check_decision_stability", "get_all_rules", "profile_errors",
    "generate_report", "generate_investigation_report",
    "investigate", "InvestigationResult",
    "enrich_analysis", "enrich_investigation_result", "search_by_indicator",
    "assess", "build_evidence", "correlate_evidence", "detect_conflicts",
    "calculate_decision_score", "get_decision_level", "get_priority",
    "generate_reasoning", "build_confidence_breakdown", "build_risk_breakdown",
    "generate_explanation", "detect_category", "detect_indicators",
    "extract_threats", "extract_recommendations", "calculate_severity", "build_summary",
    "ScamShieldError", "ConfigurationError", "ValidationError", "ServiceError",
    "KnowledgeMatch",
    "normalise", "levenshtein", "digits_only",
]


def __getattr__(name):
    import importlib
    if name in ("analyze", "extract_urls", "extract_shortened_urls", "extract_suspicious_tlds",
                "extract_domains", "extract_emails", "extract_phones", "extract_upi_ids",
                "extract_qr_keywords", "extract_bank_names", "extract_government_entities",
                "extract_currency_amounts", "extract_otp_codes", "extract_ip_addresses",
                "extract_social_handles", "extract_ifsc_codes", "extract_bank_accounts",
                "extract_tracking_ids", "extract_transaction_ids"):
        return getattr(importlib.import_module("domains.intelligence.public"), name)
    if name in ("reason", "refine", "check_decision_stability", "get_all_rules", "profile_errors"):
        return getattr(importlib.import_module("domains.reasoning.public"), name)
    if name in ("generate_report", "generate_investigation_report"):
        return getattr(importlib.import_module("domains.reporting.public"), name)
    if name in ("investigate", "InvestigationResult"):
        return getattr(importlib.import_module("domains.investigation.public"), name)
    if name in ("enrich_analysis", "enrich_investigation_result", "search_by_indicator"):
        return getattr(importlib.import_module("domains.knowledge.public"), name)
    if name in ("assess", "build_evidence", "correlate_evidence", "detect_conflicts",
                "calculate_decision_score", "get_decision_level", "get_priority",
                "generate_reasoning", "build_confidence_breakdown", "build_risk_breakdown",
                "generate_explanation", "detect_category", "detect_indicators",
                "extract_threats", "extract_recommendations", "calculate_severity", "build_summary"):
        return getattr(importlib.import_module("domains.assessment.public"), name)
    if name in ("ScamShieldError", "ConfigurationError", "ValidationError", "ServiceError"):
        return getattr(importlib.import_module("domains.shared.exceptions"), name)
    if name == "KnowledgeMatch":
        return getattr(importlib.import_module("domains.shared.models"), name)
    if name in ("normalise", "levenshtein", "digits_only"):
        return getattr(importlib.import_module("domains.shared.utils"), name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
