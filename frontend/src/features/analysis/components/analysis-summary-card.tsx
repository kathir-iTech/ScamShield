import { Card, CardContent } from '@/components/ui/card';
import { Shield } from 'lucide-react';

interface Props {
  prediction: string;
  confidence: number;
  riskLevel: string;
  assessmentBand: string;
  assessmentScore: number;
}

export function AnalysisSummaryCard({ prediction, confidence, riskLevel, assessmentBand, assessmentScore }: Props) {
  const confidenceColor = confidence > 0.8 ? 'bg-emerald-500' : confidence > 0.5 ? 'bg-amber-500' : 'bg-red-500';

  return (
    <Card>
      <CardContent className="grid gap-8 py-8 md:grid-cols-5">
        <div className="text-center md:text-left">
          <p className="text-xs text-zinc-400">Prediction</p>
          <p className="mt-1 text-lg font-semibold text-zinc-900 dark:text-zinc-50">{prediction}</p>
        </div>
        <div className="text-center md:text-left">
          <p className="text-xs text-zinc-400">Confidence</p>
          <div className="mt-1 flex items-baseline gap-1">
            <span className="text-2xl font-bold text-zinc-900 dark:text-zinc-50">{(confidence * 100).toFixed(0)}</span>
            <span className="text-sm text-zinc-400">%</span>
          </div>
          <div className="mt-2 h-1.5 w-full rounded-full bg-zinc-100 dark:bg-zinc-800" role="progressbar" aria-valuenow={Math.round(confidence * 100)} aria-valuemin={0} aria-valuemax={100}>
            <div className={`h-1.5 rounded-full transition-all ${confidenceColor}`} style={{ width: `${confidence * 100}%` }} />
          </div>
        </div>
        <div className="text-center md:text-left">
          <p className="text-xs text-zinc-400">Risk</p>
          <p className="mt-1 text-lg font-semibold text-zinc-900 dark:text-zinc-50">{riskLevel}</p>
        </div>
        <div className="text-center md:text-left">
          <p className="text-xs text-zinc-400">Score</p>
          <p className="mt-1 text-lg font-semibold text-zinc-900 dark:text-zinc-50">{assessmentScore}<span className="text-sm font-normal text-zinc-400">/100</span></p>
        </div>
        <div className="flex items-center justify-center gap-2 md:justify-start">
          <Shield className="h-4 w-4 text-emerald-500" />
          <span className="text-sm font-medium text-zinc-900 dark:text-zinc-50">{assessmentBand}</span>
        </div>
      </CardContent>
    </Card>
  );
}
