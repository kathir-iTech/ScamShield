import { Card, CardContent } from '@/components/ui/card';

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
    <Card>
      <CardContent className="space-y-5 py-6">
        <p className="text-xs text-zinc-400">Assessment</p>
        <div className="flex items-baseline gap-6">
          <div>
            <p className="text-xs text-zinc-400">Band</p>
            <p className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">{assessmentBand}</p>
          </div>
          <div>
            <p className="text-xs text-zinc-400">Score</p>
            <p className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">{assessmentScore}<span className="text-sm font-normal text-zinc-400">/100</span></p>
          </div>
          <div>
            <p className="text-xs text-zinc-400">Confidence</p>
            <p className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">{assessmentConfidence}</p>
          </div>
        </div>
        <p className="text-sm text-zinc-600 dark:text-zinc-400">{assessmentSummary}</p>
        <div className="grid gap-4 md:grid-cols-2">
          <div className="rounded-xl bg-zinc-50 p-4 dark:bg-zinc-800/50">
            <p className="text-xs text-zinc-400">Business</p>
            <p className="mt-1 text-sm text-zinc-700 dark:text-zinc-300">{businessReason}</p>
          </div>
          <div className="rounded-xl bg-zinc-50 p-4 dark:bg-zinc-800/50">
            <p className="text-xs text-zinc-400">Technical</p>
            <p className="mt-1 text-sm text-zinc-700 dark:text-zinc-300">{technicalReason}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
