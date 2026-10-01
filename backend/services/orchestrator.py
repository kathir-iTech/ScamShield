import asyncio
import hashlib
import os
from typing import Dict

from core.cache import configure_cache, get_cache
from core.context import get_request_id
from core.diagnostics import set_pipeline_stages
from core.exceptions import ScamShieldError
from core.logger import logger
from core.metrics import metrics
from pipeline import PipelineRunner
from pipeline.registry import StepRegistry
from pipeline.steps import (
    AssessmentStep,
    ConnectorStep,
    EvidenceStep,
    ExplanationStep,
    FusionStep,
    IntelligenceStep,
    KnowledgeStep,
    MLStep,
    ReasoningStep,
    RefinementStep,
    ReportStep,
    RulesStep,
)


class PipelineError(ScamShieldError):
    pass


_registry = StepRegistry()
_registry.register(MLStep())
_registry.register(RulesStep())
_registry.register(ExplanationStep())
_registry.register(IntelligenceStep())
_registry.register(EvidenceStep())
_registry.register(AssessmentStep())
_registry.register(RefinementStep())
_registry.register(ReasoningStep())
_registry.register(ReportStep())
_registry.register(KnowledgeStep())
_registry.register(ConnectorStep())
_registry.register(FusionStep())

_runner = PipelineRunner(_registry)

set_pipeline_stages([step.name for step in _registry.enabled_steps()])


def _configure_cache_from_env() -> None:
    try:
        ttl = float(os.getenv("SCAMSHIELD_CACHE_TTL", "300"))
    except ValueError:
        ttl = 300.0
    try:
        maxsize = int(os.getenv("SCAMSHIELD_CACHE_MAXSIZE", "1024"))
    except ValueError:
        maxsize = 1024
    configure_cache(
        ttl=ttl,
        maxsize=maxsize,
        redis_url=os.getenv("SCAMSHIELD_REDIS_URL", ""),
    )


_configure_cache_from_env()


def analyze_text(text: str) -> Dict[str, object]:
    rid = get_request_id()
    logger.info(
        "Starting analysis pipeline",
        extra={"structured": {"request_id": rid}},
    )
    result = _runner.run(text, request_id=rid)
    output = result.to_dict()
    summary = output.get("pipeline_summary", {})
    total = summary.get("total_steps", 0)
    duration = summary.get("duration_ms", 0)
    for t in summary.get("telemetry", []):
        metrics.record_stage(t["step_id"], t["duration_ms"])
    logger.info(
        "Analysis pipeline complete (%d steps, %.2fms)",
        total,
        duration,
        extra={"structured": {"request_id": rid}},
    )
    return output


def _cache_key(text: str) -> str:
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return f"analyze:{digest}"


async def analyze_text_async(text: str) -> Dict[str, object]:
    rid = get_request_id()
    cache = get_cache()
    key = _cache_key(text)
    cached = cache.get(key)
    if isinstance(cached, dict):
        logger.info(
            "Analysis cache hit",
            extra={"structured": {"request_id": rid}},
        )
        return cached
    output = await asyncio.to_thread(analyze_text, text)
    cache.set(key, output)
    return output
