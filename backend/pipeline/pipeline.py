from __future__ import annotations

import time
import uuid
from typing import Any, Dict, Optional

from core.logger import logger

from .context import PipelineContext
from .exceptions import PipelineError
from .registry import StepRegistry
from .result import PipelineResult
from .types import StepStatus


class PipelineRunner:
    def __init__(self, registry: StepRegistry, config: Optional[Dict[str, Any]] = None) -> None:
        self._registry = registry
        self._config = config or {}

    def run(self, text: str, request_id: Optional[str] = None) -> PipelineResult:
        ctx = PipelineContext(
            request_id=request_id or str(uuid.uuid4()),
            text=text,
            config=dict(self._config),
        )

        result = PipelineResult()
        start = time.perf_counter()
        order = self._registry.resolve_order()
        enabled = self._registry.enabled_steps()
        enabled_ids = {s.step_id for s in enabled}

        completed = 0
        for step_id in order:
            if step_id not in enabled_ids:
                ctx.record_step(step_id, StepStatus.DISABLED, 0.0)
                continue

            step = self._registry.get(step_id)
            if step is None:
                continue

            step_start = time.perf_counter()

            try:
                step_result = step.execute(ctx)
            except PipelineError:
                raise
            except Exception as e:
                duration = (time.perf_counter() - step_start) * 1000
                logger.warning("Pipeline step '%s' failed — skipping", step_id, exc_info=True)
                ctx.record_step(step_id, StepStatus.FAILED, duration, str(e))
                if step.fatal:
                    raise PipelineError(f"{step.name} failed — cannot continue") from e
                continue

            duration = (time.perf_counter() - step_start) * 1000
            ctx.record_step(
                step_id,
                step_result.status,
                duration,
                step_result.error,
                step_result.warnings,
            )

            if step_result.status in (StepStatus.COMPLETED, StepStatus.SKIPPED):
                completed += 1

            ctx.store_result(step_id, step_result)
            result.merge_step_data(step_id, step_result.data)

        total_duration = (time.perf_counter() - start) * 1000
        result.warnings = [t.error for t in ctx.telemetry if t.error]
        result.pipeline_summary = {
            "total_steps": len(order),
            "completed_steps": completed,
            "duration_ms": round(total_duration, 2),
            "has_errors": any(t.status == StepStatus.FAILED for t in ctx.telemetry),
            "warnings": result.warnings,
            "telemetry": [
                {
                    "step_id": t.step_id,
                    "status": t.status.value,
                    "duration_ms": round(t.duration_ms, 2),
                    "error": t.error,
                    "warnings": t.warnings,
                }
                for t in ctx.telemetry
            ],
        }

        return result




