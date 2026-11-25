import { useEffect, useRef, useState } from "react";
import { Icon } from "./Icon";
import {
  decisionAt,
  downloadFile,
  readDecisions,
  reviewKey,
  reviewMarkdown,
  reviewRevisions,
  reviewStatuses,
  saveDecisions,
  type ReviewDecisions,
  type ReviewStatus,
} from "./review-plan";
import type { Report } from "./types";
import "./review-plan.css";

const pageSize = 40;
const statuses = Object.keys(reviewStatuses) as ReviewStatus[];
type Filter = "all" | ReviewStatus;

export function ReviewPlan({
  report,
  onInspect,
}: {
  report: Report;
  onInspect: (id: string) => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const launcher = useRef<HTMLButtonElement>(null);
  const closeButton = useRef<HTMLButtonElement>(null);
  const inspecting = useRef(false);
  const [open, setOpen] = useState(false);
  const [decisions, setDecisions] = useState<ReviewDecisions>({});
  const [key, setKey] = useState<string | null>(null);
  const [storage, setStorage] = useState<"loading" | "saved" | "temporary">(
    "loading",
  );
  const [filter, setFilter] = useState<Filter>("all");
  const [search, setSearch] = useState("");
  const [limit, setLimit] = useState(pageSize);
  const [selected, setSelected] = useState(0);
  const { recommendations } = report;

  useEffect(() => {
    let current = true;
    const handleStorage = () => {
      if (!key) return;
      try {
        setDecisions(readDecisions(key, recommendations.length));
      } catch {
        setStorage("temporary");
      }
    };
    if (key && storage === "saved") {
      window.addEventListener("storage", handleStorage);
    } else if (open && storage === "loading")
      reviewKey(report)
        .then((digest) => {
          if (!current) return;
          setDecisions(readDecisions(digest, recommendations.length));
          setKey(digest);
          setStorage("saved");
        })
        .catch(() => {
          if (current) setStorage("temporary");
        });
    return () => {
      current = false;
      window.removeEventListener("storage", handleStorage);
    };
  }, [key, open, recommendations.length, report, storage]);

  useEffect(() => {
    if (open && !dialog.current?.open) {
      dialog.current?.showModal();
      closeButton.current?.focus();
    }
  }, [open]);

  function setDecision(index: number, status: ReviewStatus) {
    const update = (previous: ReviewDecisions) => {
      const next = { ...previous };
      if (status === "pending") delete next[index];
      else next[index] = status;
      return next;
    };
    let next = update(decisions);
    if (key && storage === "saved") {
      try {
        next = update(readDecisions(key, recommendations.length));
        saveDecisions(key, next);
      } catch {
        setStorage("temporary");
      }
    }
    setDecisions(next);
  }

  const items = open
    ? recommendations.map((test, index) => ({
        test,
        index,
        status: decisionAt(decisions, index),
      }))
    : [];
  const counts = { pending: 0, followUp: 0, reviewed: 0 };
  for (const item of items) counts[item.status]++;
  const terms = search.toLowerCase().trim().split(/\s+/);
  const visible = items.filter(
    ({ test, status }) =>
      (filter === "all" || filter === status) &&
      terms.every((term) => test.symbol.toLowerCase().includes(term)),
  );
  const visiblePage = visible.slice(0, limit);
  const focused =
    visiblePage.find(({ index }) => index === selected) ?? visiblePage[0];
  const pending = items.find(({ status }) => status === "pending");

  return (
    <>
      <button
        className="secondary review-plan-trigger"
        aria-haspopup="dialog"
        aria-label="Review plan"
        ref={launcher}
        onClick={() => setOpen(true)}
      >
        <Icon name="tests" />
        <span className="review-plan-trigger-full">Review plan</span>
        <span className="review-plan-trigger-short">Plan</span>
      </button>
      <dialog
        ref={dialog}
        className="review-plan-dialog"
        aria-labelledby="review-plan-title"
        onClose={() => {
          setOpen(false);
          if (!inspecting.current) launcher.current?.focus();
          inspecting.current = false;
        }}
      >
        {open && (
          <>
            <header className="review-plan-heading">
              <div className="review-plan-icon">
                <Icon name="tests" />
              </div>
              <div>
                <h2 id="review-plan-title">Review plan</h2>
                <p>{report.label}</p>
              </div>
              <button
                type="button"
                className="icon-button"
                aria-label="Close review plan"
                ref={closeButton}
                onClick={() => dialog.current?.close()}
              >
                <Icon name="close" />
              </button>
            </header>
            <div className="review-plan-summary">
              <div className="review-plan-progress">
                <label>
                  <strong role="status">
                    {counts.reviewed} of {recommendations.length} reviewed
                  </strong>
                  <progress
                    aria-label="Evidence review progress"
                    value={counts.reviewed}
                    max={recommendations.length || 1}
                  />
                </label>
                <p>
                  {counts.pending} pending · {counts.followUp} follow-up
                </p>
              </div>
              <button
                className="primary"
                disabled={!pending || storage === "loading"}
                onClick={() => {
                  if (!pending) return;
                  setFilter("pending");
                  setSearch("");
                  setLimit(pageSize);
                  setSelected(pending.index);
                }}
              >
                Next pending <Icon name="arrow" />
              </button>
            </div>
            <div className="review-plan-body">
              <section className="review-plan-queue" aria-label="Review queue">
                <div className="review-plan-controls">
                  <input
                    type="search"
                    aria-label="Search review plan"
                    placeholder="Find a test or file…"
                    value={search}
                    onChange={(event) => {
                      setSearch(event.target.value);
                      setLimit(pageSize);
                    }}
                  />
                  <select
                    aria-label="Review status"
                    value={filter}
                    onChange={(event) => {
                      setFilter(event.target.value as Filter);
                      setLimit(pageSize);
                    }}
                  >
                    <option value="all">All statuses</option>
                    {statuses.map((status) => (
                      <option key={status} value={status}>
                        {reviewStatuses[status]} ({counts[status]})
                      </option>
                    ))}
                  </select>
                </div>
                {visible.length > 0 ? (
                  <ul className="review-plan-list">
                    {visiblePage.map(({ test, index, status }) => {
                      const [path, name] = test.symbol.split("::");
                      return (
                        <li key={test.symbol}>
                          <button
                            type="button"
                            aria-pressed={focused?.index === index}
                            onClick={() => setSelected(index)}
                          >
                            <span>
                              <strong>{name ?? test.symbol}</strong>
                              <code>{path}</code>
                            </span>
                            <small className={`review-status ${status}`}>
                              {reviewStatuses[status]}
                            </small>
                          </button>
                        </li>
                      );
                    })}
                  </ul>
                ) : (
                  <p className="review-plan-empty">
                    {recommendations.length
                      ? "No tests match this search and status."
                      : "This report has no recommended tests."}
                  </p>
                )}
                {visible.length > limit && (
                  <button
                    className="text-button review-plan-more"
                    onClick={() => setLimit((value) => value + pageSize)}
                  >
                    Show {Math.min(pageSize, visible.length - limit)} more
                  </button>
                )}
              </section>
              {focused && (
                <section
                  className="review-plan-evidence"
                  aria-label="Plan evidence"
                >
                  <div className="review-plan-test-heading">
                    <div>
                      <h3>{focused.test.symbol.split("::").at(-1)}</h3>
                      <p>{focused.test.reason}</p>
                    </div>
                    <span className="review-plan-score">
                      <strong>{focused.test.score}</strong>
                      <small>Priority</small>
                    </span>
                  </div>
                  <div className="review-plan-revision">
                    <Icon name="branch" />
                    {reviewRevisions[focused.test.path_revision]}
                  </div>
                  <ol
                    className="review-plan-path"
                    aria-label="Dependency path"
                    tabIndex={0}
                  >
                    {focused.test.evidence_path.map((id) => (
                      <li key={id}>
                        <strong>{id.split("::").at(-1)}</strong>
                        <code>{id.split("::")[0]}</code>
                      </li>
                    ))}
                  </ol>
                  <div className="review-plan-decision">
                    <button
                      className="primary"
                      disabled={storage === "loading"}
                      onClick={() =>
                        setDecision(
                          focused.index,
                          focused.status === "reviewed"
                            ? "pending"
                            : "reviewed",
                        )
                      }
                    >
                      {focused.status === "reviewed"
                        ? "Return to pending"
                        : "Mark reviewed"}
                    </button>
                    <button
                      className="secondary"
                      disabled={storage === "loading"}
                      onClick={() =>
                        setDecision(
                          focused.index,
                          focused.status === "followUp"
                            ? "pending"
                            : "followUp",
                        )
                      }
                    >
                      {focused.status === "followUp"
                        ? "Clear follow-up"
                        : "Flag follow-up"}
                    </button>
                  </div>
                  <button
                    className="text-button"
                    onClick={() => {
                      inspecting.current = true;
                      dialog.current?.close();
                      onInspect(focused.test.symbol);
                    }}
                  >
                    Open full evidence <Icon name="arrow" />
                  </button>
                </section>
              )}
            </div>
            <footer className="review-plan-footer">
              <p>
                {storage === "saved"
                  ? "Decisions are saved in this browser."
                  : storage === "temporary"
                    ? "Decisions are kept while this report is open."
                    : "Loading saved decisions…"}
                <span> Keep the full suite as your merge gate.</span>
              </p>
              <button
                className="secondary"
                disabled={storage === "loading"}
                onClick={() =>
                  downloadFile(
                    "codeimpact-review-plan.md",
                    reviewMarkdown(report, decisions),
                    "text/markdown;charset=utf-8",
                  )
                }
              >
                <Icon name="download" /> Download Markdown
              </button>
            </footer>
          </>
        )}
      </dialog>
    </>
  );
}
