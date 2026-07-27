from typing import Any

from connectors.manager import enrich_with_connectors

from ..step import AnalysisStep


class ConnectorStep(AnalysisStep):
    def __init__(self) -> None:
        super().__init__(step_id="connector", name="Connector Enrichment", priority=110, dependencies=["knowledge"])

    def execute(self, context: Any) -> Any:
        enrichment = enrich_with_connectors(dict(context.shared))
        rep = context.shared.get("investigation_report")
        if isinstance(rep, dict):
            rep["connector_enrichment"] = enrichment
        return self._ok({
            "connector_matches": enrichment,
        })
