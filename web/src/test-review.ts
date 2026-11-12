import type { Recommendation } from "./types";

export const categories = {
  resolved: "Resolved calls",
  conservative: "Conservative fallback",
  changed: "Test changed",
  other: "Other explanation",
} as const;
export type Category = keyof typeof categories;
export type TestControls = {
  query: string;
  category: "all" | Category;
  sort: "analysis" | "name" | "file" | "priority";
};
export const defaultTestControls: TestControls = {
  query: "",
  category: "all",
  sort: "analysis",
};

export function explanationCategory(reason: string): Category {
  switch (reason) {
    case "Resolved call path":
      return "resolved";
    case "Conservative module/import dependency":
      return "conservative";
    case "Test itself changed":
      return "changed";
    default:
      return "other";
  }
}

// Code-point ordering and a stable symbol tie-breaker are locale independent.
const compare = (a: string, b: string) => (a < b ? -1 : a > b ? 1 : 0);
export function reviewTests(
  recommendations: Recommendation[],
  controls: TestControls,
) {
  const terms = controls.query
    .trim()
    .toLowerCase()
    .split(/\s+/)
    .filter(Boolean);
  const result = recommendations.filter(
    (r) =>
      (controls.category === "all" ||
        explanationCategory(r.reason) === controls.category) &&
      terms.every((term) => r.symbol.toLowerCase().includes(term)),
  );
  if (controls.sort !== "analysis")
    result.sort((a, b) => {
      const order =
        controls.sort === "priority"
          ? a.score - b.score
          : controls.sort === "name"
            ? compare(
                a.symbol.split("::")[1] ?? a.symbol,
                b.symbol.split("::")[1] ?? b.symbol,
              )
            : compare(a.symbol.split("::")[0], b.symbol.split("::")[0]);
      return order || compare(a.symbol, b.symbol);
    });
  return result;
}
