from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Optional, Type

from .contracts import PipelineStep
from .exceptions import DependencyError
from .types import StepHealth, StepID


class StepRegistry:
    def __init__(self) -> None:
        self._steps: Dict[StepID, PipelineStep] = {}
        self._order: List[StepID] = []

    def register(self, step: PipelineStep) -> None:
        self._steps[step.step_id] = step
        self._order = []

    def get(self, step_id: StepID) -> Optional[PipelineStep]:
        return self._steps.get(step_id)

    def all(self) -> List[PipelineStep]:
        return list(self._steps.values())

    def resolve_order(self) -> List[StepID]:
        if self._order:
            return self._order

        steps = self._steps
        visited: set[str] = set()
        resolved: list[str] = []
        in_progress: set[str] = set()

        def dfs(step_id: str) -> None:
            if step_id in resolved:
                return
            if step_id in in_progress:
                raise DependencyError(step_id, f"circular dependency detected")
            if step_id not in steps:
                return
            in_progress.add(step_id)
            step = steps[step_id]
            for dep_id in step.dependencies:
                if dep_id in steps:
                    dfs(dep_id)
                elif not step.optional:
                    raise DependencyError(step_id, dep_id)
            in_progress.remove(step_id)
            resolved.append(step_id)
            visited.add(step_id)

        sorted_ids = sorted(steps.keys(), key=lambda sid: steps[sid].priority)
        for sid in sorted_ids:
            if sid not in visited:
                dfs(sid)

        self._order = resolved
        return self._order

    def enabled_steps(self) -> List[PipelineStep]:
        return [s for s in self._steps.values() if not s.disabled]

    def health_check(self) -> Dict[StepID, StepHealth]:
        return {sid: step.health for sid, step in self._steps.items()}

    def disable(self, step_id: StepID) -> None:
        step = self._steps.get(step_id)
        if step:
            step.disabled = True
            self._order = []

    def enable(self, step_id: StepID) -> None:
        step = self._steps.get(step_id)
        if step:
            step.disabled = False
            self._order = []

    def __contains__(self, step_id: StepID) -> bool:
        return step_id in self._steps
