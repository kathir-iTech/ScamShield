import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { AnalysisResponse } from '@/types';
import { Lightbulb, AlertTriangle, ChevronRight } from 'lucide-react';

interface ReasoningSectionProps {
  result: AnalysisResponse;
}

export function ReasoningSection({ result }: ReasoningSectionProps) {
  const hasBreakdown = result.confidence_breakdown;

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center gap-2">
          <Lightbulb className="h-4 w-4 text-amber-500" />
          <CardTitle className="text-sm">Reasoning & Confidence</CardTitle>
        </div>
      </CardHeader>
      <CardContent className="space-y-4 pt-0">
        {result.reasons.length > 0 && (
          <div>
            <p className="mb-2 text-xs font-medium text-zinc-500">Analysis Reasons</p>
            <ul className="space-y-1.5">
              {result.reasons.map((reason, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-zinc-700 dark:text-zinc-300">
                  <ChevronRight className="mt-0.5 h-3.5 w-3.5 shrink-0 text-zinc-400" />
                  <span>{reason}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {result.suggested_action && (
          <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 dark:border-amber-800 dark:bg-amber-900/20">
            <div className="flex items-start gap-2">
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-600 dark:text-amber-400" />
              <div>
                <p className="text-xs font-medium text-amber-800 dark:text-amber-300">Suggested Action</p>
                <p className="mt-0.5 text-sm text-amber-700 dark:text-amber-200">{result.suggested_action}</p>
              </div>
            </div>
          </div>
        )}

        {hasBreakdown && (
          <div>
            <p className="mb-2 text-xs font-medium text-zinc-500">Confidence Breakdown</p>
            <div className="space-y-1.5">
              {Object.entries(result.confidence_breakdown).map(([key, value]) => {
                if (typeof value !== 'number') return null;
                return (
                  <div key={key} className="flex items-center gap-2">
                    <span className="w-24 text-xs text-zinc-500 capitalize">{key.replace(/_/g, ' ')}</span>
                    <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-zinc-200 dark:bg-zinc-700">
                      <div
                        className="h-full rounded-full bg-emerald-500"
                        style={{ width: `${(value * 100).toFixed(0)}%` }}
                      />
                    </div>
                    <span className="w-8 text-right text-xs text-zinc-400">{(value * 100).toFixed(0)}%</span>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {result.risk_breakdown && (
          <div>
            <p className="mb-2 text-xs font-medium text-zinc-500">Risk Breakdown</p>
            <div className="flex flex-wrap gap-1.5">
              {Object.entries(result.risk_breakdown).map(([key, value]) => (
                <Badge key={key} variant={value > 0.6 ? 'destructive' : value > 0.3 ? 'warning' : 'secondary'}>
                  {key.replace(/_/g, ' ')}: {(value * 100).toFixed(0)}%
                </Badge>
              ))}
            </div>
          </div>
        )}

        {result.detected_indicators.length > 0 && (
          <div>
            <p className="mb-2 text-xs font-medium text-zinc-500">Detected Indicators</p>
            <div className="flex flex-wrap gap-1.5">
              {result.detected_indicators.map((indicator, i) => (
                <Badge key={i} variant="outline">{indicator}</Badge>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
