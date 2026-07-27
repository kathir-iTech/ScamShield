from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .contracts import PipelineContext as PipelineContextContract, StepResult
from .types import StepID, TelemetryEntry, StepStatus


@dataclass
class PipelineContext(PipelineContextContract):
    request_id: str
    text: str
    config: Dict[str, Any] = field(default_factory=dict)
    shared: Dict[str, Any] = field(default_factory=dict)
    telemetry: List[TelemetryEntry] = field(default_factory=list)
    step_results: Dict[StepID, StepResult] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def record_step(
        self,
        step_id: StepID,
        status: StepStatus,
        duration_ms: float,
        error: Optional[str] = None,
        warnings: Optional[List[str]] = None,
    ) -> None:
        self.telemetry.append(
            TelemetryEntry(
                step_id=step_id,
                status=status,
                duration_ms=duration_ms,
                error=error,
                warnings=warnings or [],
            )
        )

    def store_result(self, step_id: StepID, result: StepResult) -> None:
        self.step_results[step_id] = result
        self.shared.update(result.data)
