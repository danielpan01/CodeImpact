import { useMemo, type RefObject } from "react";
import type { Report } from "./types";
import { EdgeEvidence, PathRevision } from "./Evidence";
import { Icon } from "./Icon";

export function EvidenceInspector({
  report,
  selected,
  openCode,
  onBack,
  headingRef,
}: {
  report: Report;
  selected: string | null;
  openCode: (id: string) => void;
  onBack: () => void;
  headingRef: RefObject<HTMLHeadingElement | null>;
}) {
  const symbol = report.nodes.find((n) => n.id === selected);
  const recommendation = report.recommendations.find(
    (r) => r.symbol === selected,
  );
  const edgesById = useMemo(
    () => new Map(report.edges.map((e) => [e.id, e])),
    [report],
  );
  return (
    <aside className="detail-panel" aria-label="Evidence inspector">
      <div className="inspector-heading">
        <h2 ref={headingRef} tabIndex={-1}>
          <Icon name="evidence" /> Evidence
        </h2>
        <button className="secondary evidence-back" onClick={onBack}>
          <Icon name="back" /> Back to results
        </button>
      </div>
      <div className="inspector-scroll">
        {symbol ? (
          <div className="detail-content">
            <span className="eyebrow">Selected {symbol.kind}</span>
            <h3>{symbol.name}</h3>
            <code className="symbol-location">
              {symbol.path}:{symbol.line}
            </code>
            {recommendation ? (
              <>
                <div className="recommendation-reason">
                  <span className="eyebrow">Why this test</span>
                  <h4>{recommendation.reason}</h4>
                  <PathRevision recommendation={recommendation} />
                </div>
                <button
                  className="primary open-code"
                  onClick={() => openCode(recommendation.evidence_path.at(-1)!)}
                >
                  Open changed code <Icon name="arrow" />
                </button>
                <h4 className="trail-heading">
                  Dependency trail <small>test → changed dependency</small>
                </h4>
                <ol className="evidence-path">
                  {recommendation.evidence_path.map((id, i) => (
                    <li key={id}>
                      <span className="trail-role">
                        {i === 0
                          ? "Test"
                          : i === recommendation.evidence_path.length - 1
                            ? "Changed dependency"
                            : "Depends on"}
                      </span>
                      <strong>{id.split("::")[1]}</strong>
                      <small>{id.split("::")[0]}</small>
                      {edgesById.get(recommendation.evidence_edges[i]) && (
                        <EdgeEvidence
                          edge={edgesById.get(
                            recommendation.evidence_edges[i],
                          )!}
                        />
                      )}
                    </li>
                  ))}
                </ol>
                <div className="risk-score">
                  <span>
                    Heuristic priority{" "}
                    <small>Review priority, not failure probability</small>
                  </span>
                  <strong>
                    {recommendation.score}
                    <small>/100</small>
                  </strong>
                </div>
              </>
            ) : (
              <>
                <p>
                  {report.changed.includes(symbol.id)
                    ? "This symbol changed between snapshots."
                    : report.impacted.includes(symbol.id)
                      ? "A dependency path reaches a changed symbol."
                      : "No path to a changed symbol was found in this static graph."}
                </p>
                {report.changed.includes(symbol.id) && (
                  <button
                    className="primary"
                    onClick={() => openCode(symbol.id)}
                  >
                    Open changed code <Icon name="arrow" />
                  </button>
                )}
                <h4>Outgoing evidence</h4>
                {report.edges
                  .filter((e) => e.source === symbol.id)
                  .map((e) => (
                    <EdgeEvidence edge={e} key={e.id} />
                  ))}
              </>
            )}
          </div>
        ) : (
          <div className="empty-state">
            <Icon name="evidence" />
            <h3>Select a test or symbol</h3>
            <p>
              Inspect its explanation, dependency trail and source evidence
              here.
            </p>
          </div>
        )}
      </div>
      <div className="confidence-note">
        <Icon name="shield" /> Static evidence guides review. Keep the full test
        suite as your merge gate.
      </div>
    </aside>
  );
}
