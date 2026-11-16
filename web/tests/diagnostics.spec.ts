import { test, expect, type Page } from "@playwright/test";
import { readFile } from "node:fs/promises";
import type { Report } from "../src/types";

async function showReport(page: Page, report: Report) {
  await page.route("**/api/demo", (route) => route.fulfill({ json: report }));
  await page.goto("/");
  await page.getByRole("button", { name: "Load demo", exact: true }).click();
  await expect(page.locator(".test-row")).toHaveCount(
    report.recommendations.length,
  );
  await page.locator(".limitations > summary").click();
}

test("diagnostics preserve duplicate occurrences, literal search and complete exports", async ({
  page,
  request,
}) => {
  const report: Report = await (await request.get("/api/demo")).json();
  report.warnings = [
    "New format [.*] Ω <script>window.diagnosticExecuted = true</script>\nsecond line",
    "New format [.*] Ω <script>window.diagnosticExecuted = true</script>\nsecond line",
    "Cannot parse tests/test_pricing.py: SyntaxError",
    "Unresolved call unknown: tests/test_pricing.py:4",
  ];
  await showReport(page, report);
  await page
    .getByRole("searchbox", { name: "Search analysis notes" })
    .fill("[.*]");
  await expect(page.getByRole("status", { name: "Note results" })).toHaveText(
    "2 matching notes of 4 total",
  );
  await page
    .getByRole("button", { name: /General \/ unclassified.*2/ })
    .click();
  await expect(page.locator(".diagnostic-text")).toHaveText(
    report.warnings.slice(0, 2),
  );
  await expect(page.locator(".limitations script")).toHaveCount(0);
  await expect(page.locator(".diagnostic-entry")).toHaveCount(2);
  const download = page.waitForEvent("download");
  await page
    .getByRole("button", { name: "Export report", exact: true })
    .click();
  expect(
    JSON.parse(await readFile((await (await download).path())!, "utf8")),
  ).toEqual(report);
  await page
    .getByRole("searchbox", { name: "Search analysis notes" })
    .fill("not present");
  await expect(page.getByText("No matching notes")).toBeVisible();
  await page.getByRole("button", { name: "Reset notes", exact: true }).click();
  await expect(page.getByRole("status", { name: "Note results" })).toHaveText(
    "4 matching notes of 4 total",
  );
});

test("diagnostics page every occurrence and preserve controls across views, then reset on a new report", async ({
  page,
  request,
}) => {
  const report: Report = await (await request.get("/api/demo")).json();
  const path = report.nodes.find((n) => n.kind === "test")!.path;
  report.warnings = [
    ...Array.from({ length: 57 }, (_, i) => `Dynamic call: ${path}:${i + 1}`),
    "Unknown note",
    "Risk scores prioritize review; they are not calibrated failure probabilities.",
  ];
  await showReport(page, report);
  const selected = await page.locator(".test-row.selected").textContent();
  const summary = await page
    .getByRole("region", { name: "Analysis summary" })
    .textContent();
  await page
    .getByLabel("Note category", { exact: true })
    .selectOption("dynamic");
  await page
    .getByLabel("Note file", { exact: true })
    .selectOption(JSON.stringify(path));
  await expect(page.getByRole("status", { name: "Note results" })).toHaveText(
    "57 matching notes of 59 total",
  );
  await page.getByRole("button", { name: /^Dynamic calls/ }).click();
  await page
    .getByRole("button", {
      name: new RegExp(`^${path.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}`),
    })
    .click();
  await expect(page.locator(".diagnostic-entry")).toHaveCount(50);
  await expect(
    page.getByRole("button", { name: "Previous notes", exact: true }),
  ).toBeDisabled();
  await page
    .getByRole("button", { name: "Next notes", exact: true })
    .press("Enter");
  await expect(page.locator(".diagnostic-entries")).toBeFocused();
  await expect(page.locator(".diagnostic-text")).toHaveText(
    report.warnings.slice(50, 57),
  );
  await expect(
    page.getByRole("button", { name: "Next notes", exact: true }),
  ).toBeDisabled();
  for (const view of ["Map", "Changes", "Tests"])
    await page
      .getByRole("button", {
        name: view === "Map" ? "Map" : new RegExp(`^${view} \\d+$`),
        exact: true,
      })
      .click();
  await expect(page.locator(".diagnostic-text")).toHaveText(
    report.warnings.slice(50, 57),
  );
  await expect(page.locator(".test-row.selected")).toHaveText(selected!);
  await expect(
    page.getByRole("region", { name: "Analysis summary" }),
  ).toHaveText(summary!);
  await page
    .getByRole("searchbox", { name: "Search analysis notes" })
    .fill(":57");
  await expect(page.locator(".diagnostic-text")).toHaveText([
    report.warnings[56],
  ]);
  await expect(page.getByRole("status", { name: "Note results" })).toHaveText(
    "1 matching note of 59 total",
  );
  await page.locator(".limitations > summary").click();
  await page.locator(".limitations > summary").click();
  await expect(
    page.getByRole("searchbox", { name: "Search analysis notes" }),
  ).toHaveValue(":57");
  report.warnings = ["Fresh report note"];
  await page.getByRole("button", { name: "New analysis", exact: true }).click();
  await page.getByRole("button", { name: "Load demo", exact: true }).click();
  await expect(page.locator(".limitations")).not.toHaveAttribute("open", "");
  await page.locator(".limitations > summary").click();
  await expect(
    page.getByRole("searchbox", { name: "Search analysis notes" }),
  ).toHaveValue("");
  await expect(page.getByLabel("Note category", { exact: true })).toHaveCount(
    0,
  );
  await expect(page.getByLabel("Note file", { exact: true })).toHaveCount(0);
  await expect(page.getByRole("status", { name: "Note results" })).toHaveText(
    "1 matching note of 1 total",
  );
  await expect(
    page.getByRole("button", { name: /General \/ unclassified/ }),
  ).toHaveAttribute("aria-expanded", "false");
});

test("empty diagnostics stay distinct from a filter with no matches", async ({
  page,
  request,
}) => {
  const report: Report = await (await request.get("/api/demo")).json();
  report.warnings = [];
  await showReport(page, report);
  await expect(page.locator(".limitations > summary")).toContainText(
    "0 total notes",
  );
  await expect(
    page.getByRole("heading", { name: "No analysis notes", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText("No matching notes", { exact: true }),
  ).toHaveCount(0);
  await expect(page.locator(".diagnostics-caution")).toContainText(
    "A missing dependency path does not establish safety",
  );
});

for (const [width, height] of [
  [1440, 900],
  [768, 1024],
  [390, 844],
  [360, 844],
]) {
  test(`diagnostics wrap long messages and keep keyboard targets at ${width}×${height}`, async ({
    page,
    request,
    browserName,
  }) => {
    await page.setViewportSize({ width, height });
    const report: Report = await (await request.get("/api/demo")).json();
    const path = `src/工具/${"long_segment_".repeat(22)}.py`;
    report.nodes.push({
      id: `${path}::<module>`,
      path,
      name: "long",
      kind: "module",
      line: 1,
      end_line: 5,
    });
    report.warnings = [
      `Cannot parse ${path}: SyntaxError`,
      `<img src=x onerror=alert(1)> [.*] Ω\n${"long_text_".repeat(80)}`,
    ];
    await showReport(page, report);
    for (const theme of ["light", "dark"]) {
      if (theme === "dark")
        await page
          .getByRole("button", { name: "Switch to dark theme" })
          .click();
      const search = page.getByRole("searchbox", {
        name: "Search analysis notes",
      });
      await search.focus();
      await search.press(browserName === "webkit" ? "Alt+Tab" : "Tab");
      await expect(
        page.getByLabel("Note category", { exact: true }),
      ).toBeFocused();
      expect(
        await page
          .getByLabel("Note category", { exact: true })
          .evaluate((el) => getComputedStyle(el).outlineStyle),
      ).toBe("solid");
      await page
        .getByRole("button", { name: /^Parse failures/ })
        .press("Enter");
      await page
        .getByRole("button", { name: new RegExp("^src/工具/") })
        .press("Enter");
      await page
        .getByRole("button", { name: /General \/ unclassified/ })
        .press("Enter");
      await expect(page.locator(".diagnostic-text")).toHaveText(
        report.warnings,
      );
      expect(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= innerWidth,
        ),
      ).toBe(true);
      const controls = await page
        .locator(".diagnostics")
        .locator("button,input,select,summary")
        .evaluateAll((els) =>
          els
            .filter((el) => el.getClientRects().length)
            .map((el) => ({
              name: el.textContent,
              width: el.getBoundingClientRect().width,
              height: el.getBoundingClientRect().height,
            })),
        );
      for (const control of controls) {
        expect(control.width, String(control.name)).toBeGreaterThanOrEqual(44);
        expect(control.height, String(control.name)).toBeGreaterThanOrEqual(44);
      }
      await expect(page.locator(".diagnostics img")).toHaveCount(0);
      await page.getByRole("button", { name: /^Parse failures/ }).click();
      await page
        .getByRole("button", { name: /General \/ unclassified/ })
        .click();
      // The file disclosure remains expanded when its category is reopened.
      if (theme === "light") {
        await page.getByRole("button", { name: /^Parse failures/ }).click();
        await page
          .getByRole("button", { name: new RegExp("^src/工具/") })
          .click();
        await page.getByRole("button", { name: /^Parse failures/ }).click();
      }
    }
  });
}

test("pinned LFU diagnostics search all raw notes and preserve the complete analysis export", async ({
  page,
}) => {
  const fixture = JSON.parse(
    await readFile(
      new URL(
        "../../corpus/real-v2/cases/cachetools_lfu.json",
        import.meta.url,
      ),
      "utf8",
    ),
  );
  await page.goto("/");
  const response = page.waitForResponse("**/api/analyze");
  await page.getByLabel("Upload snapshot JSON").setInputFiles({
    name: "lfu.json",
    mimeType: "application/json",
    buffer: Buffer.from(JSON.stringify(fixture.request)),
  });
  const report: Report = await (await response).json();
  expect(report.warnings).toHaveLength(3128);
  expect(report.recommendations).toHaveLength(139);
  await page.locator(".limitations > summary").click();
  await expect(page.getByRole("status", { name: "Note results" })).toHaveText(
    "3128 matching notes of 3128 total",
  );
  const last = report.warnings.at(-1)!;
  await page
    .getByRole("searchbox", { name: "Search analysis notes" })
    .fill(last);
  await expect(page.getByRole("status", { name: "Note results" })).toHaveText(
    "1 matching note of 3128 total",
  );
  await page.getByRole("button", { name: /^Unresolved calls/ }).click();
  await page
    .getByRole("button", { name: /^src\/cachetools\/_descriptor.py/ })
    .click();
  await expect(page.locator(".diagnostic-text")).toHaveText([last]);
  const download = page.waitForEvent("download");
  await page
    .getByRole("button", { name: "Export report", exact: true })
    .click();
  expect(
    JSON.parse(await readFile((await (await download).path())!, "utf8")),
  ).toEqual(report);
  await page.getByRole("button", { name: "Reset notes", exact: true }).click();
  await expect(page.getByRole("status", { name: "Note results" })).toHaveText(
    "3128 matching notes of 3128 total",
  );
});
