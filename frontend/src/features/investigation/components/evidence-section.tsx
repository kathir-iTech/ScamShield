import { useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { AnalysisResponse } from '@/types';
import { CheckCircle, XCircle } from 'lucide-react';

interface EvidenceSectionProps {
  result: AnalysisResponse;
}

const SEVERITY_COLORS: Record<string, string> = {
  critical: 'bg-red-500',
  high: 'bg-orange-500',
  medium: 'bg-amber-500',
  low: 'bg-blue-500',
  info: 'bg-zinc-400',
};

export function EvidenceSection({ result }: EvidenceSectionProps) {
  const supporting = useMemo(() => result.supporting_evidence ?? [], [result]);
  const conflicting = useMemo(() => result.conflicting_evidence ?? [], [result]);

  const allEvidence = useMemo(() => {
    const items = [
      ...supporting.map((e) => ({ ...e, _type: 'supporting' as const })),
      ...conflicting.map((e) => ({ ...e, _type: 'conflicting' as const })),
    ];
    return items.sort((a, b) => b.weight - a.weight);
  }, [supporting, conflicting]);

  if (allEvidence.length === 0) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center p-6">
          <p className="text-sm text-zinc-500">No evidence available</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm">Evidence</CardTitle>
          <div className="flex items-center gap-3 text-xs">
            <span className="flex items-center gap-1 text-emerald-600 dark:text-emerald-400">
              <CheckCircle className="h-3 w-3" /> {supporting.length} supporting
            </span>
            <span className="flex items-center gap-1 text-red-600 dark:text-red-400">
              <XCircle className="h-3 w-3" /> {conflicting.length} conflicting
            </span>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-2 pt-0">
        {allEvidence.map((item) => (
          <div
            key={item.id}
            className={`rounded-lg border p-3 text-sm transition-colors ${
              item._type === 'supporting'
                ? 'border-emerald-200 bg-emerald-50/50 dark:border-emerald-800 dark:bg-emerald-900/10'
                : 'border-red-200 bg-red-50/50 dark:border-red-800 dark:bg-red-900/10'
            }`}
          >
            <div className="flex items-start justify-between gap-2">
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  {item._type === 'supporting'
                    ? <CheckCircle className="h-3.5 w-3.5 shrink-0 text-emerald-500" />
                    : <XCircle className="h-3.5 w-3.5 shrink-0 text-red-500" />
                  }
                  <span className="font-medium text-zinc-800 dark:text-zinc-200">{item.description}</span>
                </div>
                <div className="mt-1 flex flex-wrap items-center gap-2 pl-5">
                  <Badge variant="outline" className="text-[10px]">{item.type}</Badge>
                  {item.source && (
                    <span className="text-[10px] text-zinc-400">source: {item.source}</span>
                  )}
                </div>
              </div>
              <div className="flex shrink-0 items-center gap-1.5">
                {item.severity && (
                  <span className={`h-2 w-2 rounded-full ${SEVERITY_COLORS[item.severity] ?? 'bg-zinc-400'}`} />
                )}
                <span className="text-[10px] text-zinc-400">w:{item.weight}</span>
              </div>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
