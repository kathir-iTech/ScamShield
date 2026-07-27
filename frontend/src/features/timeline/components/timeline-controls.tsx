import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { TIMELINE_EVENT_LABELS, type TimelineEventType } from '@/features/timeline/types';
import { Search, ZoomIn, ZoomOut, Filter, X } from 'lucide-react';

interface TimelineControlsProps {
  searchQuery: string;
  onSearchChange: (q: string) => void;
  zoomLevel: number;
  onZoomIn: () => void;
  onZoomOut: () => void;
  activeTypes: TimelineEventType[];
  allTypes: TimelineEventType[];
  onToggleType: (t: TimelineEventType) => void;
  showFilters: boolean;
  onToggleFilters: () => void;
}

export function TimelineControls({
  searchQuery,
  onSearchChange,
  zoomLevel,
  onZoomIn,
  onZoomOut,
  activeTypes,
  allTypes,
  onToggleType,
  showFilters,
  onToggleFilters,
}: TimelineControlsProps) {
  const hasFilters = activeTypes.length > 0 && activeTypes.length < allTypes.length;

  return (
    <Card>
      <CardContent className="flex flex-wrap items-center gap-2 p-3">
        <div className="relative min-w-[160px] flex-1">
          <Search className="pointer-events-none absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-400" />
          <Input
            placeholder="Search timeline..."
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            className="h-9 pl-8 text-sm"
            aria-label="Search timeline events"
          />
          {searchQuery && (
            <button
              onClick={() => onSearchChange('')}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-zinc-600"
              aria-label="Clear search"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          )}
        </div>

        <div className="flex items-center gap-1">
          <Button variant="ghost" size="icon" className="h-9 w-9" onClick={onZoomIn} aria-label="Zoom in timeline">
            <ZoomIn className="h-4 w-4" />
          </Button>
          <span className="min-w-[3ch] text-center text-xs text-zinc-400">{zoomLevel}x</span>
          <Button variant="ghost" size="icon" className="h-9 w-9" onClick={onZoomOut} aria-label="Zoom out timeline">
            <ZoomOut className="h-4 w-4" />
          </Button>
        </div>

        <div className="relative">
          <Button
            variant={hasFilters || showFilters ? 'secondary' : 'ghost'}
            size="sm"
            className="h-9"
            onClick={onToggleFilters}
            aria-label="Toggle event type filters"
          >
            <Filter className="mr-1.5 h-4 w-4" />
            Filters
            {hasFilters && (
              <span className="ml-1 rounded-full bg-emerald-600 px-1.5 py-0.5 text-[10px] text-white">
                {allTypes.length - activeTypes.length}
              </span>
            )}
          </Button>
        </div>

        <span className="hidden text-xs text-zinc-400 md:block">
          {allTypes.length} event types
        </span>
      </CardContent>

      {showFilters && (
        <div className="border-t border-zinc-200 px-3 pb-3 pt-2 dark:border-zinc-700">
          <div className="flex flex-wrap gap-1.5">
            {allTypes.map((type) => {
              const active = activeTypes.length === 0 || activeTypes.includes(type);
              return (
                <button
                  key={type}
                  onClick={() => onToggleType(type)}
                  className={`rounded-full px-2.5 py-0.5 text-[11px] font-medium transition-colors ${
                    active
                      ? 'bg-zinc-800 text-zinc-100 dark:bg-zinc-100 dark:text-zinc-800'
                      : 'bg-zinc-100 text-zinc-500 hover:bg-zinc-200 dark:bg-zinc-800 dark:text-zinc-400 dark:hover:bg-zinc-700'
                  }`}
                >
                  {TIMELINE_EVENT_LABELS[type]}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </Card>
  );
}
