import { memo } from 'react';
import { TIMELINE_EVENT_LABELS, TIMELINE_EVENT_COLORS, type TimelineEvent as TEvent } from '@/features/timeline/types';

interface TimelineEventProps {
  event: TEvent;
  isSelected: boolean;
  isDimmed: boolean;
  onClick: (id: string) => void;
  onHover: (id: string | null) => void;
}

export const TimelineEventRow = memo(function TimelineEventRow({
  event,
  isSelected,
  isDimmed,
  onClick,
  onHover,
}: TimelineEventProps) {
  const color = TIMELINE_EVENT_COLORS[event.type];
  const time = new Date(event.timestamp).toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });

  return (
    <div
      className={`group relative flex cursor-pointer items-start gap-4 rounded-lg p-3 transition-all ${
        isSelected
          ? 'bg-zinc-100 ring-1 ring-zinc-300 dark:bg-zinc-800 dark:ring-zinc-600'
          : 'hover:bg-zinc-50 dark:hover:bg-zinc-800/50'
      }`}
      style={{ opacity: isDimmed ? 0.3 : 1 }}
      onClick={() => onClick(event.id)}
      onMouseEnter={() => onHover(event.id)}
      onMouseLeave={() => onHover(null)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => { if (e.key === 'Enter') onClick(event.id); }}
      aria-label={`${TIMELINE_EVENT_LABELS[event.type]}: ${event.label}`}
    >
      {/* Timeline dot + line */}
      <div className="flex shrink-0 flex-col items-center pt-1.5">
        <div
          className="h-3 w-3 rounded-full ring-2 ring-white dark:ring-zinc-900"
          style={{ backgroundColor: color }}
        />
      </div>

      {/* Time */}
      <div className="w-20 shrink-0 pt-0.5 text-right">
        <span className="text-[11px] font-mono text-zinc-400">{time}</span>
      </div>

      {/* Content */}
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className="truncate text-sm font-medium text-zinc-900 dark:text-zinc-100">
            {event.label}
          </span>
          <span className="shrink-0 text-[10px] text-zinc-400">{TIMELINE_EVENT_LABELS[event.type]}</span>
        </div>
        <p className="mt-0.5 line-clamp-2 text-xs text-zinc-500 dark:text-zinc-400">
          {event.description}
        </p>

        {/* Metadata chips */}
        <div className="mt-1.5 flex flex-wrap gap-1.5">
          {event.confidence !== undefined && (
            <span className="rounded bg-zinc-100 px-1.5 py-0.5 text-[10px] text-zinc-500 dark:bg-zinc-700 dark:text-zinc-400">
              conf: {(event.confidence * 100).toFixed(0)}%
            </span>
          )}
          {event.severity && (
            <span className={`rounded px-1.5 py-0.5 text-[10px] font-medium ${
              event.severity === 'critical' || event.severity === 'high'
                ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                : event.severity === 'medium'
                  ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400'
                  : 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
            }`}>
              {event.severity}
            </span>
          )}
          {event.source && (
            <span className="rounded bg-zinc-100 px-1.5 py-0.5 text-[10px] text-zinc-500 dark:bg-zinc-700 dark:text-zinc-400">
              {event.source}
            </span>
          )}
        </div>
      </div>
    </div>
  );
});

export function TimelineDot({ color, isCluster = false }: { color: string; isCluster?: boolean }) {
  return (
    <div className="flex shrink-0 flex-col items-center">
      <div
        className={`${isCluster ? 'h-4 w-4' : 'h-3 w-3'} rounded-full ring-2 ring-white dark:ring-zinc-900`}
        style={{ backgroundColor: color }}
      />
    </div>
  );
}
