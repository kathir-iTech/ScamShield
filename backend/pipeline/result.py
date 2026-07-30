from __future__ import annotations

from typing import Any, Dict, List, Optional

from .shared import PipelineData


class PipelineResult:
    def __init__(self) -> None:
        self._pipeline_data: PipelineData = PipelineData()
        self.warnings: List[str] = []
        self.pipeline_summary: Dict[str, Any] = {}
        self._data_cache: Optional[Dict[str, Any]] = None

    @property
    def telemetry(self) -> List[Dict[str, Any]]:
        return self.pipeline_summary.get("telemetry", [])

    @property
    def data(self) -> Dict[str, Any]:
        if self._data_cache is None:
            self._data_cache = self._pipeline_data.to_dict()
        return self._data_cache

    @data.setter
    def data(self, value: Dict[str, Any]) -> None:
        self._pipeline_data = PipelineData.from_dict(value)
        self._data_cache = value

    @property
    def pipeline_data(self) -> PipelineData:
        return self._pipeline_data

    def merge_step_data(self, step_id: str, data: Dict[str, Any]) -> None:
        self._pipeline_data.update_from(data)
        self._data_cache = None

    def to_dict(self) -> Dict[str, Any]:
        result = self._pipeline_data.to_dict()
        result["warnings"] = list(self.warnings)
        result["pipeline_summary"] = dict(self.pipeline_summary)
        return result
