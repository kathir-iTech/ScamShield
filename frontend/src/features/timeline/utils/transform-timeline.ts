import type { AnalysisResponse } from '@/types';
import type { TimelineEvent, TimelineEventType } from '@/features/timeline/types';

export function transformToTimelineEvents(
  result: AnalysisResponse,
  analysisTimestamp: number
): TimelineEvent[] {
  const events: TimelineEvent[] = [];
  const baseTime = analysisTimestamp - 180_000;
  let offset = 0;

  function event(
    type: TimelineEventType,
    label: string,
    description: string,
    timeOffset: number,
    extra?: Partial<TimelineEvent>
  ): TimelineEvent {
    return {
      id: `${type}_${events.length}`,
      type,
      timestamp: baseTime + timeOffset,
      label,
      description,
      ...extra,
    };
  }

  events.push(event('analysis_created', 'Investigation Started', 'Analysis pipeline initiated', offset, {
    confidence: result.confidence,
  }));
  offset += 5_000;

  if (result.detected_indicators.length > 0) {
    for (let i = 0; i < result.detected_indicators.length; i++) {
      events.push(event('indicator_extracted', `Indicator ${i + 1}`, result.detected_indicators[i], offset, {
        risk: 'medium', metadata: { indicator: result.detected_indicators[i] },
      }));
      offset += 3_000;
    }
  }

  if (result.entities.length > 0) {
    for (const ent of result.entities) {
      events.push(event('entity_identified', `Entity: ${ent.value}`, `${ent.type} — ${ent.risk_reason || ent.source}`, offset, {
        severity: ent.risk,
        confidence: ent.confidence,
        metadata: { value: ent.value, type: ent.type, source: ent.source },
      }));
      offset += 3_000;
    }
  }

  if (result.supporting_evidence.length > 0) {
    for (const ev of result.supporting_evidence) {
      events.push(event('evidence_supporting', 'Supporting Evidence', ev.description, offset, {
        severity: ev.severity,
        confidence: ev.confidence,
        source: ev.source,
        metadata: { id: ev.id, weight: ev.weight, type: ev.type },
      }));
      offset += 3_000;
    }
  }

  if (result.conflicting_evidence.length > 0) {
    for (const ev of result.conflicting_evidence) {
      events.push(event('evidence_conflicting', 'Conflicting Evidence', ev.description, offset, {
        severity: ev.severity,
        confidence: ev.confidence,
        source: ev.source,
        metadata: { id: ev.id, weight: ev.weight, type: ev.type },
      }));
      offset += 3_000;
    }
  }

  if (result.threats.length > 0) {
    for (const t of result.threats) {
      events.push(event('threat_detected', 'Threat Detected', t, offset, { risk: 'high' }));
      offset += 3_000;
    }
  }

  if (result.scam_category) {
    events.push(event('scam_classification', 'Scam Classification', result.scam_category, offset, {
      risk: result.risk_level, confidence: result.confidence,
      metadata: { category: result.scam_category, assessment: result.assessment_band },
    }));
    offset += 5_000;
  }

  events.push(event('assessment', 'Final Assessment', result.summary, offset, {
    severity: result.risk_level,
    confidence: result.confidence,
    metadata: {
      band: result.assessment_band,
      score: result.assessment_score,
      priority: result.recommended_priority,
      review: result.review_required,
    },
  }));
  offset += 5_000;

  if (result.connector_matches && Array.isArray(result.connector_matches)) {
    for (let i = 0; i < result.connector_matches.length; i++) {
      const c = result.connector_matches[i] as Record<string, unknown>;
      events.push(event('connector_lookup', `Connector: ${c?.connector_name ?? c?.source ?? `Source ${i + 1}`}`,
        `Verdict: ${c?.verdict ?? 'unknown'}`, offset, {
          confidence: Number(c?.confidence ?? 0.5),
          metadata: c as Record<string, unknown>,
        }));
      offset += 3_000;
    }
  }

  if (result.knowledge_matches && Array.isArray(result.knowledge_matches)) {
    for (let i = 0; i < result.knowledge_matches.length; i++) {
      const k = result.knowledge_matches[i] as Record<string, unknown>;
      events.push(event('knowledge_match', `Knowledge Match ${i + 1}`,
        String(k?.pattern ?? k?.label ?? `Match ${i + 1}`), offset, {
          confidence: Number(k?.similarity ?? 0.5),
          metadata: k as Record<string, unknown>,
        }));
      offset += 3_000;
    }
  }

  if (result.threat_intel_fusion) {
    const tf = result.threat_intel_fusion as Record<string, unknown>;
    events.push(event('fusion_result', 'Threat Intel Fusion',
      `Verdict: ${tf?.overall_verdict ?? 'unknown'} (agreement: ${tf?.agreement_score ?? 'N/A'})`, offset, {
        confidence: Number(tf?.overall_confidence ?? 0.5),
        severity: String(tf?.overall_severity ?? 'unknown'),
        metadata: tf as Record<string, unknown>,
      }));
  }

  return events.sort((a, b) => a.timestamp - b.timestamp);
}

export function generateCampaigns(events: TimelineEvent[]): CampaignGroup[] {
  const campaignMap = new Map<string, TimelineEvent[]>();
  const entityMap = new Map<string, Set<string>>();
  const indicatorMap = new Map<string, Set<string>>();

  for (const ev of events) {
    if (ev.type === 'scam_classification') {
      const key = ev.description || 'Unknown Campaign';
      if (!campaignMap.has(key)) campaignMap.set(key, []);
      campaignMap.get(key)!.push(ev);
    } else {
      const key = String(ev.metadata?.category ?? 'Unknown Campaign');
      if (!campaignMap.has(key)) campaignMap.set(key, []);
      campaignMap.get(key)!.push(ev);
    }
  }

  for (const ev of events) {
    const key = String(ev.metadata?.category ?? 'Unknown Campaign');
    if (!entityMap.has(key)) entityMap.set(key, new Set());
    if (!indicatorMap.has(key)) indicatorMap.set(key, new Set());

    if (ev.type === 'entity_identified' && ev.metadata?.value) {
      entityMap.get(key)!.add(String(ev.metadata.value));
    }
    if (ev.type === 'indicator_extracted') {
      indicatorMap.get(key)!.add(ev.description);
    }
  }

  const campaigns: CampaignGroup[] = [];
  for (const [name, groupEvents] of campaignMap) {
    const avgConf = groupEvents.reduce((s, e) => s + (e.confidence ?? 0), 0) / Math.max(groupEvents.length, 1);
    const entities = Array.from(entityMap.get(name) ?? []);
    const indicators = Array.from(indicatorMap.get(name) ?? []);
    const riskLevels = groupEvents.map((e) => e.severity ?? e.risk ?? 'unknown');
    const topRisk = riskLevels.includes('critical') ? 'critical'
      : riskLevels.includes('high') ? 'high'
      : riskLevels.includes('medium') ? 'medium'
      : riskLevels.includes('low') ? 'low' : 'unknown';

    campaigns.push({
      id: `campaign_${campaigns.length}`,
      name,
      events: groupEvents,
      confidence: avgConf,
      sharedEntities: entities,
      repeatedIndicators: indicators,
      riskLevel: topRisk,
      eventCount: groupEvents.length,
    });
  }

  return campaigns.length > 0
    ? campaigns
    : [{ id: 'campaign_default', name: 'General Analysis', events, confidence: 0.5, sharedEntities: [], repeatedIndicators: [], riskLevel: 'unknown', eventCount: events.length }];
}

interface CampaignGroup {
  id: string;
  name: string;
  events: TimelineEvent[];
  confidence: number;
  sharedEntities: string[];
  repeatedIndicators: string[];
  riskLevel: string;
  eventCount: number;
}
