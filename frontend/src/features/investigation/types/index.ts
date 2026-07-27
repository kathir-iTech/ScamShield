import type { ReactNode } from 'react';

export type PanelId = 'summary' | 'evidence' | 'timeline' | 'reasoning' | 'graph' | 'report';

export interface PanelConfig {
  id: PanelId;
  label: string;
  icon: ReactNode;
  defaultVisible: boolean;
}

export interface WorkspaceState {
  leftPanelOpen: boolean;
  rightPanelOpen: boolean;
  centerPanelId: PanelId;
  leftWidth: number;
  rightWidth: number;
  splitDirection: 'vertical' | 'horizontal';
}

export interface CaseSummary {
  title: string;
  riskLevel: string;
  scamCategory: string;
  confidence: number;
  timestamp: number;
  entityCount: number;
  evidenceCount: number;
  threatCount: number;
}
