from typing import Dict

from core.context import get_request_id
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
