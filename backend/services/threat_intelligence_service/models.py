from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class EvidenceRank:
    indicator: str
    indicator_type: str
    matched: bool
    risk: str
    confidence: float
    source: str
    rank: str
    rank_reason: str
    summary: str = ""
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "indicator": self.indicator,
            "indicator_type": self.indicator_type,
            "matched": self.matched,
            "risk": self.risk,
            "confidence": self.confidence,
            "source": self.source,
            "rank": self.rank,
            "rank_reason": self.rank_reason,
            "summary": self.summary,
            "error": self.error,
        }


@dataclass
class ConflictRecord:
    indicator: str
    source_a: str
    verdict_a: str
    source_b: str
    verdict_b: str
    resolution: str
    resolution_reason: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "indicator": self.indicator,
            "source_a": self.source_a,
            "verdict_a": self.verdict_a,
            "source_b": self.source_b,
            "verdict_b": self.verdict_b,
            "resolution": self.resolution,
            "resolution_reason": self.resolution_reason,
        }


@dataclass
class FuseResult:
    overall_verdict: str
    overall_confidence: float
    overall_risk: str
    contributing_sources: List[Dict[str, Any]] = field(default_factory=list)
    agreement_score: float = 0.0
    conflict_score: float = 0.0
    missing_evidence: List[str] = field(default_factory=list)
    evidence_ranking: List[Dict[str, Any]] = field(default_factory=list)
    conflict_resolution: List[Dict[str, Any]] = field(default_factory=list)
    sources_consulted: int = 0
    matched_sources: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_verdict": self.overall_verdict,
            "overall_confidence": self.overall_confidence,
            "overall_risk": self.overall_risk,
            "contributing_sources": self.contributing_sources,
            "agreement_score": self.agreement_score,
            "conflict_score": self.conflict_score,
            "missing_evidence": self.missing_evidence,
            "evidence_ranking": self.evidence_ranking,
            "conflict_resolution": self.conflict_resolution,
            "sources_consulted": self.sources_consulted,
            "matched_sources": self.matched_sources,
        }
