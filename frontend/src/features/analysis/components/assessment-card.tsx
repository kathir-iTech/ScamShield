interface Props {
  assessmentScore: number;
  assessmentBand: string;
  assessmentConfidence: string;
  assessmentSummary: string;
  businessReason: string;
  technicalReason: string;
}

export function AssessmentCard({ assessmentScore, assessmentBand, assessmentConfidence, assessmentSummary, businessReason, technicalReason }: Props) {
  return (
    <div className="space-y-5">
      <p className="text-xs text-text-tertiary">Assessment</p>
      <div className="flex items-baseline gap-6">
        <div>
          <p className="text-xs text-text-tertiary">Band</p>
          <p className="text-lg font-semibold text-text-primary">{assessmentBand}</p>
        </div>
        <div>
          <p className="text-xs text-text-tertiary">Score</p>
          <p className="text-lg font-semibold text-text-primary">{assessmentScore}<span className="text-sm font-normal text-text-tertiary">/100</span></p>
        </div>
        <div>
          <p className="text-xs text-text-tertiary">Confidence</p>
          <p className="text-lg font-semibold text-text-primary">{assessmentConfidence}</p>
        </div>
      </div>
      <p className="text-sm text-text-secondary/80">{assessmentSummary}</p>
      <div className="grid gap-3 md:grid-cols-2">
        <div className="rounded-xl bg-glass border border-glass-border p-4">
          <p className="text-xs text-text-tertiary">Business</p>
          <p className="mt-1 text-sm text-text-secondary/90">{businessReason}</p>
        </div>
        <div className="rounded-xl bg-glass border border-glass-border p-4">
          <p className="text-xs text-text-tertiary">Technical</p>
          <p className="mt-1 text-sm text-text-secondary/90">{technicalReason}</p>
        </div>
      </div>
    </div>
  );
}
