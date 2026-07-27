import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { NODE_TYPE_LABELS, EDGE_TYPE_LABELS, type NodeType, type EdgeType } from '@/features/graph/types';
import { useGraph } from '@/features/graph/components/graph-context';

export function Legend() {
  const { config } = useGraph();
  const colorEntries = Object.entries(config.colors) as [NodeType, string][];
  const edgeEntries = Object.entries(config.edgeColors) as [EdgeType, string][];
  const riskEntries = Object.entries(config.riskColors) as [string, string][];

  return (
    <Card className="w-full">
      <CardHeader className="pb-3">
        <CardTitle className="text-sm">Legend</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4 pt-0">
        <div>
          <p className="mb-1.5 text-xs font-medium text-zinc-500 dark:text-zinc-400">Node Types</p>
          <div className="grid grid-cols-2 gap-1">
            {colorEntries.map(([type, color]) => (
              <div key={type} className="flex items-center gap-2 text-xs">
                <span className="h-2.5 w-2.5 shrink-0 rounded-full" style={{ backgroundColor: color }} />
                <span className="text-zinc-700 dark:text-zinc-300">{NODE_TYPE_LABELS[type]}</span>
              </div>
            ))}
          </div>
        </div>

        <div>
          <p className="mb-1.5 text-xs font-medium text-zinc-500 dark:text-zinc-400">Risk Levels</p>
          <div className="grid grid-cols-2 gap-1">
            {riskEntries.map(([risk, color]) => (
              <div key={risk} className="flex items-center gap-2 text-xs">
                <span className="h-2.5 w-2.5 shrink-0 rounded-full" style={{ backgroundColor: color }} />
                <span className="capitalize text-zinc-700 dark:text-zinc-300">{risk}</span>
              </div>
            ))}
          </div>
        </div>

        <div>
          <p className="mb-1.5 text-xs font-medium text-zinc-500 dark:text-zinc-400">Relationships</p>
          <div className="space-y-1">
            {edgeEntries.map(([type, color]) => (
              <div key={type} className="flex items-center gap-2 text-xs">
                <svg width="20" height="8" className="shrink-0">
                  <line x1="0" y1="4" x2="16" y2="4" stroke={color} strokeWidth="1.5" />
                  <polygon points="16,4 12,2 12,6" fill={color} />
                </svg>
                <span className="text-zinc-700 dark:text-zinc-300">{EDGE_TYPE_LABELS[type]}</span>
              </div>
            ))}
          </div>
        </div>

        <div>
          <p className="mb-1.5 text-xs font-medium text-zinc-500 dark:text-zinc-400">Size</p>
          <div className="flex items-center gap-3 text-xs">
            <div className="flex items-center gap-1.5">
              <span className="inline-block h-2 w-2 rounded-full bg-zinc-400" />
              <span className="text-zinc-500">Low conf</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="inline-block h-3.5 w-3.5 rounded-full bg-zinc-400" />
              <span className="text-zinc-500">High conf</span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
