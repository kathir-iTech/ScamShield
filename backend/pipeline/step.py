from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from .contracts import PipelineStep, StepResult
from .types import StepHealth, StepID, StepName, StepPriority, StepStatus


class AnalysisStep(ABC):
    def __init__(
        self,
        step_id: StepID,
        name: StepName,
        priority: StepPriority = 100,
        dependencies: Optional[List[str]] = None,
        optional: bool = False,
        disabled: bool = False,
        fatal: bool = False,
    ) -> None:
        self.step_id = step_id
        self.name = name
        self.priority = priority
        self.dependencies = dependencies or []
        self.optional = optional
        self.disabled = disabled
        self.fatal = fatal
        self._health = StepHealth()

    @property
    def health(self) -> StepHealth:
        return self._health

    def initialize(self) -> None:
        pass

    @abstractmethod
    def execute(self, context: Any) -> StepResult:
        ...

    def cleanup(self) -> None:
        pass

    def _ok(self, data: Dict[str, Any]) -> StepResult:
        return StepResult(step_id=self.step_id, status=StepStatus.COMPLETED, data=data)

    def _fail(self, error: str, data: Optional[Dict[str, Any]] = None) -> StepResult:
        return StepResult(
            step_id=self.step_id,
            status=StepStatus.FAILED,
            data=data or {},
            error=error,
        )

    def _skip(self, reason: str) -> StepResult:
        return StepResult(
            step_id=self.step_id,
            status=StepStatus.SKIPPED,
            data={},
            error=reason,
        )
