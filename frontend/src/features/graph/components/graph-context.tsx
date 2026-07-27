import { createContext, useContext, useState, useCallback, useRef, useMemo, useEffect, type ReactNode } from 'react';
import type {
  GraphData,
  Viewport,
  SelectionState,
  FilterState,
  NodeType,
  EdgeType,
  GraphContextValue,
} from '@/features/graph/types';
import { DEFAULT_GRAPH_CONFIG } from '@/features/graph/types';
import { forceLayout } from '@/features/graph/utils/layout';

const GraphContext = createContext<GraphContextValue | null>(null);

interface GraphProviderProps {
  data: GraphData;
  children: ReactNode;
  width?: number;
  height?: number;
}

export function GraphProvider({ data, children, width = 800, height = 600 }: GraphProviderProps) {
  const svgRef = useRef<SVGSVGElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);

  const [viewport, setViewportRaw] = useState<Viewport>({ x: 0, y: 0, zoom: 1 });
  const [selection, setSelection] = useState<SelectionState>({ selectedNodeId: null, hoveredNodeId: null });
  const [filters, setFiltersRaw] = useState<FilterState>({
    nodeTypes: [],
    edgeTypes: [],
    searchQuery: '',
  });
  const [layoutRunning, setLayoutRunning] = useState(true);
  const [nodePositions, setNodePositions] = useState<Map<string, { x: number; y: number }>>(new Map());

  const config = DEFAULT_GRAPH_CONFIG;

  const setViewport = useCallback((vp: Viewport) => setViewportRaw(vp), []);

  const panBy = useCallback((dx: number, dy: number) => {
    setViewportRaw((prev) => ({ ...prev, x: prev.x + dx, y: prev.y + dy }));
  }, []);

  const zoomBy = useCallback((factor: number, cx?: number, cy?: number) => {
    setViewportRaw((prev) => {
      const newZoom = Math.max(0.1, Math.min(5, prev.zoom * factor));
      if (cx !== undefined && cy !== undefined) {
        const newX = cx - (cx - prev.x) * (newZoom / prev.zoom);
        const newY = cy - (cy - prev.y) * (newZoom / prev.zoom);
        return { x: newX, y: newY, zoom: newZoom };
      }
      return { ...prev, zoom: newZoom };
    });
  }, []);

  const resetView = useCallback(() => {
    setViewportRaw({ x: 0, y: 0, zoom: 1 });
    setSelection({ selectedNodeId: null, hoveredNodeId: null });
  }, []);

  const fitToScreen = useCallback(() => {
    if (data.nodes.length === 0) return;
    const padding = 80;
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    for (const n of data.nodes) {
      if (n.x < minX) minX = n.x;
      if (n.y < minY) minY = n.y;
      if (n.x > maxX) maxX = n.x;
      if (n.y > maxY) maxY = n.y;
    }
    const graphW = maxX - minX || 1;
    const graphH = maxY - minY || 1;
    const zoom = Math.min((width - padding * 2) / graphW, (height - padding * 2) / graphH, 2);
    const cx = (minX + maxX) / 2;
    const cy = (minY + maxY) / 2;
    setViewportRaw({
      x: width / 2 - cx * zoom,
      y: height / 2 - cy * zoom,
      zoom,
    });
  }, [data.nodes, width, height]);

  const selectNode = useCallback((id: string | null) => {
    setSelection((prev) => ({ ...prev, selectedNodeId: id }));
  }, []);

  const hoverNode = useCallback((id: string | null) => {
    setSelection((prev) => ({ ...prev, hoveredNodeId: id }));
  }, []);

  const setFilters = useCallback((f: FilterState) => setFiltersRaw(f), []);

  const setSearchQuery = useCallback((q: string) => {
    setFiltersRaw((prev) => ({ ...prev, searchQuery: q }));
  }, []);

  const toggleNodeType = useCallback((t: NodeType) => {
    setFiltersRaw((prev) => {
      const exists = prev.nodeTypes.includes(t);
      return {
        ...prev,
        nodeTypes: exists ? prev.nodeTypes.filter((x) => x !== t) : [...prev.nodeTypes, t],
      };
    });
  }, []);

  const toggleEdgeType = useCallback((t: EdgeType) => {
    setFiltersRaw((prev) => {
      const exists = prev.edgeTypes.includes(t);
      return {
        ...prev,
        edgeTypes: exists ? prev.edgeTypes.filter((x) => x !== t) : [...prev.edgeTypes, t],
      };
    });
  }, []);

  const collapseCluster = useCallback((nodeId: string) => {
    setNodePositions((prev) => {
      const next = new Map(prev);
      return next;
    });
    data.nodes = data.nodes.map((n) =>
      n.id === nodeId ? { ...n, collapsed: true } : n
    );
  }, [data]);

  const expandCluster = useCallback((nodeId: string) => {
    data.nodes = data.nodes.map((n) =>
      n.id === nodeId ? { ...n, collapsed: false } : n
    );
  }, [data]);

  const filteredData = useMemo(() => {
    let filtered = data;

    if (filters.searchQuery) {
      const q = filters.searchQuery.toLowerCase();
      filtered = {
        ...filtered,
        nodes: filtered.nodes.filter((n) => n.label.toLowerCase().includes(q)),
      };
    }

    if (filters.nodeTypes.length > 0) {
      filtered = {
        ...filtered,
        nodes: filtered.nodes.filter((n) => filters.nodeTypes.includes(n.type)),
      };
    }

    if (filters.edgeTypes.length > 0) {
      filtered = {
        ...filtered,
        edges: filtered.edges.filter((e) => filters.edgeTypes.includes(e.type)),
      };
    }

    const nodeIds = new Set(filtered.nodes.map((n) => n.id));
    filtered = {
      ...filtered,
      edges: filtered.edges.filter((e) => nodeIds.has(e.source) && nodeIds.has(e.target)),
    };

    return filtered;
  }, [data, filters]);

  useEffect(() => {
    if (data.nodes.length === 0) return;
    setLayoutRunning(true);

    const nodesCopy = data.nodes.map((n) => ({ ...n }));
    const edgesCopy = data.edges.map((e) => ({ ...e }));
    forceLayout(nodesCopy, edgesCopy, config, width, height);

    const posMap = new Map<string, { x: number; y: number }>();
    for (const n of nodesCopy) {
      posMap.set(n.id, { x: n.x, y: n.y });
    }
    setNodePositions(posMap);
    setLayoutRunning(false);

    const timer = setTimeout(() => fitToScreen(), 50);
    return () => clearTimeout(timer);
  }, [data.nodes.length, data.edges.length]);

  const value = useMemo<GraphContextValue>(
    () => ({
      data,
      filteredData,
      viewport,
      selection,
      filters,
      config,
      svgRef,
      containerRef,
      selectNode,
      hoverNode,
      setViewport,
      panBy,
      zoomBy,
      fitToScreen,
      setFilters,
      setSearchQuery,
      toggleNodeType,
      toggleEdgeType,
      collapseCluster,
      expandCluster,
      resetView,
      layoutRunning,
      nodePositions,
    }),
    [
      data,
      filteredData,
      viewport,
      selection,
      filters,
      selectNode,
      hoverNode,
      setViewport,
      panBy,
      zoomBy,
      fitToScreen,
      setFilters,
      setSearchQuery,
      toggleNodeType,
      toggleEdgeType,
      collapseCluster,
      expandCluster,
      resetView,
      layoutRunning,
      nodePositions,
    ]
  );

  return (
    <GraphContext.Provider value={value}>
      {children}
    </GraphContext.Provider>
  );
}

export function useGraph(): GraphContextValue {
  const ctx = useContext(GraphContext);
  if (!ctx) throw new Error('useGraph must be used within GraphProvider');
  return ctx;
}
