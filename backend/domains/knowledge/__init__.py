__all__ = [
    "enrich_analysis",
    "enrich_investigation_result",
    "search_by_indicator",
]


def __getattr__(name):
    import importlib
    return getattr(importlib.import_module("domains.knowledge.public"), name)
