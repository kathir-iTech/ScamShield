export type TimelineEventType =
  | 'analysis_created'
  | 'evidence_supporting'
  | 'evidence_conflicting'
  | 'entity_identified'
  | 'threat_detected'
  | 'indicator_extracted'
  | 'connector_lookup'
  | 'knowledge_match'
  | 'fusion_result'
  | 'scam_classification'
  | 'assessment'
  | 'campaign_event';

export interface TimelineEvent {
  id: string;
  type: TimelineEventType;
  timestamp: number;
  label: string;
  description: string;
  severity?: string;
  confidence?: number;
  risk?: string;
  source?: string;
  metadata?: Record<string, unknown>;
  groupKey?: string;
}

export interface TimeCluster {
  id: string;
  startTime: number;
  endTime: number;
  events: TimelineEvent[];
  count: number;
}

export interface CampaignGroup {
  id: string;
  name: string;
  events: TimelineEvent[];
  confidence: number;
  sharedEntities: string[];
  repeatedIndicators: string[];
  riskLevel: string;
  eventCount: number;
}

export interface TimelineViewState {
  zoomLevel: number;
  searchQuery: string;
  activeTypes: TimelineEventType[];
  selectedEventId: string | null;
  clusterThreshold: number;
}

export const TIMELINE_EVENT_LABELS: Record<TimelineEventType, string> = {
  analysis_created: 'Analysis Started',
  evidence_supporting: 'Supporting Evidence',
  evidence_conflicting: 'Conflicting Evidence',
  entity_identified: 'Entity Identified',
  threat_detected: 'Threat Detected',
  indicator_extracted: 'Indicator Extracted',
  connector_lookup: 'Connector Lookup',
  knowledge_match: 'Knowledge Match',
  fusion_result: 'Fusion Result',
  scam_classification: 'Scam Classification',
  assessment: 'Assessment',
  campaign_event: 'Campaign Event',
};

export const TIMELINE_EVENT_ICONS: Record<TimelineEventType, string> = {
  analysis_created: 'play',
  evidence_supporting: 'check',
  evidence_conflicting: 'x',
  entity_identified: 'user',
  threat_detected: 'alert',
  indicator_extracted: 'flag',
  connector_lookup: 'globe',
  knowledge_match: 'book',
  fusion_result: 'merge',
  scam_classification: 'tag',
  assessment: 'bar-chart',
  campaign_event: 'layers',
};

export const TIMELINE_EVENT_COLORS: Record<TimelineEventType, string> = {
  analysis_created: '#3b82f6',
  evidence_supporting: '#10b981',
  evidence_conflicting: '#ef4444',
  entity_identified: '#6366f1',
  threat_detected: '#dc2626',
  indicator_extracted: '#f59e0b',
  connector_lookup: '#06b6d4',
  knowledge_match: '#f97316',
  fusion_result: '#8b5cf6',
  scam_classification: '#ec4899',
  assessment: '#14b8a6',
  campaign_event: '#a855f7',
};
