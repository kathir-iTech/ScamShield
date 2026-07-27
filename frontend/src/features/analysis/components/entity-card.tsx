interface EntityItem {
  value: string;
  type: string;
  confidence: number;
  source: string;
  risk: string;
  risk_reason: string;
}

interface Props {
  entities: EntityItem[];
}

export function EntityCard({ entities }: Props) {
  if (entities.length === 0) return null;

  return (
    <div>
      <p className="text-xs text-text-tertiary mb-3">Entities ({entities.length})</p>
      <div className="space-y-2">
        {entities.map((e, i) => (
          <div key={i} className="flex items-start gap-3 rounded-xl bg-glass border border-glass-border p-3">
            <span className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${
              e.risk === 'HIGH' ? 'bg-danger' :
              e.risk === 'MEDIUM' ? 'bg-warning' :
              'bg-text-tertiary'
            }`} />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-text-primary truncate">{e.value}</p>
              <p className="text-xs text-text-tertiary">{e.type} &middot; {e.source}</p>
            </div>
            <span className="shrink-0 text-xs text-text-tertiary tabular-nums">{(e.confidence * 100).toFixed(0)}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}
