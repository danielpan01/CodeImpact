import { StrictMode, useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  Background,
  Controls,
  MarkerType,
  Position,
  ReactFlow,
  type Node,
  type Edge,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import "./style.css";
import type { Report } from "./types";

async function getReport(url: string, body?: unknown): Promise<Report> {
  const response = await fetch(
    url,
    body
      ? {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        }
      : {},
  );
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(
      typeof data.detail === "string"
        ? data.detail
        : `Analysis rejected (${response.status}). Check your snapshot format and limits.`,
    );
  }
  return response.json();
}

function App() {
  const [report, setReport] = useState<Report | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [showModules, setShowModules] = useState(false);
  const [query, setQuery] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(true);
  const [revision, setRevision] = useState(0);
  const [view, setView] = useState<"graph" | "tests">("graph");

  async function load(body?: unknown) {
    setBusy(true);
    setError("");
    try {
      const next = await getReport(body ? "/api/analyze" : "/api/demo", body);
      setReport(next);
      setSelected(next.recommendations[0]?.symbol ?? null);
      setRevision((n) => n + 1);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not load analysis");
    } finally {
      setBusy(false);
    }
  }
  useEffect(() => {
    void load();
  }, []);

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
        ?.evidence_path ?? [];
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
      };
    });
    const edges: Edge[] = report.edges
      .filter((e) => ids.has(e.source) && ids.has(e.target))
      .map((e, i) => {
        const a = evidence.indexOf(e.source),
          highlighted = a >= 0 && evidence[a + 1] === e.target;
        return {
          id: `${i}-${e.kind}`,
          source: e.source,
          target: e.target,
          animated: highlighted,
          markerEnd: { type: MarkerType.ArrowClosed },
          style: {
            stroke: highlighted ? "#51e0b2" : "#58726d",
            strokeWidth: highlighted ? 3 : 1.5,
            strokeDasharray: e.kind === "call" ? undefined : "5 4",
          },
        };
      });
    return { nodes, edges };
  }, [report, selected, showModules, query]);

  const symbol = report?.nodes.find((n) => n.id === selected);
  const recommendation = report?.recommendations.find(
    (r) => r.symbol === selected,
  );
  const changedCount =
    report?.nodes.filter(
      (n) => n.kind !== "module" && report.changed.includes(n.id),
    ).length ?? 0;

  function download() {
    if (!report) return;
    const url = URL.createObjectURL(
      new Blob([JSON.stringify(report, null, 2)], { type: "application/json" }),
    );
    const a = document.createElement("a");
    a.href = url;
    a.download = "codeimpact-report.json";
    a.click();
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a className="brand" href="/" aria-label="CodeImpact home">
          <span className="brand-mark">ci</span> CodeImpact
        </a>
        <div className="workspace-label">DEVELOPER WORKSPACE</div>
        <button
          className={view === "graph" ? "nav active" : "nav"}
          onClick={() => setView("graph")}
        >
          <span>◉</span> Impact explorer
        </button>
        <button
          className={view === "tests" ? "nav active" : "nav"}
          onClick={() => setView("tests")}
        >
          <span>✓</span> Recommended tests{" "}
          <b>{report?.recommendations.length ?? 0}</b>
        </button>
        <div className="sidebar-bottom">
          <span className="status-dot" /> Local analysis
          <br />
          <small>Python · static evidence</small>
          <p>
            Know what changed.
            <br />
            Understand what follows.
          </p>
        </div>
      </aside>
      <main>
        <header>
          <span>
            Workspace <span className="muted">/</span>{" "}
            <strong>Change analysis</strong>
          </span>
          <span className="version">
            MVP 0.1 <span className="status-dot" />
          </span>
        </header>
        <section className="page-heading">
          <div>
            <div className="eyebrow">BEFORE YOU MERGE</div>
            <h1>Know your blast radius.</h1>
            <p>
              Trace a code change to the functions and tests that depend on it.
            </p>
          </div>
          <button className="secondary" onClick={download} disabled={!report}>
            ↓ Export report
          </button>
        </section>
        <section className="analysis-bar">
          <div>
            <span className="repo-icon">⌘</span>
            <span className="analysis-label">
              {busy
                ? "Analyzing Python snapshots…"
                : (report?.label ?? "Ready for analysis")}
              <small>AST comparison · base + head dependency graph</small>
            </span>
          </div>
          <div className="actions">
            <button
              className="secondary"
              disabled={busy}
              onClick={() => void load()}
            >
              Load demo
            </button>
            <label className={`primary upload ${busy ? "disabled" : ""}`}>
              ↑ Analyze snapshots
              <input
                aria-label="Upload snapshot JSON"
                type="file"
                accept=".json,application/json"
                disabled={busy}
                onChange={async (event) => {
                  const file = event.target.files?.[0];
                  if (!file) return;
                  try {
                    if (file.size > 6_000_000)
                      throw new Error("Snapshot file exceeds 6 MB.");
                    await load(JSON.parse(await file.text()));
                  } catch (e) {
                    setError(e instanceof Error ? e.message : "Invalid JSON");
                  }
                  event.target.value = "";
                }}
              />
            </label>
          </div>
        </section>
        {error && (
          <div className="error" role="alert">
            {error} <button onClick={() => void load()}>Retry demo</button>
          </div>
        )}
        <section className="metrics">
          <div>
            <span>Changed symbols</span>
            <strong className="coral">
              {changedCount.toString().padStart(2, "0")}
            </strong>
            <small>AST changes, excluding modules</small>
          </div>
          <div>
            <span>Potentially affected</span>
            <strong className="amber">{report?.stats.impacted ?? "—"}</strong>
            <small>Dependent symbols + modules</small>
          </div>
          <div>
            <span>Tests to prioritize</span>
            <strong className="mint">
              {report?.recommendations.length ?? "—"}
            </strong>
            <small>Ranked with traceable evidence</small>
          </div>
          <div>
            <span>Analysis time</span>
            <strong>
              {report?.stats.elapsed_ms ?? "—"}
              <em>ms</em>
            </strong>
            <small>Measured for this analysis</small>
          </div>
        </section>
        <div className="explorer-layout">
          <section className="graph-panel">
            <div className="panel-heading">
              <div>
                <h2>
                  {view === "graph" ? "Dependency map" : "Recommended tests"}
                </h2>
                <span>
                  {view === "graph"
                    ? "Select a test to reveal its evidence path"
                    : "Priority scores are heuristics, not failure probabilities"}
                </span>
              </div>
              <div className="view-toggle" aria-label="Explorer view">
                <button
                  aria-pressed={view === "graph"}
                  onClick={() => setView("graph")}
                >
                  Map
                </button>
                <button
                  aria-pressed={view === "tests"}
                  onClick={() => setView("tests")}
                >
                  Tests
                </button>
              </div>
            </div>
            {view === "graph" ? (
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
                <div className="graph-canvas" data-testid="dependency-graph">
                  <ReactFlow
                    key={`${revision}-${showModules}-${query}`}
                    nodes={graph.nodes}
                    edges={graph.edges}
                    fitView
                    fitViewOptions={{ padding: 0.18 }}
                    minZoom={0.25}
                    nodesDraggable={false}
                    nodesConnectable={false}
                    onNodeClick={(_, n) => setSelected(n.id)}
                    colorMode="dark"
                  >
                    <Background color="#263b36" gap={22} />
                    <Controls showInteractive={false} />
                  </ReactFlow>
                  {!busy && !graph.nodes.length && (
                    <div className="empty-graph">
                      No symbols match this view.
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
                    Arrows: caller → dependency · dashed: module fallback
                  </small>
                </div>
              </>
            ) : (
              <div className="test-list">
                {report?.recommendations.length ? (
                  report.recommendations.map((r) => (
                    <button
                      key={r.symbol}
                      className={`test-row ${selected === r.symbol ? "selected" : ""}`}
                      onClick={() => setSelected(r.symbol)}
                    >
                      <strong>{r.symbol.split("::")[1]}</strong>
                      <span>{r.reason}</span>
                      <b>{r.score}</b>
                    </button>
                  ))
                ) : (
                  <p>No tests were selected. This does not establish safety.</p>
                )}
              </div>
            )}
          </section>
          <aside className="detail-panel">
            <div className="panel-heading">
              <div>
                <div className="eyebrow">FOLLOW THE EVIDENCE</div>
                <h2>Why this matters</h2>
              </div>
            </div>
            {symbol ? (
              <div className="detail-content">
                <span className="pill">{symbol.kind}</span>
                <h3>{symbol.name}</h3>
                <code>
                  {symbol.path}:{symbol.line}
                </code>
                {recommendation ? (
                  <>
                    <div className="risk-score">
                      <strong>
                        {recommendation.score}
                        <small>/100</small>
                      </strong>
                      <span>
                        Test priority
                        <br />
                        <small>Heuristic score</small>
                      </span>
                    </div>
                    <p>{recommendation.reason}</p>
                    <ol className="evidence-path">
                      {recommendation.evidence_path.map((id, i) => (
                        <li key={id}>
                          <span>
                            {i === 0
                              ? "TEST"
                              : i === recommendation.evidence_path.length - 1
                                ? "CHANGED"
                                : "DEPENDS ON"}
                          </span>
                          <strong>{id.split("::")[1]}</strong>
                          <small>{id.split("::")[0]}</small>
                        </li>
                      ))}
                    </ol>
                  </>
                ) : (
                  <>
                    <p>
                      {report?.changed.includes(symbol.id)
                        ? "This symbol changed between snapshots."
                        : report?.impacted.includes(symbol.id)
                          ? "A dependency path reaches a changed symbol."
                          : "No path to a changed symbol was found in this static graph."}
                    </p>
                    <h4>Outgoing evidence</h4>
                    {report?.edges
                      .filter((e) => e.source === symbol.id)
                      .map((e, i) => (
                        <p className="edge-evidence" key={i}>
                          {e.evidence}
                        </p>
                      ))}
                  </>
                )}
              </div>
            ) : (
              <p className="detail-content">
                Select a symbol to inspect its dependencies.
              </p>
            )}
            <div className="confidence-note">
              Static evidence guides review. Keep the full test suite as your
              merge gate.
            </div>
          </aside>
        </div>
        <details className="limitations">
          <summary>
            Analysis scope & limitations{" "}
            <span>{report?.warnings.length ?? 0} notes</span>
          </summary>
          {report?.warnings.map((w) => (
            <p key={w}>{w}</p>
          ))}
        </details>
        <footer>
          CODEIMPACT <span>Understand the change. Make a better review.</span>
          <a href="http://127.0.0.1:8000/docs" target="_blank" rel="noreferrer">
            API reference ↗
          </a>
        </footer>
      </main>
    </div>
  );
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
