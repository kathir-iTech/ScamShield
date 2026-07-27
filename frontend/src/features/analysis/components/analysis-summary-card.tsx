interface Props {
  prediction: string;
  confidence: number;
  riskLevel: string;
  assessmentBand: string;
  assessmentScore: number;
}

export function AnalysisSummaryCard({ prediction, confidence, riskLevel, assessmentBand, assessmentScore }: Props) {
  const confidenceColor = confidence > 0.8 ? 'bg-success' : confidence > 0.5 ? 'bg-warning' : 'bg-danger';

  return (
    <div className="grid gap-8 py-4 md:grid-cols-5">
      <div className="text-center md:text-left">
        <p className="text-xs text-text-tertiary">Prediction</p>
        <p className="mt-1 text-lg font-semibold text-text-primary">{prediction}</p>
      </div>
      <div className="text-center md:text-left">
        <p className="text-xs text-text-tertiary">Confidence</p>
        <div className="mt-1 flex items-baseline gap-1">
          <span className="text-2xl font-bold text-text-primary">{(confidence * 100).toFixed(0)}</span>
          <span className="text-sm text-text-tertiary">%</span>
        </div>
        <div className="mt-2 h-1.5 w-full rounded-full bg-glass-border" role="progressbar" aria-valuenow={Math.round(confidence * 100)} aria-valuemin={0} aria-valuemax={100}>
          <div className={`h-1.5 rounded-full transition-all ${confidenceColor}`} style={{ width: `${confidence * 100}%` }} />
        </div>
      </div>
      <div className="text-center md:text-left">
        <p className="text-xs text-text-tertiary">Risk</p>
        <p className="mt-1 text-lg font-semibold text-text-primary">{riskLevel}</p>
      </div>
      <div className="text-center md:text-left">
        <p className="text-xs text-text-tertiary">Score</p>
        <p className="mt-1 text-lg font-semibold text-text-primary">{assessmentScore}<span className="text-sm font-normal text-text-tertiary">/100</span></p>
      </div>
      <div className="flex items-center justify-center gap-2 md:justify-start">
        <span className="flex h-6 w-6 items-center justify-center rounded-lg bg-accent/10">
          <svg className="h-3 w-3 text-accent" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
        </span>
        <span className="text-sm font-medium text-text-primary">{assessmentBand}</span>
      </div>
    </div>
  );
}
