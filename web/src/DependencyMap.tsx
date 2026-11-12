import { useEffect, useMemo, useRef, useState, type RefObject } from "react";
import {
  Background,
  Controls,
  MarkerType,
  Position,
  ReactFlow,
  useStore,
  useReactFlow,
  getViewportForBounds,
  type Node,
  type Edge,
  type ReactFlowInstance,
  type Viewport,
} from "@xyflow/react";
import type { Report } from "./types";
import type { Theme } from "./theme";

function frameNodes(
  flow: ReactFlowInstance,
  canvas: HTMLDivElement | null,
  id?: string,
  minZoom = 0.01,
) {
  if (!canvas || !flow.viewportInitialized) return;
  const nodes = id
    ? flow.getNodes().filter((node) => node.id === id)
    : flow.getNodes();
  if (!nodes.length) return;
  const bounds = flow.getNodesBounds(nodes);
  void flow.setViewport(
    getViewportForBounds(
      bounds,
      canvas.clientWidth,
      canvas.clientHeight,
      minZoom,
      1,
      0.18,
    ),
  );
}

// Wait for measured cards before framing; preserve pan/zoom across view switches.
function MapFrame({
  frameKey,
  focused,
  viewport,
  fitAll,
  jumpTo,
  canvas,
}: {
  frameKey: string;
  focused: string | null;
  viewport: RefObject<Viewport | null>;
  fitAll: RefObject<boolean>;
  jumpTo: RefObject<string | null>;
  canvas: RefObject<HTMLDivElement | null>;
}) {
  // These cards are controlled by report data. Read measured dimensions from
  // the flow, without copying layout measurements into the report-derived nodes.
  const initialized = useStore(
    (state) =>
      state.nodeLookup.size > 0 &&
      [...state.nodeLookup.values()].every(
        (node) => !!node.measured.width && !!node.measured.height,
      ),
  );
  const flow = useReactFlow();
  const previous = useRef<string | null>(null);
  const saved = useRef(viewport.current);
  useEffect(() => {
    if (
      !initialized ||
      !flow.viewportInitialized ||
      previous.current === frameKey
    )
      return;
    // Let React Flow commit changed positions before reading their bounds.
    const frame = requestAnimationFrame(() => {
      const restore = previous.current === null ? saved.current : null;
      previous.current = frameKey;
      if (jumpTo.current) {
        frameNodes(flow, canvas.current, jumpTo.current, 0.85);
        jumpTo.current = null;
      } else if (fitAll.current) {
        fitAll.current = false;
        frameNodes(flow, canvas.current);
      } else if (restore) void flow.setViewport(restore);
      else if (focused) frameNodes(flow, canvas.current, focused, 0.85);
      else frameNodes(flow, canvas.current, undefined, 0.8);
    });
    return () => cancelAnimationFrame(frame);
  }, [initialized, frameKey, focused, flow, fitAll, jumpTo, canvas]);
  return null;
}

export function DependencyMap({
  theme,
  report,
  selected,
  onSelect,
  query,
  setQuery,
  showModules,
  setShowModules,
  focusedPath,
  setFocusedPath,
  viewport,
}: {
  theme: Theme;
  report: Report;
  selected: string | null;
  onSelect: (id: string) => void;
  query: string;
  setQuery: (query: string) => void;
  showModules: boolean;
  setShowModules: (show: boolean) => void;
  focusedPath: string | null;
  setFocusedPath: (id: string | null) => void;
  viewport: RefObject<Viewport | null>;
}) {
  const canvas = useRef<HTMLDivElement>(null);
  const fitAll = useRef(false);
  const jumpTo = useRef<string | null>(null);
  const [frameVersion, setFrameVersion] = useState(0);
  const [horizontal, setHorizontal] = useState(
    () => window.matchMedia("(min-width: 701px)").matches,
  );
  useEffect(() => {
    const media = window.matchMedia("(min-width: 701px)");
    const update = () => setHorizontal(media.matches);
    media.addEventListener("change", update);
    return () => media.removeEventListener("change", update);
  }, []);
  const selectedRecommendation = report.recommendations.find(
    (r) => r.symbol === selected,
  );
  const focused = report.recommendations.find((r) => r.symbol === focusedPath);
  const recommendation = focused ?? selectedRecommendation;
  const graph = useMemo(() => {
    const changed = new Set(report.changed),
      impacted = new Set(report.impacted),
      removed = new Set(report.removed);
    const evidenceNodes = new Set(recommendation?.evidence_path ?? []);
    const evidenceEdges = new Set(recommendation?.evidence_edges ?? []);
    const byId = new Map(report.nodes.map((n) => [n.id, n]));
    // Focus includes module nodes even when they are hidden in the overview.
    const visible = focused
      ? focused.evidence_path.map((id) => byId.get(id)!).filter(Boolean)
      : report.nodes.filter(
          (n) =>
            (showModules || n.kind !== "module") &&
            `${n.name} ${n.path}`
              .toLowerCase()
              .includes(query.trim().toLowerCase()),
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
    let pathY = 0;
    const nodes: Node[] = visible.map((n, index) => {
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
      const position = focused
        ? horizontal
          ? { x: index * 320, y: 0 }
          : { x: 0, y: pathY }
        : { x: (4 - column) * 265, y: row * 118 };
      // Reserve wrapping space for full labels, including long source paths.
      pathY +=
        Math.max(
          130,
          64 +
            Math.ceil(n.name.length / 24) * 24 +
            Math.ceil(n.path.length / 32) * 18,
        ) + 60;
      return {
        id: n.id,
        position,
        sourcePosition:
          focused && !horizontal ? Position.Bottom : Position.Right,
        targetPosition: focused && !horizontal ? Position.Top : Position.Left,
        className: `${state} ${selected === n.id ? "active-node" : ""} ${evidenceNodes.has(n.id) ? "path-node" : recommendation ? "context-node" : ""}`,
        data: {
          label: (
            <div className="symbol-label">
              <span className="node-type">
                {focused ? `${index + 1} / ${visible.length} · ` : ""}
                {n.kind} · {state}
              </span>
              <strong>{n.name}</strong>
              <small>
                {n.path}:{n.line}
              </small>
            </div>
          ),
        },
        style: { width: focused ? 260 : 230 },
        ariaLabel: `${n.name}, ${n.kind}, ${state}, ${n.path}:${n.line}`,
      };
    });
    const edges: Edge[] = report.edges
      .filter(
        (e) =>
          ids.has(e.source) &&
          ids.has(e.target) &&
          (!focused || evidenceEdges.has(e.id)),
      )
      .map((e) => {
        const highlighted = evidenceEdges.has(e.id);
        return {
          id: e.id,
          source: e.source,
          target: e.target,
          animated: false,
          className: highlighted ? "evidence-edge" : "context-edge",
          ariaLabel: `${e.kind === "call" ? "Resolved call" : `Conservative ${e.kind} dependency`}: ${e.source} → ${e.target}, ${e.revision} revisions`,
          markerEnd: {
            type: MarkerType.ArrowClosed,
            color: highlighted ? "var(--graph-evidence)" : "var(--graph-edge)",
          },
          style: {
            stroke: highlighted ? "var(--graph-evidence)" : "var(--graph-edge)",
            strokeWidth: highlighted ? 3 : 1.5,
            strokeDasharray: e.kind === "call" ? undefined : "5 4",
          },
        };
      });
    return { nodes, edges };
  }, [
    report,
    selected,
    showModules,
    query,
    focused,
    recommendation,
    horizontal,
  ]);
  const frameKey = `${focusedPath ?? "overview"}:${showModules}:${query}:${frameVersion}:${horizontal}`;
  function fit() {
    jumpTo.current = null;
    fitAll.current = true;
    setFrameVersion((version) => version + 1);
  }
  function reset() {
    fit();
    setFocusedPath(null);
    setQuery("");
    setShowModules(false);
    viewport.current = null;
  }
  return (
    <>
      <div className={focused ? "map-top focused" : "map-top"}>
        <div className="graph-toolbar">
          {focused ? (
            <div className="focused-path-label">
              <strong>Focused evidence path</strong>
              <span>
                {focused.symbol.split("::")[1]} ·{" "}
                {
                  {
                    before: "Before only",
                    after: "After only",
                    both: "Both revisions",
                    mixed: "Mixed revisions",
                  }[focused.path_revision]
                }
              </span>
            </div>
          ) : (
            <>
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
            </>
          )}
        </div>
        <div className="map-actions">
          <div className="map-buttons">
            {(!focused ||
              (selectedRecommendation && focused.symbol !== selected)) && (
              <button
                className="secondary"
                disabled={!selectedRecommendation || focusedPath === selected}
                onClick={() => {
                  viewport.current = null;
                  setFocusedPath(selected);
                }}
              >
                Focus path
              </button>
            )}
            <button
              className="secondary"
              disabled={!graph.nodes.length}
              onClick={fit}
            >
              Fit view
            </button>
            <button className="text-button" onClick={reset}>
              Reset map
            </button>
          </div>
          <span className="map-count" role="status">
            {graph.nodes.length} symbols · {graph.edges.length} dependencies
          </span>
        </div>
      </div>
      {focused && (
        <div className="path-navigation">
          <label>
            Jump to path symbol
            <select
              aria-label="Jump to path symbol"
              defaultValue=""
              key={focused.symbol}
              onChange={(e) => {
                if (e.target.value) {
                  jumpTo.current = e.target.value;
                  fitAll.current = false;
                  setFrameVersion((version) => version + 1);
                }
              }}
            >
              <option value="" disabled>
                Choose a step…
              </option>
              {focused.evidence_path.map((id, i) => (
                <option key={id} value={id}>
                  {i + 1}. {id}
                </option>
              ))}
            </select>
          </label>
          <button
            className="text-button"
            onClick={() => onSelect(focused.symbol)}
          >
            Inspect test
          </button>
          {focused.path_revision === "mixed" && (
            <p>
              No single revision contains this entire path. This combined path
              is a conservative estimate.
            </p>
          )}
        </div>
      )}
      <div
        ref={canvas}
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
          nodes={graph.nodes}
          edges={graph.edges}
          onMoveEnd={(_, next) => {
            viewport.current = next;
          }}
          minZoom={0.01}
          maxZoom={2}
          nodesDraggable={false}
          nodesConnectable={false}
          onNodeClick={(_, n) => onSelect(n.id)}
          colorMode={theme}
        >
          <MapFrame
            canvas={canvas}
            frameKey={frameKey}
            focused={focused?.symbol ?? null}
            viewport={viewport}
            fitAll={fitAll}
            jumpTo={jumpTo}
          />
          <Background color="var(--graph-grid)" gap={22} />
          <Controls showInteractive={false} showFitView={false} />
        </ReactFlow>
        {!graph.nodes.length && (
          <div className="empty-graph">
            <strong>No symbols match this view.</strong>
            <p>
              {report.nodes.length
                ? "Try a different name or include module dependencies."
                : "These snapshots contain no indexed Python symbols."}
            </p>
            {report.nodes.length > 0 && (
              <button
                className="secondary"
                onClick={() => {
                  setQuery("");
                  setShowModules(true);
                }}
              >
                Show all symbols
              </button>
            )}
          </div>
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
          {recommendation ? " · cobalt: selected evidence path" : ""}
        </small>
      </div>
    </>
  );
}
