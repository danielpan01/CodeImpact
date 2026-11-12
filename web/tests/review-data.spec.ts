import { test, expect } from "@playwright/test";
import {
  categories,
  defaultTestControls,
  explanationCategory,
  reviewTests,
} from "../src/test-review";
import { colorSource } from "../src/source-tokens";
import type { Recommendation } from "../src/types";

const item = (
  symbol: string,
  score: number,
  reason = "Resolved call path",
): Recommendation => ({
  symbol,
  score,
  reason,
  distance: 0,
  evidence_path: [symbol],
  evidence_edges: [],
  path_revision: "both",
});

test("test review filters literal terms and categories without mutating report order", () => {
  const data = [
    item("z.py::test_A", 90),
    item("a.py::test_Z", 10, "Conservative module/import dependency"),
    item("a.py::test_A", 90, "Test itself changed"),
    item("b.py::test_[literal]", 10, "Future explanation"),
  ];
  const before = structuredClone(data);
  data.forEach(Object.freeze);
  Object.freeze(data);
  expect(reviewTests(data, defaultTestControls)).toEqual(before);
  expect(
    reviewTests(data, {
      ...defaultTestControls,
      query: "  A.PY  test_a  ",
    }).map((r) => r.symbol),
  ).toEqual(["a.py::test_A"]);
  expect(
    reviewTests(data, { ...defaultTestControls, query: "[literal]" }).map(
      (r) => r.symbol,
    ),
  ).toEqual(["b.py::test_[literal]"]);
  expect(reviewTests(data, { ...defaultTestControls, query: ".*" })).toEqual(
    [],
  );
  for (const category of Object.keys(
    categories,
  ) as (keyof typeof categories)[]) {
    expect(
      reviewTests(data, { ...defaultTestControls, category }),
    ).toHaveLength(1);
  }
  expect(explanationCategory("Conservative but new wording")).toBe("other");
  expect(data).toEqual(before);
});

test("all test sort modes have deterministic ties and retain original priorities", () => {
  const data = [
    item("z.py::test_A", 90),
    item("b.py::test_Z", 10),
    item("a.py::test_A", 90),
    item("a.py::test_B", 10),
  ];
  expect(
    reviewTests(data, { ...defaultTestControls, sort: "name" }).map(
      (r) => r.symbol,
    ),
  ).toEqual(["a.py::test_A", "z.py::test_A", "a.py::test_B", "b.py::test_Z"]);
  expect(
    reviewTests(data, { ...defaultTestControls, sort: "file" }).map(
      (r) => r.symbol,
    ),
  ).toEqual(["a.py::test_A", "a.py::test_B", "b.py::test_Z", "z.py::test_A"]);
  expect(
    reviewTests(data, { ...defaultTestControls, sort: "priority" }).map((r) => [
      r.symbol,
      r.score,
    ]),
  ).toEqual([
    ["a.py::test_B", 10],
    ["b.py::test_Z", 10],
    ["a.py::test_A", 90],
    ["z.py::test_A", 90],
  ]);
  expect(data[0].symbol).toBe("z.py::test_A");
});

test("source colors preserve text, multiline strings, escapes and malformed input", () => {
  const lines = [
    "def greet():",
    '    text = """hello',
    "# still a string",
    'end""" # a comment',
    "    return '<img src=x onerror=evil()>'",
    "VALUE = 'unterminated",
    "if True: return 1.2e-3 # note",
    "x = 'escaped\\' quote'",
    "return '" + "x".repeat(500),
  ];
  const result = colorSource(lines);
  expect(result.map((tokens) => tokens.map((t) => t.text).join(""))).toEqual(
    lines,
  );
  expect(result[2]).toEqual([{ kind: "string", text: lines[2] }]);
  expect(result[3].at(-1)?.kind).toBe("comment");
  expect(result[4].at(-1)?.kind).toBe("string");
  expect(result[6]).toContainEqual({ kind: "number", text: "1.2e-3" });
  expect(result[6].some((t) => t.kind === "keyword")).toBe(true);
  expect(
    colorSource(["", "'''", "", "'''return 2"]).map((tokens) =>
      tokens.map((t) => t.text).join(""),
    ),
  ).toEqual(["", "'''", "", "'''return 2"]);
});
