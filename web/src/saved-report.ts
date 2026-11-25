import type {
  DependencyEdge,
  DependencyEvidence,
  Recommendation,
  Report,
  SourceRange,
  SourceRevision,
  SymbolChange,
  SymbolNode,
} from "./types";

// Separate from snapshot upload: pretty-printed exports also carry the graph
// and both revisions' evidence. The worker permits 32 MiB of compact output.
export const maxReportMiB = 96;
// The report records files accepted by the analyzer's Snapshot contract.
const maxSourceBytes = 200_000;
const maxSnapshotBytes = 2_000_000;
const revisions = ["before", "after"] as const;
type Revision = (typeof revisions)[number];

function requireField(ok: unknown, message: string): asserts ok {
  if (!ok) throw new Error(message);
}

type Check<T> = (value: unknown, field: string) => value is T;
const string: Check<string> = (v): v is string => typeof v === "string";
const integer: Check<number> = (v): v is number => Number.isSafeInteger(v);
const positive: Check<number> = (v, f): v is number => integer(v, f) && v > 0;
function oneOf<const T extends string>(...values: T[]): Check<T> {
  return (v): v is T => values.some((choice) => choice === v);
}
function array<T>(check: Check<T>): Check<T[]> {
  return (v, f): v is T[] => {
    if (!Array.isArray(v)) return false;
    v.forEach((item, i) => {
      const path = f + "[" + i + "]";
      requireField(check(item, path), "Invalid " + path + ".");
    });
    return true;
  };
}
function nullable<T>(check: Check<T>): Check<T | null> {
  return (v, f): v is T | null => v === null || check(v, f);
}
function record(v: unknown): v is Record<string, unknown> {
  return !!v && typeof v === "object" && !Array.isArray(v);
}
// Validate in place: export field order and the existing fingerprint survive.
function object<T>(fields: { [K in keyof T]-?: Check<T[K]> }): Check<T> {
  return (v, f): v is T => {
    if (!record(v)) return false;
    for (const key of Object.keys(fields) as (keyof T & string)[]) {
      const path = f + "." + key;
      requireField(
        fields[key](Object.hasOwn(v, key) ? v[key] : undefined, path),
        "Invalid or missing " + path + ".",
      );
    }
    requireField(
      Object.keys(v).every((key) => Object.hasOwn(fields, key)),
      "Unexpected field in " + f + ".",
    );
    return true;
  };
}
const rangeFields = { line: positive, end_line: positive };
const range = object<SourceRange>(rangeFields);
const location = object<DependencyEvidence["location"]>({
  ...rangeFields,
  path: string,
});
const evidence = object<DependencyEvidence>({
  text: string,
  location,
  target_location: location,
});
const sourceRevision = nullable(
  object<SourceRevision>({
    text: string,
    parse_status: oneOf("parsed", "unparseable"),
  }),
);
const node = object<SymbolNode>({
  ...rangeFields,
  id: string,
  name: string,
  path: string,
  kind: oneOf("module", "class", "test", "function"),
});
const edge = object<DependencyEdge>({
  id: string,
  source: string,
  target: string,
  kind: oneOf("call", "fixture", "import", "module"),
  revision: oneOf("before", "after", "both"),
  before: array(evidence),
  after: array(evidence),
});
const change = object<SymbolChange>({
  symbol: string,
  path: string,
  status: oneOf("modified", "added", "removed"),
  before: nullable(range),
  after: nullable(range),
});
const strings = array(string);
const recommendation = object<Recommendation>({
  symbol: string,
  score: integer,
  reason: string,
  distance: integer,
  evidence_edges: strings,
  evidence_path: strings,
  path_revision: oneOf("before", "after", "both", "mixed"),
});
const provenance = object<NonNullable<Report["source"]>>({
  kind: oneOf("github_pr"),
  repository: string,
  head_repository: string,
  pr_number: positive,
  pr_url: string,
  title: string,
  base_sha: string,
  head_sha: string,
  merge_base_sha: string,
  analyzer_version: string,
});
const reportFields = object<Report>({
  schema_version: oneOf("2.0", "2.1"),
  label: string,
  nodes: array(node),
  edges: array(edge),
  changes: array(change),
  changed: strings,
  removed: strings,
  impacted: strings,
  source_files: array(
    object<Report["source_files"][number]>({
      path: string,
      before: sourceRevision,
      after: sourceRevision,
    }),
  ),
  recommendations: array(recommendation),
  warnings: strings,
  stats: (v): v is Report["stats"] =>
    record(v) &&
    Object.values(v).every(
      (n) => typeof n === "number" && Number.isFinite(n) && n >= 0,
    ),
  source: (v, f): v is Report["source"] => v === undefined || provenance(v, f),
});

function index<T>(items: T[], key: (item: T) => string, field: string) {
  const entries = new Map<string, T>();
  for (const item of items) {
    const id = key(item);
    requireField(!entries.has(id), "Duplicate ID in " + field + ".");
    entries.set(id, item);
  }
  return entries;
}

function presence(before: boolean, after: boolean) {
  return before ? (after ? "both" : "before") : after ? "after" : "mixed";
}

function checkProvenance(source: NonNullable<Report["source"]>) {
  const repository = /^[a-zA-Z0-9][a-zA-Z0-9-]{0,38}\/[a-zA-Z0-9_.-]{1,100}$/;
  for (const name of [source.repository, source.head_repository]) {
    requireField(
      repository.test(name) && ![".", ".."].includes(name.split("/")[1]),
      "Invalid GitHub repository in the recorded provenance.",
    );
  }
  requireField(
    source.pr_url ===
      "https://github.com/" + source.repository + "/pull/" + source.pr_number,
    "The recorded PR link must match its GitHub repository and number.",
  );
  requireField(
    [source.base_sha, source.head_sha, source.merge_base_sha].every((sha) =>
      /^[0-9a-f]{40}$/.test(sha),
    ),
    "Invalid revision in the recorded GitHub provenance.",
  );
}

function checkRecommendations(
  report: Report,
  nodes: Map<string, SymbolNode>,
  edges: Map<string, DependencyEdge>,
  changes: Map<string, SymbolChange>,
) {
  const seen = new Set<string>();
  for (const rec of report.recommendations) {
    const path = rec.evidence_path;
    const startChange = changes.get(rec.symbol);
    requireField(
      !seen.has(rec.symbol) &&
        nodes.get(rec.symbol)?.kind === "test" &&
        startChange?.status !== "removed",
      "Invalid or duplicate recommended test.",
    );
    seen.add(rec.symbol);
    requireField(
      rec.score >= 1 && rec.score <= 100,
      "Invalid recommendation score.",
    );
    requireField(
      path[0] === rec.symbol &&
        changes.has(path.at(-1)!) &&
        new Set(path).size === path.length &&
        path.length === rec.distance + 1 &&
        rec.evidence_edges.length === rec.distance,
      "Invalid recommendation evidence path, endpoint or distance.",
    );
    let before = startChange?.status !== "added";
    let after = true;
    const kinds = rec.evidence_edges.map((id, i) => {
      const edge = edges.get(id);
      requireField(
        edge && edge.source === path[i] && edge.target === path[i + 1],
        "Recommendation evidence must follow its recorded edges from caller to dependency.",
      );
      before &&= edge.before.length > 0;
      after &&= edge.after.length > 0;
      return edge.kind;
    });
    const revision = presence(before, after);
    requireField(
      revision === rec.path_revision,
      "Recommendation revision does not match its evidence.",
    );
    const definition = nodes.get(path.at(-1)!)?.kind !== "module";
    let reason = "Conservative module/import dependency";
    if (!kinds.length) reason = "Test itself changed";
    else if (kinds[0] === "fixture") {
      requireField(
        definition &&
          revision !== "mixed" &&
          kinds.slice(1).every((k) => k === "call"),
        "Invalid fixture evidence path.",
      );
      reason = "Resolved fixture dependency";
    } else if (definition && kinds.every((k) => k === "call"))
      reason = "Resolved call path";
    requireField(
      rec.reason === reason,
      "Recommendation reason does not match its typed evidence.",
    );
  }
}

export function validateSavedReport(value: unknown): Report {
  requireField(
    record(value) && Object.hasOwn(value, "schema_version"),
    "Choose an exported CodeImpact report with a schema version.",
  );
  requireField(
    value.schema_version === "2.0" || value.schema_version === "2.1",
    "Unsupported report version. Open a schema 2.0 or 2.1 export.",
  );
  requireField(reportFields(value, "report"), "Invalid CodeImpact report.");
  requireField(
    value.label.length <= 320 && [...value.label].length <= 160,
    "Report label exceeds the analysis limit.",
  );
  if (value.source) checkProvenance(value.source);
  const nodes = index(value.nodes, (n) => n.id, "nodes");
  const edges = index(value.edges, (e) => e.id, "edges");
  const changes = index(value.changes, (c) => c.symbol, "changes");
  const files = index(value.source_files, (f) => f.path, "source_files");
  for (const ids of [value.changed, value.impacted, value.removed]) {
    requireField(
      new Set(ids).size === ids.length && ids.every((id) => nodes.has(id)),
      "Duplicate or unknown symbol in report lists.",
    );
  }
  requireField(
    changes.size === value.changed.length &&
      value.changed.every((id) => changes.has(id)) &&
      value.impacted.every((id) => !changes.has(id)),
    "Changed and impacted symbols disagree with the change records.",
  );
  const removed = new Set(value.removed);
  requireField(
    value.removed.every((id) => changes.has(id)),
    "Missing removed symbol change.",
  );
  const changedFiles = new Set(value.changes.map((c) => c.path));
  requireField(
    files.size === changedFiles.size &&
      [...changedFiles].every((p) => files.has(p)),
    "Changed files and captured sources disagree.",
  );

  const bytes = { before: 0, after: 0 };
  const encoder = new TextEncoder();
  const lengths = {
    before: new Map<string, number>(),
    after: new Map<string, number>(),
  };
  for (const file of files.values()) {
    requireField(
      file.before || file.after,
      "Captured source is absent in both revisions.",
    );
    for (const side of revisions) {
      const source = file[side];
      if (source) {
        requireField(
          source.text.length <= maxSourceBytes,
          "Captured source exceeds the per-file byte limit.",
        );
        const size = encoder.encode(source.text).byteLength;
        bytes[side] += size;
        requireField(
          size <= maxSourceBytes && bytes[side] <= maxSnapshotBytes,
          "Captured source exceeds the snapshot byte limits.",
        );
        const lines = source.text.split(/\r\n|\r|\n/);
        lengths[side].set(
          file.path,
          Math.max(1, lines.length - Number(lines.at(-1) === "")),
        );
      }
    }
  }
  // A typed target location spans the whole dependency. Module targets can
  // therefore supply the before extent of a file whose text was omitted.
  for (const e of edges.values()) {
    const target = nodes.get(e.target);
    if (target?.kind !== "module") continue;
    for (const side of revisions) {
      for (const { target_location: loc } of e[side]) {
        const extent = lengths[side].get(target.path);
        requireField(
          loc.path === target.path &&
            loc.line === 1 &&
            (extent === undefined || loc.end_line === extent),
          "Module evidence range disagrees with its revision.",
        );
        if (!files.has(target.path))
          lengths[side].set(target.path, loc.end_line);
      }
    }
  }
  function checkRange(r: SourceRange, path: string, side: Revision) {
    // Unchanged files have no exported source. After metadata still supplies
    // the module extent; before-only physical line movement may be invisible.
    const last =
      lengths[side].get(path) ??
      (files.has(path)
        ? 0
        : side === "after"
          ? nodes.get(path + "::<module>")?.end_line
          : undefined);
    requireField(
      r.line <= r.end_line &&
        r.end_line <= maxSourceBytes &&
        r.end_line <= (last ?? maxSourceBytes),
      "Source range exceeds its " + side + " file or has reversed lines.",
    );
  }
  for (const n of nodes.values()) {
    const module = nodes.get(n.path + "::<module>");
    requireField(
      n.path.length <= 1000 &&
        [...n.path].length <= 500 &&
        n.path.endsWith(".py") &&
        !/[\\:]/.test(n.path) &&
        n.path
          .split("/")
          .every((part) => part && part !== "." && part !== "..") &&
        module?.kind === "module" &&
        n.id === n.path + "::" + (n.kind === "module" ? "<module>" : n.name),
      "Invalid symbol ID or Python file path.",
    );
    const side = removed.has(n.id) ? "before" : "after";
    checkRange(n, n.path, side);
    if (n.kind === "module") {
      const extent = lengths[side].get(n.path);
      requireField(
        n.line === 1 && (extent === undefined || n.end_line === extent),
        "Module range disagrees with its captured source.",
      );
    }
  }
  for (const c of changes.values()) {
    requireField(
      nodes.get(c.symbol)?.path === c.path &&
        (c.status === "removed") === removed.has(c.symbol) &&
        Boolean(c.before) === (c.status !== "added") &&
        Boolean(c.after) === (c.status !== "removed"),
      "Change status, file or revision range disagrees with its symbol.",
    );
    for (const side of revisions)
      if (c[side]) checkRange(c[side], c.path, side);
    const current = c.after ?? c.before!;
    const definition = nodes.get(c.symbol)!;
    requireField(
      current.line <= definition.line &&
        current.end_line === definition.end_line,
      "Change range disagrees with its symbol definition.",
    );
  }
  const typedEdges = new Set<string>();
  let hasFixture = false;
  for (const e of edges.values()) {
    const from = nodes.get(e.source),
      to = nodes.get(e.target);
    const key = JSON.stringify([e.source, e.target, e.kind]);
    requireField(
      from &&
        to &&
        from !== to &&
        /^[0-9a-f]{64}$/.test(e.id) &&
        !typedEdges.has(key),
      "Invalid edge ID, duplicate typed edge or unknown endpoint.",
    );
    typedEdges.add(key);
    hasFixture ||= e.kind === "fixture";
    requireField(
      presence(!!e.before.length, !!e.after.length) === e.revision,
      "Edge revision does not match its evidence locations.",
    );
    for (const side of revisions) {
      for (const item of e[side]) {
        const targetRange = changes.get(to.id)?.[side];
        if (targetRange) {
          requireField(
            item.target_location.line === targetRange.line &&
              item.target_location.end_line === targetRange.end_line,
            "Evidence target range disagrees with its changed definition.",
          );
        }
        for (const [endpoint, loc] of [
          [from, item.location],
          [to, item.target_location],
        ] as const) {
          requireField(
            loc.path === endpoint.path &&
              changes.get(endpoint.id)?.[side] !== null,
            "Evidence location disagrees with its endpoint or revision.",
          );
          checkRange(loc, loc.path, side);
        }
      }
    }
  }
  requireField(
    hasFixture === (value.schema_version === "2.1"),
    "Fixture edge kind and report version disagree.",
  );
  checkRecommendations(value, nodes, edges, changes);
  const modules = [...nodes.values()].filter((n) => n.kind === "module");
  const counts = {
    files_base: modules.filter((n) => changes.get(n.id)?.status !== "added")
      .length,
    files_head: modules.filter((n) => !removed.has(n.id)).length,
    symbols: nodes.size,
    edges: edges.size,
    changed: changes.size,
    impacted: value.impacted.length,
    recommended_tests: value.recommendations.length,
  };
  requireField(
    Object.entries(counts).every(([key, n]) => value.stats[key] === n) &&
      value.stats.files_base <= 300 &&
      value.stats.files_head <= 300 &&
      Object.hasOwn(value.stats, "elapsed_ms"),
    "Missing or inconsistent analysis statistics.",
  );
  return value;
}

export async function readSavedReport(file: File): Promise<Report> {
  requireField(
    file.size <= maxReportMiB * 1024 * 1024,
    "Saved report exceeds the " + maxReportMiB + " MiB file limit.",
  );
  const text = await file.text().catch(() => {
    throw new Error("The file could not be read. Choose it again.");
  });
  let value: unknown;
  try {
    value = JSON.parse(text);
  } catch {
    throw new Error(
      "The file is not valid JSON. Choose the original CodeImpact export.",
    );
  }
  return validateSavedReport(value);
}
