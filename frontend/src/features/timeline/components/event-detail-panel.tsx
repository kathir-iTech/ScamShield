import { useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { TIMELINE_EVENT_LABELS, TIMELINE_EVENT_COLORS, type TimelineEvent } from '@/features/timeline/types';
import { X, ExternalLink, Clock } from 'lucide-react';

interface EventDetailPanelProps {
  event: TimelineEvent | null;
  allEvents: TimelineEvent[];
  onClose: () => void;
  onSelectEvent: (id: string) => void;
}

export function EventDetailPanel({ event, allEvents, onClose, onSelectEvent }: EventDetailPanelProps) {
  const relatedEvents = useMemo(() => {
    if (!event) return [];
    return allEvents
      .filter((e) => e.id !== event.id && e.type === event.type)
      .slice(0, 5);
  }, [event, allEvents]);

  if (!event) {
    return (
      <Card className="h-full">
        <CardContent className="flex h-full items-center justify-center p-6">
          <p className="text-center text-sm text-zinc-500 dark:text-zinc-400">
            Select a timeline event to view details
          </p>
        </CardContent>
      </Card>
    );
  }

  const color = TIMELINE_EVENT_COLORS[event.type];
  const time = new Date(event.timestamp).toLocaleString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    month: 'short',
    day: 'numeric',
  });

  return (
    <Card className="h-full overflow-auto">
      <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-3">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className="h-2.5 w-2.5 shrink-0 rounded-full" style={{ backgroundColor: color }} />
            <CardTitle className="truncate text-sm">{event.label}</CardTitle>
          </div>
          <div className="mt-1 flex items-center gap-2">
            <Badge variant="outline" className="text-[10px]">
              {TIMELINE_EVENT_LABELS[event.type]}
            </Badge>
            <span className="flex items-center gap-1 text-[10px] text-zinc-400">
              <Clock className="h-3 w-3" />
              {time}
            </span>
          </div>
        </div>
        <Button variant="ghost" size="icon" className="h-8 w-8 shrink-0" onClick={onClose} aria-label="Close details">
          <X className="h-4 w-4" />
        </Button>
      </CardHeader>

      <CardContent className="space-y-4 pt-0">
        {/* Description */}
        <div>
          <p className="mb-1 text-xs font-medium text-zinc-500 dark:text-zinc-400">Description</p>
          <p className="text-sm text-zinc-800 dark:text-zinc-200">{event.description}</p>
        </div>

        {/* Confidence */}
        {event.confidence !== undefined && (
          <div>
            <p className="mb-1 text-xs font-medium text-zinc-500 dark:text-zinc-400">Confidence</p>
            <div className="flex items-center gap-2">
              <div className="h-2 flex-1 overflow-hidden rounded-full bg-zinc-200 dark:bg-zinc-700">
                <div className="h-full rounded-full bg-emerald-500" style={{ width: `${(event.confidence * 100).toFixed(0)}%` }} />
              </div>
              <span className="text-xs text-zinc-600 dark:text-zinc-400">{(event.confidence * 100).toFixed(0)}%</span>
            </div>
          </div>
        )}

        {/* Risk/Severity */}
        {(event.severity || event.risk) && (
          <div>
            <p className="mb-1 text-xs font-medium text-zinc-500 dark:text-zinc-400">Risk Level</p>
            <Badge
              variant={
                (event.severity ?? event.risk) === 'critical' || (event.severity ?? event.risk) === 'high'
                  ? 'destructive'
                  : (event.severity ?? event.risk) === 'medium'
                    ? 'warning'
                    : 'info'
              }
            >
              {(event.severity ?? event.risk)?.toUpperCase()}
            </Badge>
          </div>
        )}

        {/* Source */}
        {event.source && (
          <div>
            <p className="mb-1 text-xs font-medium text-zinc-500 dark:text-zinc-400">Source</p>
            <p className="text-sm text-zinc-800 dark:text-zinc-200">{event.source}</p>
          </div>
        )}

        {/* Metadata */}
        {event.metadata && Object.keys(event.metadata).length > 0 && (
          <div>
            <p className="mb-1 text-xs font-medium text-zinc-500 dark:text-zinc-400">Metadata</p>
            <div className="space-y-1 rounded-lg bg-zinc-50 p-2 dark:bg-zinc-800">
              {Object.entries(event.metadata).map(([key, value]) => (
                <div key={key} className="flex justify-between gap-2 text-xs">
                  <span className="text-zinc-500 dark:text-zinc-400">{key}</span>
                  <span className="max-w-[180px] truncate text-right text-zinc-700 dark:text-zinc-300">
                    {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Related events */}
        {relatedEvents.length > 0 && (
          <div>
            <p className="mb-1.5 text-xs font-medium text-zinc-500 dark:text-zinc-400">
              Related Events ({relatedEvents.length})
            </p>
            <div className="space-y-1">
              {relatedEvents.map((re) => (
                <button
                  key={re.id}
                  onClick={() => onSelectEvent(re.id)}
                  className="flex w-full items-center gap-2 rounded-lg bg-zinc-50 px-2.5 py-2 text-left text-xs hover:bg-zinc-100 dark:bg-zinc-800 dark:hover:bg-zinc-700"
                >
                  <span className="h-2 w-2 shrink-0 rounded-full" style={{ backgroundColor: TIMELINE_EVENT_COLORS[re.type] }} />
                  <span className="flex-1 truncate text-zinc-700 dark:text-zinc-300">{re.label}</span>
                  <span className="shrink-0 text-zinc-400">
                    {new Date(re.timestamp).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </button>
              ))}
            </div>
          </div>
        )}

        <Button variant="ghost" size="sm" className="w-full text-xs" onClick={onClose}>
          <ExternalLink className="mr-1.5 h-3 w-3" />
          Close details
        </Button>
      </CardContent>
    </Card>
  );
}
