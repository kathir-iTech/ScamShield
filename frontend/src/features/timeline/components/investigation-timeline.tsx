import { useState, useMemo, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { TimelineControls } from '@/features/timeline/components/timeline-controls';
import { TimelineEventRow } from '@/features/timeline/components/timeline-event';
import { EventDetailPanel } from '@/features/timeline/components/event-detail-panel';
import type { TimelineEvent, TimelineEventType, TimelineViewState } from '@/features/timeline/types';

const ALL_EVENT_TYPES: TimelineEventType[] = [
  'analysis_created',
  'evidence_supporting',
  'evidence_conflicting',
  'entity_identified',
  'threat_detected',
  'indicator_extracted',
  'connector_lookup',
  'knowledge_match',
  'fusion_result',
  'scam_classification',
  'assessment',
  'campaign_event',
];

interface InvestigationTimelineProps {
  events: TimelineEvent[];
  onSearchChange?: (query: string) => void;
}

export function InvestigationTimeline({ events, onSearchChange: _onSearchChange }: InvestigationTimelineProps) {
  const [viewState, setViewState] = useState<TimelineViewState>({
    zoomLevel: 1,
    searchQuery: '',
    activeTypes: [],
    selectedEventId: null,
    clusterThreshold: 60_000,
  });

  const [showFilters, setShowFilters] = useState(false);

  const setSearchQuery = useCallback((q: string) => {
    setViewState((prev) => ({ ...prev, searchQuery: q }));
    _onSearchChange?.(q);
  }, [_onSearchChange]);

  const setSelectedEventId = useCallback((id: string | null) => {
    setViewState((prev) => ({ ...prev, selectedEventId: id }));
  }, []);

  const toggleType = useCallback((type: TimelineEventType) => {
    setViewState((prev) => {
      const current = prev.activeTypes.length === 0 ? [...ALL_EVENT_TYPES] : prev.activeTypes;
      const exists = current.includes(type);
      const next = exists ? current.filter((t) => t !== type) : [...current, type];
      return { ...prev, activeTypes: next.length === ALL_EVENT_TYPES.length ? [] : next };
    });
  }, []);

  const zoomIn = useCallback(() => {
    setViewState((prev) => ({
      ...prev,
      zoomLevel: Math.min(10, prev.zoomLevel * 1.5),
      clusterThreshold: Math.max(5_000, prev.clusterThreshold / 1.5),
    }));
  }, []);

  const zoomOut = useCallback(() => {
    setViewState((prev) => ({
      ...prev,
      zoomLevel: Math.max(0.1, prev.zoomLevel / 1.5),
      clusterThreshold: Math.min(600_000, prev.clusterThreshold * 1.5),
    }));
  }, []);

  const selectEvent = useCallback((id: string) => {
    setViewState((prev) => ({ ...prev, selectedEventId: prev.selectedEventId === id ? null : id }));
  }, []);

  const filteredEvents = useMemo(() => {
    let result = events;

    if (viewState.activeTypes.length > 0) {
      result = result.filter((e) => viewState.activeTypes.includes(e.type));
    }

    if (viewState.searchQuery) {
      const q = viewState.searchQuery.toLowerCase();
      result = result.filter(
        (e) =>
          e.label.toLowerCase().includes(q) ||
          e.description.toLowerCase().includes(q) ||
          (e.source && e.source.toLowerCase().includes(q))
      );
    }

    return result;
  }, [events, viewState.activeTypes, viewState.searchQuery]);

  const clusteredEvents = useMemo(() => {
    if (filteredEvents.length === 0) return [];
    const threshold = viewState.clusterThreshold;
    const clusters: { events: TimelineEvent[] }[] = [];
    let currentCluster: TimelineEvent[] = [filteredEvents[0]];

    for (let i = 1; i < filteredEvents.length; i++) {
      const prev = filteredEvents[i - 1];
      const curr = filteredEvents[i];
      if (curr.timestamp - prev.timestamp < threshold) {
        currentCluster.push(curr);
      } else {
        clusters.push({ events: currentCluster });
        currentCluster = [curr];
      }
    }
    clusters.push({ events: currentCluster });
    return clusters;
  }, [filteredEvents, viewState.clusterThreshold]);

  const selectedEvent = useMemo(
    () => events.find((e) => e.id === viewState.selectedEventId) ?? null,
    [events, viewState.selectedEventId]
  );

  const controlsProps = {
    searchQuery: viewState.searchQuery,
    onSearchChange: setSearchQuery,
    zoomLevel: viewState.zoomLevel,
    onZoomIn: zoomIn,
    onZoomOut: zoomOut,
    activeTypes: viewState.activeTypes,
    allTypes: ALL_EVENT_TYPES,
    onToggleType: toggleType,
    showFilters,
    onToggleFilters: () => setShowFilters((p) => !p),
  };

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
      {/* Timeline list */}
      <div className="flex flex-col gap-4 lg:col-span-2">
        <TimelineControls {...controlsProps} />

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">
              Event Timeline
              <span className="ml-2 text-xs font-normal text-zinc-400">
                {filteredEvents.length} events
                {viewState.clusterThreshold > 30_000 && (
                  <span className="ml-1">· {clusteredEvents.length} clusters</span>
                )}
              </span>
            </CardTitle>
          </CardHeader>
          <CardContent className="max-h-[600px] overflow-y-auto pt-0">
            {clusteredEvents.length === 0 ? (
              <p className="py-8 text-center text-sm text-zinc-500">
                {viewState.searchQuery ? 'No events match your search.' : 'No timeline events available.'}
              </p>
            ) : (
              <div className="relative space-y-1">
                {/* Timeline vertical line */}
                <div className="pointer-events-none absolute left-[22px] top-0 h-full w-px bg-zinc-200 dark:bg-zinc-700" />

                {clusteredEvents.map((cluster, ci) => {
                  if (cluster.events.length === 1) {
                    const ev = cluster.events[0];
                    return (
                      <TimelineEventRow
                        key={ev.id}
                        event={ev}
                        isSelected={viewState.selectedEventId === ev.id}
                        isDimmed={!!viewState.selectedEventId && viewState.selectedEventId !== ev.id}
                        onClick={selectEvent}
                        onHover={() => {}}
                      />
                    );
                  }

                  // Cluster view
                  return (
                    <div key={`cluster_${ci}`} className="space-y-0.5">
                      <div className="flex items-center gap-3 px-3 py-1">
                        <div className="flex shrink-0 items-center justify-center">
                          <div className="flex h-5 w-5 items-center justify-center rounded-full bg-zinc-200 text-[10px] font-medium text-zinc-600 dark:bg-zinc-700 dark:text-zinc-300">
                            {cluster.events.length}
                          </div>
                        </div>
                        <div className="h-px flex-1 bg-zinc-200 dark:bg-zinc-700" />
                        <span className="text-[10px] text-zinc-400">
                          {new Date(cluster.events[0].timestamp).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}
                          {' — '}
                          {new Date(cluster.events[cluster.events.length - 1].timestamp).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}
                        </span>
                      </div>
                      {cluster.events.map((ev) => (
                        <TimelineEventRow
                          key={ev.id}
                          event={ev}
                          isSelected={viewState.selectedEventId === ev.id}
                          isDimmed={!!viewState.selectedEventId && viewState.selectedEventId !== ev.id}
                          onClick={selectEvent}
                          onHover={() => {}}
                        />
                      ))}
                    </div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Event detail panel */}
      <div className="lg:sticky lg:top-6 lg:self-start">
        <EventDetailPanel
          event={selectedEvent}
          allEvents={events}
          onClose={() => setSelectedEventId(null)}
          onSelectEvent={selectEvent}
        />
      </div>
    </div>
  );
}
