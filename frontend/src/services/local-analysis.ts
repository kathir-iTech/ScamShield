import { analyzeText as pipelineAnalyze } from '@/lib/scamshield/pipeline.js';
import { repairUrls } from '@/lib/scamshield/repair-urls.js';
import type {
  AnalysisResponse,
  EntityItem,
  EntitySummary,
  EntityRisk,
  EvidenceItem,
  ConfidenceBreakdown,
  RiskBreakdown,
} from '@/types';

// Pipeline result type (JS)
interface PipelineResult {
  risk_level: string;
  scam_category: string;
  prediction: string;
  confidence: number;
  rule_score: number;
  rule_label: string;
  reasons: string[];
  detected_indicators: string[];
  matched_tactics?: Array<{ trigger: string; tactic: string; explainer: string }>;
  threats: string[];
  recommended_actions: string[];
  summary: string;
  confidence_reason: string;
  entities: EntityItem[];
  entity_summary: EntitySummary;
  entity_risk: EntityRisk;
  decision_score: number;
  supporting_evidence: EvidenceItem[];
  conflicting_evidence: EvidenceItem[];
  evidence_confidence_breakdown: ConfidenceBreakdown;
  evidence_risk_breakdown: RiskBreakdown;
  assessment_score: number;
  assessment_band: string;
  assessment_confidence: string;
  review_required: boolean;
  refined_prediction: string;
  refined_assessment_score: number;
  refined_confidence: string;
  decision_stable: boolean;
  stability_concerns: string[];
  refinement_summary: string;
}

// Helpers to map pipeline's 0-100 scores to frontend's expected 0-1 where needed,
// while keeping compatibility with components that expect 0-100.
function normalizeConfidenceBreakdown(raw: ConfidenceBreakdown | undefined): ConfidenceBreakdown {
  if (!raw) return { ml: 0, rules: 0, entities: 0, explanation: 0, overall: 0 };
  // pipeline returns 0-100, frontend confidence-card expects 0-1 -> divide by 100
  const toNorm = (v: number) => (v > 1 ? v / 100 : v);
  return {
    ml: toNorm((raw as unknown as { ml: number }).ml ?? 0),
    rules: toNorm((raw as unknown as { rules: number }).rules ?? 0),
    entities: toNorm((raw as unknown as { entities: number }).entities ?? 0),
    explanation: toNorm((raw as unknown as { explanation: number }).explanation ?? 0),
    overall: toNorm((raw as unknown as { overall: number }).overall ?? 0),
  };
}

function toDecisionLevel(score: number): string {
  // score normalized 0-1 or 0-100? Handle both
  const s = score > 1 ? score : score * 100;
  if (s >= 80) return 'CRITICAL';
  if (s >= 60) return 'HIGH RISK';
  if (s >= 35) return 'SUSPICIOUS';
  if (s >= 15) return 'LOW RISK';
  return 'SAFE';
}

function toPriority(score: number, _level: string): string {
  const s = score > 1 ? score : score * 100;
  if (s >= 70) return 'URGENT';
  if (s >= 50) return 'HIGH';
  if (s >= 25) return 'NORMAL';
  return 'LOW';
}

function toAnalysisResponse(pipelineResult: PipelineResult): AnalysisResponse {
  const {
    risk_level,
    scam_category,
    prediction,
    confidence,
    rule_score,
    rule_label,
    reasons,
    detected_indicators,
    matched_tactics,
    threats,
    recommended_actions,
    summary,
    confidence_reason,
    entities,
    entity_summary,
    entity_risk,
    decision_score,
    supporting_evidence,
    conflicting_evidence,
    evidence_confidence_breakdown,
    evidence_risk_breakdown,
    assessment_score,
    assessment_band,
    assessment_confidence,
    review_required,
    refined_prediction,
    refined_assessment_score,
    refined_confidence,
    decision_stable,
    stability_concerns,
    refinement_summary,
  } = pipelineResult;

  // Normalize scores that frontend expects as 0-1
  const normDecisionScore = decision_score > 1 ? decision_score / 100 : decision_score;
  const confidenceBreakdown = normalizeConfidenceBreakdown(evidence_confidence_breakdown as unknown as ConfidenceBreakdown);

  // Derive decision_level and priority
  const decision_level = toDecisionLevel(decision_score);
  const decision_reasoning = confidence_reason || summary || 'Analysis based on ML and rule engine';
  const risk_breakdown = (evidence_risk_breakdown && typeof evidence_risk_breakdown === 'object'
    ? evidence_risk_breakdown
    : { credential_theft: 0, financial_loss: 0, identity_theft: 0, malware: 0, social_engineering: 0 });
  const recommended_priority = toPriority(decision_score, decision_level);

  // Business / technical reasons
  const business_reason = summary || confidence_reason || 'No significant scam indicators detected.';
  const technical_reason = confidence_reason || `ML confidence ${(confidence * 100).toFixed(0)}%, rule score ${rule_score} (${rule_label})`;
  const assessment_summary = summary || business_reason;
  const suggested_action = recommended_actions[0] || summary || 'No action required';
  const recommended_action = suggested_action;
  const manual_review_reason = review_required
    ? refinement_summary || `Assessment confidence is ${assessment_confidence}, review recommended.`
    : '';

  // Ensure entity_summary/entity_risk defaults
  const safeEntitySummary: EntitySummary = entity_summary || { total_entities: entities.length, by_type: {}, threat_indicators: [] };
  const safeEntityRisk: EntityRisk = entity_risk || { high: [], medium: [], low: [] };

  // Investigation report synthesis (minimal, since backend's report is complex)
  const investigation_report: Record<string, unknown> = {
    reasoning_family: scam_category,
    summary,
    decision_score: decision_score,
    risk_level,
    scam_category,
    threats,
    indicators: detected_indicators,
  };

  return {
    prediction,
    confidence,
    rule_score,
    rule_label,
    reasons,
    suggested_action,
    summary,
    risk_level,
    scam_category,
    detected_indicators,
    matched_tactics: matched_tactics || [],
    threats,
    recommended_actions,
    entities,
    entity_summary: safeEntitySummary,
    entity_risk: safeEntityRisk,
    decision_score: normDecisionScore,
    decision_level,
    decision_reasoning,
    supporting_evidence: supporting_evidence || [],
    conflicting_evidence: conflicting_evidence || [],
    confidence_breakdown: confidenceBreakdown,
    risk_breakdown,
    recommended_priority,
    recommended_action,
    assessment_score: assessment_score, // keep 0-100 for technical-details-card; why-flagged will handle both (see its fix)
    assessment_band: assessment_band || 'Unknown',
    assessment_confidence: assessment_confidence || 'LOW',
    assessment_summary,
    business_reason,
    technical_reason,
    review_required: !!review_required,
    manual_review_reason,
    investigation_report,
    refined_prediction: refined_prediction || prediction,
    refined_assessment_score: refined_assessment_score ?? assessment_score,
    refined_assessment_confidence: refined_confidence || assessment_confidence,
    refined_review_required: !!review_required,
    refinement_summary: refinement_summary || '',
    decision_stable: !!decision_stable,
    stability_concerns: stability_concerns || [],
    reasoning_family: scam_category,
    reasoning_subfamily: '',
    reasoning_family_confidence: confidence,
    reasoning_primary_evidence: supporting_evidence?.slice(0, 2) as unknown as Record<string, unknown>[],
    reasoning_supporting_evidence: supporting_evidence as unknown as Record<string, unknown>[],
    reasoning_weak_evidence: [],
    reasoning_contradictory_evidence: conflicting_evidence as unknown as Record<string, unknown>[],
    reasoning_dominant_evidence_chain: detected_indicators.slice(0, 3),
    reasoning_summary: summary,
    knowledge_matches: [],
    advisory_references: [],
    historical_matches: [],
    connector_matches: [],
    threat_intel_fusion: {},
  };
}

export function analyzeTextLocal(text: string): AnalysisResponse {
  if (!text || typeof text !== 'string' || text.trim() === '') {
    // Return safe minimal response for empty input (matches pipeline's early return)
    const empty = pipelineAnalyze('');
    return toAnalysisResponse(empty as unknown as PipelineResult);
  }
  // Apply URL repair for OCR-extracted text robustness even for direct text?
  // For direct text input, repair is harmless and helps if user pastes OCR-like garble.
  const repaired = repairUrls(text);
  const result = pipelineAnalyze(repaired) as unknown as PipelineResult;
  return toAnalysisResponse(result);
}

export function analyzeTextWithRepair(text: string): AnalysisResponse {
  const repaired = repairUrls(text);
  const result = pipelineAnalyze(repaired) as unknown as PipelineResult;
  return toAnalysisResponse(result);
}

export { repairUrls };
