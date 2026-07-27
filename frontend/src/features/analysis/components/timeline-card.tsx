import { useAnalysis } from '@/features/analysis/context/analysis-context';

export function TimelineCard() {
  const { history } = useAnalysis();
  if (history.length === 0) return null;

  return (
    <div>
      <p className="text-xs text-text-tertiary mb-4">Recent analyses</p>
      <div className="space-y-3">
        {history.slice(0, 5).map((h) => (
          <div key={h.id} className="flex items-center gap-3">
            <span className="h-2 w-2 shrink-0 rounded-full bg-accent" />
            <div className="flex-1 min-w-0">
              <p className="truncate text-sm text-text-secondary">
                {h.inputText || h.inputFileName || 'Analysis'}
              </p>
            </div>
            <span className="shrink-0 text-xs text-text-tertiary tabular-nums">{new Date(h.timestamp).toLocaleTimeString()}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
