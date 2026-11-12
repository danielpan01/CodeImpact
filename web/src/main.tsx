import {
  StrictMode,
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
} from "react";
import { createRoot } from "react-dom/client";
import "@xyflow/react/dist/style.css";
import "./style.css";
import type { Report } from "./types";
import { AnalysisError, getReport } from "./api";
import { Icon } from "./Icon";
import { AnalysisInput } from "./AnalysisInput";
import { ReportContext } from "./ReportContext";
import { TestsView } from "./TestsView";
import { DependencyMap } from "./DependencyMap";
import { ChangesView } from "./ChangesView";
import { EvidenceInspector } from "./EvidenceInspector";
import { defaultTestControls } from "./test-review";
import type { Viewport } from "@xyflow/react";
import { useTheme } from "./theme";

type View = "tests" | "graph" | "changes";
function App() {
  const { theme, toggleTheme } = useTheme();
  const [report, setReport] = useState<Report | null>(null);
  const [kind, setKind] = useState<"demo" | "snapshots" | "github">("demo");
  const [selected, setSelected] = useState<string | null>(null);
  const [selectedChange, setSelectedChange] = useState<string | null>(null);
  const [showModules, setShowModules] = useState(false);
  const [query, setQuery] = useState("");
  const [testControls, setTestControls] = useState(defaultTestControls);
  const [focusedPath, setFocusedPath] = useState<string | null>(null);
  const mapViewport = useRef<Viewport | null>(null);
  const [error, setError] = useState("");
  const [errorKind, setErrorKind] = useState<AnalysisError["kind"]>("response");
  const [retrySnapshot, setRetrySnapshot] = useState<unknown>(undefined);
  const [snapshotError, setSnapshotError] = useState(false);
  const [busy, setBusy] = useState(false);
  const [view, setView] = useState<View>("tests");
  const [inputOpen, setInputOpen] = useState(true);
  const [evidenceOpen, setEvidenceOpen] = useState(false);
  const [prUrl, setPrUrl] = useState("");
  const [retryPR, setRetryPR] = useState<string | null>(null);
  const explorer = useRef<HTMLElement>(null);
  const evidenceHeading = useRef<HTMLHeadingElement>(null);
  const prInput = useRef<HTMLInputElement>(null);
  const snapshotButton = useRef<HTMLButtonElement>(null);
  const errorMessage = useRef<HTMLDivElement>(null);
  const newAnalysis = useRef<HTMLButtonElement>(null);
  const evidenceTrigger = useRef<HTMLElement | null>(null);
  const requestVersion = useRef(0);

  // Move focus after React commits the destination, never before it is mounted.
  const [focusRequest, setFocusRequest] = useState<{
    target:
      | "loaded"
      | "input"
      | "snapshot"
      | "evidence"
      | "explorer"
      | "back"
      | "error";
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
      case "snapshot":
        snapshotButton.current?.focus();
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
  useEffect(() => {
    const media = window.matchMedia("(max-width: 1100px)");
    let inspectorHadFocus = false;
    const trackFocus = (event: FocusEvent) => {
      // Some engines blur a focused element as soon as its pane becomes hidden,
      // before the media-query event arrives. Retain the last real focus target.
      if (event.target !== document.body)
        inspectorHadFocus = !!evidenceHeading.current
          ?.closest("aside")
          ?.contains(event.target as Node);
    };
    const retainFocus = () => {
      const inspector = evidenceHeading.current?.closest("aside");
      if (
        media.matches &&
        inspectorHadFocus &&
        inspector &&
        !inspector.getClientRects().length
      ) {
        setEvidenceOpen(true);
        setFocusRequest({ target: "evidence" });
      }
    };
    document.addEventListener("focusin", trackFocus);
    media.addEventListener("change", retainFocus);
    // WebKit can coalesce rapid breakpoint changes into one resize without a
    // media-query change event. Recover only when the focused pane became hidden.
    window.addEventListener("resize", retainFocus);
    return () => {
      document.removeEventListener("focusin", trackFocus);
      media.removeEventListener("change", retainFocus);
      window.removeEventListener("resize", retainFocus);
    };
  }, []);

  async function load(body?: unknown, githubUrl?: string) {
    const version = ++requestVersion.current;
    setBusy(true);
    setError("");
    setErrorKind("response");
    setSnapshotError(body !== undefined);
    setRetrySnapshot(body);
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
      setShowModules(false);
      setTestControls(defaultTestControls);
      setFocusedPath(null);
      mapViewport.current = null;
      setView("tests");
      setInputOpen(false);
      setRetrySnapshot(undefined);
      setFocusRequest({ target: "loaded" });
    } catch (e) {
      if (version !== requestVersion.current) return;
      setError(e instanceof Error ? e.message : "Could not load analysis");
      setErrorKind(e instanceof AnalysisError ? e.kind : "response");
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
    setInputOpen(true);
    setRetrySnapshot(undefined);
    setSnapshotError(true);
    try {
      if (file.size > 6_000_000) throw new Error("Snapshot file exceeds 6 MB.");
      let body: unknown;
      try {
        body = JSON.parse(await file.text());
      } catch {
        throw new Error(
          "This file is not valid JSON. Choose a snapshot pair with base.files and head.files objects.",
        );
      }
      if (version === requestVersion.current) await load(body);
    } catch (e) {
      if (version !== requestVersion.current) return;
      setReport(null);
      setSelected(null);
      setSelectedChange(null);
      setRetryPR(null);
      setEvidenceOpen(false);
      setError(e instanceof Error ? e.message : "Invalid JSON");
      setErrorKind("input");
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
          <button
            className="theme-toggle"
            aria-label={`Switch to ${theme === "light" ? "dark" : "light"} theme`}
            title="Switch light or dark appearance"
            onClick={toggleTheme}
          >
            <Icon name={theme === "light" ? "moon" : "sun"} />
            <span>{theme === "light" ? "Dark" : "Light"}</span>
          </button>
          <a
            href="/docs"
            target="_blank"
            rel="noreferrer"
            aria-label="API reference"
          >
            <span className="top-link-label">API reference</span>{" "}
            <Icon name="external" />
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
          <div
            role="status"
            aria-live="polite"
            aria-atomic="true"
            className="analysis-status"
          >
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
              <strong>
                {
                  {
                    network: "Connection unavailable",
                    limited: "Request temporarily limited",
                    input: "Check your analysis input",
                    response: "Analysis could not complete",
                  }[errorKind]
                }
              </strong>
              <p>{error}</p>
            </div>
            <div className="recovery-actions">
              <button
                className="secondary"
                onClick={() => {
                  setInputOpen(true);
                  setFocusRequest({
                    target: snapshotError ? "snapshot" : "input",
                  });
                }}
              >
                {snapshotError ? "Choose a snapshot" : "Edit PR URL"}
              </button>
              <button
                className="secondary"
                disabled={busy}
                onClick={() => void load(retrySnapshot, retryPR ?? undefined)}
              >
                {retryPR
                  ? "Retry GitHub PR"
                  : retrySnapshot !== undefined
                    ? "Retry snapshots"
                    : "Retry demo"}
              </button>
            </div>
          </div>
        )}
        <div
          id="analysis-entry"
          hidden={!inputOpen}
          aria-busy={busy}
          onKeyDown={(event) => {
            if (event.key === "Escape" && report && !busy) {
              setInputOpen(false);
              newAnalysis.current?.focus();
            }
          }}
        >
          <AnalysisInput
            busy={busy}
            prUrl={prUrl}
            setPrUrl={setPrUrl}
            onPR={() => void load(undefined, prUrl.trim())}
            onDemo={() => void load()}
            onUpload={(file) => void upload(file)}
            inputRef={prInput}
            snapshotButtonRef={snapshotButton}
            invalidPR={!!error && !snapshotError && errorKind === "input"}
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
                    controls={testControls}
                    setControls={setTestControls}
                    report={report}
                    selected={selected}
                    onSelect={showEvidence}
                    onChanges={() =>
                      openCode(selectedChange ?? report.changed[0] ?? null)
                    }
                  />
                ) : view === "graph" ? (
                  <DependencyMap
                    theme={theme}
                    focusedPath={focusedPath}
                    setFocusedPath={setFocusedPath}
                    viewport={mapViewport}
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
                focusPath={(id) => {
                  setFocusedPath(id);
                  mapViewport.current = null;
                  changeView("graph");
                  setFocusRequest({ target: "explorer" });
                }}
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
