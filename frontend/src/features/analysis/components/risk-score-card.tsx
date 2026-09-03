const riskStyles: Record<string, string> = {
  CRITICAL: 'bg-danger/10 text-danger border border-danger/20',
  HIGH: 'bg-danger/10 text-danger border border-danger/20',
  MEDIUM: 'bg-warning/10 text-warning border border-warning/20',
  LOW: 'bg-success/10 text-success border border-success/20',
  'VERY LOW': 'bg-success/10 text-success border border-success/20',
  SAFE: 'bg-success/10 text-success border border-success/20',
};

interface Props {
  ruleScore: number;
  ruleLabel: string;
  decisionScore: number;
  decisionLevel: string;
  riskLevel: string;
  scamCategory: string;
}

export function RiskScoreCard({ ruleScore, ruleLabel, decisionScore, decisionLevel, riskLevel, scamCategory }: Props) {
  const riskStyle = riskStyles[riskLevel] || riskStyles.LOW;

  return (
    <div className="space-y-5">
      <p className="text-xs text-text-tertiary">Risk &amp; Scoring</p>
      <div className="flex gap-3 items-center">
        <span className={`rounded-full px-3 py-1 text-xs font-medium ${riskStyle}`}>{riskLevel}</span>
        <span className="text-sm text-text-secondary">{scamCategory}</span>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div className="rounded-xl bg-glass border border-glass-border p-4">
          <p className="text-xs text-text-tertiary">Rule Score</p>
          <p className="mt-1 text-xl font-bold text-text-primary">{ruleScore.toFixed(1)}</p>
          <p className="text-xs text-text-tertiary">{ruleLabel}</p>
        </div>
        <div className="rounded-xl bg-glass border border-glass-border p-4">
          <p className="text-xs text-text-tertiary">Decision</p>
          <p className="mt-1 text-xl font-bold text-text-primary">{decisionScore}</p>
          <p className="text-xs text-text-tertiary">{decisionLevel}</p>
        </div>
      </div>
    </div>
  );
}
