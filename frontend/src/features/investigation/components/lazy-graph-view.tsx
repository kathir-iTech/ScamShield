import { GraphProvider, EvidenceGraph, GraphToolbar, NodeDetailsPanel, Legend } from '@/features/graph';
import type { GraphData } from '@/features/graph/types';

interface LazyGraphViewProps {
  graphData: GraphData;
  width: number;
  height: number;
}

export default function LazyGraphView({ graphData, width, height }: LazyGraphViewProps) {
  return (
    <GraphProvider data={graphData} width={width} height={height}>
      <div className="grid h-full grid-cols-1 gap-4 lg:grid-cols-4">
        <div className="lg:col-span-1">
          <div className="space-y-4">
            <Legend />
          </div>
        </div>
        <div className="flex flex-col gap-4 lg:col-span-2">
          <GraphToolbar />
          <div className="min-h-[400px] flex-1">
            <EvidenceGraph />
          </div>
        </div>
        <div className="lg:col-span-1">
          <NodeDetailsPanel />
        </div>
      </div>
    </GraphProvider>
  );
}
