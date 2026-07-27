interface Props {
  scamCategory: string;
  summary: string;
  reasons: string[];
  businessReason: string;
  technicalReason: string;
}

export function CategoryCard({ scamCategory, summary, reasons, businessReason, technicalReason }: Props) {
  return (
    <div className="space-y-4">
      <div>
        <p className="text-xs text-text-tertiary mb-1">Category</p>
        <p className="text-sm font-medium text-text-primary">{scamCategory}</p>
      </div>
      <p className="text-sm text-text-secondary/80">{summary}</p>
      {reasons.length > 0 && (
        <div>
          <p className="text-xs text-text-tertiary mb-1">Why</p>
          <ul className="space-y-0.5 text-sm text-text-secondary/80">
            {reasons.map((r, i) => <li key={i} className="flex items-start gap-2"><span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-accent/40" />{r}</li>)}
          </ul>
        </div>
      )}
      <div className="grid gap-3 md:grid-cols-2">
        <div className="rounded-xl bg-glass p-4 border border-glass-border">
          <p className="text-xs text-text-tertiary">Business</p>
          <p className="mt-1 text-sm text-text-secondary/90">{businessReason}</p>
        </div>
        <div className="rounded-xl bg-glass p-4 border border-glass-border">
          <p className="text-xs text-text-tertiary">Technical</p>
          <p className="mt-1 text-sm text-text-secondary/90">{technicalReason}</p>
        </div>
      </div>
    </div>
  );
}
