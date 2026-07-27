import { useCallback, useState } from 'react';
import { LeftPanel } from '@/features/investigation/components/left-panel';
import { CenterPanel } from '@/features/investigation/components/center-panel';
import { RightPanel } from '@/features/investigation/components/right-panel';
import { useWorkspaceState } from '@/features/investigation/hooks/use-workspace-state';
import type { AnalysisResponse } from '@/types';
import type { TimelineEvent } from '@/features/timeline/types';
import type { StoredAnalysis } from '@/features/analysis/types';
import type { PanelId } from '@/features/investigation/types';
import { PanelLeftClose, PanelRightClose, PanelLeftOpen, PanelRightOpen } from 'lucide-react';

interface WorkspaceLayoutProps {
  current: StoredAnalysis | null;
  history: StoredAnalysis[];
  result: AnalysisResponse | null;
  events: TimelineEvent[];
  loading?: boolean;
  onSelectHistory: (id: string) => void;
  onClearCurrent: () => void;
  fullGraphView?: React.ReactNode;
  fullTimelineView?: React.ReactNode;
  fullReportView?: React.ReactNode;
}

export function WorkspaceLayout({
  current,
  history,
  result,
  events,
  loading,
  onSelectHistory,
  onClearCurrent,
  fullGraphView,
  fullTimelineView,
  fullReportView,
}: WorkspaceLayoutProps) {
  const { state, toggleLeftPanel, toggleRightPanel, setCenterPanel } = useWorkspaceState();
  const [resizing, setResizing] = useState<'left' | 'right' | null>(null);
  const [leftWidth, setLeftWidth] = useState(260);
  const [rightWidth, setRightWidth] = useState(300);

  const handleCenterPanel = useCallback((id: PanelId) => {
    setCenterPanel(id);
  }, [setCenterPanel]);

  const handleResizeStart = useCallback((side: 'left' | 'right') => (e: React.MouseEvent) => {
    e.preventDefault();
    setResizing(side);
    const startX = e.clientX;
    const startWidth = side === 'left' ? leftWidth : rightWidth;

    const handleMouseMove = (ev: MouseEvent) => {
      const delta = ev.clientX - startX;
      const newWidth = Math.max(200, Math.min(450, side === 'left' ? startWidth + delta : startWidth - delta));
      if (side === 'left') setLeftWidth(newWidth);
      else setRightWidth(newWidth);
    };

    const handleMouseUp = () => {
      setResizing(null);
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  }, [leftWidth, rightWidth]);

  const fullView = state.centerPanelId === 'graph' ? fullGraphView
    : state.centerPanelId === 'timeline' ? fullTimelineView
    : state.centerPanelId === 'report' ? fullReportView
    : null;

  return (
    <div className="flex h-full min-h-0 flex-1" role="main" aria-label="Investigation workspace">
      {state.leftPanelOpen && (
        <>
          <div
            className="shrink-0 overflow-hidden border-r border-zinc-200 bg-white dark:border-zinc-700 dark:bg-zinc-900"
            style={{ width: leftWidth }}
          >
            <LeftPanel
              currentId={current?.id ?? null}
              history={history}
              onSelectHistory={onSelectHistory}
              onClearCurrent={onClearCurrent}
            />
          </div>
          <div
            className={`w-1 shrink-0 cursor-col-resize transition-colors hover:bg-emerald-400 ${resizing === 'left' ? 'bg-emerald-400' : 'bg-transparent'}`}
            onMouseDown={handleResizeStart('left')}
            role="separator"
            tabIndex={0}
            aria-label="Resize left panel"
          />
        </>
      )}

      <div className="flex min-w-0 flex-1 flex-col">
        <div className="flex shrink-0 items-center justify-between border-b border-zinc-200 bg-white px-2 py-1 dark:border-zinc-700 dark:bg-zinc-900">
          <button
            onClick={toggleLeftPanel}
            className="flex items-center gap-1 rounded px-2 py-1 text-xs text-zinc-500 hover:bg-zinc-100 hover:text-zinc-700 dark:hover:bg-zinc-800 dark:hover:text-zinc-300"
            aria-label={state.leftPanelOpen ? 'Close sidebar' : 'Open sidebar'}
          >
            {state.leftPanelOpen ? <PanelLeftClose className="h-3.5 w-3.5" /> : <PanelLeftOpen className="h-3.5 w-3.5" />}
          </button>
          <button
            onClick={toggleRightPanel}
            className="flex items-center gap-1 rounded px-2 py-1 text-xs text-zinc-500 hover:bg-zinc-100 hover:text-zinc-700 dark:hover:bg-zinc-800 dark:hover:text-zinc-300"
            aria-label={state.rightPanelOpen ? 'Close details' : 'Open details'}
          >
            {state.rightPanelOpen ? <PanelRightClose className="h-3.5 w-3.5" /> : <PanelRightOpen className="h-3.5 w-3.5" />}
          </button>
        </div>
        <div className="flex min-h-0 flex-1">
          <CenterPanel
            panelId={state.centerPanelId}
            result={result}
            events={events}
            loading={loading}
            onNavigate={handleCenterPanel}
          >
            {fullView}
          </CenterPanel>
        </div>
      </div>

      {state.rightPanelOpen && (
        <>
          <div
            className={`w-1 shrink-0 cursor-col-resize transition-colors hover:bg-emerald-400 ${resizing === 'right' ? 'bg-emerald-400' : 'bg-transparent'}`}
            onMouseDown={handleResizeStart('right')}
            role="separator"
            tabIndex={0}
            aria-label="Resize right panel"
          />
          <div
            className="shrink-0 overflow-hidden border-l border-zinc-200 bg-white dark:border-zinc-700 dark:bg-zinc-900"
            style={{ width: rightWidth }}
          >
            <RightPanel result={result} />
          </div>
        </>
      )}
    </div>
  );
}
