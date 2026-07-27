import { Card, CardContent } from '@/components/ui/card';

interface Props {
  report: Record<string, unknown>;
}

export function ReportSummaryCard({ report }: Props) {
  const entries = Object.entries(report).filter(([, v]) => v !== null && v !== undefined);
  if (entries.length === 0) return null;

  return (
    <Card>
      <CardContent className="space-y-3 py-6">
        <p className="text-xs text-zinc-400">Report Summary</p>
        {entries.map(([key, value]) => (
          <div key={key} className="flex items-start gap-3 rounded-xl bg-zinc-50 p-3 dark:bg-zinc-800/50">
            <p className="w-32 shrink-0 text-xs font-medium text-zinc-500">{key}</p>
            <p className="text-sm text-zinc-700 dark:text-zinc-300">{String(value)}</p>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
