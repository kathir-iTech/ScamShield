import { useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { useGraph } from '@/features/graph/components/graph-context';
import { NODE_TYPE_LABELS } from '@/features/graph/types';
import { X, ExternalLink } from 'lucide-react';

export function NodeDetailsPanel() {
  const { data, selection, selectNode, config } = useGraph();

  const selectedNode = useMemo(
    () => data.nodes.find((n) => n.id === selection.selectedNodeId) ?? null,
    [data.nodes, selection.selectedNodeId]
  );

  const connectedEdges = useMemo(
    () => data.edges.filter((e) => e.source === selection.selectedNodeId || e.target === selection.selectedNodeId),
    [data.edges, selection.selectedNodeId]
  );

  if (!selectedNode) {
    return (
      <Card className="h-full">
        <CardContent className="flex h-full items-center justify-center p-6">
          <p className="text-center text-sm text-zinc-500 dark:text-zinc-400">
            Select a node to view details
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="h-full overflow-auto">
      <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-3">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span
              className="h-2.5 w-2.5 shrink-0 rounded-full"
              style={{ backgroundColor: config.colors[selectedNode.type] }}
            />
            <CardTitle className="truncate text-sm">{selectedNode.label}</CardTitle>
          </div>
          <Badge variant="outline" className="mt-1">
            {NODE_TYPE_LABELS[selectedNode.type]}
          </Badge>
        </div>
        <Button variant="ghost" size="icon" className="h-8 w-8 shrink-0" onClick={() => selectNode(null)} aria-label="Close panel">
          <X className="h-4 w-4" />
        </Button>
      </CardHeader>
      <CardContent className="space-y-4 pt-0">
        {selectedNode.confidence !== undefined && (
          <div>
            <p className="mb-1 text-xs font-medium text-zinc-500 dark:text-zinc-400">Confidence</p>
            <div className="flex items-center gap-2">
              <div className="h-2 flex-1 overflow-hidden rounded-full bg-zinc-200 dark:bg-zinc-700">
                <div
                  className="h-full rounded-full bg-emerald-500"
                  style={{ width: `${(selectedNode.confidence * 100).toFixed(0)}%` }}
                />
              </div>
              <span className="text-xs text-zinc-600 dark:text-zinc-400">
                {(selectedNode.confidence * 100).toFixed(0)}%
              </span>
            </div>
          </div>
        )}

        {selectedNode.risk && selectedNode.risk !== 'unknown' && (
          <div>
            <p className="mb-1 text-xs font-medium text-zinc-500 dark:text-zinc-400">Risk Level</p>
            <Badge
              variant={
                selectedNode.risk === 'critical' || selectedNode.risk === 'high'
                  ? 'destructive'
                  : selectedNode.risk === 'medium'
                    ? 'warning'
                    : 'info'
              }
            >
              {selectedNode.risk.toUpperCase()}
            </Badge>
          </div>
        )}

        {selectedNode.metadata && Object.keys(selectedNode.metadata).length > 0 && (
          <div>
            <p className="mb-1 text-xs font-medium text-zinc-500 dark:text-zinc-400">Metadata</p>
            <div className="space-y-1 rounded-lg bg-zinc-50 p-2 dark:bg-zinc-800">
              {Object.entries(selectedNode.metadata).map(([key, value]) => (
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

        {connectedEdges.length > 0 && (
          <div>
            <p className="mb-1 text-xs font-medium text-zinc-500 dark:text-zinc-400">
              Relationships ({connectedEdges.length})
            </p>
            <div className="space-y-1">
              {connectedEdges.slice(0, 15).map((edge) => {
                const otherId = edge.source === selectedNode.id ? edge.target : edge.source;
                const otherNode = data.nodes.find((n) => n.id === otherId);
                return (
                  <div
                    key={edge.id}
                    className="flex items-center gap-2 rounded-lg bg-zinc-50 px-2 py-1.5 text-xs dark:bg-zinc-800"
                  >
                    <span
                      className="h-2 w-2 shrink-0 rounded-full"
                      style={{ backgroundColor: config.edgeColors[edge.type] }}
                    />
                    <span className="flex-1 truncate text-zinc-500 dark:text-zinc-400">
                      <span className="font-medium text-zinc-700 dark:text-zinc-300">{edge.type}</span>
                      {' → '}
                      {otherNode?.label ?? otherId}
                    </span>
                    {edge.weight !== undefined && (
                      <span className="shrink-0 text-zinc-400">w:{edge.weight}</span>
                    )}
                  </div>
                );
              })}
              {connectedEdges.length > 15 && (
                <p className="text-center text-xs text-zinc-400">
                  +{connectedEdges.length - 15} more
                </p>
              )}
            </div>
          </div>
        )}

        <Button
          variant="ghost"
          size="sm"
          className="w-full text-xs"
          onClick={() => selectNode(null)}
        >
          <ExternalLink className="mr-1.5 h-3 w-3" />
          Close details
        </Button>
      </CardContent>
    </Card>
  );
}
