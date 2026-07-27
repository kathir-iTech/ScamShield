import { useMemo, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { AnalysisResponse } from '@/types';
import { HelpCircle, ChevronDown, ChevronRight, Scale, AlertTriangle, Shield } from 'lucide-react';

interface WhyFlaggedProps {
  result: AnalysisResponse;
}

function ScoreBar({ label, value, maxLabel }: { label: string; value: number; maxLabel?: string }) {
  const pct = Math.min(100, Math.max(0, value * 100));
  const color = pct > 70 ? 'bg-red-500' : pct > 40 ? 'bg-amber-500' : 'bg-emerald-500';
  return (
    <div className="flex items-center gap-2">
      <span className="w-28 text-xs text-zinc-500">{label}</span>
      <div className="h-2 flex-1 overflow-hidden rounded-full bg-zinc-200 dark:bg-zinc-700">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="w-10 text-right text-xs text-zinc-400">{pct.toFixed(0)}%</span>
      {maxLabel && <span className="text-[10px] text-zinc-400">({maxLabel})</span>}
    </div>
  );
}

export function WhyFlagged({ result }: WhyFlaggedProps) {
  const [expanded, setExpanded] = useState(true);

  const flags = useMemo(() => {
    const items: { icon: React.ReactNode; label: string; detail: string; severity: string }[] = [];

    if (result.risk_level === 'critical' || result.risk_level === 'high') {
      items.push({
        icon: <AlertTriangle className="h-4 w-4 text-red-500" />,
        label: 'High Risk Level',
        detail: `Overall risk assessment: ${result.risk_level.toUpperCase()}. Immediate attention recommended.`,
        severity: 'high',
      });
    }

    if (result.decision_score !== undefined && result.decision_score > 0.5) {
      items.push({
        icon: <Scale className="h-4 w-4 text-amber-500" />,
        label: 'Decision Score',
        detail: `Decision score of ${(result.decision_score * 100).toFixed(0)}% indicates ${result.review_required ? 'manual review may be needed' : 'automated decision possible'}. ${result.decision_reasoning}`,
        severity: result.decision_score > 0.7 ? 'high' : 'medium',
      });
    }

    Object.entries(result.risk_breakdown ?? {}).forEach(([key, value]) => {
      if (value > 0.3) {
        items.push({
          icon: <Shield className="h-4 w-4 text-amber-500" />,
          label: key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase()),
          detail: `Risk contribution: ${(value * 100).toFixed(0)}%`,
          severity: value > 0.6 ? 'high' : 'medium',
        });
      }
    });

    if (result.reasons.length > 0) {
      result.reasons.forEach((reason) => {
        items.push({
          icon: <HelpCircle className="h-4 w-4 text-blue-500" />,
          label: 'Analysis Reason',
          detail: reason,
          severity: 'info',
        });
      });
    }

    if (result.detected_indicators.length > 0) {
      items.push({
        icon: <AlertTriangle className="h-4 w-4 text-orange-500" />,
        label: `Detected Indicators (${result.detected_indicators.length})`,
        detail: result.detected_indicators.join(', '),
        severity: 'medium',
      });
    }

    if (result.manual_review_reason) {
      items.push({
        icon: <AlertTriangle className="h-4 w-4 text-red-500" />,
        label: 'Manual Review Required',
        detail: result.manual_review_reason,
        severity: 'high',
      });
    }

    return items;
  }, [result]);

  return (
    <Card>
      <CardHeader className="pb-3">
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex w-full items-center justify-between"
          aria-expanded={expanded}
        >
          <div className="flex items-center gap-2">
            <HelpCircle className="h-4 w-4 text-emerald-500" />
            <CardTitle className="text-sm">Why was this flagged?</CardTitle>
            <Badge variant="secondary" className="text-[9px]">{flags.length} factors</Badge>
          </div>
          {expanded ? <ChevronDown className="h-4 w-4 text-zinc-400" /> : <ChevronRight className="h-4 w-4 text-zinc-400" />}
        </button>
      </CardHeader>
      {expanded && (
        <CardContent className="space-y-4 pt-0">
          {/* Key scores */}
          <div className="space-y-1.5">
            <ScoreBar label="Overall Confidence" value={result.confidence} maxLabel={result.prediction} />
            <ScoreBar label="Decision Score" value={result.decision_score} maxLabel={result.decision_level} />
            <ScoreBar label="Assessment Score" value={result.assessment_score} maxLabel={result.assessment_band} />
          </div>

          {/* Flag factors */}
          {flags.length > 0 && (
            <div className="space-y-1.5">
              {flags.map((flag, i) => (
                <div
                  key={i}
                  className={`rounded-lg border p-3 text-sm ${
                    flag.severity === 'high'
                      ? 'border-red-200 bg-red-50/50 dark:border-red-800 dark:bg-red-900/10'
                      : flag.severity === 'medium'
                        ? 'border-amber-200 bg-amber-50/50 dark:border-amber-800 dark:bg-amber-900/10'
                        : 'border-blue-200 bg-blue-50/50 dark:border-blue-800 dark:bg-blue-900/10'
                  }`}
                >
                  <div className="flex items-start gap-2">
                    {flag.icon}
                    <div>
                      <p className="font-medium text-zinc-800 dark:text-zinc-200">{flag.label}</p>
                      <p className="mt-0.5 text-xs text-zinc-600 dark:text-zinc-400">{flag.detail}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      )}
    </Card>
  );
}
