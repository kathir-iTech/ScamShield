import { memo } from 'react';
import type { GraphEdge, GraphContextValue } from '@/features/graph/types';

interface GraphEdgeProps {
  edge: GraphEdge;
  isHighlighted: boolean;
  isDimmed: boolean;
  nodePositions: Map<string, { x: number; y: number }>;
  config: GraphContextValue['config'];
}

export const GraphEdgeComponent = memo(function GraphEdgeComponent({
  edge,
  isHighlighted,
  isDimmed,
  nodePositions,
  config,
}: GraphEdgeProps) {
  const source = nodePositions.get(edge.source);
  const target = nodePositions.get(edge.target);
  if (!source || !target) return null;

  const color = config.edgeColors[edge.type];
  const opacity = isDimmed ? 0.05 : isHighlighted ? 0.9 : 0.3;
  const strokeWidth = isHighlighted ? 2 : 1;

  return (
    <g opacity={opacity} style={{ transition: 'opacity 0.2s' }}>
      <line
        x1={source.x}
        y1={source.y}
        x2={target.x}
        y2={target.y}
        stroke={color}
        strokeWidth={strokeWidth}
        markerEnd={`url(#arrow-${edge.type})`}
      />
    </g>
  );
});
