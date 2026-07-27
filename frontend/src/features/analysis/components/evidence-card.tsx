import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { StatusBadge } from '@/components/ui/status-badge';
import { severityStatus } from '@/design/status';
import { memo } from 'react';
import type { EvidenceItem } from '@/types';

interface EvidenceCardProps {
  supporting: EvidenceItem[];
  conflicting: EvidenceItem[];
}

const EvidenceRow = memo(function EvidenceRow({
  item,
  type,
}: {
  item: EvidenceItem;
  type: 'supporting' | 'conflicting';
}) {
  return (
    <div
      className={`rounded-lg border p-3 text-sm ${
        type === 'supporting'
          ? 'border-emerald-200 bg-emerald-50 dark:border-emerald-800 dark:bg-emerald-900/20'
          : 'border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-900/20'
      }`}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <p className="font-medium text-zinc-900 dark:text-zinc-50">
            {item.description}
          </p>
          <p className="mt-0.5 text-xs text-zinc-500 dark:text-zinc-400">
            {item.source} &middot; {item.type}
          </p>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <StatusBadge status={severityStatus(item.severity)} size="sm" showIcon={false} />
          <span className="whitespace-nowrap text-xs text-zinc-400">w:{item.weight}</span>
        </div>
      </div>
    </div>
  );
});

export const EvidenceCard = memo(function EvidenceCard({
  supporting,
  conflicting,
}: EvidenceCardProps) {
  if (supporting.length === 0 && conflicting.length === 0) return null;
  return (
    <Card>
      <CardHeader>
        <CardTitle>Evidence</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {supporting.length > 0 && (
          <div>
            <p className="mb-2 text-sm font-medium text-emerald-700 dark:text-emerald-400">
              Supporting Evidence ({supporting.length})
            </p>
            <div className="space-y-2">
              {supporting.map((item) => (
                <EvidenceRow key={item.id} item={item} type="supporting" />
              ))}
            </div>
          </div>
        )}
        {conflicting.length > 0 && (
          <div>
            <p className="mb-2 text-sm font-medium text-red-700 dark:text-red-400">
              Conflicting Evidence ({conflicting.length})
            </p>
            <div className="space-y-2">
              {conflicting.map((item) => (
                <EvidenceRow key={item.id} item={item} type="conflicting" />
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
});
