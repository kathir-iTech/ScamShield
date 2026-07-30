__all__ = [
    "investigate",
    "InvestigationResult",
]


def __getattr__(name):
    import importlib
    return getattr(importlib.import_module("domains.investigation.public"), name)
