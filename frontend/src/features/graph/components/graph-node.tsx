import { memo } from 'react';
import type { GraphNode, GraphContextValue } from '@/features/graph/types';

interface GraphNodeProps {
  node: GraphNode;
  isSelected: boolean;
  isHovered: boolean;
  isNeighbor: boolean;
  isDimmed: boolean;
  config: GraphContextValue['config'];
}

export const GraphNodeComponent = memo(function GraphNodeComponent({
  node,
  isSelected,
  isHovered,
  isDimmed,
  config,
}: GraphNodeProps) {
  const radius = getNodeRadius(node.confidence, config);
  const fillColor = config.colors[node.type];
  const strokeColor = node.risk ? config.riskColors[node.risk] : fillColor;
  const opacity = isDimmed ? 0.2 : 1;
  const strokeWidth = isSelected ? 3 : isHovered ? 2.5 : 1.5;

  return (
    <g
      transform={`translate(${node.x}, ${node.y})`}
      style={{ cursor: 'pointer', opacity, transition: 'opacity 0.2s' }}
      role="graphics-symbol"
      aria-label={`${node.type}: ${node.label}`}
    >
      <circle
        r={radius}
        fill={fillColor}
        fillOpacity={0.15}
        stroke={strokeColor}
        strokeWidth={strokeWidth}
      />
      <circle
        r={radius * 0.6}
        fill={fillColor}
        fillOpacity={isHovered || isSelected ? 0.5 : 0.3}
      />
      {isSelected && (
        <circle
          r={radius + 4}
          fill="none"
          stroke={strokeColor}
          strokeWidth={1.5}
          strokeDasharray="4 3"
          opacity={0.6}
        />
      )}
      <text
        textAnchor="middle"
        dy="0.35em"
        fontSize={Math.max(8, Math.min(11, radius * 0.35))}
        fill="currentColor"
        className="dark:fill-zinc-100 fill-zinc-800"
        pointerEvents="none"
      >
        {truncateLabel(node.label, Math.floor(radius * 0.6))}
      </text>
    </g>
  );
});

function getNodeRadius(confidence: number | undefined, config: GraphContextValue['config']): number {
  const c = confidence ?? 0.5;
  const { min, max } = config.nodeRadius;
  return min + (max - min) * Math.max(0, Math.min(1, c));
}

function truncateLabel(label: string, maxChars: number): string {
  if (label.length <= maxChars) return label;
  return label.slice(0, Math.max(1, maxChars - 1)) + '…';
}
