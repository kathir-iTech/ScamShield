from dataclasses import dataclass, field
from typing import Dict, List, Optional


THREAT_TYPES = frozenset({
    "url", "domain", "phone", "email", "upi",
    "bank", "bank_account", "ifsc", "qr", "keyword",
    "ip_address", "social_handle", "tracking_id", "transaction_id",
})

VALID_SOURCES = frozenset({
    "internal", "cert-in", "rbi", "npci", "bank", "community", "history",
})

VALID_RISKS = frozenset({"CRITICAL", "HIGH", "MEDIUM", "LOW"})


@dataclass
class ThreatReference:
    title: str
    url: str = ""
    source: str = ""
    date: str = ""


@dataclass
class ThreatRecord:
    indicator_id: str
    type: str
    value: str
    aliases: List[str] = field(default_factory=list)
    family: str = ""
    subfamily: str = ""
    risk: str = "MEDIUM"
    confidence: float = 0.5
    source: str = "internal"
    first_seen: str = ""
    last_seen: str = ""
    description: str = ""
    related_indicators: List[str] = field(default_factory=list)
    references: List[ThreatReference] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "indicator_id": self.indicator_id,
            "type": self.type,
            "value": self.value,
            "aliases": self.aliases,
            "family": self.family,
            "subfamily": self.subfamily,
            "risk": self.risk,
            "confidence": self.confidence,
            "source": self.source,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "description": self.description,
            "related_indicators": self.related_indicators,
            "references": [{"title": r.title, "url": r.url, "source": r.source, "date": r.date} for r in self.references],
        }


@dataclass
class AdvisoryRecord:
    advisory_id: str
    title: str
    source: str
    date: str
    summary: str
    recommendation: str
    affected_indicators: List[str] = field(default_factory=list)
    indicator_types: List[str] = field(default_factory=list)
    severity: str = "MEDIUM"
    url: str = ""
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "advisory_id": self.advisory_id,
            "title": self.title,
            "source": self.source,
            "date": self.date,
            "summary": self.summary,
            "recommendation": self.recommendation,
            "affected_indicators": self.affected_indicators,
            "indicator_types": self.indicator_types,
            "severity": self.severity,
            "url": self.url,
            "tags": self.tags,
        }


@dataclass
class HistoricalInvestigation:
    investigation_id: str
    date: str
    artefacts_analysed: int
    overall_risk: str
    overall_score: int
    dominant_family: str
    entities: Dict[str, List[Dict]] = field(default_factory=dict)
    indicators: Dict[str, int] = field(default_factory=dict)
    campaign_detected: bool = False
    summary: str = ""

    def to_dict(self) -> Dict:
        return {
            "investigation_id": self.investigation_id,
            "date": self.date,
            "artefacts_analysed": self.artefacts_analysed,
            "overall_risk": self.overall_risk,
            "overall_score": self.overall_score,
            "dominant_family": self.dominant_family,
            "entities": self.entities,
            "indicators": self.indicators,
            "campaign_detected": self.campaign_detected,
            "summary": self.summary,
        }


def validate_schema(data: Dict) -> List[str]:
    errors = []

    if not isinstance(data.get("indicator_id"), str) or not data["indicator_id"]:
        errors.append("Missing or invalid 'indicator_id'")

    itype = data.get("type", "")
    if itype not in THREAT_TYPES:
        errors.append(f"Invalid type '{itype}'. Valid: {', '.join(sorted(THREAT_TYPES))}")

    if not isinstance(data.get("value"), str) or not data["value"]:
        errors.append("Missing or invalid 'value'")

    source = data.get("source", "internal")
    if source not in VALID_SOURCES:
        errors.append(f"Invalid source '{source}'. Valid: {', '.join(sorted(VALID_SOURCES))}")

    risk = data.get("risk", "MEDIUM")
    if risk not in VALID_RISKS:
        errors.append(f"Invalid risk '{risk}'. Valid: {', '.join(sorted(VALID_RISKS))}")

    conf = data.get("confidence", 0.5)
    if not isinstance(conf, (int, float)) or not (0 <= conf <= 1):
        errors.append(f"confidence must be 0-1, got {conf}")

    return errors
