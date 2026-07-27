import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class LookupResult:
    indicator: str
    indicator_type: str
    matched: bool
    risk: str
    confidence: float
    source: str
    summary: str = ""
    evidence: List[Dict] = field(default_factory=list)
    references: List[Dict] = field(default_factory=list)
    timestamp: float = 0.0
    latency: float = 0.0
    error: Optional[str] = None

    def __post_init__(self) -> None:
        if self.timestamp == 0.0:
            self.timestamp = time.time()

    def to_dict(self) -> Dict:
        return {
            "indicator": self.indicator,
            "indicator_type": self.indicator_type,
            "matched": self.matched,
            "risk": self.risk,
            "confidence": self.confidence,
            "source": self.source,
            "summary": self.summary,
            "evidence": self.evidence,
            "references": self.references,
            "timestamp": self.timestamp,
            "latency": self.latency,
            "error": self.error,
        }
