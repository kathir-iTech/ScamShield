import { Card, CardContent } from '@/components/ui/card';

interface Props {
  mlConfidence: number;
  decisionScore: number;
  ruleScore: number;
  assessmentScore: number;
  evidenceCount: number;
  entityCount: number;
}

export function TechnicalDetailsCard({ mlConfidence, decisionScore, ruleScore, assessmentScore, evidenceCount, entityCount }: Props) {
  return (
    <Card>
      <CardContent className="py-6">
        <p className="text-xs text-zinc-400">Scores</p>
        <div className="mt-4 grid grid-cols-2 gap-6">
          {[
            { label: 'ML Confidence', value: `${(mlConfidence * 100).toFixed(0)}%` },
            { label: 'Decision Score', value: decisionScore.toFixed(2) },
            { label: 'Rule Score', value: ruleScore.toFixed(2) },
            { label: 'Assessment', value: `${assessmentScore}/100` },
            { label: 'Evidence', value: String(evidenceCount) },
            { label: 'Entities', value: String(entityCount) },
          ].map((s) => (
            <div key={s.label}>
              <p className="text-xs text-zinc-400">{s.label}</p>
              <p className="mt-0.5 text-sm font-semibold text-zinc-900 dark:text-zinc-100">{s.value}</p>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
