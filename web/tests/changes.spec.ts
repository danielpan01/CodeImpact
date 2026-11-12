import {
  loadDemo,
  openAnalysis,
  showEvidence,
  openChangedCode,
} from "./helpers";
import { test, expect, type Page } from "@playwright/test";
import { readFile } from "node:fs/promises";
import type { Report } from "../src/types";

async function upload(
  page: Page,
  base: Record<string, string>,
  head: Record<string, string>,
) {
  await loadDemo(page);
  await openAnalysis(page);
  await expect(
    page.getByRole("button", { name: "Analyze PR", exact: true }),
  ).toBeEnabled();
  await openAnalysis(page);
  await page.getByLabel("Upload snapshot JSON").setInputFiles({
    name: "changes.json",
    mimeType: "application/json",
    buffer: Buffer.from(
      JSON.stringify({
        label: "Code review fixture",
        base: { files: base },
        head: { files: head },
      }),
    ),
  });
  await expect(page.locator(".analysis-label")).toContainText(
    "Code review fixture",
  );
}

test("changes open from a recommendation and keep its explanation", async ({
  page,
}, testInfo) => {
  await loadDemo(page);
  await expect(page.locator(".detail-content")).toContainText("test_discount");
  await showEvidence(page);
  const open = page.getByRole("button", { name: "Open changed code" });
  await open.focus();
  await page.keyboard.press("Enter");
  await expect(
    page.getByRole("region", { name: "Change explorer" }),
  ).toBeFocused();
  await expect(
    page.getByRole("button", { name: "Changes", exact: true }),
  ).toHaveAttribute("aria-pressed", "true");
  await expect(
    page.getByRole("region", { name: "Before source" }),
  ).toContainText("0.10");
  await expect(
    page.getByRole("region", { name: "After source" }),
  ).toContainText("0.15");
  await expect(page.locator(".detail-content")).toContainText("test_discount");
  await expect(page.locator(".detail-content")).toContainText(
    "Path exists in both revisions",
  );
  await expect(page.locator(".detail-content")).toContainText("Resolved call");
  await expect(page.locator(".detail-content")).toContainText("Before:");
  await expect(page.locator(".detail-content")).toContainText("After:");
  await expect(
    page.getByRole("button", { name: /modified.*discount/ }),
  ).toBeVisible();
  await page.screenshot({
    path: testInfo.outputPath("changed-code.png"),
    fullPage: true,
  });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await page.getByRole("button", { name: "Tests", exact: true }).click();
  await expect(page.locator(".test-row")).toHaveCount(3);
  await page.getByRole("button", { name: "Map", exact: true }).click();
  await expect(page.getByTestId("dependency-graph")).toBeVisible();
  await page.keyboard.press("Shift+Tab");
  await expect(
    page.getByRole("button", { name: "Tests", exact: true }),
  ).toBeFocused();
  await page.keyboard.press("Tab");
  await page.keyboard.press("Tab");
  await expect(
    page.getByRole("button", { name: "Changes", exact: true }),
  ).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(
    page.getByRole("region", { name: "Before source" }),
  ).toContainText("0.10");
});

test("deleted source, decorators, safe text, added files and export", async ({
  page,
}) => {
  const old =
    '@decorate\ndef removed():\n    return "<img src=x onerror=window.sourceExecuted=true>"\n';
  const base = {
    "old.py": old,
    "test_old.py":
      "from old import removed\ndef test_old(): return removed()\n",
  };
  const head = {
    "test_old.py": base["test_old.py"],
    "new.py": "def added(): return 3\n",
  };
  await upload(page, base, head);
  await openChangedCode(page);
  const before = page.getByRole("region", { name: "Before source" });
  const after = page.getByRole("region", { name: "After source" });
  await expect(before).toContainText("@decorate");
  await expect(before).toContainText(
    "<img src=x onerror=window.sourceExecuted=true>",
  );
  await expect(before.locator("img")).toHaveCount(0);
  expect(await page.evaluate(() => "sourceExecuted" in window)).toBe(false);
  await expect(before.locator(".source-line").first()).toHaveAttribute(
    "data-line",
    "1",
  );
  await expect(after).toContainText("File absent in this revision");
  await expect(page.locator(".detail-content")).toContainText(
    "Path exists only before",
  );
  const added = page.getByRole("button", { name: /added.*added/ });
  await added.focus();
  await page.keyboard.press("Enter");
  await expect(before).toContainText("File absent in this revision");
  await expect(after).toContainText("def added()");
  await expect(
    page.getByText("Export includes source code", { exact: true }),
  ).toBeVisible();
  const downloadPromise = page.waitForEvent("download");
  await page.getByRole("button", { name: "Export report" }).click();
  const download = await downloadPromise;
  const report: Report = JSON.parse(
    await readFile((await download.path())!, "utf8"),
  );
  expect(report.schema_version).toBe("2.0");
  expect(
    report.source_files.find((f) => f.path === "old.py")?.before?.text,
  ).toBe(old);
  const edges = new Map(report.edges.map((e) => [e.id, e]));
  for (const r of report.recommendations) {
    expect(r.evidence_path[0]).toBe(r.symbol);
    expect(report.changed).toContain(r.evidence_path.at(-1));
    expect(report.removed).not.toContain(r.symbol);
    expect(r.evidence_edges).toHaveLength(r.evidence_path.length - 1);
    r.evidence_edges.forEach((id, i) => {
      expect(edges.get(id)?.source).toBe(r.evidence_path[i]);
      expect(edges.get(id)?.target).toBe(r.evidence_path[i + 1]);
    });
  }
});

test("mixed revision path is visible while reviewing deleted code", async ({
  page,
}) => {
  const base = {
    "a.py": "def f(): return 1\n",
    "b.py": "def f(): return 2\n",
    "bridge.py": "from a import f\ndef g(): return f()\n",
    "test_bridge.py": "from b import f as g\ndef test_g(): return g()\n",
  };
  await upload(page, base, {
    ...base,
    "a.py": "",
    "bridge.py": "from b import f\ndef g(): return f()\n",
    "test_bridge.py": "from bridge import g\ndef test_g(): return g()\n",
  });
  await expect(page.locator(".detail-content")).toContainText(
    "Mixed revisions — no single revision contains this entire shown path",
  );
  await openChangedCode(page);
  await expect(
    page.getByRole("region", { name: "Before source" }),
  ).toContainText("def f()");
  await expect(
    page.getByRole("region", { name: "After source" }),
  ).toContainText("Empty file");
  await expect(page.locator(".detail-content")).toContainText("Before only");
  await expect(page.locator(".detail-content")).toContainText("After only");
});

test("parse failures and bounded previews are explicit", async ({ page }) => {
  await upload(page, { "a.py": "VALUE =\n" }, { "a.py": "# fixed\n" });
  await page.getByRole("button", { name: "Changes", exact: true }).click();
  await expect(
    page.getByRole("region", { name: "Before source" }),
  ).toContainText("Could not parse");
  await expect(
    page.getByRole("region", { name: "Before source" }),
  ).toContainText("VALUE =");
  await expect(
    page.getByRole("region", { name: "After source" }),
  ).toContainText("# fixed");
  const large =
    "# padding\n".repeat(200) +
    "@decorate\ndef late(): return '" +
    "x".repeat(16000) +
    "'\n";
  await upload(page, {}, { "large.py": large });
  await page.getByRole("button", { name: "Changes", exact: true }).click();
  await expect(
    page.getByRole("region", { name: "After source" }),
  ).toContainText("Preview truncated");
  await page.getByRole("button", { name: /added.*late/ }).click();
  const after = page.getByRole("region", { name: "After source" });
  await expect(after.locator(".source-line").first()).toHaveAttribute(
    "data-line",
    "201",
  );
  await expect(after).toContainText("@decorate");
  await expect(after).toContainText("Preview truncated");
  expect((await after.textContent())!.length).toBeLessThan(14000);
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
});

test("module fallback, comment controls and report-version recovery", async ({
  page,
}) => {
  const base = {
    "a.py": "VALUE = 1\n",
    "test_a.py": "import a\ndef test_a(): return a.VALUE\n",
  };
  await upload(page, base, { ...base, "a.py": "VALUE = 2\n" });
  await expect(page.locator(".detail-content")).toContainText(
    "Conservative module/import dependency",
  );
  await openChangedCode(page);
  await expect(
    page.getByRole("region", { name: "After source" }),
  ).toContainText("VALUE = 2");
  await expect(page.locator(".detail-content")).toContainText(
    "Conservative import dependency",
  );
  await showEvidence(page);
  await page.locator(".revision-evidence summary").first().click();
  await expect(page.locator(".revision-evidence").first()).toContainText(
    "test_a.py:2",
  );
  await upload(page, { "a.py": "" }, { "a.py": "# comment only\n" });
  await page.getByRole("button", { name: "Changes", exact: true }).click();
  await expect(
    page.getByText("No semantic changes in these snapshots."),
  ).toBeVisible();
  await page.route("**/api/demo", (route) =>
    route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({ schema_version: "1.0" }),
    }),
  );
  await openAnalysis(page);
  await page.getByRole("button", { name: "Load demo" }).click();
  await expect(page.getByRole("alert")).toContainText(
    "Unsupported report version",
  );
  await expect(
    page.getByRole("button", { name: "Export report" }),
  ).toBeDisabled();
  await page.unroute("**/api/demo");
  await page.getByRole("button", { name: "Retry demo" }).click();
  await openChangedCode(page);
  await expect(
    page.getByRole("region", { name: "After source" }),
  ).toContainText("0.15");
});

test("preview character budget includes line breaks and export preserves full source", async ({
  page,
}) => {
  const source = ("#" + "x".repeat(499) + "\n").repeat(50) + "VALUE = 1\n";
  await upload(page, {}, { "large.py": source });
  const previewRequests: string[] = [];
  page.on("request", (request) => {
    if (request.url().includes("/api/")) previewRequests.push(request.url());
  });
  await page.getByRole("button", { name: "Changes", exact: true }).click();
  const after = page.getByRole("region", { name: "After source" });
  await expect(after).toContainText("Preview truncated");
  // Count source text and rendered newlines, excluding the generated truncation marker.
  const characters = await after
    .locator(".source-line > code")
    .evaluateAll((codes) =>
      codes.reduce(
        (total, code) =>
          total +
          Array.from(code.childNodes)
            .filter((node) => node.nodeType === Node.TEXT_NODE)
            .reduce(
              (length, node) => length + (node.textContent?.length ?? 0),
              0,
            ),
        0,
      ),
    );
  expect(characters).toBeGreaterThan(0);
  expect(characters).toBeLessThanOrEqual(12_000);
  expect(await after.locator(".source-line").count()).toBeLessThanOrEqual(120);
  const downloadPromise = page.waitForEvent("download");
  await page.getByRole("button", { name: "Export report" }).click();
  const report: Report = JSON.parse(
    await readFile((await (await downloadPromise).path())!, "utf8"),
  );
  expect(report.source_files[0].after?.text).toBe(source);
  expect(previewRequests).toEqual([]);
});
