import { test, expect, type Page } from "@playwright/test";
import { readFile } from "node:fs/promises";
import { loadDemo, showEvidence, openChangedCode } from "./helpers";
import type { Report } from "../src/types";

async function backToResults(page: Page) {
  const back = page.getByRole("button", {
    name: "Back to results",
    exact: true,
  });
  if (await back.isVisible()) await back.click();
}
async function upload(page: Page, request: unknown): Promise<Report> {
  await page.goto("/");
  const response = page.waitForResponse("**/api/analyze");
  await page.getByLabel("Upload snapshot JSON").setInputFiles({
    name: "review.json",
    mimeType: "application/json",
    buffer: Buffer.from(JSON.stringify(request)),
  });
  const result = await response;
  expect(result.status()).toBe(200);
  await expect(
    page.getByRole("button", { name: "Tests", exact: true }),
  ).toHaveAttribute("aria-pressed", "true");
  return result.json();
}
async function expectExport(page: Page, report: Report) {
  const download = page.waitForEvent("download");
  await page
    .getByRole("button", { name: "Export report", exact: true })
    .click();
  expect(
    JSON.parse(await readFile((await (await download).path())!, "utf8")),
  ).toEqual(report);
}
async function expectPath(page: Page, report: Report, id: string) {
  const recommendation = report.recommendations.find((r) => r.symbol === id)!;
  await expect(page.locator(".react-flow__node")).toHaveCount(
    recommendation.evidence_path.length,
  );
  expect(
    await page
      .locator(".react-flow__node")
      .evaluateAll((nodes) => nodes.map((n) => n.getAttribute("data-id"))),
  ).toEqual(recommendation.evidence_path);
  await expect(page.locator(".react-flow__edge")).toHaveCount(
    recommendation.evidence_edges.length,
  );
  expect(
    (
      await page
        .locator(".react-flow__edge")
        .evaluateAll((edges) => edges.map((e) => e.getAttribute("data-id")))
    ).sort(),
  ).toEqual([...recommendation.evidence_edges].sort());
  for (const id of recommendation.evidence_edges) {
    const edge = report.edges.find((e) => e.id === id)!;
    // Accessible labels retain the original caller → dependency direction and revision.
    await expect(
      page.getByLabel(
        `${edge.kind === "call" ? "Resolved call" : `Conservative ${edge.kind} dependency`}: ${edge.source} → ${edge.target}, ${edge.revision} revisions`,
        { exact: true },
      ),
    ).toHaveCount(1);
  }
}

test("test search, sort and reset retain selection and expanded evidence by keyboard", async ({
  page,
}) => {
  const response = page.waitForResponse("**/api/demo");
  await loadDemo(page);
  const report: Report = await (await response).json();
  await page.getByRole("button", { name: /test_create_order/ }).click();
  await page.locator(".revision-evidence summary").first().click();
  await backToResults(page);
  const search = page.getByRole("searchbox", { name: "Search tests" });
  await search.focus();
  await search.fill("TEST_PRICING.PY discount");
  await expect(page.locator(".test-row")).toHaveCount(1);
  await expect(page.getByRole("status")).toHaveText("1 of 3 tests");
  await expect(
    page.getByText(
      "Selected test is outside these results. Its evidence is retained.",
    ),
  ).toBeVisible();
  await expect(page.locator(".detail-content h3")).toHaveText(
    "test_create_order",
  );
  await search.fill("missing[");
  await expect(
    page.getByRole("heading", { name: "No matching tests" }),
  ).toBeVisible();
  const reveal = page.getByRole("button", { name: "Show selected test" });
  await reveal.focus();
  await reveal.press("Enter");
  await expect(
    page.getByRole("button", { name: /test_create_order/ }),
  ).toBeFocused();
  await page.getByLabel("Sort tests").selectOption("name");
  await expect(page.locator(".test-identity strong")).toHaveText([
    "test_checkout",
    "test_create_order",
    "test_discount",
  ]);
  await page.getByRole("button", { name: "Map", exact: true }).click();
  await page.getByRole("button", { name: "Tests", exact: true }).click();
  await expect(page.getByLabel("Sort tests")).toHaveValue("name");
  await showEvidence(page);
  await expect(page.locator(".revision-evidence").first()).toHaveAttribute(
    "open",
    "",
  );
  await openChangedCode(page);
  await page.getByRole("button", { name: "Tests", exact: true }).click();
  await page.getByRole("button", { name: "Reset tests" }).click();
  expect(
    await page
      .locator(".test-row")
      .evaluateAll((rows) =>
        rows.map((row) => row.getAttribute("data-symbol")),
      ),
  ).toEqual(report.recommendations.map((r) => r.symbol));
  await expectExport(page, report);
});

for (const caseId of ["slugify_ascii", "slugify_boundary", "cachetools_lfu"]) {
  test(`pinned ${caseId} filters, focuses exact evidence and exports the full report`, async ({
    page,
  }) => {
    const fixture = JSON.parse(
      await readFile(
        new URL(`../../corpus/real-v2/cases/${caseId}.json`, import.meta.url),
        "utf8",
      ),
    );
    const report = await upload(page, fixture.request);
    const selected = report.recommendations.at(-1)!;
    await page
      .getByRole("searchbox", { name: "Search tests" })
      .fill(selected.symbol);
    await expect(page.locator(".test-row")).toHaveCount(1);
    await page
      .getByLabel("Explanation", { exact: true })
      .selectOption(
        selected.reason === "Resolved call path" ? "resolved" : "conservative",
      );
    await page.getByLabel("Sort tests").selectOption("file");
    await page.locator(".test-row").click();
    await page
      .getByRole("button", { name: "Focus path in Map" })
      .press("Enter");
    await expectPath(page, report, selected.symbol);
    await page
      .getByLabel("Jump to path symbol")
      .selectOption(selected.evidence_path.at(-1)!);
    await page
      .getByRole("button", { name: "Inspect test", exact: true })
      .click();
    await openChangedCode(page);
    await expect(
      page.getByRole("region", { name: "Selected changed code" }),
    ).toContainText(selected.evidence_path.at(-1)!.split("::")[1]);
    await page.getByRole("button", { name: "Tests", exact: true }).click();
    await expect(page.locator(".test-row[aria-pressed=true]")).toHaveAttribute(
      "data-symbol",
      selected.symbol,
    );
    await expect(page.getByRole("status")).toHaveText(
      `1 of ${report.recommendations.length} tests`,
    );
    await expectExport(page, report);
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
  });
}

test("graph focus retains fallback module identities and reset fits the full overview", async ({
  page,
}) => {
  const base = {
    "a.py": "VALUE = 1\n",
    "test_a.py": "import a\ndef test_a(): return a.VALUE\n",
  };
  const report = await upload(page, {
    label: "Fallback review",
    base: { files: base },
    head: { files: { ...base, "a.py": "VALUE = 2\n" } },
  });
  await page
    .getByLabel("Explanation", { exact: true })
    .selectOption("conservative");
  await page.locator(".test-row").click();
  await page.getByRole("button", { name: "Focus path in Map" }).click();
  await expectPath(page, report, report.recommendations[0].symbol);
  await expect(page.locator(".react-flow__edge-path").first()).toHaveCSS(
    "stroke-dasharray",
    "5px, 4px",
  );
  const node = page.locator(".react-flow__node").last();
  await page
    .getByLabel("Jump to path symbol")
    .selectOption(report.recommendations[0].evidence_path.at(-1)!);
  await node.focus();
  await node.press("Enter");
  await backToResults(page);
  await expect(
    page.getByText("Focused evidence path", { exact: true }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Reset map", exact: true })
    .press("Enter");
  await expect(page.getByLabel("Search symbols")).toHaveValue("");
  await expect(page.getByLabel("Module dependencies")).not.toBeChecked();
  await expect(page.locator(".react-flow__node")).toHaveCount(
    report.nodes.filter((n) => n.kind !== "module").length,
  );
  await expect
    .poll(() =>
      page.getByTestId("dependency-graph").evaluate((canvas) => {
        const bounds = canvas.getBoundingClientRect();
        return [...canvas.querySelectorAll(".react-flow__node")].every((n) => {
          const r = n.getBoundingClientRect();
          return (
            r.left >= bounds.left &&
            r.right <= bounds.right &&
            r.top >= bounds.top &&
            r.bottom <= bounds.bottom
          );
        });
      }),
    )
    .toBe(true);
});

test("long focused paths can jump to their endpoint and preserve viewport across views", async ({
  page,
}) => {
  const functions =
    Array.from(
      { length: 10 },
      (_, i) => `def f${i}(): return ${i === 9 ? "1" : `f${i + 1}()`}`,
    ).join("\n") + "\n";
  const files = {
    "chain.py": functions,
    "test_chain.py": "from chain import f0\ndef test_chain(): return f0()\n",
  };
  const report = await upload(page, {
    label: "Long path",
    base: { files },
    head: {
      files: {
        ...files,
        "chain.py": functions.replace("return 1\n", "return 2\n"),
      },
    },
  });
  await page.locator(".test-row").click();
  await page.getByRole("button", { name: "Focus path in Map" }).click();
  const recommendation = report.recommendations[0];
  expect(recommendation.evidence_path.length).toBe(11);
  await expectPath(page, report, recommendation.symbol);
  await page
    .getByLabel("Jump to path symbol")
    .selectOption(recommendation.evidence_path.at(-1)!);
  const last = page.locator(".react-flow__node").last();
  await expect
    .poll(async () => {
      const r = await last.boundingBox();
      const c = await page.getByTestId("dependency-graph").boundingBox();
      return !!r && !!c && r.y >= c.y && r.y + r.height <= c.y + c.height;
    })
    .toBe(true);
  const transform = await page
    .locator(".react-flow__viewport")
    .getAttribute("style");
  await page.getByRole("button", { name: "Tests", exact: true }).click();
  await page.getByRole("button", { name: "Map", exact: true }).click();
  await expect(page.locator(".react-flow__viewport")).toHaveAttribute(
    "style",
    transform!,
  );
});

test("syntax coloring remains escaped text with unchanged line content", async ({
  page,
}) => {
  const source =
    'def message():\n    """hello\n    # string content\n    """\n    return "<img src=x onerror=window.sourceExecuted=true>" # note\n';
  await upload(page, {
    label: "Safe source",
    base: { files: {} },
    head: { files: { "message.py": source } },
  });
  await page.getByRole("button", { name: "Changes", exact: true }).click();
  const code = page.getByRole("region", { name: "After source" });
  expect(
    (await code.locator(".source-line > code").allTextContents()).join(""),
  ).toBe(source);
  await expect(code.locator(".syntax-keyword").first()).toHaveText("def");
  await expect(code.locator(".syntax-comment")).toHaveText("# note");
  await expect(code.locator("img")).toHaveCount(0);
  expect(await page.evaluate(() => "sourceExecuted" in window)).toBe(false);
});

test("focused mixed paths keep removed nodes, exact edges and the source route", async ({
  page,
}) => {
  const files = {
    "a.py": "def f(): return 1\n",
    "b.py": "def f(): return 2\n",
    "bridge.py": "from a import f\ndef g(): return f()\n",
    "test_bridge.py": "from b import f as g\ndef test_g(): return g()\n",
  };
  const report = await upload(page, {
    label: "Mixed path",
    base: { files },
    head: {
      files: {
        ...files,
        "a.py": "",
        "bridge.py": "from b import f\ndef g(): return f()\n",
        "test_bridge.py": "from bridge import g\ndef test_g(): return g()\n",
      },
    },
  });
  const recommendation = report.recommendations[0];
  expect(recommendation.path_revision).toBe("mixed");
  await page.locator(".test-row").first().click();
  await page.getByRole("button", { name: "Focus path in Map" }).click();
  await expectPath(page, report, recommendation.symbol);
  await expect(
    page.getByText(
      "No single revision contains this entire path. This combined path is a conservative estimate.",
      { exact: true },
    ),
  ).toBeVisible();
  await expect(page.locator(".react-flow__node.removed")).toHaveCount(1);
  await page.getByRole("button", { name: "Inspect test", exact: true }).click();
  await openChangedCode(page);
  await expect(
    page.getByRole("region", { name: "After source" }),
  ).toContainText("Empty file");
  await expectExport(page, report);
});

test("a new analysis resets review filters and map focus without carrying stale state", async ({
  page,
}) => {
  await loadDemo(page);
  await page.getByRole("searchbox", { name: "Search tests" }).fill("checkout");
  await page.getByLabel("Sort tests").selectOption("priority");
  await page.locator(".test-row").click();
  await page.getByRole("button", { name: "Focus path in Map" }).click();
  await page.getByRole("button", { name: "New analysis", exact: true }).click();
  await page.getByRole("button", { name: "Load demo", exact: true }).click();
  await expect(
    page.getByRole("searchbox", { name: "Search tests" }),
  ).toHaveValue("");
  await expect(page.getByLabel("Sort tests")).toHaveValue("analysis");
  await expect(page.getByLabel("Explanation", { exact: true })).toHaveValue(
    "all",
  );
  await page.getByRole("button", { name: "Map", exact: true }).click();
  await expect(page.getByLabel("Search symbols")).toHaveValue("");
  await expect(
    page.getByText("Focused evidence path", { exact: true }),
  ).toHaveCount(0);
  await expect(page.locator(".react-flow__node")).toHaveCount(8);
});
