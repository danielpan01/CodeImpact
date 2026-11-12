import type { Report } from "./types";
import { Icon } from "./Icon";

export function TestsView({
  report,
  selected,
  onSelect,
  onChanges,
}: {
  report: Report;
  selected: string | null;
  onSelect: (id: string) => void;
  onChanges: () => void;
}) {
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
    <div className="test-list">
      <div className="list-columns" aria-hidden="true">
        <span>Test / supporting evidence</span>
        <span>Heuristic priority</span>
      </div>
      {report.recommendations.map((r, index) => (
        <button
          key={r.symbol}
          className={`test-row ${selected === r.symbol ? "selected" : ""}`}
          aria-pressed={selected === r.symbol}
          onClick={() => onSelect(r.symbol)}
        >
          <span className="test-order" aria-hidden="true">
            {String(index + 1).padStart(2, "0")}
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
        All {report.recommendations.length} recommendations · original analysis
        order
      </p>
    </div>
  );
}
