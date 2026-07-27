import { useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { StatusBadge } from '@/components/ui/status-badge';
import { Metric } from '@/components/ui/metric';
import { assessmentStatus } from '@/design/status';
import { ClipboardList } from 'lucide-react';

interface AssessmentCardProps {
  assessmentScore: number;
  assessmentBand: string;
  assessmentConfidence: string;
  assessmentSummary: string;
  businessReason: string;
  technicalReason: string;
}

export function AssessmentCard({
  assessmentScore,
  assessmentBand,
  assessmentConfidence,
  assessmentSummary,
  businessReason,
  technicalReason,
}: AssessmentCardProps) {
  const bandStatus = useMemo(() => assessmentStatus(assessmentBand), [assessmentBand]);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <ClipboardList className="h-5 w-5" />
          Assessment
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex flex-wrap gap-6">
          <Metric
            label="Band"
            value={<StatusBadge status={bandStatus} />}
          />
          <Metric
            label="Score"
            value={`${assessmentScore}/100`}
            size="lg"
          />
          <Metric
            label="Confidence"
            value={assessmentConfidence}
          />
        </div>
        <div>
          <p className="text-xs text-zinc-500 dark:text-zinc-400">Summary</p>
          <p className="mt-1 text-sm text-zinc-700 dark:text-zinc-300">
            {assessmentSummary}
          </p>
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          <div className="rounded-lg bg-zinc-50 p-3 dark:bg-zinc-800/50">
            <p className="text-xs font-medium text-zinc-500 dark:text-zinc-400">
              Business Reason
            </p>
            <p className="mt-1 text-sm text-zinc-700 dark:text-zinc-300">
              {businessReason}
            </p>
          </div>
          <div className="rounded-lg bg-zinc-50 p-3 dark:bg-zinc-800/50">
            <p className="text-xs font-medium text-zinc-500 dark:text-zinc-400">
              Technical Reason
            </p>
            <p className="mt-1 text-sm text-zinc-700 dark:text-zinc-300">
              {technicalReason}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
