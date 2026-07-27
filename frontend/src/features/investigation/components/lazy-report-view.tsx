import { ReportBuilder } from '@/features/report';
import type { AnalysisResponse } from '@/types';
import type { TimelineEvent } from '@/features/timeline/types';

interface LazyReportViewProps {
  result: AnalysisResponse;
  events: TimelineEvent[];
}

export default function LazyReportView({ result, events }: LazyReportViewProps) {
  return (
    <div className="h-full overflow-y-auto p-1">
      <ReportBuilder result={result} events={events} />
    </div>
  );
}
