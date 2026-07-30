__all__ = [
    "assess", "build_evidence", "correlate_evidence", "detect_conflicts",
    "calculate_decision_score", "get_decision_level", "get_priority",
    "generate_reasoning", "build_confidence_breakdown", "build_risk_breakdown",
    "generate_explanation", "detect_category", "detect_indicators",
    "extract_threats", "extract_recommendations", "calculate_severity", "build_summary",
]


def __getattr__(name):
    import importlib
    return getattr(importlib.import_module("domains.assessment.public"), name)
