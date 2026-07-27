import type { GraphNode, GraphEdge, GraphConfig } from '@/features/graph/types';

interface Bounds {
  minX: number;
  minY: number;
  maxX: number;
  maxY: number;
}

function computeBounds(nodes: GraphNode[]): Bounds {
  let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
  for (const n of nodes) {
    if (n.x < minX) minX = n.x;
    if (n.y < minY) minY = n.y;
    if (n.x > maxX) maxX = n.x;
    if (n.y > maxY) maxY = n.y;
  }
  return { minX, minY, maxX, maxY };
}

function initializeCircle(nodes: GraphNode[], cx: number, cy: number, radius: number): void {
  const len = nodes.length;
  for (let i = 0; i < len; i++) {
    const angle = (2 * Math.PI * i) / len;
    nodes[i].x = cx + radius * Math.cos(angle);
    nodes[i].y = cy + radius * Math.sin(angle);
    nodes[i].vx = 0;
    nodes[i].vy = 0;
  }
}

export function forceLayout(
  nodes: GraphNode[],
  edges: GraphEdge[],
  config: GraphConfig,
  width: number,
  height: number
): void {
  if (nodes.length === 0) return;

  const cx = width / 2;
  const cy = height / 2;
  const initRadius = Math.min(width, height) * 0.3;
  initializeCircle(nodes, cx, cy, initRadius);

  const { repulsion, attraction, centerForce, damping, iterations, maxSpeed } = config.layout;
  const restLength = Math.min(width, height) * 0.15;

  const nodeMap = new Map(nodes.map((n) => [n.id, n]));
  const adjacency = new Map<string, string[]>();
  for (const n of nodes) adjacency.set(n.id, []);
  for (const e of edges) {
    adjacency.get(e.source)?.push(e.target);
    adjacency.get(e.target)?.push(e.source);
  }

  for (let iter = 0; iter < iterations; iter++) {
    const cooling = 1 - iter / iterations;

    for (let i = 0; i < nodes.length; i++) {
      const a = nodes[i];
      if (a.fx !== null) { a.x = a.fx; a.y = a.fy ?? a.y; continue; }

      let fx = 0, fy = 0;

      for (let j = 0; j < nodes.length; j++) {
        if (i === j) continue;
        const b = nodes[j];
        const dx = a.x - b.x;
        const dy = a.y - b.y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
        const force = repulsion / (dist * dist);
        fx += (dx / dist) * force;
        fy += (dy / dist) * force;
      }

      const neighbors = adjacency.get(a.id) ?? [];
      for (const nid of neighbors) {
        const b = nodeMap.get(nid);
        if (!b || b.fx !== null) continue;
        const dx = b.x - a.x;
        const dy = b.y - a.y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
        const force = attraction * (dist - restLength);
        fx += (dx / dist) * force;
        fy += (dy / dist) * force;
      }

      fx += (cx - a.x) * centerForce;
      fy += (cy - a.y) * centerForce;

      a.vx = (a.vx + fx) * damping * cooling;
      a.vy = (a.vy + fy) * damping * cooling;

      const speed = Math.sqrt(a.vx * a.vx + a.vy * a.vy);
      if (speed > maxSpeed) {
        a.vx = (a.vx / speed) * maxSpeed;
        a.vy = (a.vy / speed) * maxSpeed;
      }

      a.x += a.vx;
      a.y += a.vy;

      const margin = 50;
      a.x = Math.max(margin, Math.min(width - margin, a.x));
      a.y = Math.max(margin, Math.min(height - margin, a.y));
    }
  }

  const bounds = computeBounds(nodes);
  const graphW = bounds.maxX - bounds.minX || 1;
  const graphH = bounds.maxY - bounds.minY || 1;
  const scale = Math.min((width - 100) / graphW, (height - 100) / graphH, 1);
  const offsetX = cx - (bounds.minX + bounds.maxX) / 2;
  const offsetY = cy - (bounds.minY + bounds.maxY) / 2;

  for (const n of nodes) {
    n.x = (n.x + offsetX - cx) * scale + cx;
    n.y = (n.y + offsetY - cy) * scale + cy;
  }
}
