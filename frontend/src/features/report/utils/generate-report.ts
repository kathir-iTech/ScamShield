import type { AnalysisResponse } from '@/types';
import type { ReportContent, ReportSection, ReportSectionType, ReportTemplate } from '@/features/report/types';
import type { TimelineEvent } from '@/features/timeline/types';

function sectionsForTemplate(template: ReportTemplate): ReportSectionType[] {
  const all: ReportSectionType[] = [
    'executive_summary', 'timeline', 'entities', 'evidence', 'reasoning',
    'threat_intelligence', 'knowledge_matches', 'connector_results', 'campaign_analysis', 'recommendations',
  ];
  if (template === 'executive') return ['executive_summary', 'evidence', 'threat_intelligence', 'campaign_analysis', 'recommendations'];
  if (template === 'customer') return ['executive_summary', 'entities', 'evidence', 'recommendations'];
  return all;
}

export function generateReport(
  result: AnalysisResponse,
  template: ReportTemplate,
  events?: TimelineEvent[],
): ReportContent {
  const sections: ReportSection[] = [];
  const wanted = sectionsForTemplate(template);

  function add(type: ReportSectionType, title: string, lines: string[], extra?: Partial<ReportSection>): void {
    if (wanted.includes(type)) {
      sections.push({ type, title, content: lines, ...extra });
    }
  }

  const execLines: string[] = [];
  execLines.push(`Prediction: ${result.prediction.toUpperCase()}`);
  execLines.push(`Confidence: ${(result.confidence * 100).toFixed(1)}%`);
  execLines.push(`Risk Level: ${result.risk_level}`);
  execLines.push(`Scam Category: ${result.scam_category}`);
  execLines.push(`Assessment Band: ${result.assessment_band} (Score: ${result.assessment_score})`);
  execLines.push(`Assessment Confidence: ${result.assessment_confidence}`);
  execLines.push(`Summary: ${result.summary || 'N/A'}`);
  if (template !== 'customer') {
    execLines.push(`Decision Level: ${result.decision_level}`);
    execLines.push(`Business Reason: ${result.business_reason || 'N/A'}`);
    execLines.push(`Technical Reason: ${result.technical_reason || 'N/A'}`);
  }
  add('executive_summary', 'Executive Summary', execLines, { confidence: result.confidence, severity: result.risk_level });

  if (events && events.length > 0) {
    const timelineLines = events.map(
      (e) => `[${new Date(e.timestamp).toLocaleString()}] ${e.type}: ${e.label} — ${e.description}`
    );
    add('timeline', 'Investigation Timeline', timelineLines);
  }

  if (result.entities.length > 0) {
    const entityLines = result.entities.map(
      (e) => `• ${e.value} (${e.type}) — Risk: ${e.risk}, Confidence: ${(e.confidence * 100).toFixed(0)}%, Source: ${e.source}`
    );
    add('entities', 'Entities of Interest', entityLines, { severity: result.risk_level });
  }

  const evidenceLines: string[] = [];
  if (result.supporting_evidence.length > 0) {
    evidenceLines.push('Supporting Evidence:');
    for (const ev of result.supporting_evidence) {
      evidenceLines.push(`  • ${ev.description} (Severity: ${ev.severity}, Weight: ${ev.weight}, Source: ${ev.source})`);
    }
  }
  if (result.conflicting_evidence.length > 0) {
    evidenceLines.push('Conflicting Evidence:');
    for (const ev of result.conflicting_evidence) {
      evidenceLines.push(`  • ${ev.description} (Severity: ${ev.severity}, Weight: ${ev.weight}, Source: ${ev.source})`);
    }
  }
  if (evidenceLines.length > 0) {
    add('evidence', 'Evidence Analysis', evidenceLines, { severity: result.risk_level });
  }

  const reasoningLines: string[] = [
    `Overall Confidence: ${(result.confidence * 100).toFixed(1)}%`,
    `ML Confidence: ${(result.confidence_breakdown.ml * 100).toFixed(0)}%`,
    `Rules Confidence: ${(result.confidence_breakdown.rules * 100).toFixed(0)}%`,
    `Entity Confidence: ${(result.confidence_breakdown.entities * 100).toFixed(0)}%`,
    `Explanation Confidence: ${(result.confidence_breakdown.explanation * 100).toFixed(0)}%`,
    `Rule Score: ${result.rule_score} (${result.rule_label})`,
    `Decision Score: ${result.decision_score} — ${result.decision_level}`,
    `Decision Reasoning: ${result.decision_reasoning || 'N/A'}`,
  ];
  add('reasoning', 'Reasoning & Confidence Analysis', reasoningLines, { confidence: result.confidence });

  const threatLines: string[] = [];
  if (result.threats.length > 0) {
    threatLines.push('Detected Threats:');
    for (const t of result.threats) threatLines.push(`  • ${t}`);
  }
  if (result.detected_indicators.length > 0) {
    threatLines.push('Detected Indicators:');
    for (const ind of result.detected_indicators) threatLines.push(`  • ${ind}`);
  }
  threatLines.push('Risk Breakdown:');
  const rb = result.risk_breakdown;
  threatLines.push(`  • Credential Theft: ${rb.credential_theft}`);
  threatLines.push(`  • Financial Theft: ${rb.financial_loss}`);
  threatLines.push(`  • Identity Theft: ${rb.identity_theft}`);
  threatLines.push(`  • Malware: ${rb.malware}`);
  threatLines.push(`  • Social Engineering: ${rb.social_engineering}`);
  add('threat_intelligence', 'Threat Intelligence', threatLines, { severity: result.risk_level });

  if (result.knowledge_matches && Array.isArray(result.knowledge_matches) && result.knowledge_matches.length > 0) {
    const kmLines = result.knowledge_matches.map((k, i) => {
      const km = k as Record<string, unknown>;
      return `  ${i + 1}. ${km?.pattern ?? km?.label ?? 'Match'} (Similarity: ${(Number(km?.similarity ?? 0) * 100).toFixed(0)}%)`;
    });
    add('knowledge_matches', 'Knowledge Base Matches', kmLines);
  }

  if (result.connector_matches && Array.isArray(result.connector_matches) && result.connector_matches.length > 0) {
    const connLines = result.connector_matches.map((c, i) => {
      const cm = c as Record<string, unknown>;
      return `  ${i + 1}. ${cm?.connector_name ?? cm?.source ?? 'Unknown'} — Verdict: ${cm?.verdict ?? 'unknown'} (Confidence: ${(Number(cm?.confidence ?? 0) * 100).toFixed(0)}%)`;
    });
    add('connector_results', 'Connector Results', connLines);
  }

  if (result.scam_category) {
    const campaignLines = [
      `Primary Campaign: ${result.scam_category}`,
      `Assessment: ${result.assessment_band}`,
      `Review Required: ${result.review_required ? 'Yes' : 'No'}`,
    ];
    if (result.review_required) campaignLines.push(`Review Reason: ${result.manual_review_reason || 'N/A'}`);
    add('campaign_analysis', 'Campaign Analysis', campaignLines, { severity: result.risk_level });
  }

  const recLines: string[] = [
    `Suggested Action: ${result.suggested_action}`,
    `Recommended Action: ${result.recommended_action}`,
    `Priority: ${result.recommended_priority}`,
    `Review Required: ${result.review_required ? 'Yes — ' + (result.manual_review_reason || 'Manual review needed') : 'No'}`,
  ];
  if (result.recommended_actions.length > 0) {
    recLines.push('Actions:');
    for (const a of result.recommended_actions) recLines.push(`  • ${a}`);
  }
  add('recommendations', 'Recommendations', recLines);

  return {
    title: `${template === 'customer' ? 'Analysis Report' : template === 'law_enforcement' ? 'Investigation Report' : template === 'executive' ? 'Executive Summary' : 'Technical Investigation Report'}`,
    template,
    generatedAt: Date.now(),
    sections,
    metadata: {
      prediction: result.prediction,
      confidence: result.confidence,
      riskLevel: result.risk_level,
      scamCategory: result.scam_category,
      totalEvidence: result.supporting_evidence.length + result.conflicting_evidence.length,
      totalEntities: result.entities.length,
      totalThreats: result.threats.length,
    },
  };
}
