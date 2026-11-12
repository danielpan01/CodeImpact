import { StrictMode, useLayoutEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import "@xyflow/react/dist/style.css";
import "./style.css";
import type { Report } from "./types";
import { getReport } from "./api";
import { Icon } from "./Icon";
import { AnalysisInput } from "./AnalysisInput";
import { ReportContext } from "./ReportContext";
import { TestsView } from "./TestsView";
import { DependencyMap } from "./DependencyMap";
import { ChangesView } from "./ChangesView";
import { EvidenceInspector } from "./EvidenceInspector";

type View = "tests" | "graph" | "changes";
function App() {
  const [report, setReport] = useState<Report | null>(null);
  const [kind, setKind] = useState<"demo" | "snapshots" | "github">("demo");
  const [selected, setSelected] = useState<string | null>(null);
  const [selectedChange, setSelectedChange] = useState<string | null>(null);
  const [showModules, setShowModules] = useState(false);
  const [query, setQuery] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [view, setView] = useState<View>("tests");
  const [inputOpen, setInputOpen] = useState(true);
  const [evidenceOpen, setEvidenceOpen] = useState(false);
  const [prUrl, setPrUrl] = useState("");
  const [retryPR, setRetryPR] = useState<string | null>(null);
  const explorer = useRef<HTMLElement>(null);
  const evidenceHeading = useRef<HTMLHeadingElement>(null);
  const prInput = useRef<HTMLInputElement>(null);
  const errorMessage = useRef<HTMLDivElement>(null);
  const newAnalysis = useRef<HTMLButtonElement>(null);
  const evidenceTrigger = useRef<HTMLElement | null>(null);
  const requestVersion = useRef(0);

  // Move focus after React commits the destination, never before it is mounted.
  const [focusRequest, setFocusRequest] = useState<{
    target: "loaded" | "input" | "evidence" | "explorer" | "back" | "error";
  } | null>(null);
  useLayoutEffect(() => {
    const compact = window.matchMedia("(max-width: 1100px)").matches;
    switch (focusRequest?.target) {
      case "loaded":
        explorer.current?.focus({ preventScroll: true });
        window.scrollTo({ top: 0 });
        break;
      case "input":
        prInput.current?.focus();
        break;
      case "error":
        errorMessage.current?.focus();
        break;
      case "evidence":
        if (compact) {
          evidenceHeading.current?.focus({ preventScroll: true });
          document
            .getElementById("review-workspace")
            ?.scrollIntoView({ block: "start" });
        }
        break;
      case "explorer":
        explorer.current?.focus({ preventScroll: true });
        if (compact)
          document
            .getElementById("review-workspace")
            ?.scrollIntoView({ block: "start" });
        break;
      case "back": {
        const trigger = evidenceTrigger.current;
        if (trigger?.isConnected && trigger.getClientRects().length)
          trigger.focus();
        else explorer.current?.focus();
        break;
      }
    }
  }, [focusRequest]);

  async function load(body?: unknown, githubUrl?: string) {
    const version = ++requestVersion.current;
    setBusy(true);
    setError("");
    setReport(null);
    setSelected(null);
    setSelectedChange(null);
    setEvidenceOpen(false);
    setInputOpen(true);
    setRetryPR(githubUrl ?? null);
    try {
      const next = await getReport(
        githubUrl
          ? "/api/github/pr"
          : body !== undefined
            ? "/api/analyze"
            : "/api/demo",
        githubUrl ? { url: githubUrl } : body,
      );
      if (version !== requestVersion.current) return;
      setReport(next);
      setKind(githubUrl ? "github" : body !== undefined ? "snapshots" : "demo");
      setSelected(next.recommendations[0]?.symbol ?? null);
      setSelectedChange(
        next.recommendations[0]?.evidence_path.at(-1) ??
          next.changed[0] ??
          null,
      );
      setQuery("");
      setView("tests");
      setInputOpen(false);
      setFocusRequest({ target: "loaded" });
    } catch (e) {
      if (version !== requestVersion.current) return;
      setError(e instanceof Error ? e.message : "Could not load analysis");
      setFocusRequest({ target: "error" });
    } finally {
      if (version === requestVersion.current) setBusy(false);
    }
  }
  async function upload(file: File) {
    // Bound the upload before reading it. Python source stays JSON string data.
    const version = ++requestVersion.current;
    setBusy(true);
    setError("");
    try {
      if (file.size > 6_000_000) throw new Error("Snapshot file exceeds 6 MB.");
      const body: unknown = JSON.parse(await file.text());
      if (version === requestVersion.current) await load(body);
    } catch (e) {
      if (version !== requestVersion.current) return;
      setReport(null);
      setSelected(null);
      setSelectedChange(null);
      setRetryPR(null);
      setEvidenceOpen(false);
      setError(e instanceof Error ? e.message : "Invalid JSON");
      setFocusRequest({ target: "error" });
    } finally {
      if (version === requestVersion.current) setBusy(false);
    }
  }
  function showEvidence(id?: string) {
    evidenceTrigger.current = document.activeElement as HTMLElement;
    if (id) setSelected(id);
    setEvidenceOpen(true);
    setFocusRequest({ target: "evidence" });
  }
  function closeEvidence() {
    setEvidenceOpen(false);
    setFocusRequest({ target: "back" });
  }

  function changeView(next: View) {
    setView(next);
    setEvidenceOpen(false);
  }
  function openCode(id: string | null) {
    setSelectedChange(id);
    changeView("changes");
    setFocusRequest({ target: "explorer" });
  }

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
      <a className="skip-link" href="#review-workspace">
        Skip to workspace
      </a>
      <header className="topbar">
        <a className="brand" href="/" aria-label="CodeImpact home">
          <span className="brand-mark">
            <Icon name="branch" />
          </span>
          CodeImpact
        </a>
        <span className="nav-context">Developer workspace</span>
        <div className="top-actions">
          <span className="local-status">
            <i /> Local analysis
          </span>
          <a href="/docs" target="_blank" rel="noreferrer">
            API reference <Icon name="external" />
          </a>
        </div>
      </header>
      <main>
        <div className="workspace-bar">
          <span>
            Workspace <span className="separator">/</span>{" "}
            <strong>Change analysis</strong>
          </span>
          <div className="actions">
            <button
              className="secondary"
              ref={newAnalysis}
              disabled={busy || !report}
              aria-expanded={inputOpen}
              aria-controls="analysis-entry"
              onClick={() => {
                setInputOpen(true);
                setFocusRequest({ target: "input" });
              }}
            >
              <Icon name="plus" /> New analysis
            </button>
            <div className="export-action">
              <button
                className="secondary"
                onClick={download}
                disabled={!report || busy}
                aria-describedby="export-notice"
              >
                <Icon name="download" /> Export report
              </button>
              <small id="export-notice">Export includes source code</small>
            </div>
          </div>
        </div>
        {busy && (
          <div role="status" className="analysis-status">
            <Icon name="clock" />
            <div>
              <strong>
                {retryPR ? "Reading GitHub revisions…" : "Loading analysis…"}
              </strong>
              <p>
                {retryPR
                  ? "Fetching complete Python snapshots and analyzing dependencies…"
                  : "Comparing the before and after snapshots and tracing dependencies."}
              </p>
            </div>
          </div>
        )}
        {error && (
          <div className="error" role="alert" tabIndex={-1} ref={errorMessage}>
            <div>
              <strong>Analysis could not complete</strong>
              <p>{error}</p>
            </div>
            <button
              className="secondary"
              disabled={busy}
              onClick={() => void load(undefined, retryPR ?? undefined)}
            >
              {retryPR ? "Retry GitHub PR" : "Retry demo"}
            </button>
          </div>
        )}
        <div id="analysis-entry" hidden={!inputOpen}>
          <AnalysisInput
            busy={busy}
            prUrl={prUrl}
            setPrUrl={setPrUrl}
            onPR={() => void load(undefined, prUrl.trim())}
            onDemo={() => void load()}
            onUpload={(file) => void upload(file)}
            inputRef={prInput}
            onClose={
              report
                ? () => {
                    setInputOpen(false);
                    newAnalysis.current?.focus();
                  }
                : undefined
            }
          />
        </div>
        {report ? (
          <>
            <ReportContext report={report} kind={kind} />
            <div className="workspace-nav" id="review-workspace">
              <nav className="view-toggle" aria-label="Explorer view">
                {(
                  [
                    ["tests", "Tests", "tests"],
                    ["graph", "Map", "map"],
                    ["changes", "Changes", "code"],
                  ] as const
                ).map(([id, label, icon]) => (
                  <button
                    key={id}
                    aria-pressed={view === id}
                    aria-label={label}
                    onClick={() => changeView(id)}
                  >
                    <Icon name={icon} />
                    {label}
                    {id !== "graph" && (
                      <span className="view-count" aria-hidden="true">
                        {id === "tests"
                          ? report.recommendations.length
                          : report.changes.length}
                      </span>
                    )}
                  </button>
                ))}
              </nav>
              <button
                className="secondary evidence-toggle"
                aria-expanded={evidenceOpen}
                onClick={() =>
                  evidenceOpen ? closeEvidence() : showEvidence()
                }
              >
                <Icon name="evidence" />{" "}
                {evidenceOpen ? "Close evidence" : "View evidence"}
              </button>
              <span className="workspace-hint">
                Review the change. Follow the evidence.
              </span>
            </div>
            <div
              className={`explorer-layout ${evidenceOpen ? "evidence-open" : ""}`}
              onKeyDown={(event) => {
                if (event.key === "Escape" && evidenceOpen) {
                  event.stopPropagation();
                  closeEvidence();
                }
              }}
            >
              <section
                className="graph-panel"
                ref={explorer}
                tabIndex={-1}
                aria-label="Change explorer"
              >
                <div className="panel-heading">
                  <div>
                    <h2>
                      {view === "tests"
                        ? "Recommended tests"
                        : view === "graph"
                          ? "Dependency map"
                          : "Changed code"}
                    </h2>
                    <p>
                      {view === "tests"
                        ? "Prioritized by static evidence. Scores are heuristics, not failure probabilities."
                        : view === "graph"
                          ? "Select a symbol to inspect its dependencies and revision evidence."
                          : "Before and after · exact analyzed source"}
                    </p>
                  </div>
                  {view === "tests" && (
                    <span className="badge">
                      {report.recommendations.length} tests
                    </span>
                  )}
                </div>
                {view === "tests" ? (
                  <TestsView
                    report={report}
                    selected={selected}
                    onSelect={showEvidence}
                    onChanges={() =>
                      openCode(selectedChange ?? report.changed[0] ?? null)
                    }
                  />
                ) : view === "graph" ? (
                  <DependencyMap
                    report={report}
                    selected={selected}
                    onSelect={showEvidence}
                    query={query}
                    setQuery={setQuery}
                    showModules={showModules}
                    setShowModules={setShowModules}
                  />
                ) : (
                  <ChangesView
                    report={report}
                    selected={selectedChange}
                    onSelect={(id) => {
                      setSelectedChange(id);
                      setSelected(id);
                    }}
                  />
                )}
              </section>
              <EvidenceInspector
                report={report}
                selected={selected}
                openCode={openCode}
                onBack={closeEvidence}
                headingRef={evidenceHeading}
              />
            </div>
            <details className="limitations">
              <summary>
                Analysis scope & limitations{" "}
                <span>{report.warnings.length} notes</span>
              </summary>
              <p>
                Static Python analysis is incomplete. A missing dependency path
                does not establish safety.
              </p>
              {report.warnings.map((w) => (
                <p key={w}>{w}</p>
              ))}
            </details>
          </>
        ) : (
          <div id="review-workspace" />
        )}
        <footer>
          <span>
            CodeImpact <span className="separator">/</span> Explainable
            change-impact analysis
          </span>
          <span>Python · source as data</span>
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
