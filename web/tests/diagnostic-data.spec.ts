import { test, expect } from "@playwright/test";
import {
  classifyNotes,
  groupNotes,
  defaultNoteFilters,
} from "../src/diagnostics";
import type { Report, SymbolNode } from "../src/types";

const path = "src/工具.py";
const node = (
  id: string,
  kind: SymbolNode["kind"] = "function",
): SymbolNode => ({ id, path, kind, name: id, line: 1, end_line: 20 });
const report = (warnings: string[]) =>
  ({
    warnings,
    nodes: [node(`${path}::<module>`, "module"), node(`${path}::work`)],
    source_files: [
      {
        path: "deleted.py",
        before: { text: "bad", parse_status: "unparseable" as const },
        after: null,
      },
    ],
  }) satisfies Pick<Report, "warnings" | "nodes" | "source_files">;

test("known diagnostics require exact formats and confirmed file or symbol associations", () => {
  const raw = [
    `Cannot parse ${path}: SyntaxError`,
    "Cannot parse deleted.py: ValueError",
    `Unresolved call 工具.run: ${path}:12`,
    `Dynamic call: ${path}:9`,
    `Wildcard import is unresolved: ${path}:2`,
    `Wildcard local import is unresolved: ${path}::work`,
    `Ambiguous module import binding: ${path}::<module>: os, sys`,
    `Ambiguous or unsupported local import binding: ${path}::work: 工具`,
    `Conservative fallback retained: unmodeled protocol change in ${path}`,
    `Conservative fallback retained: reference budget exceeded for ${path}::work`,
  ];
  const result = classifyNotes(report(raw));
  expect(result.map((n) => n.category)).toEqual([
    "parse",
    "parse",
    "unresolved",
    "dynamic",
    "imports",
    "imports",
    "imports",
    "imports",
    "fallback",
    "fallback",
  ]);
  expect(result.map((n) => n.file)).toEqual(
    raw.map((_, i) => (i === 1 ? "deleted.py" : path)),
  );
  expect(result.map((n) => n.text)).toEqual(raw);
});

test("unknown malformed and ambiguous formats remain unclassified without guessed locations", () => {
  const raw = [
    "Cannot parse missing.py: SyntaxError",
    `Cannot parse ${path}: NewError`,
    `Dynamic call: ${path}:0`,
    `Dynamic call: ${path}:2 trailing text`,
    `Unresolved call a.*: ${path}:2`,
    `Unresolved call a: ${path}:2 and deleted.py:3`,
    `Wildcard local import is unresolved: ${path}::unknown`,
    `Ambiguous module import binding: ${path}::work: os`,
    `Dynamic call: ${path}:2\n`,
    "Future parser notice: src/工具.py:2",
    "",
    "<img src=x onerror=alert(1)>",
  ];
  expect(
    classifyNotes(report(raw)).map((n) => [n.category, n.file, n.text]),
  ).toEqual(raw.map((text) => ["general", null, text]));
});

test("scope notes keep multi-file skipped entries report-wide", () => {
  const raw = [
    "Risk scores prioritize review; they are not calibrated failure probabilities.",
    "Static analysis is incomplete: dynamic dispatch, fixtures, reflection, re-exports, inheritance and runtime imports may hide dependencies. Keep the full test suite as a gate.",
    "No Python files were found in the supported analysis scope.",
    "base: skipped 2 excluded Python files (vendor/a.py, vendor/b.py).",
    "head: skipped 1 symlinks (src/工具.py).",
    "head: skipped 1 submodules (dep).",
  ];
  expect(classifyNotes(report(raw)).map((n) => [n.category, n.file])).toEqual(
    raw.map(() => ["scope", null]),
  );
});

test("duplicates retain distinct stable identities and no original data is mutated", () => {
  const data = report([
    `Dynamic call: ${path}:1`,
    "Unknown",
    `Dynamic call: ${path}:1`,
    "Unknown",
  ]);
  const original = structuredClone(data);
  Object.freeze(data.warnings);
  const notes = classifyNotes(data);
  notes.forEach(Object.freeze);
  Object.freeze(notes);
  expect(notes.map((n) => n.id)).toEqual([0, 1, 2, 3]);
  expect(classifyNotes(data)).toEqual(notes);
  const groups = groupNotes(notes, defaultNoteFilters);
  expect(groups.map((g) => g.category)).toEqual(["dynamic", "general"]);
  expect(groups.map((g) => [g.total, g.matching])).toEqual([
    [2, 2],
    [2, 2],
  ]);
  expect(groups[0].files[0].notes.map((n) => n.id)).toEqual([0, 2]);
  expect(data).toEqual(original);
});

test("complete literal search combines with category and file filters", () => {
  const data = report([
    "Unknown [.*] Ω\nsecond line",
    "unknown [.*] ω",
    `Dynamic call: ${path}:1`,
    "Unknown otherwise",
  ]);
  const notes = classifyNotes(data);
  const groups = groupNotes(notes, {
    query: "  [.*] Ω  ",
    category: "general",
    file: null,
  });
  expect(groups[0].total).toBe(3);
  expect(groups[0].matching).toBe(2);
  expect(
    groupNotes(notes, {
      query: "SECOND LINE",
      category: "all",
      file: undefined,
    })[0].files[0].notes[0].id,
  ).toBe(0);
  expect(
    groupNotes(notes, { query: "[.*]", category: "general", file: path }),
  ).toEqual([]);
  expect(
    groupNotes(notes, { query: ".+", category: "all", file: undefined }),
  ).toEqual([]);
  expect(
    groupNotes(notes, { query: "工具", category: "dynamic", file: path })[0]
      .matching,
  ).toBe(1);
});

test("file ordering is deterministic while note order inside files stays original", () => {
  const data = report([
    "Dynamic call: z.py:5",
    "Dynamic call: a.py:8",
    "Dynamic call: z.py:1",
  ]);
  data.nodes.push(
    { ...node("z.py::<module>", "module"), path: "z.py" },
    { ...node("a.py::<module>", "module"), path: "a.py" },
  );
  const files = groupNotes(classifyNotes(data), defaultNoteFilters)[0].files;
  expect(files.map((g) => g.file)).toEqual(["a.py", "z.py"]);
  expect(files[1].notes.map((n) => n.id)).toEqual([0, 2]);
});

test("empty data and long multiline notes remain lossless", () => {
  expect(classifyNotes(report([]))).toEqual([]);
  expect(groupNotes([], defaultNoteFilters)).toEqual([]);
  const text = `未来 ${"long/path/".repeat(100)}[literal]\nsecond line\n<script>alert('x')</script>`;
  const notes = classifyNotes(report([text]));
  expect(
    groupNotes(notes, { ...defaultNoteFilters, query: "<script>" })[0].files[0]
      .notes[0].text,
  ).toBe(text);
});
