import { useState, useMemo, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import type { AnalysisResponse, EntityItem } from '@/types';
import { Users, Search, Copy, Check, ChevronDown, ChevronRight } from 'lucide-react';

interface EntityExplorerProps {
  result: AnalysisResponse;
}

const RISK_BADGE: Record<string, 'destructive' | 'warning' | 'info' | 'outline' | 'default'> = {
  high: 'destructive',
  medium: 'warning',
  low: 'info',
  unknown: 'outline',
};

export function EntityExplorer({ result }: EntityExplorerProps) {
  const [expanded, setExpanded] = useState(true);
  const [search, setSearch] = useState('');
  const [copied, setCopied] = useState<string | null>(null);

  const allEntities = useMemo(() => {
    const items: (EntityItem & { risk: string })[] = [
      ...(result.entity_risk?.high ?? []).map((e) => ({ ...e, risk: 'high' })),
      ...(result.entity_risk?.medium ?? []).map((e) => ({ ...e, risk: 'medium' })),
      ...(result.entity_risk?.low ?? []).map((e) => ({ ...e, risk: 'low' })),
    ];
    return items;
  }, [result]);

  const grouped = useMemo(() => {
    const groups: Record<string, (EntityItem & { risk: string })[]> = {};
    for (const entity of allEntities) {
      const key = entity.type || 'unknown';
      if (!groups[key]) groups[key] = [];
      groups[key].push(entity);
    }
    return groups;
  }, [allEntities]);

  const filteredGroups = useMemo(() => {
    if (!search) return grouped;
    const q = search.toLowerCase();
    const result: Record<string, (EntityItem & { risk: string })[]> = {};
    for (const [type, items] of Object.entries(grouped)) {
      const filtered = items.filter((e) => e.value.toLowerCase().includes(q));
      if (filtered.length > 0) result[type] = filtered;
    }
    return result;
  }, [grouped, search]);

  const handleCopy = useCallback(async (value: string) => {
    await navigator.clipboard.writeText(value);
    setCopied(value);
    setTimeout(() => setCopied(null), 1500);
  }, []);

  const sortedTypes = useMemo(() => {
    return Object.entries(filteredGroups).sort(([, a], [, b]) => b.length - a.length);
  }, [filteredGroups]);

  return (
    <Card>
      <CardHeader className="pb-3">
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex w-full items-center justify-between"
          aria-expanded={expanded}
        >
          <div className="flex items-center gap-2">
            <Users className="h-4 w-4 text-blue-500" />
            <CardTitle className="text-sm">Entity Explorer</CardTitle>
            <Badge variant="outline" className="text-[9px]">{allEntities.length} entities</Badge>
          </div>
          {expanded ? <ChevronDown className="h-4 w-4 text-zinc-400" /> : <ChevronRight className="h-4 w-4 text-zinc-400" />}
        </button>
      </CardHeader>
      {expanded && (
        <CardContent className="space-y-3 pt-0">
          {allEntities.length > 0 && (
            <div className="relative">
              <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-zinc-400" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search entities..."
                className="w-full rounded-lg border border-zinc-200 bg-white py-1.5 pl-8 pr-3 text-xs placeholder-zinc-400 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100"
              />
            </div>
          )}

          {sortedTypes.length === 0 ? (
            <p className="py-4 text-center text-xs text-zinc-500">
              {search ? 'No entities match your search.' : 'No entities found.'}
            </p>
          ) : (
            sortedTypes.map(([type, entities]) => (
              <div key={type}>
                <div className="mb-1.5 flex items-center gap-2">
                  <span className="text-xs font-medium text-zinc-500 capitalize">{type}</span>
                  <span className="text-[10px] text-zinc-400">({entities.length})</span>
                </div>
                <div className="space-y-1">
                  {entities.map((entity, i) => (
                    <div
                      key={`${entity.value}_${i}`}
                      className="flex items-center gap-2 rounded-lg bg-zinc-50 px-2.5 py-2 dark:bg-zinc-800/50"
                    >
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-1.5">
                          <span className="text-xs font-medium text-zinc-800 dark:text-zinc-200">{entity.value}</span>
                          <Badge variant={RISK_BADGE[entity.risk]} className="text-[9px] px-1 py-0">
                            {entity.risk}
                          </Badge>
                        </div>
                        <div className="mt-0.5 flex items-center gap-2">
                          <span className="text-[10px] text-zinc-400">source: {entity.source}</span>
                          <span className="text-[10px] text-zinc-400">conf: {(entity.confidence * 100).toFixed(0)}%</span>
                        </div>
                      </div>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-6 w-6 shrink-0"
                        onClick={() => handleCopy(entity.value)}
                        aria-label={`Copy ${entity.value}`}
                      >
                        {copied === entity.value ? <Check className="h-3 w-3 text-emerald-500" /> : <Copy className="h-3 w-3" />}
                      </Button>
                    </div>
                  ))}
                </div>
              </div>
            ))
          )}
        </CardContent>
      )}
    </Card>
  );
}
