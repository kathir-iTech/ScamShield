import { Card, CardContent } from '@/components/ui/card';

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
    <Card>
      <CardContent className="space-y-3 py-6">
        <p className="text-xs text-zinc-400">Entities ({entities.length})</p>
        {entities.map((e, i) => (
          <div key={i} className="flex items-start gap-3 rounded-xl bg-zinc-50 p-3 dark:bg-zinc-800/50">
            <span className={`mt-1 h-2 w-2 shrink-0 rounded-full ${e.risk === 'HIGH' ? 'bg-red-500' : e.risk === 'MEDIUM' ? 'bg-amber-500' : 'bg-zinc-300'}`} />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-zinc-900 dark:text-zinc-100 truncate">{e.value}</p>
              <p className="text-xs text-zinc-500">{e.type} &middot; {e.source}</p>
            </div>
            <span className="shrink-0 text-xs text-zinc-400">{(e.confidence * 100).toFixed(0)}%</span>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
