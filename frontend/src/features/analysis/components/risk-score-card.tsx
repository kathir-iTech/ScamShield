import { memo, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { StatusBadge } from '@/components/ui/status-badge';
import { Metric } from '@/components/ui/metric';
import { riskStatus } from '@/design/status';
import { Gauge } from 'lucide-react';

interface RiskScoreCardProps {
  ruleScore: number;
  ruleLabel: string;
  decisionScore: number;
  decisionLevel: string;
  riskLevel: string;
  scamCategory: string;
}

export const RiskScoreCard = memo(function RiskScoreCard({
  ruleScore,
  ruleLabel,
  decisionScore,
  decisionLevel,
  riskLevel,
  scamCategory,
}: RiskScoreCardProps) {
  const riskStatusConfig = useMemo(() => riskStatus(riskLevel), [riskLevel]);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Gauge className="h-5 w-5" />
          Risk &amp; Scoring
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex flex-wrap gap-6">
          <Metric
            label="Risk Level"
            value={<StatusBadge status={riskStatusConfig} />}
          />
          <Metric
            label="Category"
            value={scamCategory}
          />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div className="rounded-lg bg-zinc-50 p-3 dark:bg-zinc-800/50">
            <p className="text-xs text-zinc-500 dark:text-zinc-400">Rule Score</p>
            <p className="text-lg font-bold text-zinc-900 dark:text-zinc-50">
              {ruleScore.toFixed(1)}
            </p>
            <p className="text-xs text-zinc-400">{ruleLabel}</p>
          </div>
          <div className="rounded-lg bg-zinc-50 p-3 dark:bg-zinc-800/50">
            <p className="text-xs text-zinc-500 dark:text-zinc-400">Decision Score</p>
            <p className="text-lg font-bold text-zinc-900 dark:text-zinc-50">
              {decisionScore}
            </p>
            <p className="text-xs text-zinc-400">{decisionLevel}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
});
