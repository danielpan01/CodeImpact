import type { Recommendation, Report } from "./types";

export const reviewStatuses = {
  pending: "Pending",
  followUp: "Follow-up",
  reviewed: "Reviewed",
} as const;
export type ReviewStatus = keyof typeof reviewStatuses;
export type ReviewDecisions = Partial<
  Record<number, Exclude<ReviewStatus, "pending">>
>;

export const decisionAt = (
  decisions: ReviewDecisions,
  index: number,
): ReviewStatus => decisions[index] ?? "pending";

const storageKey = "codeimpact.review-plans.v1";
const storedPlanLimit = 12;

export async function reviewKey(report: Report): Promise<string> {
  // Key the exact stable report, not the user-supplied label or a moving PR URL.
  // Runtime timing is the only field excluded.
  const { elapsed_ms: _, ...stats } = report.stats;
  const bytes = new TextEncoder().encode(JSON.stringify({ ...report, stats }));
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  return Array.from(new Uint8Array(digest), (byte) =>
    byte.toString(16).padStart(2, "0"),
  ).join("");
}

function readPlans(): [string, unknown][] {
  const data: unknown = JSON.parse(localStorage.getItem(storageKey) ?? "[]");
  return Array.isArray(data)
    ? data
        .slice(0, storedPlanLimit)
        .filter(
          (row): row is [string, unknown] =>
            Array.isArray(row) &&
            row.length === 2 &&
            typeof row[0] === "string" &&
            /^[a-f0-9]{64}$/.test(row[0]),
        )
    : [];
}

export function readDecisions(key: string, count: number): ReviewDecisions {
  const data = readPlans().find(([savedKey]) => savedKey === key)?.[1];
  if (!data || typeof data !== "object") return {};
  const decisions: ReviewDecisions = {};
  for (let index = 0; index < count; index++) {
    const status: unknown = (data as Record<number, unknown>)[index];
    if (status === "reviewed" || status === "followUp")
      decisions[index] = status;
  }
  return decisions;
}

export function saveDecisions(key: string, decisions: ReviewDecisions) {
  const others = readPlans().filter(([savedKey]) => savedKey !== key);
  const plans = Object.keys(decisions).length
    ? [[key, decisions], ...others]
    : others;
  localStorage.setItem(
    storageKey,
    JSON.stringify(plans.slice(0, storedPlanLimit)),
  );
}

export const reviewRevisions: Record<Recommendation["path_revision"], string> =
  {
    before: "Before only",
    after: "After only",
    both: "Both revisions",
    mixed: "Mixed revisions",
  };

function inlineCode(value: string) {
  const singleLine = value.replace(/[\r\n]/g, " ");
  let length = 0;
  for (const [run] of singleLine.matchAll(/`+/g))
    length = Math.max(length, run.length);
  const fence = "`".repeat(length + 1);
  return `${fence} ${singleLine} ${fence}`;
}

export function reviewMarkdown(report: Report, decisions: ReviewDecisions) {
  const lines = [
    "# CodeImpact review plan",
    "",
    inlineCode(report.label),
    "",
    "Statuses record evidence review. Keep the full test suite as the merge gate.",
  ];
  if (report.source) {
    lines.push(
      "",
      `Pull request ${inlineCode(report.source.pr_url)}`,
      `- Before ${inlineCode(report.source.merge_base_sha)}`,
      `- After ${inlineCode(report.source.head_sha)}`,
    );
  }
  for (const status of ["followUp", "pending", "reviewed"] as const) {
    const tests = report.recommendations.filter(
      (_, index) => decisionAt(decisions, index) === status,
    );
    if (!tests.length) continue;
    lines.push("", `## ${reviewStatuses[status]} (${tests.length})`, "");
    for (const test of tests) {
      lines.push(
        `- ${inlineCode(test.symbol)} · heuristic priority ${test.score}/100`,
        `  - ${inlineCode(test.reason)} · ${reviewRevisions[test.path_revision]}`,
        `  - Path: ${test.evidence_path.map(inlineCode).join(" → ")}`,
      );
    }
  }
  if (!report.recommendations.length) lines.push("", "No recommended tests.");
  return lines.join("\n") + "\n";
}

export function downloadFile(name: string, contents: string, type: string) {
  const url = URL.createObjectURL(new Blob([contents], { type }));
  const link = document.createElement("a");
  link.href = url;
  link.download = name;
  link.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}
