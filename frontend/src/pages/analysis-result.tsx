import { useMemo, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCurrentAnalysis, useAnalysis } from '@/features/analysis/context/analysis-context';
import { CategoryCard } from '@/features/analysis/components/category-card';
import { EvidenceCard } from '@/features/analysis/components/evidence-card';
import { EntityCard } from '@/features/analysis/components/entity-card';
import { ThreatCard } from '@/features/analysis/components/threat-card';
import { ConfidenceCard } from '@/features/analysis/components/confidence-card';
import { TimelineCard } from '@/features/analysis/components/timeline-card';
import { TechnicalDetailsCard } from '@/features/analysis/components/technical-details-card';
import { ReportSummaryCard } from '@/features/analysis/components/report-summary-card';
import { EmptyAnalysisState } from '@/features/analysis/components/empty-analysis-state';
import { VerdictHero } from '@/components/ui/verdict-hero';
import { ExpandablePanel } from '@/components/ui/expandable-panel';
import { PageTransition } from '@/components/ui/page-transition';
import { ArrowLeft, FileText, Image as ImageIcon, Shield } from 'lucide-react';

export default function AnalysisResult() {
  const current = useCurrentAnalysis();
  const { clearCurrent } = useAnalysis();
  const navigate = useNavigate();

  const handleNewAnalysis = useCallback(() => {
    clearCurrent();
    navigate('/analyze/text');
  }, [clearCurrent, navigate]);

  const handleDeepDive = useCallback(() => {
    navigate('/investigation');
  }, [navigate]);

  const evidenceCount = useMemo(
    () =>
      (current?.result?.supporting_evidence?.length ?? 0) +
      (current?.result?.conflicting_evidence?.length ?? 0),
    [current]
  );

  if (!current) return <EmptyAnalysisState />;

  const r = current.result;
  const isImage = current.isImage;

  const verdict = r.prediction === 'scam' || r.risk_level === 'HIGH' || r.risk_level === 'CRITICAL'
    ? 'scam' as const
    : r.risk_level === 'MEDIUM' || r.risk_level === 'SUSPICIOUS'
    ? 'suspicious' as const
    : 'safe' as const;

  const verdictTitle = verdict === 'scam'
    ? 'Scam Detected'
    : verdict === 'suspicious'
    ? 'Needs Review'
    : 'Looks Safe';

  const verdictDescription = verdict === 'scam'
    ? r.summary
    : verdict === 'suspicious'
    ? r.summary
    : undefined;

  return (
    <PageTransition>
      <div className="mx-auto max-w-4xl px-6 py-10 sm:py-14">
        <div className="mb-8 flex items-center justify-between animate-slide-up">
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate(-1)}
              className="flex h-9 w-9 items-center justify-center rounded-xl glass text-text-tertiary hover:text-text-secondary transition-all duration-200 hover:bg-glass-hover"
              aria-label="Go back"
            >
              <ArrowLeft className="h-5 w-5" />
            </button>
            <div>
              <h1 className="text-lg font-bold tracking-tight text-text-primary">Result</h1>
              <p className="flex items-center gap-1.5 text-sm text-text-tertiary">
                {isImage ? <ImageIcon className="h-4 w-4" /> : <FileText className="h-4 w-4" />}
                {isImage ? 'Image' : 'Text'} &middot; {new Date(current.timestamp).toLocaleTimeString()}
              </p>
            </div>
          </div>
          <button
            onClick={handleNewAnalysis}
            className="glass relative inline-flex h-10 items-center gap-2 rounded-xl px-4 text-sm font-medium text-text-secondary hover:text-text-primary transition-all duration-200"
          >
            New analysis
          </button>
        </div>

        <div className="glass rounded-3xl p-8 sm:p-12 mb-8 animate-glass-enter">
          <VerdictHero
            verdict={verdict}
            title={verdictTitle}
            confidence={Math.round(r.confidence * 100)}
            description={verdictDescription}
          />
          {verdict !== 'safe' && (
            <div className="mt-8 text-center animate-slide-up" style={{ animationDelay: '0.5s' }}>
              <button
                onClick={handleDeepDive}
                className="glass relative inline-flex h-11 items-center gap-2 rounded-xl px-6 text-sm font-medium text-text-secondary hover:text-text-primary transition-all duration-200"
              >
                <Shield className="h-4 w-4" />
                Deep dive investigation
              </button>
            </div>
          )}
        </div>

        {r.recommended_actions && r.recommended_actions.length > 0 && (
          <div className="glass rounded-2xl p-6 mb-8 animate-slide-up stagger-2">
            <div className="flex items-start gap-3">
              <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-accent/10">
                <Shield className="h-4 w-4 text-accent" />
              </div>
              <div className="space-y-2">
                <p className="text-sm font-semibold text-text-primary">What you can do</p>
                <ul className="space-y-1.5">
                  {r.recommended_actions.slice(0, 3).map((action, i) => (
                    <li key={i} className="text-sm text-text-secondary/80">{action}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}

        <div className="grid gap-6 lg:grid-cols-2 mb-6">
          <div className="glass rounded-2xl p-6 animate-slide-up stagger-3">
            <CategoryCard
              scamCategory={r.scam_category}
              summary={r.summary}
              reasons={r.reasons}
              businessReason={r.business_reason}
              technicalReason={r.technical_reason}
            />
          </div>
          <div className="glass rounded-2xl p-6 animate-slide-up stagger-4">
            <ThreatCard
              threats={r.threats}
              detectedIndicators={r.detected_indicators}
              decisionLevel={r.decision_level}
              recommendedPriority={r.recommended_priority}
              riskBreakdown={r.risk_breakdown as unknown as Record<string, number>}
              riskLevel={r.risk_level}
            />
          </div>
        </div>

        {r.matched_tactics && r.matched_tactics.length > 0 && (
          <div className="glass rounded-2xl p-6 mb-6 animate-slide-up" style={{ animationDelay: '0.4s' }}>
            <p className="text-xs text-text-tertiary mb-3">Why this trick works</p>
            <div className="space-y-3">
              {r.matched_tactics.map((t, i) => (
                <div key={i} className="rounded-xl bg-glass border border-glass-border p-4">
                  <p className="text-sm font-medium text-text-primary">{t.tactic}</p>
                  <p className="mt-1 text-sm text-text-secondary/80">{t.explainer}</p>
                  <p className="mt-1 text-xs text-text-tertiary">Trigger: {t.trigger}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="space-y-3 animate-slide-up stagger-5">
          <ExpandablePanel title="Supporting evidence" count={r.supporting_evidence?.length} defaultOpen={verdict !== 'safe'}>
            <EvidenceCard supporting={r.supporting_evidence} conflicting={[]} />
          </ExpandablePanel>

          {r.conflicting_evidence?.length > 0 && (
            <ExpandablePanel title="Conflicting evidence" count={r.conflicting_evidence.length}>
              <EvidenceCard supporting={[]} conflicting={r.conflicting_evidence} />
            </ExpandablePanel>
          )}

          <ExpandablePanel title="Detected entities" count={r.entities?.length}>
            <EntityCard entities={r.entities} />
          </ExpandablePanel>

          <ExpandablePanel title="Technical details">
            <div className="grid gap-6 lg:grid-cols-2">
              <ConfidenceCard
                ml={r.confidence_breakdown.ml}
                rules={r.confidence_breakdown.rules}
                entities={r.confidence_breakdown.entities}
                explanation={r.confidence_breakdown.explanation}
                overall={r.confidence_breakdown.overall}
              />
              <TechnicalDetailsCard
                mlConfidence={r.confidence}
                decisionScore={r.decision_score}
                ruleScore={r.rule_score}
                assessmentScore={r.assessment_score}
                evidenceCount={evidenceCount}
                entityCount={r.entities.length}
              />
            </div>
          </ExpandablePanel>

          <ExpandablePanel title="Analysis timeline">
            <TimelineCard />
          </ExpandablePanel>

          <ExpandablePanel title="Investigation report">
            <ReportSummaryCard report={r.investigation_report} />
          </ExpandablePanel>
        </div>
      </div>
    </PageTransition>
  );
}
