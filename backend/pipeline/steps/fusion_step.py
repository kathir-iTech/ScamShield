from typing import Any

from services.threat_intelligence_service import fuse_connector_results

from ..step import AnalysisStep


class FusionStep(AnalysisStep):
    def __init__(self) -> None:
        super().__init__(step_id="fusion", name="Threat Intel Fusion", priority=120, dependencies=["connector"])

    def execute(self, context: Any) -> Any:
        connector_matches = context.data.connector_matches
        fusion = fuse_connector_results(connector_matches)
        fusion_dict = fusion.to_dict()
        context.data.threat_intel_fusion = fusion_dict
        rep = context.data.investigation_report
        if isinstance(rep, dict):
            rep["threat_intel_fusion"] = fusion_dict
        return self._ok({
            "threat_intel_fusion": fusion_dict,
        })
