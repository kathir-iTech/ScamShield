import { Card, CardContent } from '@/components/ui/card';

interface Props {
  ruleScore: number;
  ruleLabel: string;
  decisionScore: number;
  decisionLevel: string;
  riskLevel: string;
  scamCategory: string;
}

const riskColors: Record<string, string> = {
  HIGH: 'text-red-600 bg-red-50 dark:bg-red-900/20 dark:text-red-400',
  MEDIUM: 'text-amber-600 bg-amber-50 dark:bg-amber-900/20 dark:text-amber-400',
  LOW: 'text-emerald-600 bg-emerald-50 dark:bg-emerald-900/20 dark:text-emerald-400',
  SAFE: 'text-emerald-600 bg-emerald-50 dark:bg-emerald-900/20 dark:text-emerald-400',
};

export function RiskScoreCard({ ruleScore, ruleLabel, decisionScore, decisionLevel, riskLevel, scamCategory }: Props) {
  const riskColor = riskColors[riskLevel] || riskColors.LOW;

  return (
    <Card>
      <CardContent className="space-y-5 py-6">
        <p className="text-xs text-zinc-400">Risk &amp; Scoring</p>
        <div className="flex gap-4">
          <span className={`rounded-full px-3 py-1 text-xs font-medium ${riskColor}`}>{riskLevel}</span>
          <span className="text-sm text-zinc-600 dark:text-zinc-400">{scamCategory}</span>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div className="rounded-xl bg-zinc-50 p-4 dark:bg-zinc-800/50">
            <p className="text-xs text-zinc-400">Rule Score</p>
            <p className="mt-1 text-xl font-bold text-zinc-900 dark:text-zinc-50">{ruleScore.toFixed(1)}</p>
            <p className="text-xs text-zinc-400">{ruleLabel}</p>
          </div>
          <div className="rounded-xl bg-zinc-50 p-4 dark:bg-zinc-800/50">
            <p className="text-xs text-zinc-400">Decision</p>
            <p className="mt-1 text-xl font-bold text-zinc-900 dark:text-zinc-50">{decisionScore}</p>
            <p className="text-xs text-zinc-400">{decisionLevel}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
