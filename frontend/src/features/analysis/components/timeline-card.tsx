import { Card, CardContent } from '@/components/ui/card';
import { useAnalysis } from '@/features/analysis/context/analysis-context';

export function TimelineCard() {
  const { history } = useAnalysis();
  if (history.length === 0) return null;

  return (
    <Card>
      <CardContent className="py-6">
        <p className="text-xs text-zinc-400">Recent analyses</p>
        <div className="mt-4 space-y-3">
          {history.slice(0, 5).map((h) => (
            <div key={h.id} className="flex items-center gap-3">
              <span className="h-2 w-2 rounded-full bg-emerald-500" />
              <div className="flex-1 min-w-0">
                <p className="truncate text-sm text-zinc-600 dark:text-zinc-400">
                  {h.inputText || h.inputFileName || 'Analysis'}
                </p>
              </div>
              <span className="shrink-0 text-xs text-zinc-400">{new Date(h.timestamp).toLocaleTimeString()}</span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
