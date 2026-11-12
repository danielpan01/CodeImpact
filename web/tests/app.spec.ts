import { test, expect } from "@playwright/test";
import { readFile } from "node:fs/promises";
import type { Report } from "../src/types";

const publicPR = "https://github.com/acme/widget/pull/7";

test("demo graph and explanation show real backend results", async ({
  page,
}) => {
  await page.goto("/");
  await expect(
    page.getByText("Checkout service · discount 10% → 15%"),
  ).toBeVisible();
  await expect(page.getByTestId("dependency-graph")).toBeVisible();
  await expect(page.locator(".detail-content")).toContainText("test_discount");
  await expect(page.locator(".detail-content")).toContainText(
    "Resolved call path",
  );
  await expect(page.locator(".react-flow__node")).toHaveCount(8);
  await page.getByLabel("Search symbols").fill("test_health");
  await expect(page.locator(".react-flow__node")).toHaveCount(1);
  await expect(page.locator(".react-flow__node")).toHaveClass(/unaffected/);
  await page.getByRole("button", { name: "Tests", exact: true }).click();
  await expect(page.locator(".test-row")).toHaveCount(3);
  await page.getByRole("button", { name: /test_create_order/ }).click();
  await expect(page.locator(".evidence-path li")).toHaveCount(4);
  await expect(page.locator(".evidence-path li").last()).toContainText(
    "discount",
  );
});

test("upload handles valid empty snapshots and invalid input", async ({
  page,
}) => {
  await page.goto("/");
  await expect(
    page.getByText("Checkout service · discount 10% → 15%"),
  ).toBeVisible();
  await page.getByLabel("Upload snapshot JSON").setInputFiles({
    name: "empty.json",
    mimeType: "application/json",
    buffer: Buffer.from(
      JSON.stringify({
        base: { files: {} },
        head: { files: {} },
        label: "Empty repository",
      }),
    ),
  });
  await expect(page.locator(".analysis-label")).toContainText(
    "Empty repository",
  );
  await expect(page.getByText("No symbols match this view.")).toBeVisible();
  await page.getByLabel("Upload snapshot JSON").setInputFiles({
    name: "invalid.json",
    mimeType: "application/json",
    buffer: Buffer.from("{broken"),
  });
  await expect(page.getByRole("alert")).toBeVisible();
  await page.getByRole("button", { name: "Retry demo" }).click();
  await expect(
    page.getByText("Checkout service · discount 10% → 15%"),
  ).toBeVisible();
});

test("report downloads with analysis data", async ({ page }) => {
  await page.goto("/");
  await expect(
    page.getByText("Checkout service · discount 10% → 15%"),
  ).toBeVisible();
  const promise = page.waitForEvent("download");
  await page.getByRole("button", { name: "Export report" }).click();
  expect((await promise).suggestedFilename()).toBe("codeimpact-report.json");
});

test("local import corpus upload shows resolved evidence and exports scoped imports", async ({
  page,
}) => {
  // Snapshot Python remains JSON string data; only CodeImpact analyzes it.
  const fixture = JSON.parse(
    await readFile(
      new URL("../../corpus/cases/local_import.json", import.meta.url),
      "utf8",
    ),
  );
  await page.goto("/");
  await expect(page.locator(".detail-content")).toContainText("test_discount");
  const responsePromise = page.waitForResponse("**/api/analyze");
  await page.getByLabel("Upload snapshot JSON").setInputFiles({
    name: "local-import.json",
    mimeType: "application/json",
    buffer: Buffer.from(JSON.stringify(fixture.request)),
  });
  const response = await responsePromise;
  expect(response.status()).toBe(200);
  const report: Report = await response.json();
  await expect(page.locator(".analysis-label")).toContainText("local_import");
  await page.getByRole("button", { name: "Tests", exact: true }).click();
  await expect(page.locator(".test-row")).toHaveCount(1);
  await page.getByRole("button", { name: /test_read/ }).click();
  await expect(page.locator(".detail-content")).toContainText(
    "Resolved call path",
  );
  await expect(page.locator(".evidence-path li")).toHaveCount(3);
  expect(report.recommendations.map((item) => item.symbol)).toEqual([
    "tests/test_worker.py::test_read",
  ]);
  expect(report.recommendations[0].evidence_path).toEqual([
    "tests/test_worker.py::test_read",
    "worker.py::read",
    "core.py::price",
  ]);
  expect(report.edges).toEqual(
    expect.arrayContaining([
      expect.objectContaining({
        source: "worker.py::read",
        target: "core.py::<module>",
        kind: "import",
        revision: "both",
      }),
    ]),
  );
  expect(
    report.edges.some(
      (edge) => edge.source === "worker.py::<module>" && edge.kind === "import",
    ),
  ).toBe(false);
  await page.getByRole("button", { name: "Open changed code" }).click();
  await expect(
    page.getByRole("region", { name: "Before source" }),
  ).toContainText("return 1");
  await expect(
    page.getByRole("region", { name: "After source" }),
  ).toContainText("return 2");
  await expect(page.locator(".detail-content")).toContainText(
    "Path exists in both revisions",
  );
  const downloadPromise = page.waitForEvent("download");
  await page.getByRole("button", { name: "Export report" }).click();
  const download = await downloadPromise;
  expect(JSON.parse(await readFile((await download.path())!, "utf8"))).toEqual(
    report,
  );
});

test("rebound module import keeps graph evidence without selecting the unrelated wrapper", async ({
  page,
}) => {
  const fixture = JSON.parse(
    await readFile(
      new URL("../../corpus/cases/module_rebinding.json", import.meta.url),
      "utf8",
    ),
  );
  await page.goto("/");
  await expect(page.locator(".detail-content")).toContainText("test_discount");
  const responsePromise = page.waitForResponse("**/api/analyze");
  await page.getByLabel("Upload snapshot JSON").setInputFiles({
    name: "module-rebinding.json",
    mimeType: "application/json",
    buffer: Buffer.from(JSON.stringify(fixture.request)),
  });
  const response = await responsePromise;
  expect(response.status()).toBe(200);
  const report: Report = await response.json();
  await expect(page.locator(".analysis-label")).toContainText(
    "module_rebinding",
  );
  await page.getByRole("button", { name: "Tests", exact: true }).click();
  await expect(page.locator(".test-row")).toHaveCount(1);
  await expect(page.locator(".test-row")).toContainText("test_price");
  await expect(page.locator(".detail-content")).toContainText(
    "Resolved call path",
  );
  await expect(page.locator(".risk-score")).toContainText("81");
  await expect(page.locator(".evidence-path li")).toHaveCount(2);
  expect(report.recommendations.map((item) => item.symbol)).toEqual([
    "tests/test_price.py::test_price",
  ]);
  expect(
    report.edges.some(
      (edge) =>
        edge.source === "worker.py::<module>" &&
        edge.target === "core.py::<module>" &&
        edge.kind === "import",
    ),
  ).toBe(true);
  expect(
    report.edges.some(
      (edge) => edge.source === "worker.py::read" && edge.kind === "call",
    ),
  ).toBe(false);
  await page.getByRole("button", { name: "Open changed code" }).click();
  await expect(page.locator(".detail-content")).toContainText(
    "Path exists in both revisions",
  );
  await expect(
    page.getByRole("region", { name: "After source" }),
  ).toContainText("return 2");
  const downloadPromise = page.waitForEvent("download");
  await page.getByRole("button", { name: "Export report" }).click();
  const download = await downloadPromise;
  expect(JSON.parse(await readFile((await download.path())!, "utf8"))).toEqual(
    report,
  );
});

test("public PR uses real ingestion, pinned revisions and valid exported evidence", async ({
  page,
}, testInfo) => {
  await page.goto("/");
  await expect(
    page.getByRole("button", { name: "Analyze PR", exact: true }),
  ).toBeEnabled();
  const input = page.getByLabel("Analyze a GitHub pull request", {
    exact: true,
  });
  await input.fill(publicPR);
  const responsePromise = page.waitForResponse("**/api/github/pr");
  // Submitting by keyboard must work as well as clicking the button.
  await input.press("Enter");
  const response = await responsePromise;
  expect(response.status()).toBe(200);
  const report: Report = await response.json();
  await expect(
    page.getByRole("region", { name: "GitHub analysis source" }),
  ).toContainText("acme/widget #7");
  await page.getByText("Exact analyzed revisions", { exact: true }).click();
  await expect(page.locator(".pr-source")).toContainText("a".repeat(40));
  await expect(page.locator(".pr-source")).toContainText("c".repeat(40));
  await expect(page.locator(".pr-source")).toContainText(
    "contributor/widget-fork",
  );
  await expect(page.locator(".react-flow__node")).toHaveCount(5);
  await expect(page.locator(".detail-content")).toContainText(
    "Resolved call path",
  );
  await expect(page.locator(".evidence-path li")).toHaveCount(3);
  await expect(page.locator(".evidence-path li").first()).toContainText(
    "test_cart",
  );
  await expect(page.locator(".evidence-path li").last()).toContainText("price");
  const edges = new Set(report.edges.map((e) => `${e.source}\n${e.target}`));
  expect(report.recommendations).toHaveLength(1);
  for (const item of report.recommendations) {
    expect(item.evidence_path[0]).toBe(item.symbol);
    expect(report.changed).toContain(item.evidence_path.at(-1));
    expect(report.removed).not.toContain(item.symbol);
    for (let i = 1; i < item.evidence_path.length; i++) {
      expect(
        edges.has(`${item.evidence_path[i - 1]}\n${item.evidence_path[i]}`),
      ).toBe(true);
    }
  }
  expect(report.impacted).not.toContain("test_health.py::test_health");
  await page.getByRole("button", { name: "Open changed code" }).click();
  await expect(
    page.getByRole("region", { name: "Before source" }),
  ).toContainText("return 10");
  await expect(
    page.getByRole("region", { name: "After source" }),
  ).toContainText("return 20");
  await expect(page.locator(".detail-content")).toContainText(
    "Path exists in both revisions",
  );
  expect(report.schema_version).toBe("2.0");
  expect(report.source_files[0].path).toBe("core.py");
  const typedEdges = new Map(report.edges.map((edge) => [edge.id, edge]));
  for (const item of report.recommendations) {
    expect(item.evidence_edges).toHaveLength(item.evidence_path.length - 1);
    item.evidence_edges.forEach((id, i) => {
      expect(typedEdges.get(id)?.source).toBe(item.evidence_path[i]);
      expect(typedEdges.get(id)?.target).toBe(item.evidence_path[i + 1]);
      expect(typedEdges.get(id)?.kind).toBe("call");
    });
  }
  const downloadPromise = page.waitForEvent("download");
  await page.getByRole("button", { name: "Export report" }).click();
  const download = await downloadPromise;
  expect(JSON.parse(await readFile((await download.path())!, "utf8"))).toEqual(
    report,
  );
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: testInfo.outputPath("public-pr.png"),
    fullPage: true,
  });
  // Switching back must clear PR provenance while preserving the demo behavior.
  await page.getByRole("button", { name: "Load demo" }).click();
  await expect(page.locator(".analysis-label")).toContainText(
    "Checkout service",
  );
  await expect(page.locator(".pr-source")).toHaveCount(0);
  await expect(
    page.getByRole("region", { name: "After source" }),
  ).toContainText("0.15");
});

test("PR rate-limit failure clears old results and retries the same URL", async ({
  page,
}, testInfo) => {
  let attempts = 0;
  let releaseRequest!: () => void;
  const released = new Promise<void>((resolve) => {
    releaseRequest = resolve;
  });
  await page.route("**/api/github/pr", async (route) => {
    attempts++;
    expect(route.request().postDataJSON()).toEqual({ url: publicPR });
    if (attempts === 1) {
      await released;
      await route.fulfill({
        status: 429,
        contentType: "application/json",
        body: JSON.stringify({
          detail: {
            code: "rate_limited",
            message: "GitHub limited this request. Wait before retrying.",
            retryable: true,
          },
        }),
      });
    } else {
      await route.continue();
    }
  });
  await page.goto("/");
  await expect(
    page.getByRole("button", { name: "Analyze PR", exact: true }),
  ).toBeEnabled();
  await page
    .getByLabel("Analyze a GitHub pull request", { exact: true })
    .fill(publicPR);
  await page.getByRole("button", { name: "Analyze PR", exact: true }).click();
  await expect(page.getByRole("status")).toContainText(
    "Fetching complete Python snapshots",
  );
  await expect(
    page.getByRole("button", { name: "Analyze PR", exact: true }),
  ).toBeDisabled();
  await expect(
    page.getByRole("button", { name: "Export report" }),
  ).toBeDisabled();
  releaseRequest();
  await expect(page.getByRole("alert")).toContainText("Wait before retrying");
  await expect(page.locator(".react-flow__node")).toHaveCount(0);
  await page.screenshot({
    path: testInfo.outputPath("pr-error.png"),
    fullPage: true,
  });
  await page.getByRole("button", { name: "Retry GitHub PR" }).click();
  await expect(page.locator(".pr-source")).toContainText("acme/widget #7");
  expect(attempts).toBe(2);
});

test("invalid PR URL is rejected by backend and can be corrected", async ({
  page,
}) => {
  await page.goto("/");
  await expect(
    page.getByRole("button", { name: "Analyze PR", exact: true }),
  ).toBeEnabled();
  const input = page.getByLabel("Analyze a GitHub pull request", {
    exact: true,
  });
  await input.fill("https://example.com/acme/widget/pull/7");
  await input.press("Enter");
  await expect(page.getByRole("alert")).toContainText(
    "Enter an exact https://github.com",
  );
  await input.fill(publicPR);
  await input.press("Enter");
  await expect(page.locator(".pr-source")).toContainText("acme/widget #7");
  await expect(page.getByRole("alert")).toHaveCount(0);
});

test("method edits retain conservative evidence without selecting unrelated constructors", async ({
  page,
}) => {
  const source =
    "class Widget:\n    def price(self): return 1\n    def healthy(self): return True\n";
  const tests =
    "from widget import Widget\ndef test_price(): return Widget().price()\ndef test_health(): return Widget().healthy()\ndef test_construct(): return Widget()\n";
  await page.goto("/");
  await expect(page.locator(".detail-content")).toContainText("test_discount");
  const responsePromise = page.waitForResponse("**/api/analyze");
  await page.getByLabel("Upload snapshot JSON").setInputFiles({
    name: "method-change.json",
    mimeType: "application/json",
    buffer: Buffer.from(
      JSON.stringify({
        base: { files: { "widget.py": source, "test_widget.py": tests } },
        head: {
          files: {
            "widget.py": source.replace("return 1", "return 2"),
            "test_widget.py": tests,
          },
        },
      }),
    ),
  });
  const response = await responsePromise;
  expect(response.status()).toBe(200);
  const report: Report = await response.json();
  expect(report.changed).toEqual([
    "widget.py::<module>",
    "widget.py::Widget",
    "widget.py::Widget.price",
  ]);
  expect(report.recommendations.map((r) => r.symbol)).toEqual([
    "test_widget.py::test_price",
  ]);
  await page.getByRole("button", { name: "Tests", exact: true }).click();
  await expect(page.locator(".test-row")).toHaveCount(1);
  await expect(page.locator(".detail-content")).toContainText(
    "Conservative module/import dependency",
  );
  await page.getByRole("button", { name: "Open changed code" }).click();
  await expect(
    page.getByRole("region", { name: "After source" }),
  ).toContainText("return 2");
  const downloadPromise = page.waitForEvent("download");
  await page.getByRole("button", { name: "Export report" }).click();
  const download = await downloadPromise;
  expect(JSON.parse(await readFile((await download.path())!, "utf8"))).toEqual(
    report,
  );
});

test("constructor overrides exclude unrelated tests while default users keep evidence", async ({
  page,
}) => {
  const source =
    'class Engine:\n    default_mode = "old"\n    def __init__(self, mode=None):\n        if mode is None: mode=self.default_mode\n        self.mode=mode\n';
  const tests =
    'from engine import Engine\ndef test_default(): return Engine()\ndef test_override(): return Engine(mode="explicit")\n';
  await page.goto("/");
  await expect(page.locator(".detail-content")).toContainText("test_discount");
  const responsePromise = page.waitForResponse("**/api/analyze");
  await page.getByLabel("Upload snapshot JSON").setInputFiles({
    name: "constructor-arguments.json",
    mimeType: "application/json",
    buffer: Buffer.from(
      JSON.stringify({
        base: { files: { "engine.py": source, "test_engine.py": tests } },
        head: {
          files: {
            "engine.py": source.replace('"old"', '"new"'),
            "test_engine.py": tests,
          },
        },
      }),
    ),
  });
  const response = await responsePromise;
  expect(response.status()).toBe(200);
  const report: Report = await response.json();
  expect(report.recommendations.map((r) => r.symbol)).toEqual([
    "test_engine.py::test_default",
  ]);
  expect(report.recommendations[0].evidence_path).toEqual([
    "test_engine.py::test_default",
    "engine.py::Engine",
  ]);
  expect(report.recommendations[0].path_revision).toBe("both");
  await page.getByRole("button", { name: "Tests", exact: true }).click();
  await expect(page.locator(".test-row")).toHaveCount(1);
  await expect(page.locator(".detail-content")).toContainText(
    "Resolved call path",
  );
  await page.getByRole("button", { name: "Open changed code" }).click();
  await expect(
    page.getByRole("region", { name: "After source" }),
  ).toContainText('default_mode = "new"');
  const downloadPromise = page.waitForEvent("download");
  await page.getByRole("button", { name: "Export report" }).click();
  const download = await downloadPromise;
  expect(JSON.parse(await readFile((await download.path())!, "utf8"))).toEqual(
    report,
  );
});
