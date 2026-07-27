import { Card, CardContent } from '@/components/ui/card';

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
    <Card>
      <CardContent className="space-y-6 py-6">
        <p className="text-xs text-zinc-400">Evidence</p>
        {supporting.length > 0 && (
          <div className="space-y-3">
            {supporting.map((e) => (
              <div key={e.id} className="flex items-start gap-3 rounded-xl bg-emerald-50 p-4 dark:bg-emerald-900/10">
                <span className="mt-0.5 h-2 w-2 shrink-0 rounded-full bg-emerald-500" />
                <div>
                  <p className="text-sm font-medium text-zinc-900 dark:text-zinc-100">{e.type}</p>
                  <p className="text-sm text-zinc-600 dark:text-zinc-400">{e.description}</p>
                </div>
              </div>
            ))}
          </div>
        )}
        {conflicting.length > 0 && (
          <div className="space-y-3">
            {conflicting.map((e) => (
              <div key={e.id} className="flex items-start gap-3 rounded-xl bg-zinc-50 p-4 dark:bg-zinc-800/50">
                <span className="mt-0.5 h-2 w-2 shrink-0 rounded-full bg-zinc-300" />
                <div>
                  <p className="text-sm font-medium text-zinc-900 dark:text-zinc-100">{e.type}</p>
                  <p className="text-sm text-zinc-600 dark:text-zinc-400">{e.description}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
