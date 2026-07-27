from typing import Dict, List

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


class EntityItem(BaseModel):
    value: str
    type: str
    confidence: float
    source: str
    risk: str = ""
    risk_reason: str = ""


class EntitySummary(BaseModel):
    total_entities: int
    by_type: Dict[str, int]
    threat_indicators: List[str]


class EntityRisk(BaseModel):
    high: List[EntityItem]
    medium: List[EntityItem]
    low: List[EntityItem]


class EvidenceItem(BaseModel):
    id: str
    type: str
    source: str
    description: str
    severity: str
    confidence: float
    weight: int


class ConfidenceBreakdown(BaseModel):
    ml: int
    rules: int
    entities: int
    explanation: int
    overall: int


class RiskBreakdown(BaseModel):
    credential_theft: int
    financial_loss: int
    identity_theft: int
    malware: int
    social_engineering: int


class AnalysisResponse(BaseModel):
    prediction: str
    confidence: float
    rule_score: float
    rule_label: str
    reasons: List[str]
    suggested_action: str
    summary: str
    risk_level: str
    scam_category: str
    detected_indicators: List[str]
    threats: List[str]
    recommended_actions: List[str]
    entities: List[EntityItem]
    entity_summary: EntitySummary
    entity_risk: EntityRisk
    decision_score: int
    decision_level: str
    decision_reasoning: str
    supporting_evidence: List[EvidenceItem]
    conflicting_evidence: List[EvidenceItem]
    confidence_breakdown: ConfidenceBreakdown
    risk_breakdown: RiskBreakdown
    recommended_priority: str
    recommended_action: str
    assessment_score: int
    assessment_band: str
    assessment_confidence: str
    assessment_summary: str
    business_reason: str
    technical_reason: str
    review_required: bool
    manual_review_reason: str
    investigation_report: Dict
    refined_prediction: str = ""
    refined_assessment_score: int = 0
    refined_assessment_confidence: str = ""
    refined_review_required: bool = False
    refinement_summary: str = ""
    decision_stable: bool = True
    stability_concerns: List[str] = []
    reasoning_family: str = ""
    reasoning_subfamily: str = ""
    reasoning_family_confidence: float = 0.0
    reasoning_primary_evidence: List[Dict] = []
    reasoning_supporting_evidence: List[Dict] = []
    reasoning_weak_evidence: List[Dict] = []
    reasoning_contradictory_evidence: List[Dict] = []
    reasoning_dominant_evidence_chain: List[str] = []
    reasoning_summary: str = ""
    knowledge_matches: List[Dict] = []
    advisory_references: List[Dict] = []
    historical_matches: List[Dict] = []
    connector_matches: List[Dict] = []
    threat_intel_fusion: Dict = {}


class ImageAnalysisResponse(AnalysisResponse):
    extracted_text: str


class InvestigationArtefactResult(BaseModel):
    index: int
    type: str
    text_preview: str
    prediction: str
    assessment_score: int
    assessment_confidence: str
    scam_category: str
    reasoning_family: str


class TimelineEvent(BaseModel):
    index: int
    artefact: int
    event_type: str
    description: str
    details: str


class CampaignResult(BaseModel):
    campaign_detected: bool
    confidence: float
    indicators: Dict
    summary: str


class RelationshipGraph(BaseModel):
    nodes: List[Dict]
    edges: List[Dict]


class GlobalAssessment(BaseModel):
    overall_risk: str
    overall_score: int
    confidence: float
    dominant_family: str
    peak_single_score: int
    average_score: float
    highest_risk_artefact: int
    strongest_evidence: List[str]
    weakest_signals: List[str]
    open_questions: List[str]


class InvestigationPredictions(BaseModel):
    investigation_id: str
    artefacts_analysed: int
    artefact_results: List[InvestigationArtefactResult]
    merged_entities: Dict
    repeated_indicators: Dict
    campaign: CampaignResult
    timeline: List[TimelineEvent]
    relationship_graph: RelationshipGraph
    global_assessment: GlobalAssessment
    investigation_report: Dict


class InvestigationResponse(BaseModel):
    status: str = "success"
    investigation_id: str
    artefacts_analysed: int
    artefact_results: List[InvestigationArtefactResult]
    merged_entities: Dict
    repeated_indicators: Dict
    campaign: CampaignResult
    timeline: List[TimelineEvent]
    relationship_graph: RelationshipGraph
    global_assessment: GlobalAssessment
    investigation_report: Dict
    knowledge_matches: List[Dict] = []
    advisory_references: List[Dict] = []
    historical_matches: List[Dict] = []
    connector_matches: List[Dict] = []
    threat_intel_fusion: Dict = {}


class ErrorResponse(BaseModel):
    detail: str
