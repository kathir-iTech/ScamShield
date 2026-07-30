from typing import Any

from domains.intelligence.public import analyze as threat_intel

from ..step import AnalysisStep


class IntelligenceStep(AnalysisStep):
    def __init__(self) -> None:
        super().__init__(step_id="intelligence", name="Threat Intelligence", priority=40, dependencies=["ml", "rules", "explanation"])

    def execute(self, context: Any) -> Any:
        intel = threat_intel(context.text)
        context.data.entities = intel["entities"]
        context.data.entity_summary = intel["entity_summary"]
        context.data.entity_risk = intel["entity_risk"]
        return self._ok({
            "entities": intel["entities"],
            "entity_summary": intel["entity_summary"],
            "entity_risk": intel["entity_risk"],
        })
