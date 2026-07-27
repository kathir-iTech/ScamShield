interface Props {
  report: Record<string, unknown>;
}

export function ReportSummaryCard({ report }: Props) {
  const entries = Object.entries(report).filter(([, v]) => v !== null && v !== undefined);
  if (entries.length === 0) return null;

  return (
    <div>
      <p className="text-xs text-text-tertiary mb-3">Report Summary</p>
      <div className="space-y-2">
        {entries.map(([key, value]) => (
          <div key={key} className="flex items-start gap-4 rounded-xl bg-glass border border-glass-border p-3">
            <p className="w-32 shrink-0 text-xs font-medium text-text-secondary">{key}</p>
            <p className="text-sm text-text-secondary/90 break-words">{String(value)}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
