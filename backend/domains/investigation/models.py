from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class InvestigationArtefact:
    index: int
    artefact_type: str
    text: str
    analysis: Dict[str, Any]


@dataclass
class MergedEntity:
    value: str
    entity_type: str
    occurrences: int
    first_seen: int
    sources: List[int]
    max_risk: str


@dataclass
class TimelineEvent:
    index: int
    artefact_index: int
    event_type: str
    description: str
    details: str = ""


@dataclass
class CampaignIndicators:
    shared_phones: List[str] = field(default_factory=list)
    shared_domains: List[str] = field(default_factory=list)
    shared_upi: List[str] = field(default_factory=list)
    shared_emails: List[str] = field(default_factory=list)
    shared_banks: List[str] = field(default_factory=list)
    shared_indicators: List[str] = field(default_factory=list)
    repeated_wording: bool = False
    same_scam_family: bool = False


@dataclass
class InvestigationResult:
    investigation_id: str
    artefacts_analysed: int
    merged_entities: Dict[str, List[Dict]] = field(default_factory=dict)
    repeated_indicators: Dict[str, int] = field(default_factory=dict)
    timeline: List[Dict] = field(default_factory=list)
    campaign: Dict = field(default_factory=dict)
    relationship_graph: Dict = field(default_factory=dict)
    global_risk: Dict = field(default_factory=dict)
    strongest_evidence: List[str] = field(default_factory=list)
    weakest_signals: List[str] = field(default_factory=list)
    open_questions: List[str] = field(default_factory=list)
    investigation_report: Dict = field(default_factory=dict)
    artefact_summaries: List[Dict] = field(default_factory=list)


_ARTEFACT_TYPES = frozenset({"sms", "screenshot", "whatsapp", "email", "telegram", "chat", "text"})
