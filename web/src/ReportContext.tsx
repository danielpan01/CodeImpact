import type { Report } from "./types";
import { Icon } from "./Icon";
export function ReportContext({
  report,
  kind,
}: {
  report: Report;
  kind: "demo" | "snapshots" | "github";
}) {
  return (
    <>
      <section className="report-context" aria-label="Report context">
        <div className="context-icon">
          <Icon name="branch" />
        </div>
        <div>
          <div className="context-meta">
            <span className="eyebrow">Analysis workspace</span>
            <span className="badge">
              {kind === "demo"
                ? "Checkout demo"
                : kind === "github"
                  ? "Public GitHub PR"
                  : "Snapshot upload"}
            </span>
          </div>
          <h1 className="analysis-label">{report.label}</h1>
        </div>
      </section>
      {report.source && (
        <section className="pr-source" aria-label="GitHub analysis source">
          <a href={report.source.pr_url} target="_blank" rel="noreferrer">
            {report.source.repository} #{report.source.pr_number}{" "}
            <Icon name="external" />
          </a>
          <span>{report.source.title}</span>
          <details>
            <summary>Exact analyzed revisions</summary>
            <dl>
              <dt>Before (merge base)</dt>
              <dd>
                <code>{report.source.merge_base_sha}</code>
              </dd>
              <dt>After (PR head)</dt>
              <dd>
                <code>{report.source.head_sha}</code>
              </dd>
              <dt>Target branch at retrieval</dt>
              <dd>
                <code>{report.source.base_sha}</code>
              </dd>
              <dt>Head repository</dt>
              <dd>{report.source.head_repository}</dd>
              <dt>Analyzer version</dt>
              <dd>{report.source.analyzer_version}</dd>
            </dl>
          </details>
        </section>
      )}
      <section className="metrics" aria-label="Analysis summary">
        <div>
          <Icon name="code" />
          <strong>
            {
              report.nodes.filter(
                (n) => n.kind !== "module" && report.changed.includes(n.id),
              ).length
            }
          </strong>
          <span>
            Changed symbols<small>excluding modules</small>
          </span>
        </div>
        <div>
          <Icon name="branch" />
          <strong>{report.stats.impacted}</strong>
          <span>
            Potentially affected<small>symbols + modules</small>
          </span>
        </div>
        <div>
          <Icon name="tests" />
          <strong>{report.recommendations.length}</strong>
          <span>
            Tests to prioritize<small>with traceable evidence</small>
          </span>
        </div>
        <div>
          <Icon name="clock" />
          <strong>
            {report.stats.elapsed_ms}
            <small>ms</small>
          </strong>
          <span>
            Analysis time<small>measured this request</small>
          </span>
        </div>
      </section>
    </>
  );
}
