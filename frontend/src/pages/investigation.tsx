import { useState, useMemo, useCallback, lazy, Suspense } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCurrentAnalysis, useAnalysis } from '@/features/analysis/context/analysis-context';
import { WorkspaceLayout } from '@/features/investigation';
import { transformAnalysisToGraph } from '@/features/graph';
import { transformToTimelineEvents, generateCampaigns } from '@/features/timeline';
import { DemoPanel, DemoWalkthrough } from '@/features/demo';
import { GraphSkeleton, TimelineSkeleton, ReportSkeleton } from '@/features/shared/investigation-skeleton';
import type { AnalysisResponse } from '@/types';
import type { PanelId } from '@/features/investigation/types';
import { PageTransition } from '@/components/ui/page-transition';
import { Button } from '@/components/ui/button';
import { EmptyPanel } from '@/components/ui/empty-panel';
import { ArrowLeft, FlaskConical, Sparkles } from 'lucide-react';

const GraphViewLazy = lazy(() => import('@/features/investigation/components/lazy-graph-view'));
const TimelineViewLazy = lazy(() => import('@/features/investigation/components/lazy-timeline-view'));
const ReportViewLazy = lazy(() => import('@/features/investigation/components/lazy-report-view'));

export default function Investigation() {
  const current = useCurrentAnalysis();
  const { storeAnalysis, clearCurrent, history } = useAnalysis();
  const navigate = useNavigate();
  const [showDemo, setShowDemo] = useState(false);
  const [showWalkthrough, setShowWalkthrough] = useState(false);
  const [walkthroughTab, setWalkthroughTab] = useState<PanelId>('summary');

  const result = useMemo(() => {
    if (!current?.result) return null;
    return current.result as AnalysisResponse;
  }, [current]);

  const graphData = useMemo(() => {
    if (!result) return null;
    return transformAnalysisToGraph(result);
  }, [result]);

  const timelineEvents = useMemo(() => {
    if (!current || !result) return [];
    return transformToTimelineEvents(result, current.timestamp);
  }, [result, current]);

  const campaigns = useMemo(() => {
    if (timelineEvents.length === 0) return [];
    return generateCampaigns(timelineEvents);
  }, [timelineEvents]);

  const handleLoadDemoCase = useCallback((result: AnalysisResponse, title: string) => {
    storeAnalysis(result, false, `[Demo] ${title}`);
  }, [storeAnalysis]);

  const handleSelectHistory = useCallback((_id: string) => {
    // history selection - in a full implementation, this would load the analysis
    // For now, we keep the current analysis
  }, []);

  const handleClearCurrent = useCallback(() => {
    clearCurrent();
  }, [clearCurrent]);

  if (!current && !showDemo) {
    return (
      <PageTransition>
        <div className="mx-auto max-w-6xl">
          <div className="mb-6 flex items-center gap-3">
            <Button variant="ghost" size="icon" onClick={() => navigate('/analyze/text')} aria-label="Go to analysis">
              <ArrowLeft className="h-5 w-5" />
            </Button>
            <h1 className="text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">
              Investigation Workspace
            </h1>
          </div>
          <EmptyPanel
            icon={FlaskConical}
            title="No analysis data"
            description="Run an analysis first or load a demo case to explore the investigation workspace."
            action={
              <div className="flex flex-wrap gap-3">
                <Button onClick={() => navigate('/analyze/text')}>
                  <FlaskConical className="mr-2 h-4 w-4" />
                  Analyze a URL or message
                </Button>
                <Button variant="outline" onClick={() => setShowDemo(true)}>
                  <Sparkles className="mr-2 h-4 w-4" />
                  Browse Demo Cases
                </Button>
              </div>
            }
          />
        </div>
      </PageTransition>
    );
  }

  if (!current && showDemo) {
    return (
      <PageTransition>
        <div className="mx-auto max-w-6xl">
          <div className="mb-6 flex items-center gap-3">
            <Button variant="ghost" size="icon" onClick={() => setShowDemo(false)} aria-label="Back">
              <ArrowLeft className="h-5 w-5" />
            </Button>
            <h1 className="text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">
              Demo Cases
            </h1>
          </div>
          <DemoPanel onLoadCase={handleLoadDemoCase} />
        </div>
      </PageTransition>
    );
  }

  return (
    <PageTransition>
      <div className="flex h-[calc(100vh-4rem)] flex-col">
        <div className="flex shrink-0 items-center justify-between border-b border-zinc-200 bg-white px-4 py-2 dark:border-zinc-700 dark:bg-zinc-900">
          <div className="flex items-center gap-3">
            <Button variant="ghost" size="icon" onClick={() => navigate('/analysis/result')} aria-label="Back to report">
              <ArrowLeft className="h-4 w-4" />
            </Button>
            <h1 className="text-base font-bold tracking-tight text-zinc-900 dark:text-zinc-50">
              Investigation
            </h1>
            {graphData && (
              <span className="text-xs text-zinc-400">
                {graphData.nodes.length} nodes &middot; {graphData.edges.length} edges &middot; {timelineEvents.length} events
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" onClick={() => setShowWalkthrough(true)}>
              <Sparkles className="mr-1.5 h-3.5 w-3.5" />
              Tour
            </Button>
            <Button variant="outline" size="sm" onClick={() => navigate('/analysis/result')}>
              View Report
            </Button>
          </div>
        </div>

        <div className="flex min-h-0 flex-1">
          <WorkspaceLayout
            current={current}
            history={history}
            result={result}
            events={timelineEvents}
            onSelectHistory={handleSelectHistory}
            onClearCurrent={handleClearCurrent}
            fullGraphView={
              graphData && (
                <Suspense fallback={<GraphSkeleton />}>
                  <GraphViewLazy
                    graphData={graphData}
                    width={1200}
                    height={700}
                  />
                </Suspense>
              )
            }
            fullTimelineView={
              <Suspense fallback={<TimelineSkeleton />}>
                <TimelineViewLazy
                  events={timelineEvents}
                  campaigns={campaigns}
                />
              </Suspense>
            }
            fullReportView={
              result && (
                <Suspense fallback={<ReportSkeleton />}>
                  <ReportViewLazy
                    result={result}
                    events={timelineEvents}
                  />
                </Suspense>
              )
            }
          />
        </div>
      </div>

      {showWalkthrough && (
        <DemoWalkthrough
          onClose={() => setShowWalkthrough(false)}
          onNavigateTab={(tab) => {
            const mapped: PanelId = tab === 'campaigns' ? 'timeline' : tab as PanelId;
            setWalkthroughTab(mapped);
          }}
        />
      )}
    </PageTransition>
  );
}
