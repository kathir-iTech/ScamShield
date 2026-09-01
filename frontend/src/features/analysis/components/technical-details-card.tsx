interface Props {
  mlConfidence: number;
  decisionScore: number;
  ruleScore: number;
  assessmentScore: number;
  evidenceCount: number;
  entityCount: number;
}

function fmtDecision(v: number): string {
  if (v == null || isNaN(v)) return '0';
  // decision_score may be 0-1 (local) or 0-100 (backend)
  if (v > 1) return v.toFixed(2);
  return (v * 100).toFixed(2);
}
function fmtAssessment(v: number): string {
  if (v == null || isNaN(v)) return '0/100';
  if (v > 1) return `${Math.round(v)}/100`;
  return `${Math.round(v * 100)}/100`;
}

export function TechnicalDetailsCard({ mlConfidence, decisionScore, ruleScore, assessmentScore, evidenceCount, entityCount }: Props) {
  const scores = [
    { label: 'ML Confidence', value: `${(mlConfidence * 100).toFixed(0)}%` },
    { label: 'Decision Score', value: fmtDecision(decisionScore) },
    { label: 'Rule Score', value: ruleScore.toFixed(2) },
    { label: 'Assessment', value: fmtAssessment(assessmentScore) },
    { label: 'Evidence', value: String(evidenceCount) },
    { label: 'Entities', value: String(entityCount) },
  ];

  return (
    <div>
      <p className="text-xs text-text-tertiary mb-4">Scores</p>
      <div className="grid grid-cols-2 gap-4">
        {scores.map((s) => (
          <div key={s.label} className="rounded-xl bg-glass border border-glass-border p-3">
            <p className="text-xs text-text-tertiary">{s.label}</p>
            <p className="mt-1 text-sm font-semibold text-text-primary">{s.value}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
