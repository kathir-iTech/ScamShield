from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

StepID = str
StepName = str
StepPriority = int


class StepStatus(enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    DISABLED = "disabled"


class StepSeverity(enum.Enum):
    FATAL = "fatal"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class StepHealth:
    healthy: bool = True
    message: Optional[str] = None
    last_run_duration_ms: Optional[float] = None
    last_run_status: Optional[StepStatus] = None
    consecutive_failures: int = 0


@dataclass
class DependencySpec:
    step_id: StepID
    optional: bool = False


@dataclass
class TelemetryEntry:
    step_id: StepID
    status: StepStatus
    duration_ms: float
    error: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
