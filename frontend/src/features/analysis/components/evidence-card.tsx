interface EvidenceItem {
  id: string;
  type: string;
  source: string;
  description: string;
  severity: string;
  confidence: number;
}

interface Props {
  supporting: EvidenceItem[];
  conflicting: EvidenceItem[];
}

export function EvidenceCard({ supporting, conflicting }: Props) {
  if (supporting.length === 0 && conflicting.length === 0) return null;

  return (
    <div className="space-y-4">
      <p className="text-xs text-text-tertiary">Evidence</p>
      {supporting.length > 0 && (
        <div className="space-y-2">
          {supporting.map((e) => (
            <div key={e.id} className="flex items-start gap-3 rounded-xl bg-success/5 border border-success/10 p-4">
              <span className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-success" />
              <div>
                <p className="text-sm font-medium text-text-primary">{e.type}</p>
                <p className="text-sm text-text-secondary/80">{e.description}</p>
              </div>
            </div>
          ))}
        </div>
      )}
      {conflicting.length > 0 && (
        <div className="space-y-2">
          {conflicting.map((e) => (
            <div key={e.id} className="flex items-start gap-3 rounded-xl bg-glass border border-glass-border p-4">
              <span className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-text-tertiary" />
              <div>
                <p className="text-sm font-medium text-text-primary">{e.type}</p>
                <p className="text-sm text-text-secondary/80">{e.description}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
