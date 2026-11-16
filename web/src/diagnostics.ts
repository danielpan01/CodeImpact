import type { Report } from "./types";

// Presentation-only allowlist of current warning producers. See
// docs/FRONTEND_MILESTONE8B.md before extending it. Unknown formats stay general.
export const noteCategories = {
  scope: "Analysis scope",
  parse: "Parse failures",
  imports: "Unresolved imports",
  unresolved: "Unresolved calls",
  dynamic: "Dynamic calls",
  fallback: "Conservative fallback",
  general: "General / unclassified",
} as const;
export type NoteCategory = keyof typeof noteCategories;
export type DiagnosticNote = {
  id: number;
  text: string;
  category: NoteCategory;
  file: string | null;
};
export type NoteFilters = {
  query: string;
  category: NoteCategory | "all";
  file: string | null | undefined;
};
export const defaultNoteFilters: NoteFilters = {
  query: "",
  category: "all",
  file: undefined,
};
export type NoteFileGroup = {
  id: string;
  file: string | null;
  total: number;
  notes: DiagnosticNote[];
};
export type NoteGroup = {
  category: NoteCategory;
  total: number;
  matching: number;
  files: NoteFileGroup[];
};
const scopeNotes = new Set([
  "Static analysis is incomplete: dynamic dispatch, fixtures, reflection, re-exports, inheritance and runtime imports may hide dependencies. Keep the full test suite as a gate.",
  "Risk scores prioritize review; they are not calibrated failure probabilities.",
  "No Python files were found in the supported analysis scope.",
]);
const identifier = String.raw`[\p{ID_Start}_][\p{ID_Continue}]*`;
const unresolvedCall = new RegExp(
  `^Unresolved call ${identifier}(?:\\.${identifier})*: (.+):([1-9][0-9]*)$`,
  "u",
);
const importBindings = new RegExp(
  `^(Ambiguous module import binding|Ambiguous or unsupported local import binding): (.+): ${identifier}(?:, ${identifier})*$`,
  "u",
);

export function classifyNotes(
  report: Pick<Report, "warnings" | "nodes" | "source_files">,
): DiagnosticNote[] {
  const files = new Set([
    ...report.nodes.map((n) => n.path),
    ...report.source_files.map((f) => f.path),
  ]);
  const symbols = new Map(report.nodes.map((n) => [n.id, n]));
  const symbolFile = (id: string, moduleOnly = false) => {
    const node = symbols.get(id);
    return node &&
      id.startsWith(`${node.path}::`) &&
      (moduleOnly
        ? node.kind === "module"
        : node.kind === "function" || node.kind === "test")
      ? node.path
      : null;
  };
  return report.warnings.map((text, id) => {
    const general: DiagnosticNote = {
      id,
      text,
      category: "general",
      file: null,
    };
    if (/[\r\n]/.test(text)) return general;
    const classified = (
      category: NoteCategory,
      file: string | null,
    ): DiagnosticNote => ({ id, text, category, file });
    if (
      scopeNotes.has(text) ||
      /^(base|head): skipped [1-9][0-9]* (symlinks|submodules|excluded Python files) \(.+\)\.$/u.test(
        text,
      )
    )
      return classified("scope", null);
    const parse =
      /^Cannot parse (.+): (SyntaxError|ValueError|RecursionError)$/u.exec(
        text,
      );
    if (parse && files.has(parse[1])) return classified("parse", parse[1]);
    for (const [category, pattern] of [
      ["unresolved", unresolvedCall],
      ["dynamic", /^Dynamic call: (.+):([1-9][0-9]*)$/u],
      ["imports", /^Wildcard import is unresolved: (.+):([1-9][0-9]*)$/u],
    ] as const) {
      const match = pattern.exec(text);
      if (
        match &&
        files.has(match[1]) &&
        Number.isSafeInteger(Number(match[2]))
      )
        return classified(category, match[1]);
    }
    const wildcard = /^Wildcard local import is unresolved: (.+)$/u.exec(text);
    const bindings = importBindings.exec(text);
    const localFile = wildcard
      ? symbolFile(wildcard[1])
      : bindings
        ? symbolFile(
            bindings[2],
            bindings[1] === "Ambiguous module import binding",
          )
        : null;
    if (localFile) return classified("imports", localFile);
    const protocol =
      /^Conservative fallback retained: unmodeled protocol change in (.+)$/u.exec(
        text,
      );
    if (protocol && files.has(protocol[1]))
      return classified("fallback", protocol[1]);
    const budget =
      /^Conservative fallback retained: reference budget exceeded for (.+)$/u.exec(
        text,
      );
    // Budget warnings can name any indexed symbol, including a module or class.
    const node = budget ? symbols.get(budget[1]) : undefined;
    if (node && budget![1].startsWith(`${node.path}::`))
      return classified("fallback", node.path);
    return general;
  });
}

export function groupNotes(
  notes: readonly DiagnosticNote[],
  filters: NoteFilters,
): NoteGroup[] {
  const query = filters.query.trim().toLowerCase();
  const groups: NoteGroup[] = [];
  for (const category of Object.keys(noteCategories) as NoteCategory[]) {
    if (filters.category !== "all" && filters.category !== category) continue;
    const all = notes.filter((n) => n.category === category);
    const byFile = new Map<string | null, DiagnosticNote[]>();
    for (const note of all) {
      const entries = byFile.get(note.file) ?? [];
      entries.push(note);
      byFile.set(note.file, entries);
    }
    const files: NoteFileGroup[] = [];
    for (const [file, entries] of byFile) {
      if (filters.file !== undefined && file !== filters.file) continue;
      const matches = entries.filter((n) =>
        n.text.toLowerCase().includes(query),
      );
      if (matches.length)
        files.push({
          id: JSON.stringify([category, file]),
          file,
          total: entries.length,
          notes: matches,
        });
    }
    // Code-point ordering is independent of locale; report-wide entries go first.
    files.sort((a, b) =>
      a.file === b.file
        ? 0
        : a.file === null
          ? -1
          : b.file === null
            ? 1
            : a.file < b.file
              ? -1
              : 1,
    );
    const matching = files.reduce((total, f) => total + f.notes.length, 0);
    if (matching) groups.push({ category, total: all.length, matching, files });
  }
  return groups;
}
