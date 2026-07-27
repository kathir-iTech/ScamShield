export type ReportTemplate = 'technical' | 'executive' | 'law_enforcement' | 'customer';

export type ReportSectionType =
  | 'executive_summary'
  | 'timeline'
  | 'entities'
  | 'evidence'
  | 'reasoning'
  | 'threat_intelligence'
  | 'knowledge_matches'
  | 'connector_results'
  | 'campaign_analysis'
  | 'recommendations';

export interface ReportSection {
  type: ReportSectionType;
  title: string;
  content: string[];
  severity?: string;
  confidence?: number;
  metadata?: Record<string, unknown>;
}

export interface ReportContent {
  title: string;
  template: ReportTemplate;
  generatedAt: number;
  sections: ReportSection[];
  metadata: {
    prediction: string;
    confidence: number;
    riskLevel: string;
    scamCategory: string;
    totalEvidence: number;
    totalEntities: number;
    totalThreats: number;
  };
}

export const REPORT_TEMPLATE_LABELS: Record<ReportTemplate, string> = {
  technical: 'Technical Report',
  executive: 'Executive Summary',
  law_enforcement: 'Law Enforcement',
  customer: 'Customer Friendly',
};

export const REPORT_TEMPLATE_DESCRIPTIONS: Record<ReportTemplate, string> = {
  technical: 'Full detail with reasoning chains, ML scores, and technical indicators',
  executive: 'Risk overview, business impact, and key findings for decision-makers',
  law_enforcement: 'Evidence-focused with chain of custody, entity details, and threat mapping',
  customer: 'Simple language, action-oriented, minimal technical jargon',
};

export const SECTION_LABELS: Record<ReportSectionType, string> = {
  executive_summary: 'Executive Summary',
  timeline: 'Investigation Timeline',
  entities: 'Entities of Interest',
  evidence: 'Evidence Analysis',
  reasoning: 'Reasoning & Confidence',
  threat_intelligence: 'Threat Intelligence',
  knowledge_matches: 'Knowledge Base Matches',
  connector_results: 'Connector Results',
  campaign_analysis: 'Campaign Analysis',
  recommendations: 'Recommendations',
};
