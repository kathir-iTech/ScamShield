from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class PipelineData:
    """Typed shared data passed between pipeline steps.

    This replaces the untyped Dict[str, Any] pattern to provide
    compile-time safety and self-documenting step interfaces.
    """
    # ML step outputs
    prediction: str = "safe"
    confidence: float = 0.0

    # Rules step outputs
    rule_score: float = 0.0
    rule_label: str = "LOW"
    reasons: List[str] = field(default_factory=list)
    suggested_action: str = ""

    # Explanation step outputs
    summary: str = ""
    risk_level: str = "VERY_LOW"
    scam_category: str = "Unknown"
    detected_indicators: List[str] = field(default_factory=list)
    threats: List[str] = field(default_factory=list)
    recommended_actions: List[str] = field(default_factory=list)

    # Intelligence step outputs
    entities: List[Dict[str, Any]] = field(default_factory=list)
    entity_summary: Dict[str, Any] = field(default_factory=lambda: {
        "total_entities": 0, "by_type": {}, "threat_indicators": [],
    })
    entity_risk: Dict[str, Any] = field(default_factory=lambda: {
        "high": [], "medium": [], "low": [],
    })

    # Evidence step outputs
    decision_score: int = 0
    decision_level: str = "SAFE"
    decision_reasoning: str = ""
    supporting_evidence: List[Dict[str, Any]] = field(default_factory=list)
    conflicting_evidence: List[Dict[str, Any]] = field(default_factory=list)
    confidence_breakdown: Dict[str, int] = field(default_factory=lambda: {
        "ml": 0, "rules": 0, "entities": 0, "explanation": 0, "overall": 0,
    })
    risk_breakdown: Dict[str, int] = field(default_factory=lambda: {
        "credential_theft": 0, "financial_loss": 0, "identity_theft": 0,
        "malware": 0, "social_engineering": 0,
    })
    recommended_priority: str = "LOW"
    recommended_action: str = "Ignore"

    # Assessment step outputs
    assessment_score: int = 0
    assessment_band: str = "Suitable for normal communication"
    assessment_confidence: str = "LOW"
    assessment_summary: str = ""
    business_reason: str = ""
    technical_reason: str = ""
    review_required: bool = False
    manual_review_reason: str = ""

    # Refinement step outputs
    refined_prediction: str = ""
    refined_assessment_score: int = 0
    refined_assessment_confidence: str = ""
    refined_review_required: bool = False
    refinement_applied_rules: List[Any] = field(default_factory=list)
    refinement_summary: str = ""
    decision_stable: bool = True
    stability_concerns: List[str] = field(default_factory=list)

    # Reasoning step outputs
    reasoning_family: str = ""
    reasoning_subfamily: str = ""
    reasoning_family_confidence: float = 0.0
    reasoning_summary: str = ""
    reasoning_evidence_graph: Dict[str, Any] = field(default_factory=dict)
    reasoning_decision_trace: Dict[str, Any] = field(default_factory=dict)
    reasoning_primary_evidence: List[Dict[str, Any]] = field(default_factory=list)
    reasoning_supporting_evidence: List[Dict[str, Any]] = field(default_factory=list)
    reasoning_weak_evidence: List[Dict[str, Any]] = field(default_factory=list)
    reasoning_contradictory_evidence: List[Dict[str, Any]] = field(default_factory=list)
    reasoning_dominant_evidence_chain: List[str] = field(default_factory=list)

    # Report step output
    investigation_report: Dict[str, Any] = field(default_factory=dict)

    # Knowledge step outputs
    knowledge_matches: List[Dict[str, Any]] = field(default_factory=list)
    advisory_references: List[Dict[str, Any]] = field(default_factory=list)
    historical_matches: List[Dict[str, Any]] = field(default_factory=list)

    # Connector step outputs
    connector_matches: List[Dict[str, Any]] = field(default_factory=list)

    # Fusion step output
    threat_intel_fusion: Dict[str, Any] = field(default_factory=dict)

    # Extra fields (unknown keys from step data, for backward compat)
    _extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        for field_name in self.__dataclass_fields__:
            if field_name == "_extra":
                continue
            result[field_name] = getattr(self, field_name)
        result.update(self._extra)
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> PipelineData:
        instance = cls()
        instance.update_from(data)
        return instance

    def update_from(self, data: Dict[str, Any]) -> None:
        for key, value in data.items():
            if key in self.__dataclass_fields__ and key != "_extra":
                setattr(self, key, value)
            else:
                self._extra[key] = value

    def __contains__(self, key: str) -> bool:
        if key in self.__dataclass_fields__ and key != "_extra":
            return True
        return key in self._extra

    def __getitem__(self, key: str) -> Any:
        if key in self.__dataclass_fields__ and key != "_extra":
            return getattr(self, key)
        if key in self._extra:
            return self._extra[key]
        raise KeyError(f"Unknown field: {key}")
