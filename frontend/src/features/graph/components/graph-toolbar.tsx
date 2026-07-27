import { useState, useCallback } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { useGraph } from '@/features/graph/components/graph-context';
import { NODE_TYPE_LABELS, EDGE_TYPE_LABELS, type NodeType, type EdgeType } from '@/features/graph/types';
import { exportSVG, exportPNG } from '@/features/graph/utils/export';
import {
  Search,
  ZoomIn,
  ZoomOut,
  Maximize2,
  RotateCcw,
  Download,
  Image,
  Filter,
  X,
} from 'lucide-react';

export function GraphToolbar() {
  const {
    zoomBy,
    fitToScreen,
    resetView,
    setSearchQuery,
    filters,
    toggleNodeType,
    toggleEdgeType,
    svgRef,
    filteredData,
    data,
  } = useGraph();

  const [showFilters, setShowFilters] = useState(false);
  const [showExport, setShowExport] = useState(false);

  const handleSearch = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => setSearchQuery(e.target.value),
    [setSearchQuery]
  );

  const handleExportPNG = useCallback(async () => {
    if (svgRef.current) {
      try {
        await exportPNG(svgRef.current);
      } catch {
        // silently fail
      }
    }
  }, [svgRef]);

  const handleExportSVG = useCallback(() => {
    if (svgRef.current) {
      exportSVG(svgRef.current);
    }
  }, [svgRef]);

  const hasActiveFilters = filters.nodeTypes.length > 0 || filters.edgeTypes.length > 0 || filters.searchQuery.length > 0;

  return (
    <Card className="w-full">
      <CardContent className="flex flex-wrap items-center gap-2 p-3">
        <div className="relative min-w-[160px] flex-1">
          <Search className="pointer-events-none absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-400" />
          <Input
            placeholder="Search nodes..."
            value={filters.searchQuery}
            onChange={handleSearch}
            className="h-9 pl-8 text-sm"
            aria-label="Search graph nodes"
          />
          {filters.searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-zinc-600"
              aria-label="Clear search"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          )}
        </div>

        <div className="flex items-center gap-1">
          <Button variant="ghost" size="icon" className="h-9 w-9" onClick={() => zoomBy(1.2)} aria-label="Zoom in">
            <ZoomIn className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="icon" className="h-9 w-9" onClick={() => zoomBy(0.8)} aria-label="Zoom out">
            <ZoomOut className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="icon" className="h-9 w-9" onClick={fitToScreen} aria-label="Fit to screen">
            <Maximize2 className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="icon" className="h-9 w-9" onClick={resetView} aria-label="Reset view">
            <RotateCcw className="h-4 w-4" />
          </Button>
        </div>

        <div className="relative">
          <Button
            variant={showExport ? 'secondary' : 'ghost'}
            size="sm"
            className="h-9"
            onClick={() => { setShowExport(!showExport); setShowFilters(false); }}
            aria-label="Export graph"
          >
            <Download className="mr-1.5 h-4 w-4" />
            Export
          </Button>
          {showExport && (
            <Card className="absolute right-0 top-full z-50 mt-1 w-40 shadow-lg">
              <CardContent className="flex flex-col gap-1 p-2">
                <Button variant="ghost" size="sm" onClick={handleExportPNG} className="justify-start">
                  <Image className="mr-2 h-4 w-4" />
                  Export PNG
                </Button>
                <Button variant="ghost" size="sm" onClick={handleExportSVG} className="justify-start">
                  <Image className="mr-2 h-4 w-4" />
                  Export SVG
                </Button>
              </CardContent>
            </Card>
          )}
        </div>

        <div className="relative">
          <Button
            variant={hasActiveFilters ? 'secondary' : 'ghost'}
            size="sm"
            className="h-9"
            onClick={() => { setShowFilters(!showFilters); setShowExport(false); }}
            aria-label="Toggle filters"
          >
            <Filter className="mr-1.5 h-4 w-4" />
            Filters
            {filteredData.nodes.length < data.nodes.length && (
              <span className="ml-1 rounded-full bg-emerald-600 px-1.5 py-0.5 text-[10px] text-white">
                {filters.nodeTypes.length + filters.edgeTypes.length}
              </span>
            )}
          </Button>
          {showFilters && (
            <Card className="absolute right-0 top-full z-50 mt-1 w-56 shadow-lg">
              <CardContent className="space-y-3 p-3">
                <div>
                  <p className="mb-1.5 text-xs font-medium text-zinc-500">Node Types</p>
                  <div className="flex flex-wrap gap-1">
                    {(Object.keys(NODE_TYPE_LABELS) as NodeType[]).map((type) => {
                      const active = filters.nodeTypes.includes(type);
                      return (
                        <button
                          key={type}
                          onClick={() => toggleNodeType(type)}
                          className={`rounded-full px-2 py-0.5 text-[11px] font-medium transition-colors ${
                            active
                              ? 'bg-emerald-600 text-white'
                              : 'bg-zinc-100 text-zinc-600 hover:bg-zinc-200 dark:bg-zinc-800 dark:text-zinc-400 dark:hover:bg-zinc-700'
                          }`}
                        >
                          {NODE_TYPE_LABELS[type]}
                        </button>
                      );
                    })}
                  </div>
                </div>
                <div>
                  <p className="mb-1.5 text-xs font-medium text-zinc-500">Edge Types</p>
                  <div className="flex flex-wrap gap-1">
                    {(Object.keys(EDGE_TYPE_LABELS) as EdgeType[]).map((type) => {
                      const active = filters.edgeTypes.includes(type);
                      return (
                        <button
                          key={type}
                          onClick={() => toggleEdgeType(type)}
                          className={`rounded-full px-2 py-0.5 text-[11px] font-medium transition-colors ${
                            active
                              ? 'bg-emerald-600 text-white'
                              : 'bg-zinc-100 text-zinc-600 hover:bg-zinc-200 dark:bg-zinc-800 dark:text-zinc-400 dark:hover:bg-zinc-700'
                          }`}
                        >
                          {EDGE_TYPE_LABELS[type]}
                        </button>
                      );
                    })}
                  </div>
                </div>
                {hasActiveFilters && (
                  <button
                    onClick={() => {
                      setSearchQuery('');
                    }}
                    className="w-full rounded px-2 py-1 text-xs text-zinc-500 hover:bg-zinc-100 dark:hover:bg-zinc-800"
                  >
                    Clear all filters
                  </button>
                )}
              </CardContent>
            </Card>
          )}
        </div>

        <div className="hidden text-xs text-zinc-400 md:block">
          {filteredData.nodes.length} nodes &middot; {filteredData.edges.length} edges
        </div>
      </CardContent>
    </Card>
  );
}


