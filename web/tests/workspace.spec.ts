import { test, expect } from "@playwright/test";
import { readFile } from "node:fs/promises";
import { loadDemo, openChangedCode, showEvidence } from "./helpers";
import type { Report } from "../src/types";

test("entry, initial Tests, and reopening inputs by keyboard retain the report", async ({
  page,
}) => {
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Start with a change." }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Analyze snapshots", exact: true }),
  ).toBeVisible();
  const demo = page.getByRole("button", { name: "Load demo", exact: true });
  await demo.focus();
  await demo.press("Enter");
  await expect(
    page.getByRole("button", { name: "Tests", exact: true }),
  ).toHaveAttribute("aria-pressed", "true");
  await expect(
    page.getByRole("form", { name: "Analyze a public GitHub pull request" }),
  ).toBeHidden();
  await expect(
    page.getByRole("region", { name: "Change explorer" }),
  ).toBeFocused();
  await expect(page.locator(".test-row")).toHaveCount(3);
  await page.getByRole("button", { name: /test_checkout/ }).click();
  const reopen = page.getByRole("button", {
    name: "New analysis",
    exact: true,
  });
  await reopen.focus();
  await reopen.press("Enter");
  await expect(
    page.getByLabel("Analyze a GitHub pull request", { exact: true }),
  ).toBeFocused();
  await page
    .getByRole("button", { name: "Close analysis input" })
    .press("Enter");
  await expect(reopen).toBeFocused();
  await expect(page.locator(".detail-content h3")).toHaveText("test_checkout");
  await expect(
    page.getByRole("button", { name: "Tests", exact: true }),
  ).toHaveAttribute("aria-pressed", "true");
});

test("selection and expanded evidence persist across Map, Tests and changed code", async ({
  page,
}) => {
  await loadDemo(page);
  await page.getByRole("button", { name: /test_create_order/ }).click();
  await page.locator(".revision-evidence summary").first().click();
  await expect(page.locator(".revision-evidence").first()).toHaveAttribute(
    "open",
    "",
  );
  await page.getByRole("button", { name: "Map", exact: true }).click();
  await expect(page.locator(".react-flow__node.active-node")).toHaveAttribute(
    "data-id",
    "tests/test_api.py::test_create_order",
  );
  await showEvidence(page);
  await expect(page.locator(".revision-evidence").first()).toHaveAttribute(
    "open",
    "",
  );
  await openChangedCode(page);
  await expect(
    page.getByRole("region", { name: "After source" }),
  ).toContainText("0.15");
  await expect(page.locator(".detail-content h3")).toHaveText(
    "test_create_order",
  );
  await page.getByRole("button", { name: "Tests", exact: true }).click();
  await expect(
    page.getByRole("button", { name: /test_create_order/ }),
  ).toHaveAttribute("aria-pressed", "true");
  await showEvidence(page);
  await expect(page.locator(".revision-evidence").first()).toHaveAttribute(
    "open",
    "",
  );
});

test("phone and tablet evidence have keyboard back, Escape and a return from changed code", async ({
  page,
}) => {
  // Cover both breakpoints regardless of the Playwright project's default viewport.
  for (const width of [390, 768]) {
    await page.setViewportSize({ width, height: 844 });
    await loadDemo(page);
    const row = page.getByRole("button", { name: /test_create_order/ });
    await row.focus();
    await row.press("Enter");
    await expect(
      page.getByRole("heading", { name: "Evidence", exact: true }),
    ).toBeFocused();
    await expect(
      page.getByRole("region", { name: "Change explorer" }),
    ).toBeHidden();
    const back = page.getByRole("button", {
      name: "Back to results",
      exact: true,
    });
    await back.press("Enter");
    await expect(row).toBeFocused();
    await row.press("Enter");
    await page.keyboard.press("Escape");
    await expect(row).toBeFocused();
    await row.press("Enter");
    await openChangedCode(page);
    await expect(
      page.getByRole("region", { name: "Change explorer" }),
    ).toBeFocused();
    await expect(
      page.getByRole("region", { name: "After source" }),
    ).toBeVisible();
    await showEvidence(page);
    await expect(page.locator(".detail-content h3")).toHaveText(
      "test_create_order",
    );
    await back.click();
    await expect(
      page.getByRole("button", { name: "View evidence", exact: true }),
    ).toBeFocused();
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
  }
});

test("zero recommendations explicitly lead to changed code without claiming safety", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByLabel("Upload snapshot JSON").setInputFiles({
    name: "no-tests.json",
    mimeType: "application/json",
    buffer: Buffer.from(
      JSON.stringify({
        label: "A change without tests",
        base: { files: { "price.py": "def price(): return 1\n" } },
        head: { files: { "price.py": "def price(): return 2\n" } },
      }),
    ),
  });
  await expect(
    page.getByRole("heading", { name: "No tests recommended" }),
  ).toBeVisible();
  await expect(
    page.getByText(/No recommendation does not establish/),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Review changed code" })
    .press("Enter");
  await expect(
    page.getByRole("region", { name: "After source" }),
  ).toContainText("return 2");
  await expect(
    page.getByRole("region", { name: "Change explorer" }),
  ).toBeFocused();
});

test("long names remain complete at 360 pixels and source scrolls within its pane", async ({
  page,
}) => {
  await page.setViewportSize({ width: 360, height: 844 });
  const path = "test_" + "long_module_name_".repeat(8) + ".py";
  const name = "test_" + "long_definition_name_".repeat(7);
  const before = `def ${name}(): return '${"x".repeat(400)}'\n`;
  await page.goto("/");
  await page.getByLabel("Upload snapshot JSON").setInputFiles({
    name: "long-names.json",
    mimeType: "application/json",
    buffer: Buffer.from(
      JSON.stringify({
        label: "Long-name source fixture",
        base: { files: { [path]: before } },
        head: {
          files: { [path]: before.replace("return '", "return 'changed") },
        },
      }),
    ),
  });
  const row = page.getByRole("button", { name: new RegExp(name) });
  await expect(row).toContainText(path);
  await row.click();
  await openChangedCode(page);
  const pane = page.getByRole("region", { name: "After source" });
  await expect(pane).toContainText(name);
  expect(
    await pane
      .locator("pre")
      .evaluate((element) => element.scrollWidth > element.clientWidth),
  ).toBe(true);
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
});

test("graph nodes can open evidence with the keyboard and module controls remain available", async ({
  page,
}) => {
  await loadDemo(page);
  await page.getByRole("button", { name: "Map", exact: true }).click();
  await page.getByLabel("Module dependencies").check();
  await expect(page.locator(".react-flow__node")).toHaveCount(16);
  await page.getByLabel("Module dependencies").uncheck();
  await page.getByRole("button", { name: /fit view/i }).click();
  await expect
    .poll(() =>
      page.getByTestId("dependency-graph").evaluate((canvas) => {
        const bounds = canvas.getBoundingClientRect();
        return [...canvas.querySelectorAll(".react-flow__node")].every(
          (node) => {
            const rect = node.getBoundingClientRect();
            return (
              rect.left >= bounds.left - 1 &&
              rect.right <= bounds.right + 1 &&
              rect.top >= bounds.top - 1 &&
              rect.bottom <= bounds.bottom + 1
            );
          },
        );
      }),
    )
    .toBe(true);
  await page.getByLabel("Search symbols").fill("test_health");
  const node = page.getByRole("group", {
    name: /test_health, test, unaffected/,
  });
  await node.focus();
  await node.press("Enter");
  await expect(page.locator(".detail-content h3")).toHaveText("test_health");
  await expect(page.locator(".detail-content")).toContainText(
    "No path to a changed symbol was found",
  );
});

for (const caseId of ["slugify_ascii", "slugify_boundary", "cachetools_lfu"]) {
  test(`pinned ${caseId} retains the complete ordered list, scores, evidence and export`, async ({
    page,
  }) => {
    const fixture = JSON.parse(
      await readFile(
        new URL(`../../corpus/real-v2/cases/${caseId}.json`, import.meta.url),
        "utf8",
      ),
    );
    const errors: string[] = [];
    page.on("pageerror", (error) => errors.push(error.message));
    await page.goto("/");
    const responsePromise = page.waitForResponse("**/api/analyze");
    await page.getByLabel("Upload snapshot JSON").setInputFiles({
      name: `${caseId}.json`,
      mimeType: "application/json",
      buffer: Buffer.from(JSON.stringify(fixture.request)),
    });
    const response = await responsePromise;
    expect(response.status()).toBe(200);
    const report: Report = await response.json();
    await expect(page.locator(".test-row")).toHaveCount(
      report.recommendations.length,
    );
    expect(
      await page.locator(".test-identity strong").allTextContents(),
    ).toEqual(report.recommendations.map((r) => r.symbol.split("::")[1]));
    expect(await page.locator(".test-priority b").allTextContents()).toEqual(
      report.recommendations.map((r) => String(r.score)),
    );
    // The last recommendation remains reachable in a large report.
    await page.locator(".test-row").last().click();
    await expect(page.locator(".detail-content h3")).toHaveText(
      report.nodes.find((n) => n.id === report.recommendations.at(-1)?.symbol)!
        .name,
    );
    await openChangedCode(page);
    await expect(
      page.getByRole("region", { name: "Selected changed code" }),
    ).toContainText(
      report.recommendations.at(-1)!.evidence_path.at(-1)!.split("::")[1],
    );
    const downloadPromise = page.waitForEvent("download");
    await page
      .getByRole("button", { name: "Export report", exact: true })
      .click();
    expect(
      JSON.parse(
        await readFile((await (await downloadPromise).path())!, "utf8"),
      ),
    ).toEqual(report);
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    expect(errors).toEqual([]);
  });
}
