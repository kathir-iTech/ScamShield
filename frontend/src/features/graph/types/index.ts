export type NodeType =
  | 'evidence'
  | 'entity'
  | 'threat'
  | 'scam_family'
  | 'campaign'
  | 'connector'
  | 'knowledge_match';

export type EdgeType =
  | 'mentions'
  | 'supports'
  | 'contradicts'
  | 'belongs_to'
  | 'related_to'
  | 'campaign';

export type RiskLevel = 'critical' | 'high' | 'medium' | 'low' | 'unknown';

export interface GraphNode {
  id: string;
  type: NodeType;
  label: string;
  risk?: RiskLevel;
  confidence?: number;
  x: number;
  y: number;
  vx: number;
  vy: number;
  fx: number | null;
  fy: number | null;
  metadata?: Record<string, unknown>;
  collapsed?: boolean;
  childIds?: string[];
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  type: EdgeType;
  label?: string;
  weight?: number;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface Viewport {
  x: number;
  y: number;
  zoom: number;
}

export interface FilterState {
  nodeTypes: NodeType[];
  edgeTypes: EdgeType[];
  searchQuery: string;
}

export interface SelectionState {
  selectedNodeId: string | null;
  hoveredNodeId: string | null;
}

export interface GraphConfig {
  nodeRadius: { min: number; max: number };
  colors: Record<NodeType, string>;
  riskColors: Record<RiskLevel, string>;
  edgeColors: Record<EdgeType, string>;
  layout: {
    repulsion: number;
    attraction: number;
    centerForce: number;
    damping: number;
    iterations: number;
    maxSpeed: number;
  };
}

export type ExportFormat = 'png' | 'svg';

export interface GraphContextValue {
  data: GraphData;
  filteredData: GraphData;
  viewport: Viewport;
  selection: SelectionState;
  filters: FilterState;
  config: GraphConfig;
  svgRef: React.RefObject<SVGSVGElement | null>;
  containerRef: React.RefObject<HTMLDivElement | null>;
  selectNode: (id: string | null) => void;
  hoverNode: (id: string | null) => void;
  setViewport: (vp: Viewport) => void;
  panBy: (dx: number, dy: number) => void;
  zoomBy: (factor: number, cx?: number, cy?: number) => void;
  fitToScreen: () => void;
  setFilters: (f: FilterState) => void;
  setSearchQuery: (q: string) => void;
  toggleNodeType: (t: NodeType) => void;
  toggleEdgeType: (t: EdgeType) => void;
  collapseCluster: (nodeId: string) => void;
  expandCluster: (nodeId: string) => void;
  resetView: () => void;
  layoutRunning: boolean;
  nodePositions: Map<string, { x: number; y: number }>;
}

export const DEFAULT_GRAPH_CONFIG: GraphConfig = {
  nodeRadius: { min: 22, max: 44 },
  colors: {
    evidence: '#10b981',
    entity: '#3b82f6',
    threat: '#ef4444',
    scam_family: '#f59e0b',
    campaign: '#8b5cf6',
    connector: '#06b6d4',
    knowledge_match: '#f97316',
  },
  riskColors: {
    critical: '#dc2626',
    high: '#ea580c',
    medium: '#d97706',
    low: '#059669',
    unknown: '#6b7280',
  },
  edgeColors: {
    mentions: '#94a3b8',
    supports: '#10b981',
    contradicts: '#ef4444',
    belongs_to: '#6366f1',
    related_to: '#a855f7',
    campaign: '#f59e0b',
  },
  layout: {
    repulsion: 8000,
    attraction: 0.005,
    centerForce: 0.02,
    damping: 0.85,
    iterations: 120,
    maxSpeed: 10,
  },
};

export const NODE_TYPE_LABELS: Record<NodeType, string> = {
  evidence: 'Evidence',
  entity: 'Entity',
  threat: 'Threat',
  scam_family: 'Scam Family',
  campaign: 'Campaign',
  connector: 'Connector',
  knowledge_match: 'Knowledge Match',
};

export const EDGE_TYPE_LABELS: Record<EdgeType, string> = {
  mentions: 'Mentions',
  supports: 'Supports',
  contradicts: 'Contradicts',
  belongs_to: 'Belongs To',
  related_to: 'Related To',
  campaign: 'Campaign',
};
