__all__ = [
    "reason",
    "refine",
    "check_decision_stability",
    "get_all_rules",
    "profile_errors",
]


def __getattr__(name):
    import importlib
    return getattr(importlib.import_module("domains.reasoning.public"), name)
