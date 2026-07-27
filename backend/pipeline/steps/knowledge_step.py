from typing import Any

from domains.knowledge.public import enrich_analysis as knowledge_enrich

from ..step import AnalysisStep


class KnowledgeStep(AnalysisStep):
    def __init__(self) -> None:
        super().__init__(step_id="knowledge", name="Knowledge Enrichment", priority=100, dependencies=["report"])

    def execute(self, context: Any) -> Any:
        enrichment = knowledge_enrich(dict(context.shared))
        knowledge_matches = enrichment.get("knowledge_matches", [])
        advisory_references = enrichment.get("advisory_references", [])
        historical_matches = enrichment.get("historical_matches", [])
        rep = context.shared.get("investigation_report")
        if isinstance(rep, dict):
            rep["knowledge_enrichment"] = {
                "knowledge_matches": knowledge_matches,
                "advisory_references": advisory_references,
                "historical_matches": historical_matches,
            }
        return self._ok({
            "knowledge_matches": knowledge_matches,
            "advisory_references": advisory_references,
            "historical_matches": historical_matches,
        })
