from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from .types import StepHealth, StepID, StepStatus


class PipelineStep(Protocol):
    step_id: StepID
    name: str
    priority: int
    dependencies: list[str]
    optional: bool
    disabled: bool

    def initialize(self) -> None:
        ...

    def execute(self, context: Any) -> "StepResult":
        ...

    def cleanup(self) -> None:
        ...

    @property
    def health(self) -> "StepHealth":
        ...


@dataclass
class StepResult:
    step_id: StepID
    status: StepStatus
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    warnings: List[str] = field(default_factory=list)


class PipelineContext(Protocol):
    request_id: str
    text: str
    config: Dict[str, Any]
    shared: Dict[str, Any]
    telemetry: List[Any]
    step_results: Dict[StepID, StepResult]
    metadata: Dict[str, Any]
