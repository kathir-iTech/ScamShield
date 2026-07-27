from __future__ import annotations

from typing import Any, Dict, List


_DEFAULTS: Dict[str, Any] = {
    "prediction": "safe",
    "confidence": 0.0,
    "rule_score": 0.0,
    "rule_label": "LOW",
    "reasons": [],
    "suggested_action": "",
    "summary": "",
    "risk_level": "VERY_LOW",
    "scam_category": "Unknown",
    "detected_indicators": [],
    "threats": [],
    "recommended_actions": [],
    "entities": [],
    "entity_summary": {"total_entities": 0, "by_type": {}, "threat_indicators": []},
    "entity_risk": {"high": [], "medium": [], "low": []},
    "decision_score": 0,
    "decision_level": "SAFE",
    "decision_reasoning": "",
    "supporting_evidence": [],
    "conflicting_evidence": [],
    "confidence_breakdown": {"ml": 0, "rules": 0, "entities": 0, "explanation": 0, "overall": 0},
    "risk_breakdown": {"credential_theft": 0, "financial_loss": 0, "identity_theft": 0, "malware": 0, "social_engineering": 0},
    "recommended_priority": "LOW",
    "recommended_action": "Ignore",
    "assessment_score": 0,
    "assessment_band": "Suitable for normal communication",
    "assessment_confidence": "LOW",
    "assessment_summary": "",
    "business_reason": "",
    "technical_reason": "",
    "review_required": False,
    "manual_review_reason": "",
    "investigation_report": {},
    "refined_prediction": "",
    "refined_assessment_score": 0,
    "refined_assessment_confidence": "",
    "refined_review_required": False,
    "refinement_applied_rules": [],
    "refinement_summary": "",
    "decision_stable": True,
    "stability_concerns": [],
    "reasoning_family": "",
    "reasoning_subfamily": "",
    "reasoning_family_confidence": 0.0,
    "reasoning_summary": "",
    "reasoning_evidence_graph": {},
    "reasoning_decision_trace": {},
    "reasoning_primary_evidence": [],
    "reasoning_supporting_evidence": [],
    "reasoning_weak_evidence": [],
    "reasoning_contradictory_evidence": [],
    "reasoning_dominant_evidence_chain": [],
    "knowledge_matches": [],
    "advisory_references": [],
    "historical_matches": [],
    "connector_matches": [],
    "threat_intel_fusion": {},
}


class PipelineResult:
    def __init__(self) -> None:
        self._data: Dict[str, Any] = dict(_DEFAULTS)
        self.warnings: List[str] = []
        self.pipeline_summary: Dict[str, Any] = {}

    @property
    def telemetry(self) -> List[Dict[str, Any]]:
        return self.pipeline_summary.get("telemetry", [])

    @property
    def data(self) -> Dict[str, Any]:
        return self._data

    @data.setter
    def data(self, value: Dict[str, Any]) -> None:
        self._data = value

    def merge_step_data(self, step_id: str, data: Dict[str, Any]) -> None:
        self._data.update(data)

    def to_dict(self) -> Dict[str, Any]:
        result = dict(self._data)
        result["warnings"] = list(self.warnings)
        result["pipeline_summary"] = dict(self.pipeline_summary)
        return result
