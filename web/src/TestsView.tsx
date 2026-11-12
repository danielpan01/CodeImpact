import { useLayoutEffect, useRef, useState } from "react";
import type { Report } from "./types";
import { Icon } from "./Icon";
import {
  categories,
  defaultTestControls,
  explanationCategory,
  reviewTests,
  type TestControls,
} from "./test-review";

export function TestsView({
  report,
  selected,
  onSelect,
  onChanges,
  controls,
  setControls,
}: {
  report: Report;
  selected: string | null;
  onSelect: (id: string) => void;
  onChanges: () => void;
  controls: TestControls;
  setControls: (controls: TestControls) => void;
}) {
  const visible = reviewTests(report.recommendations, controls);
  const ranks = new Map(
    report.recommendations.map((r, index) => [r.symbol, index + 1]),
  );
  const counts = new Map<string, number>();
  for (const r of report.recommendations) {
    const category = explanationCategory(r.reason);
    counts.set(category, (counts.get(category) ?? 0) + 1);
  }
  const selectedHidden =
    ranks.has(selected ?? "") && !visible.some((r) => r.symbol === selected);
  const active =
    controls.query !== "" ||
    controls.category !== "all" ||
    controls.sort !== "analysis";
  const selectedRow = useRef<HTMLButtonElement>(null);
  const [reveal, setReveal] = useState(0);
  useLayoutEffect(() => {
    if (reveal) selectedRow.current?.focus();
  }, [reveal]);
  if (!report.recommendations.length)
    return (
      <div className="empty-state">
        <Icon name="tests" />
        <h3>No tests recommended</h3>
        <p>
          No recommendation does not establish that tests are safe to skip.
          Review the changed code and keep the full suite as your merge gate.
        </p>
        <button className="primary" onClick={onChanges}>
          Review changed code <Icon name="arrow" />
        </button>
      </div>
    );
  return (
    <>
      <div
        className="test-toolbar"
        role="search"
        aria-label="Filter recommended tests"
      >
        <label className="test-search">
          <span>Search tests</span>
          <input
            type="search"
            value={controls.query}
            onChange={(e) =>
              setControls({ ...controls, query: e.target.value })
            }
            placeholder="Test or file name…"
          />
        </label>
        <label>
          <span>Explanation</span>
          <select
            aria-label="Explanation"
            value={controls.category}
            onChange={(e) =>
              setControls({
                ...controls,
                category: e.target.value as TestControls["category"],
              })
            }
          >
            <option value="all">All explanations</option>
            {Object.entries(categories)
              .filter(([key]) => counts.has(key))
              .map(([key, label]) => (
                <option key={key} value={key}>
                  {label} ({counts.get(key)})
                </option>
              ))}
          </select>
        </label>
        <label>
          <span>Sort tests</span>
          <select
            aria-label="Sort tests"
            value={controls.sort}
            onChange={(e) =>
              setControls({
                ...controls,
                sort: e.target.value as TestControls["sort"],
              })
            }
          >
            <option value="analysis">Analysis order</option>
            <option value="name">Test name A–Z</option>
            <option value="file">File name A–Z</option>
            <option value="priority">Priority: low to high</option>
          </select>
        </label>
      </div>
      <div className="results-bar">
        <span role="status">
          {visible.length} of {report.recommendations.length} tests
        </span>
        <button
          className="text-button"
          disabled={!active}
          onClick={() => setControls(defaultTestControls)}
        >
          Reset tests
        </button>
      </div>
      {selectedHidden && (
        <div className="selection-notice">
          <span>
            Selected test is outside these results. Its evidence is retained.
          </span>
          <button
            className="text-button"
            onClick={() => {
              setControls(defaultTestControls);
              setReveal((n) => n + 1);
            }}
          >
            Show selected test
          </button>
        </div>
      )}
      <div className="test-list">
        <div className="list-columns" aria-hidden="true">
          <span>Analysis rank / test / evidence</span>
          <span>Heuristic priority</span>
        </div>
        {!visible.length && (
          <div className="empty-state">
            <h3>No matching tests</h3>
            <p>Try another test or file name, or reset the filters.</p>
            <button
              className="secondary"
              onClick={() => setControls(defaultTestControls)}
            >
              Clear filters
            </button>
          </div>
        )}
        {visible.map((r) => (
          <button
            key={r.symbol}
            ref={selected === r.symbol ? selectedRow : undefined}
            data-symbol={r.symbol}
            className={`test-row ${selected === r.symbol ? "selected" : ""}`}
            aria-pressed={selected === r.symbol}
            onClick={() => onSelect(r.symbol)}
          >
            <span className="test-order" aria-hidden="true">
              {String(ranks.get(r.symbol)).padStart(2, "0")}
            </span>
            <span className="test-identity">
              <strong>{r.symbol.split("::")[1]}</strong>
              <code>{r.symbol.split("::")[0]}</code>
              <span
                className={`reason-label ${r.reason.startsWith("Conservative") ? "conservative" : "resolved"}`}
              >
                <Icon
                  name={
                    r.reason.startsWith("Conservative") ? "branch" : "evidence"
                  }
                />
                {r.reason}
              </span>
            </span>
            <span className="test-priority">
              <b>{r.score}</b>
              <small>Heuristic</small>
              <Icon name="arrow" />
            </span>
          </button>
        ))}
        <p className="list-note">
          Export always includes all {report.recommendations.length}{" "}
          recommendations in analysis order.
        </p>
      </div>
    </>
  );
}
