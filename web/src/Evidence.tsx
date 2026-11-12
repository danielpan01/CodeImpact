import type { DependencyEdge, Recommendation } from "./types";

export function PathRevision({
  recommendation,
}: {
  recommendation: Recommendation;
}) {
  const labels = {
    both: "Path exists in both revisions",
    before: "Path exists only before",
    after: "Path exists only after",
    mixed:
      "Mixed revisions — no single revision contains this entire shown path",
  };
  return (
    <p className="path-revision">
      <span className={`revision-badge ${recommendation.path_revision}`}>
        {
          {
            before: "Before only",
            after: "After only",
            both: "Both revisions",
            mixed: "Mixed revisions",
          }[recommendation.path_revision]
        }
      </span>
      <span>
        {labels[recommendation.path_revision]}
        {recommendation.path_revision === "mixed" &&
          ". This combined path is a conservative estimate."}
      </span>
    </p>
  );
}

export function EdgeEvidence({ edge }: { edge: DependencyEdge }) {
  const presence = {
    both: "Both revisions",
    before: "Before only",
    after: "After only",
  };
  return (
    <div className="edge-evidence">
      <p>
        <b>
          {edge.kind === "call"
            ? "Resolved call"
            : `Conservative ${edge.kind} dependency`}
        </b>{" "}
        <span className={`revision-badge ${edge.revision}`}>
          {presence[edge.revision]}
        </span>
      </p>
      {(["before", "after"] as const).map(
        (revision) =>
          edge[revision].length > 0 && (
            <details key={revision} className="revision-evidence">
              <summary>
                {revision === "before" ? "Before" : "After"}:{" "}
                {edge[revision].length} evidence location
                {edge[revision].length === 1 ? "" : "s"}
              </summary>
              {edge[revision].map((e, i) => (
                <p key={i}>
                  {e.text}
                  <br />
                  <code>
                    {e.location.path}:{e.location.line}–{e.location.end_line} →{" "}
                    {e.target_location.path}:{e.target_location.line}–
                    {e.target_location.end_line}
                  </code>
                </p>
              ))}
            </details>
          ),
      )}
    </div>
  );
}
