import { useCallback, useRef, useMemo, useState, useEffect } from 'react';
import { useGraph } from '@/features/graph/components/graph-context';
import { GraphNodeComponent } from '@/features/graph/components/graph-node';
import { GraphEdgeComponent } from '@/features/graph/components/graph-edge';
import type { GraphNode } from '@/features/graph/types';

export function EvidenceGraph() {
  const {
    filteredData,
    viewport,
    selection,
    config,
    svgRef,
    containerRef,
    selectNode,
    hoverNode,
    panBy,
    zoomBy,
    fitToScreen,
    resetView,
    nodePositions,
  } = useGraph();

  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const [tooltipNode, setTooltipNode] = useState<GraphNode | null>(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });

  const isDragging = useRef(false);
  const dragStart = useRef({ x: 0, y: 0 });
  const dragged = useRef(false);
  const focusIndexRef = useRef(0);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const ro = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect;
        if (width > 0 && height > 0) {
          setDimensions({ width, height });
        }
      }
    });

    ro.observe(container);
    const rect = container.getBoundingClientRect();
    if (rect.width > 0 && rect.height > 0) {
      setDimensions({ width: rect.width, height: rect.height });
    }

    return () => ro.disconnect();
  }, [containerRef]);

  const mergedNodes = useMemo(() => {
    return filteredData.nodes.map((n) => {
      const pos = nodePositions.get(n.id);
      if (pos) return { ...n, x: pos.x, y: pos.y };
      return n;
    });
  }, [filteredData.nodes, nodePositions]);

  const padding = 200;
  const minX = -viewport.x / viewport.zoom - padding;
  const minY = -viewport.y / viewport.zoom - padding;
  const maxX = (dimensions.width - viewport.x) / viewport.zoom + padding;
  const maxY = (dimensions.height - viewport.y) / viewport.zoom + padding;

  const visibleNodes = useMemo(
    () => mergedNodes.filter((n) => n.x >= minX && n.x <= maxX && n.y >= minY && n.y <= maxY),
    [mergedNodes, minX, maxX, minY, maxY]
  );

  const visibleNodeIds = useMemo(() => new Set(visibleNodes.map((n) => n.id)), [visibleNodes]);

  const visibleEdges = useMemo(
    () => filteredData.edges.filter((e) => visibleNodeIds.has(e.source) && visibleNodeIds.has(e.target)),
    [filteredData.edges, visibleNodeIds]
  );

  const neighborIds = useMemo(() => {
    if (!selection.hoveredNodeId) return new Set<string>();
    const ids = new Set<string>([selection.hoveredNodeId]);
    for (const e of visibleEdges) {
      if (e.source === selection.hoveredNodeId) ids.add(e.target);
      if (e.target === selection.hoveredNodeId) ids.add(e.source);
    }
    return ids;
  }, [visibleEdges, selection.hoveredNodeId]);

  const handleWheel = useCallback(
    (e: React.WheelEvent) => {
      e.preventDefault();
      const rect = svgRef.current?.getBoundingClientRect();
      if (!rect) return;
      zoomBy(e.deltaY > 0 ? 0.92 : 1.08, e.clientX - rect.left, e.clientY - rect.top);
    },
    [zoomBy, svgRef]
  );

  const handleMouseDown = useCallback(
    (e: React.MouseEvent) => {
      if (e.button !== 0) return;
      dragged.current = false;
      isDragging.current = true;
      dragStart.current = { x: e.clientX - viewport.x, y: e.clientY - viewport.y };
    },
    [viewport]
  );

  const handleMouseMove = useCallback(
    (e: React.MouseEvent) => {
      if (!isDragging.current) return;
      if (Math.abs(e.clientX - dragStart.current.x - viewport.x) > 3 || Math.abs(e.clientY - dragStart.current.y - viewport.y) > 3) {
        dragged.current = true;
      }
      panBy(e.clientX - dragStart.current.x - viewport.x, e.clientY - dragStart.current.y - viewport.y);
      dragStart.current = { x: e.clientX - viewport.x, y: e.clientY - viewport.y };
    },
    [panBy, viewport]
  );

  const handleMouseUp = useCallback(() => {
    isDragging.current = false;
  }, []);

  const handleSvgClick = useCallback(
    (e: React.MouseEvent) => {
      if (dragged.current) { dragged.current = false; return; }
      if (e.target === svgRef.current) selectNode(null);
    },
    [selectNode, svgRef]
  );

  const handleNodeSelect = useCallback(
    (e: React.MouseEvent, id: string) => {
      e.stopPropagation();
      if (dragged.current) { dragged.current = false; return; }
      selectNode(selection.selectedNodeId === id ? null : id);
    },
    [selectNode, selection.selectedNodeId]
  );

  const handleNodeHover = useCallback(
    (e: React.MouseEvent, node: GraphNode) => {
      const rect = svgRef.current?.getBoundingClientRect();
      if (rect) setTooltipPos({ x: e.clientX - rect.left, y: e.clientY - rect.top });
      setTooltipNode(node);
      hoverNode(node.id);
    },
    [hoverNode, svgRef]
  );

  const handleNodeLeave = useCallback(() => {
    setTooltipNode(null);
    hoverNode(null);
  }, [hoverNode]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (visibleNodes.length === 0) return;

      if (e.key === 'ArrowDown' || e.key === 'ArrowRight') {
        e.preventDefault();
        focusIndexRef.current = (focusIndexRef.current + 1) % visibleNodes.length;
        const node = visibleNodes[focusIndexRef.current];
        if (node) {
          hoverNode(node.id);
          selectNode(node.id);
        }
      } else if (e.key === 'ArrowUp' || e.key === 'ArrowLeft') {
        e.preventDefault();
        focusIndexRef.current = (focusIndexRef.current - 1 + visibleNodes.length) % visibleNodes.length;
        const node = visibleNodes[focusIndexRef.current];
        if (node) {
          hoverNode(node.id);
          selectNode(node.id);
        }
      } else if (e.key === 'Escape') {
        selectNode(null);
        hoverNode(null);
      } else if (e.key === 'f' || e.key === 'F') {
        fitToScreen();
      } else if (e.key === 'r' || e.key === 'R') {
        resetView();
      }
    },
    [visibleNodes, selectNode, hoverNode]
  );

  return (
    <div
      ref={containerRef}
      className="relative h-full w-full overflow-hidden rounded-xl border border-zinc-200 bg-zinc-900 dark:border-zinc-700"
      style={{ touchAction: 'none' }}
      tabIndex={0}
      onKeyDown={handleKeyDown}
      role="graphics-document"
      aria-label="Evidence graph visualization. Use arrow keys to navigate nodes, Enter to select, Escape to deselect."
      aria-roledescription="interactive graph"
    >
      <svg
        ref={svgRef}
        width={dimensions.width}
        height={dimensions.height}
        className="h-full w-full"
        onWheel={handleWheel}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        onClick={handleSvgClick}
        role="graphics-object"
        aria-label="Graph area"
      >
        <defs>
          {Object.entries(config.edgeColors).map(([type, color]) => (
            <marker key={type} id={`arrow-${type}`} viewBox="0 0 10 10" refX="10" refY="5"
              markerWidth="6" markerHeight="6" orient="auto">
              <path d="M 0 0 L 10 5 L 0 10 z" fill={color} />
            </marker>
          ))}
        </defs>

        <g transform={`translate(${viewport.x}, ${viewport.y}) scale(${viewport.zoom})`}>
          {visibleEdges.map((edge) => (
            <GraphEdgeComponent
              key={edge.id}
              edge={edge}
              isHighlighted={!selection.hoveredNodeId || (neighborIds.has(edge.source) && neighborIds.has(edge.target))}
              isDimmed={!!selection.hoveredNodeId && !(neighborIds.has(edge.source) && neighborIds.has(edge.target))}
              nodePositions={nodePositions}
              config={config}
            />
          ))}

          {visibleNodes.map((node) => (
            <g
              key={node.id}
              onClick={(e) => handleNodeSelect(e, node.id)}
              onMouseEnter={(e) => handleNodeHover(e, node)}
              onMouseLeave={handleNodeLeave}
              style={{ cursor: 'pointer' }}
              role="graphics-symbol"
              aria-label={`${node.type}: ${node.label}`}
            >
              <GraphNodeComponent
                node={node}
                isSelected={selection.selectedNodeId === node.id}
                isHovered={selection.hoveredNodeId === node.id}
                isNeighbor={neighborIds.has(node.id)}
                isDimmed={!!selection.hoveredNodeId && !neighborIds.has(node.id)}
                config={config}
              />
            </g>
          ))}
        </g>
      </svg>

      {tooltipNode && (
        <div
          className="pointer-events-none absolute z-50"
          style={{ left: tooltipPos.x + 12, top: tooltipPos.y - 10, transform: 'translateY(-100%)' }}
          role="tooltip"
        >
          <div className="rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-xs shadow-xl">
            <div className="flex items-center gap-2">
              <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: config.colors[tooltipNode.type] }} />
              <span className="font-medium text-zinc-100">{tooltipNode.label}</span>
            </div>
            <div className="mt-1 flex gap-3 text-zinc-400">
              <span>{tooltipNode.type.replace(/_/g, ' ')}</span>
              {tooltipNode.confidence !== undefined && (
                <span>Conf: {(tooltipNode.confidence * 100).toFixed(0)}%</span>
              )}
            </div>
            {tooltipNode.risk && tooltipNode.risk !== 'unknown' && (
              <div className="mt-1 flex items-center gap-1">
                <span className="h-2 w-2 rounded-full" style={{ backgroundColor: config.riskColors[tooltipNode.risk] }} />
                <span className="font-medium" style={{ color: config.riskColors[tooltipNode.risk] }}>
                  {tooltipNode.risk.toUpperCase()}
                </span>
              </div>
            )}
          </div>
        </div>
      )}

      <div className="pointer-events-none absolute bottom-3 left-3 rounded bg-zinc-900/80 px-2 py-1 text-[11px] text-zinc-400">
        {visibleNodes.length} of {mergedNodes.length} nodes &middot; Click to select &middot; Drag to pan &middot; Scroll to zoom
        &middot; Arrow keys to navigate
      </div>
    </div>
  );
}
