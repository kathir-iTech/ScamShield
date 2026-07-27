import { useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { StatusBadge } from '@/components/ui/status-badge';
import { Info } from 'lucide-react';
import type { StatusConfig } from '@/design/status';

interface CategoryCardProps {
  scamCategory: string;
  summary: string;
  reasons: string[];
  businessReason: string;
  technicalReason: string;
}

export function CategoryCard({
  scamCategory,
  summary,
  reasons,
  businessReason,
  technicalReason,
}: CategoryCardProps) {
  const categoryBadge: StatusConfig = useMemo(
    () => ({ variant: 'info', icon: Info, label: scamCategory }),
    [scamCategory]
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Info className="h-5 w-5" />
          Scam Classification
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <p className="text-xs text-zinc-500 dark:text-zinc-400">Category</p>
          <div className="mt-1">
            <StatusBadge status={categoryBadge} />
          </div>
        </div>
        <div>
          <p className="text-xs text-zinc-500 dark:text-zinc-400">Summary</p>
          <p className="mt-1 text-sm text-zinc-700 dark:text-zinc-300">{summary}</p>
        </div>
        {reasons.length > 0 && (
          <div>
            <p className="mb-1 text-xs text-zinc-500 dark:text-zinc-400">Reasons</p>
            <ul className="list-inside list-disc space-y-0.5 text-sm text-zinc-700 dark:text-zinc-300">
              {reasons.map((r, i) => (
                <li key={i}>{r}</li>
              ))}
            </ul>
          </div>
        )}
        <div className="grid gap-4 md:grid-cols-2">
          <div className="rounded-lg bg-zinc-50 p-3 dark:bg-zinc-800/50">
            <p className="text-xs font-medium text-zinc-500 dark:text-zinc-400">
              Business Analysis
            </p>
            <p className="mt-1 text-sm text-zinc-700 dark:text-zinc-300">
              {businessReason}
            </p>
          </div>
          <div className="rounded-lg bg-zinc-50 p-3 dark:bg-zinc-800/50">
            <p className="text-xs font-medium text-zinc-500 dark:text-zinc-400">
              Technical Analysis
            </p>
            <p className="mt-1 text-sm text-zinc-700 dark:text-zinc-300">
              {technicalReason}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
