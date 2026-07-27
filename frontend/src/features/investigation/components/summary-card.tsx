import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import type { AnalysisResponse } from '@/types';
import { Shield, AlertTriangle, BarChart3, Target } from 'lucide-react';

interface SummaryCardProps {
  result: AnalysisResponse | null;
  loading?: boolean;
}

const RISK_BADGE_VARIANTS: Record<string, 'destructive' | 'warning' | 'info' | 'default' | 'outline'> = {
  critical: 'destructive',
  high: 'destructive',
  medium: 'warning',
  low: 'info',
  unknown: 'outline',
};

export function SummaryCard({ result, loading }: SummaryCardProps) {
  if (loading) {
    return (
      <Card>
        <CardHeader className="pb-3"><CardTitle className="text-sm">Case Summary</CardTitle></CardHeader>
        <CardContent className="space-y-3 pt-0">
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-4 w-1/2" />
          <Skeleton className="h-4 w-2/3" />
        </CardContent>
      </Card>
    );
  }

  if (!result) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center p-6">
          <p className="text-sm text-zinc-500">No analysis data</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm">Case Summary</CardTitle>
          <Badge variant={RISK_BADGE_VARIANTS[result.risk_level] ?? 'outline'}>
            {result.risk_level.toUpperCase()}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4 pt-0">
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-1.5 text-xs text-zinc-500">
              <Shield className="h-3 w-3" />
              Prediction
            </div>
            <p className="text-sm font-medium text-zinc-900 dark:text-zinc-100">{result.prediction}</p>
          </div>
          <div className="space-y-1">
            <div className="flex items-center gap-1.5 text-xs text-zinc-500">
              <Target className="h-3 w-3" />
              Category
            </div>
            <p className="text-sm font-medium text-zinc-900 dark:text-zinc-100">{result.scam_category}</p>
          </div>
          <div className="space-y-1">
            <div className="flex items-center gap-1.5 text-xs text-zinc-500">
              <BarChart3 className="h-3 w-3" />
              Confidence
            </div>
            <div className="flex items-center gap-2">
              <div className="h-2 w-20 overflow-hidden rounded-full bg-zinc-200 dark:bg-zinc-700">
                <div className="h-full rounded-full bg-emerald-500" style={{ width: `${(result.confidence * 100).toFixed(0)}%` }} />
              </div>
              <span className="text-xs text-zinc-500">{(result.confidence * 100).toFixed(0)}%</span>
            </div>
          </div>
          <div className="space-y-1">
            <div className="flex items-center gap-1.5 text-xs text-zinc-500">
              <AlertTriangle className="h-3 w-3" />
              Priority
            </div>
            <Badge variant={result.recommended_priority === 'high' || result.recommended_priority === 'critical' ? 'destructive' : result.recommended_priority === 'medium' ? 'warning' : 'info'}>
              {result.recommended_priority.toUpperCase()}
            </Badge>
          </div>
        </div>

        {result.entity_summary && (
          <div className="flex flex-wrap gap-2">
            <Badge variant="outline">{result.entity_summary.total_entities} entities</Badge>
            <Badge variant="outline">{result.supporting_evidence.length + result.conflicting_evidence.length} evidence</Badge>
            <Badge variant="outline">{result.threats.length} threats</Badge>
          </div>
        )}

        {result.summary && (
          <p className="text-xs leading-relaxed text-zinc-600 dark:text-zinc-400">{result.summary}</p>
        )}
      </CardContent>
    </Card>
  );
}
