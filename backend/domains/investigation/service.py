import uuid
from typing import Any, Dict, List

from core.constants import UNKNOWN_CATEGORY
from domains.shared.utils import normalise

from .models import InvestigationArtefact, InvestigationResult
from .entities import _validate_artefacts, _merge_entities, _detect_repeated_indicators
from .timeline import _analyse_artefacts, _build_timeline
from .campaign import _detect_campaign, _build_investigation_summary
from .graph import _build_relationship_graph
from .risk import _compute_global_risk


def investigate(artefacts: List[Dict]) -> InvestigationResult:
    validated = _validate_artefacts(artefacts)
    if not validated:
        return InvestigationResult(
            investigation_id=str(uuid.uuid4()),
            artefacts_analysed=0,
            global_risk={"overall_risk": "UNKNOWN", "overall_score": 0, "confidence": 0.0},
        )

    analysed = _analyse_artefacts(validated)
    merged = _merge_entities(analysed)
    repeated = _detect_repeated_indicators(analysed)
    timeline = _build_timeline(analysed)
    campaign = _detect_campaign(analysed, merged)
    relationship_graph = _build_relationship_graph(analysed, merged, campaign)
    global_risk = _compute_global_risk(analysed, merged, repeated, campaign)

    strongest = global_risk.get("strongest_evidence", [])
    weakest = global_risk.get("weakest_signals", [])
    questions = global_risk.get("open_questions", [])
    summary = _build_investigation_summary(analysed, merged, repeated, campaign, global_risk)

    def _artefact_result(a: InvestigationArtefact) -> Dict:
        return {
            "index": a.index,
            "type": a.artefact_type,
            "text_preview": a.text[:100],
            "prediction": a.analysis.get("prediction", ""),
            "assessment_score": a.analysis.get("assessment_score", 0),
            "assessment_confidence": a.analysis.get("assessment_confidence", ""),
            "scam_category": a.analysis.get("scam_category", ""),
            "reasoning_family": a.analysis.get("reasoning_family", ""),
        }

    report = {
        "investigation_id": str(uuid.uuid4()),
        "artefacts_analysed": len(analysed),
        "artefacts": [_artefact_result(a) for a in analysed],
        "investigation_summary": summary,
        "global_risk": {
            "overall_risk": global_risk["overall_risk"],
            "overall_score": global_risk["overall_score"],
            "confidence": global_risk["confidence"],
            "dominant_family": global_risk["dominant_family"],
        },
        "campaign": {
            "detected": campaign["campaign_detected"],
            "confidence": campaign["confidence"],
            "summary": campaign["summary"],
        },
        "timeline": timeline,
        "merged_entity_count": sum(len(v) for v in merged.values()),
        "repeated_indicator_count": sum(repeated.values()),
        "relationship_graph": {
            "nodes": relationship_graph["nodes"],
            "edges": relationship_graph["edges"],
        },
    }

    return InvestigationResult(
        investigation_id=report["investigation_id"],
        artefacts_analysed=len(analysed),
        merged_entities=merged,
        repeated_indicators=repeated,
        timeline=timeline,
        campaign=campaign,
        relationship_graph=relationship_graph,
        global_risk=global_risk,
        strongest_evidence=strongest,
        weakest_signals=weakest,
        open_questions=questions,
        investigation_report=report,
        artefact_summaries=[_artefact_result(a) for a in analysed],
    )
