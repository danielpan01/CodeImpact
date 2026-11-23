import type { Report } from "./types";

export function DiscoveryScope({ report }: { report: Report }) {
  const removed = new Set(report.removed);
  const current = report.nodes.filter((node) => !removed.has(node.id));
  const discovered = current.filter((node) => node.kind === "test").length;
  const outside = current.filter(
    (node) =>
      node.kind === "function" &&
      node.name.split(".").at(-1)?.startsWith("test_"),
  );
  return (
    <details className="discovery-scope">
      <summary>Test discovery scope</summary>
      <p>
        {discovered} discovered{" "}
        {discovered === 1 ? "definition" : "definitions"} in the current
        snapshot. CodeImpact recognizes <code>test_</code> functions in{" "}
        <code>test.py</code>, <code>test_*.py</code> and <code>*_test.py</code>,
        including direct class methods and nested functions.
      </p>
      <p>
        This is static discovery, not pytest collection. Definitions inside
        conditional, loop or try blocks are not indexed. Parameter variants,
        inherited test executions and fixture injection are not collected.
      </p>
      {report.schema_version === "2.1" && (
        <p>
          Fixture evidence links a test parameter to a supported same-directory
          conftest fixture.
        </p>
      )}
      {outside.length > 0 && (
        <p>
          {outside.length} indexed test-shaped{" "}
          {outside.length === 1 ? "function is" : "functions are"} outside the
          supported filenames. This count excludes definitions the index cannot
          see.
        </p>
      )}
      <p>Keep the full test suite as your merge gate.</p>
    </details>
  );
}
