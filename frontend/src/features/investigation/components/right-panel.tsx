import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import type { AnalysisResponse } from '@/types';
import { Copy, Check, ExternalLink } from 'lucide-react';
import { useState, useCallback, useMemo } from 'react';

interface RightPanelProps {
  result: AnalysisResponse | null;
}

const ENTITY_RISK_COLORS: Record<string, string> = {
  high: 'border-l-red-500',
  medium: 'border-l-amber-500',
  low: 'border-l-blue-500',
  unknown: 'border-l-zinc-400',
};

export function RightPanel({ result }: RightPanelProps) {
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const allEntities = useMemo(() => {
    if (!result) return [];
    const items = [
      ...(result.entity_risk?.high ?? []).map((e) => ({ ...e, risk: 'high' as const })),
      ...(result.entity_risk?.medium ?? []).map((e) => ({ ...e, risk: 'medium' as const })),
      ...(result.entity_risk?.low ?? []).map((e) => ({ ...e, risk: 'low' as const })),
    ];
    return items;
  }, [result]);

  const handleCopy = useCallback(async (value: string, id: string) => {
    await navigator.clipboard.writeText(value);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 1500);
  }, []);

  if (!result) {
    return (
      <div className="flex h-full items-center justify-center p-6">
        <p className="text-sm text-zinc-500">No analysis data</p>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col gap-3 overflow-y-auto p-3">
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-xs font-medium">Entities ({allEntities.length})</CardTitle>
        </CardHeader>
        <CardContent className="space-y-1.5 pt-0">
          {allEntities.length === 0 ? (
            <p className="py-2 text-center text-xs text-zinc-500">No entities found</p>
          ) : (
            allEntities.map((entity, i) => (
              <div
                key={`${entity.value}_${i}`}
                className={`rounded-r-lg border-l-4 bg-zinc-50 px-2.5 py-2 dark:bg-zinc-800/50 ${ENTITY_RISK_COLORS[entity.risk] ?? 'border-l-zinc-400'}`}
              >
                <div className="flex items-start justify-between gap-1">
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-xs font-medium text-zinc-800 dark:text-zinc-200">{entity.value}</p>
                    <div className="mt-0.5 flex flex-wrap items-center gap-1">
                      <Badge variant="outline" className="text-[9px]">{entity.type}</Badge>
                      <span className="text-[9px] text-zinc-400">{(entity.confidence * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-6 w-6 shrink-0"
                    onClick={() => handleCopy(entity.value, `${entity.value}_${i}`)}
                    aria-label="Copy entity value"
                  >
                    {copiedId === `${entity.value}_${i}` ? <Check className="h-3 w-3 text-emerald-500" /> : <Copy className="h-3 w-3" />}
                  </Button>
                </div>
                {entity.risk_reason && (
                  <p className="mt-1 text-[10px] leading-tight text-zinc-500">{entity.risk_reason}</p>
                )}
              </div>
            ))
          )}
        </CardContent>
      </Card>

      {result.threats.length > 0 && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-medium">Threats ({result.threats.length})</CardTitle>
          </CardHeader>
          <CardContent className="space-y-1 pt-0">
            {result.threats.map((threat, i) => (
              <div key={i} className="flex items-center gap-2 rounded-lg bg-red-50 px-2.5 py-1.5 text-xs dark:bg-red-900/20">
                <span className="h-1.5 w-1.5 rounded-full bg-red-500" />
                <span className="text-red-700 dark:text-red-300">{threat}</span>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {result.detected_indicators.length > 0 && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-medium">Indicators ({result.detected_indicators.length})</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-1 pt-0">
            {result.detected_indicators.map((indicator, i) => (
              <Badge key={i} variant="outline" className="text-[9px]">{indicator}</Badge>
            ))}
          </CardContent>
        </Card>
      )}

      {result.recommended_actions.length > 0 && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-medium">Recommended Actions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-1 pt-0">
            {result.recommended_actions.map((action, i) => (
              <div key={i} className="flex items-start gap-2 text-xs text-zinc-600 dark:text-zinc-400">
                <ExternalLink className="mt-0.5 h-3 w-3 shrink-0" />
                <span>{action}</span>
              </div>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
