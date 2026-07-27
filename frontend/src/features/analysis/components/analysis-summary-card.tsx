import { Card, CardContent } from '@/components/ui/card';
import { Metric } from '@/components/ui/metric';
import { StatusBadge } from '@/components/ui/status-badge';
import { predictionStatus, riskStatus } from '@/design/status';
import { Shield } from 'lucide-react';

interface AnalysisSummaryCardProps {
  prediction: string;
  confidence: number;
  riskLevel: string;
  assessmentBand: string;
  assessmentScore: number;
}

export function AnalysisSummaryCard({
  prediction,
  confidence,
  riskLevel,
  assessmentBand,
  assessmentScore,
}: AnalysisSummaryCardProps) {
  return (
    <Card>
      <CardContent className="grid gap-6 p-6 md:grid-cols-5">
        <Metric
          label="Prediction"
          value={<StatusBadge status={predictionStatus(prediction)} size="md" />}
          size="sm"
          className="items-center text-center md:items-start md:text-left"
        />

        <Metric
          label="Confidence"
          value={
            <div className="space-y-1">
              <span className="text-2xl font-bold">
                {(confidence * 100).toFixed(0)}
                <span className="text-sm font-normal text-zinc-400">%</span>
              </span>
              <div
                className="h-2 w-full rounded-full bg-zinc-200 dark:bg-zinc-700"
                role="progressbar"
                aria-valuenow={Math.round(confidence * 100)}
                aria-valuemin={0}
                aria-valuemax={100}
                aria-label={`Confidence: ${(confidence * 100).toFixed(0)}%`}
              >
                <div
                  className={`h-2 rounded-full transition-all ${
                    confidence > 0.8
                      ? 'bg-emerald-500'
                      : confidence > 0.5
                      ? 'bg-amber-500'
                      : 'bg-red-500'
                  }`}
                  style={{ width: `${confidence * 100}%` }}
                />
              </div>
            </div>
          }
          size="sm"
        />

        <Metric
          label="Risk Level"
          value={<StatusBadge status={riskStatus(riskLevel)} size="md" />}
          size="sm"
          className="items-center text-center md:items-start md:text-left"
        />

        <Metric
          label="Assessment Score"
          value={
            <span className="text-2xl font-bold">
              {assessmentScore}
              <span className="text-sm font-normal text-zinc-400">/100</span>
            </span>
          }
          size="sm"
        />

        <Metric
          label="Assessment Band"
          value={
            <div className="flex items-center gap-2">
              <Shield className="h-4 w-4 text-emerald-500" />
              <span className="text-sm font-medium text-zinc-900 dark:text-zinc-50">
                {assessmentBand}
              </span>
            </div>
          }
          size="sm"
        />
      </CardContent>
    </Card>
  );
}
