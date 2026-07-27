import { useMemo } from 'react';
import {
  BarChart3, FileText, Network, ScrollText, AlertCircle, Sparkles, Clock
} from 'lucide-react';
import { SummaryCard } from '@/features/investigation/components/summary-card';
import { EvidenceSection } from '@/features/investigation/components/evidence-section';
import { ReasoningSection } from '@/features/investigation/components/reasoning-section';
import { WhyFlagged } from '@/features/explainability/why-flagged';
import { EntityExplorer } from '@/features/entity-explorer/entity-explorer';
import { ThreatIntelViewer } from '@/features/threat-intel/threat-intel-viewer';
import type { AnalysisResponse } from '@/types';
import type { TimelineEvent } from '@/features/timeline/types';
import type { PanelId } from '@/features/investigation/types';

interface CenterPanelProps {
  panelId: PanelId;
  result: AnalysisResponse | null;
  events: TimelineEvent[];
  loading?: boolean;
  onNavigate: (id: PanelId) => void;
  children?: React.ReactNode;
}

const NAV_ITEMS: { id: PanelId; label: string; icon: React.ReactNode }[] = [
  { id: 'summary', label: 'Summary', icon: <BarChart3 className="h-3.5 w-3.5" /> },
  { id: 'evidence', label: 'Evidence', icon: <ScrollText className="h-3.5 w-3.5" /> },
  { id: 'reasoning', label: 'Reasoning', icon: <AlertCircle className="h-3.5 w-3.5" /> },
  { id: 'graph', label: 'Graph', icon: <Network className="h-3.5 w-3.5" /> },
  { id: 'timeline', label: 'Timeline', icon: <Clock className="h-3.5 w-3.5" /> },
  { id: 'report', label: 'Report', icon: <FileText className="h-3.5 w-3.5" /> },
];

export function CenterPanel({ panelId, result, events: _events, loading, onNavigate, children }: CenterPanelProps) {
  const isCompact = panelId === 'summary' || panelId === 'evidence' || panelId === 'reasoning';

  const compactPanel = useMemo(() => {
    if (loading || !result) {
      return (
        <div className="flex h-full items-center justify-center">
          <div className="flex flex-col items-center gap-3 text-zinc-400">
            <Sparkles className="h-6 w-6 animate-pulse" />
            <p className="text-sm">{loading ? 'Loading...' : 'No analysis data'}</p>
          </div>
        </div>
      );
    }

    switch (panelId) {
      case 'summary':
        return (
          <div className="space-y-4">
            <SummaryCard result={result} />
            <WhyFlagged result={result} />
            <EntityExplorer result={result} />
            <ThreatIntelViewer result={result} />
          </div>
        );
      case 'evidence':
        return <EvidenceSection result={result} />;
      case 'reasoning':
        return <ReasoningSection result={result} />;
      default:
        return <SummaryCard result={result} />;
    }
  }, [panelId, result, loading]);

  return (
    <div className="flex h-full flex-col" role="tabpanel" aria-label={`Panel: ${panelId}`}>
      {result && (
        <>
          <div className="flex items-center gap-4 border-b border-zinc-200 px-3 py-2 dark:border-zinc-700">
            <div className="flex items-center gap-1">
              <span className="text-xs font-medium text-zinc-500">Result:</span>
              <span className="text-xs text-zinc-900 dark:text-zinc-100">{result.prediction}</span>
            </div>
            <div className="flex items-center gap-1">
              <span className="text-xs font-medium text-zinc-500">Risk:</span>
              <span className={`text-xs font-medium ${
                result.risk_level === 'critical' || result.risk_level === 'high'
                  ? 'text-red-500' : result.risk_level === 'medium'
                    ? 'text-amber-500' : 'text-emerald-500'
              }`}>{result.risk_level.toUpperCase()}</span>
            </div>
          </div>

          <nav className="flex gap-1 border-b border-zinc-200 px-3 py-1.5 dark:border-zinc-700" role="tablist" aria-label="Panel tabs">
            {NAV_ITEMS.map((item) => (
              <button
                key={item.id}
                onClick={() => onNavigate(item.id)}
                role="tab"
                aria-selected={panelId === item.id}
                className={`flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs font-medium whitespace-nowrap transition-colors ${
                  panelId === item.id
                    ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300'
                    : 'text-zinc-500 hover:bg-zinc-100 hover:text-zinc-700 dark:hover:bg-zinc-800 dark:hover:text-zinc-300'
                }`}
              >
                {item.icon}
                {item.label}
              </button>
            ))}
          </nav>
        </>
      )}
      <div className="flex-1 overflow-y-auto p-3">
        {isCompact ? compactPanel : children}
      </div>
    </div>
  );
}
