import { useMemo } from "react";
import {
  Background,
  Controls,
  MarkerType,
  Position,
  ReactFlow,
  type Node,
  type Edge,
} from "@xyflow/react";
import type { Report } from "./types";

export function DependencyMap({
  report,
  selected,
  onSelect,
  query,
  setQuery,
  showModules,
  setShowModules,
}: {
  report: Report;
  selected: string | null;
  onSelect: (id: string) => void;
  query: string;
  setQuery: (query: string) => void;
  showModules: boolean;
  setShowModules: (show: boolean) => void;
}) {
  const graph = useMemo(() => {
    if (!report) return { nodes: [] as Node[], edges: [] as Edge[] };
    const changed = new Set(report.changed),
      impacted = new Set(report.impacted);
    const removed = new Set(report.removed);
    const visible = report.nodes.filter(
      (n) =>
        (showModules || n.kind !== "module") &&
        `${n.name} ${n.path}`.toLowerCase().includes(query.toLowerCase()),
    );
    const ids = new Set(visible.map((n) => n.id));
    const ranks: Record<string, number> = {};
    for (const id of report.changed) ranks[id] = 0;
    for (let i = 0; i < 5; i++)
      for (const e of report.edges) {
        if (ranks[e.target] !== undefined && ranks[e.source] === undefined)
          ranks[e.source] = Math.min(4, ranks[e.target] + 1);
      }
    const rows = new Map<number, number>();
    const evidence =
      report.recommendations.find((r) => r.symbol === selected)
        ?.evidence_edges ?? [];
    const nodes: Node[] = visible.map((n) => {
      const column = changed.has(n.id) ? 0 : (ranks[n.id] ?? 4);
      const row = rows.get(column) ?? 0;
      rows.set(column, row + 1);
      const state = removed.has(n.id)
        ? "removed"
        : changed.has(n.id)
          ? "changed"
          : impacted.has(n.id)
            ? "impacted"
            : "unaffected";
      return {
        id: n.id,
        position: { x: (4 - column) * 265, y: row * 118 },
        sourcePosition: Position.Right,
        targetPosition: Position.Left,
        className: `${state} ${selected === n.id ? "active-node" : ""}`,
        data: {
          label: (
            <div className="symbol-label">
              <span className="node-type">
                {n.kind} · {state}
              </span>
              <strong>{n.name}</strong>
              <small>
                {n.path}:{n.line}
              </small>
            </div>
          ),
        },
        style: { width: 230 },
        ariaLabel: `${n.name}, ${n.kind}, ${state}, ${n.path}:${n.line}`,
      };
    });
    const edges: Edge[] = report.edges
      .filter((e) => ids.has(e.source) && ids.has(e.target))
      .map((e) => {
        const highlighted = evidence.includes(e.id);
        return {
          id: e.id,
          source: e.source,
          target: e.target,
          animated: false,
          markerEnd: { type: MarkerType.ArrowClosed },
          style: {
            stroke: highlighted ? "#365bd6" : "#7f8a9d",
            strokeWidth: highlighted ? 3 : 1.5,
            strokeDasharray: e.kind === "call" ? undefined : "5 4",
          },
        };
      });
    return { nodes, edges };
  }, [report, selected, showModules, query]);

  return (
    <>
      <div className="graph-toolbar">
        <input
          aria-label="Search symbols"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search symbols or files…"
        />
        <label>
          <input
            type="checkbox"
            checked={showModules}
            onChange={(e) => setShowModules(e.target.checked)}
          />{" "}
          Module dependencies
        </label>
      </div>
      <div
        className="graph-canvas"
        data-testid="dependency-graph"
        onKeyDown={(event) => {
          if (event.key === "Enter" || event.key === " ") {
            const node = (event.target as HTMLElement).closest<HTMLElement>(
              ".react-flow__node",
            );
            if (node?.dataset.id) {
              event.preventDefault();
              onSelect(node.dataset.id);
            }
          }
        }}
      >
        <ReactFlow
          key={`${showModules}-${query}`}
          nodes={graph.nodes}
          edges={graph.edges}
          fitView
          fitViewOptions={{ padding: 0.18, minZoom: 0.8, maxZoom: 1 }}
          minZoom={0.25}
          nodesDraggable={false}
          nodesConnectable={false}
          onNodeClick={(_, n) => onSelect(n.id)}
          colorMode="light"
        >
          <Background color="#d6d9e0" gap={22} />
          <Controls
            showInteractive={false}
            fitViewOptions={{ padding: 0.18 }}
          />
        </ReactFlow>
        {!graph.nodes.length && (
          <div className="empty-graph">No symbols match this view.</div>
        )}
      </div>
      <div className="legend">
        <span>
          <i className="changed-dot" /> Changed
        </span>
        <span>
          <i className="impacted-dot" /> Potential impact
        </span>
        <span>
          <i /> Unaffected
        </span>
        <small>
          Arrows: caller → dependency · solid: resolved call · dashed:
          conservative fallback
        </small>
      </div>
    </>
  );
}
