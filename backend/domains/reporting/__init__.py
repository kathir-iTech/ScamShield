__all__ = [
    "generate_report",
    "generate_investigation_report",
]


def __getattr__(name):
    import importlib
    return getattr(importlib.import_module("domains.reporting.public"), name)
