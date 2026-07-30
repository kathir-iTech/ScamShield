__all__ = [
    "analyze_text",
    "PipelineError",
    "fuse_connector_results",
    "EvidenceRank",
    "ConflictRecord",
    "FuseResult",
]


def __getattr__(name):
    import importlib
    if name in ("analyze_text", "PipelineError"):
        return getattr(importlib.import_module("services.orchestrator"), name)
    if name in ("fuse_connector_results", "EvidenceRank", "ConflictRecord", "FuseResult"):
        return getattr(importlib.import_module("services.threat_intelligence_service"), name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
