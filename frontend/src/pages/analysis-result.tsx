import { useMemo, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCurrentAnalysis, useAnalysis } from '@/features/analysis/context/analysis-context';
import { AnalysisSummaryCard } from '@/features/analysis/components/analysis-summary-card';
import { AssessmentCard } from '@/features/analysis/components/assessment-card';
import { RiskScoreCard } from '@/features/analysis/components/risk-score-card';
import { EvidenceCard } from '@/features/analysis/components/evidence-card';
import { EntityCard } from '@/features/analysis/components/entity-card';
import { ThreatCard } from '@/features/analysis/components/threat-card';
import { RecommendationCard } from '@/features/analysis/components/recommendation-card';
import { CategoryCard } from '@/features/analysis/components/category-card';
import { ConfidenceCard } from '@/features/analysis/components/confidence-card';
import { TimelineCard } from '@/features/analysis/components/timeline-card';
import { TechnicalDetailsCard } from '@/features/analysis/components/technical-details-card';
import { ReportSummaryCard } from '@/features/analysis/components/report-summary-card';
import { EmptyAnalysisState } from '@/features/analysis/components/empty-analysis-state';
import { PageTransition } from '@/components/ui/page-transition';
import { Section } from '@/components/ui/section';
import { Button } from '@/components/ui/button';
import { ArrowLeft, FileText, Image as ImageIcon } from 'lucide-react';
import { motion } from 'framer-motion';

export default function AnalysisResult() {
  const current = useCurrentAnalysis();
  const { clearCurrent } = useAnalysis();
  const navigate = useNavigate();

  const handleNewAnalysis = useCallback(() => {
    clearCurrent();
    navigate('/analyze/text');
  }, [clearCurrent, navigate]);

  const evidenceCount = useMemo(
    () =>
      (current?.result?.supporting_evidence?.length ?? 0) +
      (current?.result?.conflicting_evidence?.length ?? 0),
    [current]
  );

  if (!current) return <EmptyAnalysisState />;

  const r = current.result;
  const isImage = current.isImage;

  return (
    <PageTransition>
      <div className="mx-auto max-w-6xl space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => navigate(-1)}
                aria-label="Go back"
              >
                <ArrowLeft className="h-5 w-5" />
              </Button>
            </motion.div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">
                Investigation Report
              </h1>
              <p className="flex items-center gap-1.5 text-sm text-zinc-500 dark:text-zinc-400">
                {isImage ? <ImageIcon className="h-4 w-4" /> : <FileText className="h-4 w-4" />}
                {isImage ? 'Image analysis' : 'Text analysis'}
                &middot; {new Date(current.timestamp).toLocaleTimeString()}
              </p>
            </div>
          </div>
          <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
            <Button variant="outline" onClick={handleNewAnalysis}>
              New Analysis
            </Button>
          </motion.div>
        </div>

        <Section aria-label="Executive summary">
          <AnalysisSummaryCard
            prediction={r.prediction}
            confidence={r.confidence}
            riskLevel={r.risk_level}
            assessmentBand={r.assessment_band}
            assessmentScore={r.assessment_score}
          />
        </Section>

        <Section aria-label="Scam classification" className="grid gap-6 lg:grid-cols-2">
          <CategoryCard
            scamCategory={r.scam_category}
            summary={r.summary}
            reasons={r.reasons}
            businessReason={r.business_reason}
            technicalReason={r.technical_reason}
          />
          <AssessmentCard
            assessmentScore={r.assessment_score}
            assessmentBand={r.assessment_band}
            assessmentConfidence={r.assessment_confidence}
            assessmentSummary={r.assessment_summary}
            businessReason={r.business_reason}
            technicalReason={r.technical_reason}
          />
        </Section>

        <Section aria-label="Evidence">
          <EvidenceCard
            supporting={r.supporting_evidence}
            conflicting={r.conflicting_evidence}
          />
        </Section>

        <Section aria-label="Entities">
          <EntityCard entities={r.entities} />
        </Section>

        <Section aria-label="Threat intelligence" className="grid gap-6 lg:grid-cols-2">
          <ThreatCard
            threats={r.threats}
            detectedIndicators={r.detected_indicators}
            decisionLevel={r.decision_level}
            recommendedPriority={r.recommended_priority}
            riskBreakdown={r.risk_breakdown}
          />
          <RiskScoreCard
            ruleScore={r.rule_score}
            ruleLabel={r.rule_label}
            decisionScore={r.decision_score}
            decisionLevel={r.decision_level}
            riskLevel={r.risk_level}
            scamCategory={r.scam_category}
          />
        </Section>

        <Section aria-label="Actions and confidence" className="grid gap-6 lg:grid-cols-2">
          <RecommendationCard
            recommendedActions={r.recommended_actions}
            suggestedAction={r.suggested_action}
            recommendedAction={r.recommended_action}
            reviewRequired={r.review_required}
            manualReviewReason={r.manual_review_reason}
          />
          <ConfidenceCard
            ml={r.confidence_breakdown.ml}
            rules={r.confidence_breakdown.rules}
            entities={r.confidence_breakdown.entities}
            explanation={r.confidence_breakdown.explanation}
            overall={r.confidence_breakdown.overall}
          />
        </Section>

        <Section aria-label="Timeline and details" className="grid gap-6 lg:grid-cols-2">
          <TimelineCard />
          <TechnicalDetailsCard
            mlConfidence={r.confidence}
            decisionScore={r.decision_score}
            ruleScore={r.rule_score}
            assessmentScore={r.assessment_score}
            evidenceCount={evidenceCount}
            entityCount={r.entities.length}
          />
        </Section>

        <Section aria-label="Full investigation report">
          <ReportSummaryCard report={r.investigation_report} />
        </Section>
      </div>
    </PageTransition>
  );
}
