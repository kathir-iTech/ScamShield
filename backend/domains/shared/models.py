from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List


@dataclass
class KnowledgeMatch:
    indicator_id: str
    type: str
    value: str
    matched_value: str
    match_type: str
    confidence: float
    family: str = ""
    subfamily: str = ""
    risk: str = "MEDIUM"
    source: str = "internal"
    description: str = ""
    related_indicators: List[str] = field(default_factory=list)
    references: List[Dict] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "indicator_id": self.indicator_id,
            "type": self.type,
            "value": self.value,
            "matched_value": self.matched_value,
            "match_type": self.match_type,
            "confidence": self.confidence,
            "family": self.family,
            "subfamily": self.subfamily,
            "risk": self.risk,
            "source": self.source,
            "description": self.description,
            "related_indicators": self.related_indicators,
            "references": self.references,
        }


@dataclass
class AdvisoryMatch:
    advisory_id: str
    title: str
    source: str
    date: str
    summary: str
    recommendation: str
    relevance: float
    severity: str = "MEDIUM"
    matched_indicators: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "advisory_id": self.advisory_id,
            "title": self.title,
            "source": self.source,
            "date": self.date,
            "summary": self.summary,
            "recommendation": self.recommendation,
            "relevance": self.relevance,
            "severity": self.severity,
            "matched_indicators": self.matched_indicators,
        }


@dataclass
class HistoricalMatch:
    investigation_id: str
    date: str
    overall_risk: str
    overall_score: int
    dominant_family: str
    matched_entities: List[Dict] = field(default_factory=list)
    matched_indicators: List[Dict] = field(default_factory=list)
    shared_indicator_count: int = 0
    campaign_overlap: bool = False
    confidence: float = 0.0
    summary: str = ""

    def to_dict(self) -> Dict:
        return {
            "investigation_id": self.investigation_id,
            "date": self.date,
            "overall_risk": self.overall_risk,
            "overall_score": self.overall_score,
            "dominant_family": self.dominant_family,
            "matched_entities": self.matched_entities,
            "matched_indicators": self.matched_indicators,
            "shared_indicator_count": self.shared_indicator_count,
            "campaign_overlap": self.campaign_overlap,
            "confidence": self.confidence,
            "summary": self.summary,
        }


@dataclass
class EvidenceNode:
    node_id: str
    node_type: str
    label: str
    severity: str
    weight: float
    confidence: float
    source: str
    description: str = ""


@dataclass
class EvidenceEdge:
    source_id: str
    target_id: str
    relationship: str
    weight: float
    confidence: float
    reason: str = ""


@dataclass
class ReasoningResult:
    family: str = ""
    subfamily: str = ""
    family_confidence: float = 0.0
    primary_evidence: List[Dict] = field(default_factory=list)
    supporting_evidence: List[Dict] = field(default_factory=list)
    weak_evidence: List[Dict] = field(default_factory=list)
    contradictory_evidence: List[Dict] = field(default_factory=list)
    ignored_evidence: List[Dict] = field(default_factory=list)
    evidence_graph: Dict = field(default_factory=dict)
    decision_trace: Dict = field(default_factory=dict)
    reasoning_summary: str = ""
    dominant_evidence_chain: List[Dict] = field(default_factory=list)


@dataclass
class RefinementRule:
    rule_id: str
    description: str
    category: str
    priority: str
    confidence_impact: float
    condition: Callable[[Dict[str, Any]], bool]
    reason: str


@dataclass
class RefinementResult:
    refined_prediction: str
    refined_assessment_score: int
    refined_assessment_confidence: str
    refined_review_required: bool
    decision_stable: bool
    stability_concerns: List[str] = field(default_factory=list)
    applied_rules: List[Dict[str, Any]] = field(default_factory=list)
    refinement_summary: str = ""
