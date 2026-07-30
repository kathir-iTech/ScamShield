export interface DiskUsage {
  total_gb: number;
  used_gb: number;
  free_gb: number;
  percent_free: number;
}

export interface MemoryUsage {
  total_gb: number;
  available_gb: number;
  percent_used: number;
}

export interface DependencyStatus {
  model: string;
  vectorizer: string;
  config: string;
}

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
  build_version: string;
  environment: string;
  startup_timestamp: number;
  uptime_seconds: number;
  release_id: string;
  checks: { name: string; status: string }[];
  dependencies: {
    model: string;
    vectorizer: string;
    config: string;
  };
  config_summary: Record<string, unknown>;
  service_availability: string;
  active_requests: number;
  test_mode: boolean;
}

export interface ReadinessResponse {
  status: string;
  errors?: string[];
}

export interface LivenessResponse {
  status: string;
}

export interface MetricsSnapshot {
  total_requests: number;
  successful_requests: number;
  failed_requests: number;
  active_requests: number;
  validation_failures: number;
  auth_failures: number;
  rate_limit_events: number;
  pipeline_failures: number;
  ocr_requests: number;
  text_requests: number;
  average_latency_ms: number;
  p50_latency_ms: number;
  p95_latency_ms: number;
  maximum_latency_ms: number;
  uptime_seconds: number;
  system?: {
    memory: MemoryUsage;
    cpu: { percent: number };
    process: {
      memory_mb: number;
      cpu_percent: number;
      threads: number;
    };
  };
}

export interface EntityItem {
  value: string;
  type: string;
  confidence: number;
  source: string;
  risk: string;
  risk_reason: string;
}

export interface EntitySummary {
  total_entities: number;
  by_type: Record<string, number>;
  threat_indicators: string[];
}

export interface EntityRisk {
  high: EntityItem[];
  medium: EntityItem[];
  low: EntityItem[];
}

export interface EvidenceItem {
  id: string;
  type: string;
  source: string;
  description: string;
  severity: string;
  confidence: number;
  weight: number;
}

export interface ConfidenceBreakdown {
  ml: number;
  rules: number;
  entities: number;
  explanation: number;
  overall: number;
}

export interface RiskBreakdown {
  credential_theft: number;
  financial_loss: number;
  identity_theft: number;
  malware: number;
  social_engineering: number;
}

export interface AnalysisResponse {
  prediction: string;
  confidence: number;
  rule_score: number;
  rule_label: string;
  reasons: string[];
  suggested_action: string;
  summary: string;
  risk_level: string;
  scam_category: string;
  detected_indicators: string[];
  threats: string[];
  recommended_actions: string[];
  entities: EntityItem[];
  entity_summary: EntitySummary;
  entity_risk: EntityRisk;
  decision_score: number;
  decision_level: string;
  decision_reasoning: string;
  supporting_evidence: EvidenceItem[];
  conflicting_evidence: EvidenceItem[];
  confidence_breakdown: ConfidenceBreakdown;
  risk_breakdown: RiskBreakdown;
  recommended_priority: string;
  recommended_action: string;
  assessment_score: number;
  assessment_band: string;
  assessment_confidence: string;
  assessment_summary: string;
  business_reason: string;
  technical_reason: string;
  review_required: boolean;
  manual_review_reason: string;
  investigation_report: Record<string, unknown>;
  refined_prediction?: string;
  refined_assessment_score?: number;
  refined_assessment_confidence?: string;
  refined_review_required?: boolean;
  refinement_summary?: string;
  decision_stable?: boolean;
  stability_concerns?: string[];
  reasoning_family?: string;
  reasoning_subfamily?: string;
  reasoning_family_confidence?: number;
  reasoning_primary_evidence?: Record<string, unknown>[];
  reasoning_supporting_evidence?: Record<string, unknown>[];
  reasoning_weak_evidence?: Record<string, unknown>[];
  reasoning_contradictory_evidence?: Record<string, unknown>[];
  reasoning_dominant_evidence_chain?: string[];
  reasoning_summary?: string;
  knowledge_matches?: Record<string, unknown>[];
  advisory_references?: Record<string, unknown>[];
  historical_matches?: Record<string, unknown>[];
  connector_matches?: Record<string, unknown>[];
  threat_intel_fusion?: Record<string, unknown>;
}

export interface ImageAnalysisResponse extends AnalysisResponse {
  extracted_text: string;
}

export interface ApiError {
  detail: string;
}
