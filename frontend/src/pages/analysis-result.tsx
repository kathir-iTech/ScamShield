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
import { VerdictBanner } from '@/components/ui/verdict-banner';
import { ExpandablePanel } from '@/components/ui/expandable-panel';
import { Card, CardContent } from '@/components/ui/card';
import { PageTransition } from '@/components/ui/page-transition';
import { Button } from '@/components/ui/button';
import { ArrowLeft, FileText, Image as ImageIcon, AlertTriangle, Info } from 'lucide-react';

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
    ? 'We found signs of a scam'
    : verdict === 'suspicious'
    ? 'This needs a closer look'
    : 'This looks safe';

  const verdictDescription = verdict === 'scam'
    ? r.summary
    : verdict === 'suspicious'
    ? r.summary
    : undefined;

  return (
    <PageTransition>
      <div className="space-y-8">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate(-1)}
              className="flex h-9 w-9 items-center justify-center rounded-xl text-zinc-400 transition-colors hover:bg-zinc-100 hover:text-zinc-600 dark:hover:bg-zinc-800"
              aria-label="Go back"
            >
              <ArrowLeft className="h-5 w-5" />
            </button>
            <div>
              <h1 className="text-xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">Result</h1>
              <p className="flex items-center gap-1.5 text-sm text-zinc-400">
                {isImage ? <ImageIcon className="h-4 w-4" /> : <FileText className="h-4 w-4" />}
                {isImage ? 'Image' : 'Text'} &middot; {new Date(current.timestamp).toLocaleTimeString()}
              </p>
            </div>
          </div>
          <Button variant="secondary" onClick={handleNewAnalysis}>New analysis</Button>
        </div>

        <VerdictBanner
          verdict={verdict}
          title={verdictTitle}
          description={verdictDescription}
          confidence={Math.round(r.confidence * 100)}
          riskLevel={r.risk_level}
          assessmentBand={r.assessment_band}
          actions={
            verdict !== 'safe' ? (
              <Button variant="outline" onClick={handleDeepDive}>
                <AlertTriangle className="h-4 w-4" />
                Deep dive investigation
              </Button>
            ) : undefined
          }
        />

        {r.recommended_actions && r.recommended_actions.length > 0 && (
          <Card className="animate-slide-up stagger-2">
            <CardContent className="py-6">
              <div className="flex items-start gap-3">
                <Info className="mt-0.5 h-5 w-5 shrink-0 text-emerald-500" />
                <div className="space-y-2">
                  <p className="text-sm font-medium text-zinc-900 dark:text-zinc-100">What you can do</p>
                  <ul className="space-y-1">
                    {r.recommended_actions.slice(0, 3).map((action, i) => (
                      <li key={i} className="text-sm text-zinc-600 dark:text-zinc-400">
                        &bull; {action}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        <div className="grid gap-6 lg:grid-cols-2">
          <CategoryCard
            scamCategory={r.scam_category}
            summary={r.summary}
            reasons={r.reasons}
            businessReason={r.business_reason}
            technicalReason={r.technical_reason}
          />
          <ThreatCard
            threats={r.threats}
            detectedIndicators={r.detected_indicators}
            decisionLevel={r.decision_level}
            recommendedPriority={r.recommended_priority}
            riskBreakdown={r.risk_breakdown as unknown as Record<string, number>}
          />
        </div>

        <div className="space-y-3">
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
