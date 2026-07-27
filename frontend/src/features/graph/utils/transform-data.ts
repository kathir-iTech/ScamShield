import type { AnalysisResponse } from '@/types';
import type { GraphData, GraphNode, GraphEdge, RiskLevel } from '@/features/graph/types';

export function transformAnalysisToGraph(result: AnalysisResponse): GraphData {
  const nodes: GraphNode[] = [];
  const edges: GraphEdge[] = [];
  const nodeMap = new Set<string>();

  function addNode(node: GraphNode): void {
    if (!nodeMap.has(node.id)) {
      nodeMap.add(node.id);
      nodes.push(node);
    }
  }

  const caseId = 'case_root';
  addNode({
    id: caseId,
    type: 'evidence',
    label: result.summary?.slice(0, 60) || 'Analysis Case',
    risk: toRiskLevel(result.risk_level),
    confidence: result.confidence,
    x: 0, y: 0, vx: 0, vy: 0, fx: null, fy: null,
    metadata: {
      prediction: result.prediction,
      scam_category: result.scam_category,
      assessment_band: result.assessment_band,
      decision_level: result.decision_level,
      review_required: result.review_required,
    },
  });

  for (const item of result.supporting_evidence) {
    const nid = `evidence_sup_${item.id}`;
    addNode({
      id: nid,
      type: 'evidence',
      label: item.description,
      risk: severityToRisk(item.severity),
      confidence: item.confidence,
      x: 0, y: 0, vx: 0, vy: 0, fx: null, fy: null,
      metadata: { source: item.source, type: item.type, weight: item.weight, severity: item.severity },
    });
    edges.push({ id: `e_sup_${item.id}`, source: nid, target: caseId, type: 'supports', weight: item.weight });

    const entityRef = findEntityRef(item.source, result.entities);
    if (entityRef) {
      edges.push({ id: `e_mentions_${item.id}`, source: nid, target: `ent_${entityRef.value}`, type: 'mentions' });
    }
  }

  for (const item of result.conflicting_evidence) {
    const nid = `evidence_con_${item.id}`;
    addNode({
      id: nid,
      type: 'evidence',
      label: item.description,
      risk: severityToRisk(item.severity),
      confidence: item.confidence,
      x: 0, y: 0, vx: 0, vy: 0, fx: null, fy: null,
      metadata: { source: item.source, type: item.type, weight: item.weight, severity: item.severity },
    });
    edges.push({ id: `e_con_${item.id}`, source: nid, target: caseId, type: 'contradicts', weight: item.weight });
  }

  for (const ent of result.entities) {
    const nid = `ent_${ent.value}`;
    addNode({
      id: nid,
      type: 'entity',
      label: ent.value,
      risk: toRiskLevel(ent.risk),
      confidence: ent.confidence,
      x: 0, y: 0, vx: 0, vy: 0, fx: null, fy: null,
      metadata: { type: ent.type, source: ent.source, risk_reason: ent.risk_reason },
    });

    if (result.scam_category) {
      edges.push({ id: `e_belongs_${ent.value}`, source: nid, target: 'scam_root', type: 'belongs_to' });
    }
  }

  if (result.scam_category) {
    addNode({
      id: 'scam_root',
      type: 'scam_family',
      label: result.scam_category,
      confidence: result.confidence,
      x: 0, y: 0, vx: 0, vy: 0, fx: null, fy: null,
      metadata: { assessment: result.assessment_band },
    });
    edges.push({ id: 'e_case_scam', source: caseId, target: 'scam_root', type: 'belongs_to' });
  }

  for (let i = 0; i < result.threats.length; i++) {
    const t = result.threats[i];
    const nid = `threat_${i}_${t.slice(0, 20).replace(/\s+/g, '_')}`;
    addNode({
      id: nid,
      type: 'threat',
      label: t,
      risk: 'high',
      x: 0, y: 0, vx: 0, vy: 0, fx: null, fy: null,
    });
    edges.push({ id: `e_threat_case_${i}`, source: nid, target: caseId, type: 'related_to' });
  }

  for (let i = 0; i < result.detected_indicators.length; i++) {
    const ind = result.detected_indicators[i];
    const nid = `indicator_${i}_${ind.slice(0, 20).replace(/\s+/g, '_')}`;
    addNode({
      id: nid,
      type: 'evidence',
      label: ind,
      risk: 'medium',
      x: 0, y: 0, vx: 0, vy: 0, fx: null, fy: null,
      metadata: { indicator: true },
    });
    edges.push({ id: `e_ind_case_${i}`, source: nid, target: caseId, type: 'mentions' });
  }

  if (result.connector_matches) {
    const cm = result.connector_matches;
    if (Array.isArray(cm)) {
      for (let i = 0; i < cm.length; i++) {
        const c = cm[i] as Record<string, unknown>;
        const cid = `connector_${i}`;
        const label = String(c?.connector_name ?? c?.source ?? `Connector ${i}`);
        addNode({
          id: cid,
          type: 'connector',
          label,
          risk: toRiskLevel(String(c?.verdict ?? 'unknown')),
          confidence: Number(c?.confidence ?? 0.5),
          x: 0, y: 0, vx: 0, vy: 0, fx: null, fy: null,
          metadata: c as Record<string, unknown>,
        });
        edges.push({ id: `e_conn_case_${i}`, source: cid, target: caseId, type: 'related_to' });
      }
    }
  }

  if (result.knowledge_matches) {
    const km = result.knowledge_matches;
    if (Array.isArray(km)) {
      for (let i = 0; i < km.length; i++) {
        const k = km[i] as Record<string, unknown>;
        const kid = `knowledge_${i}`;
        addNode({
          id: kid,
          type: 'knowledge_match',
          label: String(k?.pattern ?? k?.label ?? `Knowledge ${i}`),
          confidence: Number(k?.similarity ?? 0.5),
          x: 0, y: 0, vx: 0, vy: 0, fx: null, fy: null,
          metadata: k as Record<string, unknown>,
        });
        edges.push({ id: `e_know_case_${i}`, source: kid, target: caseId, type: 'supports' });
      }
    }
  }

  if (result.threat_intel_fusion) {
    const tf = result.threat_intel_fusion as Record<string, unknown> | undefined;
    if (tf && typeof tf === 'object') {
      addNode({
        id: 'fusion_root',
        type: 'connector',
        label: 'Fusion Engine',
        confidence: Number(tf?.overall_confidence ?? 0.7),
        x: 0, y: 0, vx: 0, vy: 0, fx: null, fy: null,
        metadata: tf as Record<string, unknown>,
      });
      edges.push({ id: 'e_fusion_case', source: 'fusion_root', target: caseId, type: 'supports' });
    }
  }

  return { nodes, edges };
}

function toRiskLevel(value: string | undefined): RiskLevel {
  if (!value) return 'unknown';
  const l = value.toLowerCase();
  if (l.includes('critical')) return 'critical';
  if (l.includes('high')) return 'high';
  if (l.includes('medium')) return 'medium';
  if (l.includes('low')) return 'low';
  return 'unknown';
}

function severityToRisk(severity: string): RiskLevel {
  const s = severity.toLowerCase();
  if (s === 'critical') return 'critical';
  if (s === 'high') return 'high';
  if (s === 'medium') return 'medium';
  if (s === 'low') return 'low';
  return 'unknown';
}

function findEntityRef(source: string, entities: { value: string; type: string }[]): { value: string; type: string } | undefined {
  const srcLower = source.toLowerCase();
  return entities.find((e) => srcLower.includes(e.value.toLowerCase()));
}
