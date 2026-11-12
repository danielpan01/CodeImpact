import { test, expect, type Page } from "@playwright/test";
import { readFile } from "node:fs/promises";
import { loadDemo, showEvidence, openChangedCode } from "./helpers";
import type { Report } from "../src/types";

let errors: string[];
test.beforeEach(({ page }) => {
  errors = [];
  page.on("pageerror", (error) => errors.push(error.message));
});
test.afterEach(() => expect(errors).toEqual([]));
const themeButton = (page: Page) =>
  page.getByRole("button", { name: /Switch to (dark|light) theme/ });
async function dark(page: Page) {
  await page.getByRole("button", { name: "Switch to dark theme" }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
}
async function upload(page: Page, request: unknown): Promise<Report> {
  const result = page.waitForResponse("**/api/analyze");
  await page.getByLabel("Upload snapshot JSON").setInputFiles({
    name: "release.json",
    mimeType: "application/json",
    buffer: Buffer.from(JSON.stringify(request)),
  });
  const response = await result;
  expect(response.status()).toBe(200);
  await expect(
    page.getByRole("button", { name: "Tests", exact: true }),
  ).toHaveAttribute("aria-pressed", "true");
  return response.json();
}
async function exported(page: Page) {
  const download = page.waitForEvent("download");
  await page
    .getByRole("button", { name: "Export report", exact: true })
    .click();
  return JSON.parse(await readFile((await (await download).path())!, "utf8"));
}
async function noOverflow(page: Page) {
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
}

test("theme follows the system until chosen, persists, and synchronizes between tabs", async ({
  page,
  context,
}) => {
  await page.emulateMedia({ colorScheme: "dark" });
  await page.goto("/");
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await themeButton(page).focus();
  await themeButton(page).press("Enter");
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
  await page.emulateMedia({ colorScheme: "light" });
  await page.emulateMedia({ colorScheme: "dark" });
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
  await page.reload();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
  expect(
    await page.evaluate(() => localStorage.getItem("codeimpact.theme")),
  ).toBe("light");
  const other = await context.newPage();
  await other.goto("/");
  await dark(page);
  await expect(other.locator("html")).toHaveAttribute("data-theme", "dark");
  await other.close();
});

test("unavailable preference storage never prevents analysis or theme switching", async ({
  page,
}) => {
  await page.addInitScript(() => {
    Storage.prototype.getItem = () => {
      throw new Error("Storage unavailable");
    };
    Storage.prototype.setItem = () => {
      throw new Error("Storage unavailable");
    };
  });
  await loadDemo(page);
  await dark(page);
  await page.getByRole("button", { name: /test_create_order/ }).click();
  await openChangedCode(page);
  await expect(
    page.getByRole("region", { name: "After source" }),
  ).toContainText("0.15");
});

test("theme switching preserves filters, full exports, expanded evidence and map viewport", async ({
  page,
}) => {
  const response = page.waitForResponse("**/api/demo");
  await loadDemo(page);
  const report: Report = await (await response).json();
  await page
    .getByRole("searchbox", { name: "Search tests" })
    .fill("create_order");
  await page.getByLabel("Sort tests").selectOption("name");
  await page.locator(".test-row").click();
  await page.locator(".revision-evidence summary").first().click();
  await dark(page);
  await expect(page.locator(".revision-evidence").first()).toHaveAttribute(
    "open",
    "",
  );
  await page.getByRole("button", { name: "Focus path in Map" }).click();
  await page
    .getByLabel("Jump to path symbol")
    .selectOption("shop/pricing.py::discount");
  await expect(page.locator(".react-flow__node")).toHaveCount(4);
  await expect
    .poll(() =>
      page.getByTestId("dependency-graph").evaluate((canvas) => {
        const target = [
          ...canvas.querySelectorAll<HTMLElement>(".react-flow__node"),
        ].find((node) => node.dataset.id === "shop/pricing.py::discount")!;
        const node = target.getBoundingClientRect(),
          bounds = canvas.getBoundingClientRect();
        return (
          Math.abs(node.x + node.width / 2 - bounds.x - bounds.width / 2) < 2 &&
          Math.abs(node.y + node.height / 2 - bounds.y - bounds.height / 2) < 2
        );
      }),
    )
    .toBe(true);
  const transform = await page
    .locator(".react-flow__viewport")
    .getAttribute("style");
  await themeButton(page).click();
  await expect(page.locator(".react-flow__viewport")).toHaveAttribute(
    "style",
    transform!,
  );
  const before = await page
    .locator(".react-flow__edge-path")
    .first()
    .evaluate((el) => getComputedStyle(el).stroke);
  await dark(page);
  expect(
    await page
      .locator(".react-flow__edge-path")
      .first()
      .evaluate((el) => getComputedStyle(el).stroke),
  ).not.toBe(before);
  await page.getByRole("button", { name: "Inspect test", exact: true }).click();
  await openChangedCode(page);
  await expect(
    page.getByRole("region", { name: "After source" }),
  ).toContainText("0.15");
  await page.getByRole("button", { name: "Tests", exact: true }).click();
  await expect(
    page.getByRole("searchbox", { name: "Search tests" }),
  ).toHaveValue("create_order");
  await expect(page.locator(".test-row")).toHaveCount(1);
  await expect(page.locator(".test-row")).toHaveAttribute(
    "aria-pressed",
    "true",
  );
  expect(await exported(page)).toEqual(report);
});

test("compact keyboard navigation, Escape and touch targets stay usable in both themes", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await loadDemo(page);
  for (const theme of ["light", "dark"]) {
    if (theme === "dark") await dark(page);
    await page
      .getByRole("button", { name: "New analysis", exact: true })
      .click();
    await expect(
      page.getByLabel("Analyze a GitHub pull request", { exact: true }),
    ).toBeFocused();
    await page.keyboard.press("Escape");
    await expect(
      page.getByRole("button", { name: "New analysis", exact: true }),
    ).toBeFocused();
    const row = page.getByRole("button", { name: /test_create_order/ });
    await row.focus();
    await row.press("Enter");
    await expect(
      page.getByRole("heading", { name: "Evidence", exact: true }),
    ).toBeFocused();
    await page.keyboard.press("Escape");
    await expect(row).toBeFocused();
    const rowBounds = await row.boundingBox(),
      navBounds = await page.locator(".workspace-nav").boundingBox();
    expect(rowBounds!.y).toBeGreaterThanOrEqual(
      navBounds!.y + navBounds!.height - 1,
    );
    await row.press("Enter");
    const targets = await page
      .locator(
        ".theme-toggle, .view-toggle button, .evidence-toggle, .evidence-back, .open-code, .focus-path-link",
      )
      .evaluateAll((elements) =>
        elements
          .filter((el) => el.getClientRects().length)
          .map((el) => {
            const r = el.getBoundingClientRect();
            return { name: el.textContent, width: r.width, height: r.height };
          }),
      );
    for (const target of targets) {
      expect(target.height, String(target.name)).toBeGreaterThanOrEqual(44);
      expect(target.width).toBeGreaterThanOrEqual(44);
    }
    await openChangedCode(page);
    await noOverflow(page);
    await page.getByRole("button", { name: "Tests", exact: true }).click();
  }
  await page.setViewportSize({ width: 1440, height: 900 });
  const sourceLocation = page.locator(".revision-evidence summary").first();
  // Mobile WebKit applies resized media-query styles asynchronously. Establish
  // visible, focused desktop evidence before testing the transition to tablet.
  await expect(sourceLocation).toBeVisible();
  await sourceLocation.focus();
  await expect(sourceLocation).toBeFocused();
  await page.setViewportSize({ width: 768, height: 1024 });
  await expect(
    page.getByRole("heading", { name: "Evidence", exact: true }),
  ).toBeFocused();
  await expect(
    page.getByRole("region", { name: "Change explorer" }),
  ).toBeHidden();
  // Resizing an already open inspector must not steal focus from its content.
  await sourceLocation.focus();
  await expect(sourceLocation).toBeFocused();
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(sourceLocation).toBeFocused();
  await page
    .getByRole("button", { name: "Back to results", exact: true })
    .click();
  await noOverflow(page);
});

test("snapshot network failure retries the same source and loading avoids invented progress", async ({
  page,
}) => {
  const input = {
    label: "Retry snapshot",
    base: { files: { "test_a.py": "def test_a(): return 1\n" } },
    head: { files: { "test_a.py": "def test_a(): return 2\n" } },
  };
  let attempts = 0,
    release!: () => void;
  const held = new Promise<void>((resolve) => {
    release = resolve;
  });
  await page.route("**/api/analyze", async (route) => {
    expect(route.request().postDataJSON()).toEqual(input);
    attempts++;
    if (attempts === 1) {
      await held;
      await route.abort("failed");
    } else await route.continue();
  });
  await page.goto("/");
  await dark(page);
  await page.getByLabel("Upload snapshot JSON").setInputFiles({
    name: "retry.json",
    mimeType: "application/json",
    buffer: Buffer.from(JSON.stringify(input)),
  });
  await expect(page.locator("#analysis-entry")).toHaveAttribute(
    "aria-busy",
    "true",
  );
  await expect(page.getByRole("status")).toContainText(
    "Comparing the before and after snapshots",
  );
  await expect(page.getByRole("progressbar")).toHaveCount(0);
  await expect(
    page.getByRole("button", { name: "Analyze snapshots", exact: true }),
  ).toBeDisabled();
  release();
  await expect(page.getByRole("alert")).toContainText("Connection unavailable");
  await expect(page.getByRole("alert")).toBeFocused();
  await page
    .getByRole("button", { name: "Retry snapshots", exact: true })
    .click();
  await expect(page.locator(".analysis-label")).toHaveText("Retry snapshot");
  expect(attempts).toBe(2);
});

test("invalid inputs, limited requests and unreadable responses have actionable recovery", async ({
  page,
}) => {
  await page.goto("/");
  await dark(page);
  await page.getByLabel("Upload snapshot JSON").setInputFiles({
    name: "invalid.json",
    mimeType: "application/json",
    buffer: Buffer.from("not json"),
  });
  await expect(page.getByRole("alert")).toContainText(
    "base.files and head.files",
  );
  await page
    .getByRole("button", { name: "Choose a snapshot", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Analyze snapshots", exact: true }),
  ).toBeFocused();
  const url = page.getByLabel("Analyze a GitHub pull request", { exact: true });
  await url.fill("https://example.com/owner/repo/pull/1");
  await url.press("Enter");
  await expect(url).toHaveAttribute("aria-invalid", "true");
  await page.getByRole("button", { name: "Edit PR URL", exact: true }).click();
  await expect(url).toBeFocused();
  await page.route("**/api/github/pr", (route) =>
    route.fulfill({
      status: 429,
      contentType: "application/json",
      body: JSON.stringify({
        detail: {
          code: "rate_limited",
          message: "Wait before retrying.",
          retryable: true,
        },
      }),
    }),
  );
  await url.fill("https://github.com/acme/widget/pull/7");
  await url.press("Enter");
  await expect(page.getByRole("alert")).toContainText(
    "Request temporarily limited",
  );
  await expect(
    page.getByRole("button", { name: "Retry GitHub PR" }),
  ).toBeEnabled();
  await page.route("**/api/demo", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: "not json",
    }),
  );
  await page.getByRole("button", { name: "Load demo", exact: true }).click();
  await expect(page.getByRole("alert")).toContainText("unreadable response");
  await page.unroute("**/api/demo");
  await page.getByRole("button", { name: "Retry demo", exact: true }).click();
  await expect(page.locator(".test-row")).toHaveCount(3);
});

function contrast(a: string, b: string) {
  const luminance = (hex: string) => {
    const rgb = hex
      .trim()
      .replace("#", "")
      .match(/../g)!
      .slice(0, 3)
      .map((v) => parseInt(v, 16) / 255)
      .map((c) => (c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4));
    return rgb[0] * 0.2126 + rgb[1] * 0.7152 + rgb[2] * 0.0722;
  };
  const first = luminance(a),
    second = luminance(b);
  return (Math.max(first, second) + 0.05) / (Math.min(first, second) + 0.05);
}
test("semantic text colors and focus indicators meet contrast checks in both themes", async ({
  page,
}) => {
  await loadDemo(page);
  for (const theme of ["light", "dark"]) {
    if (theme === "dark") await dark(page);
    const pairs = [
      ["ink", "panel"],
      ["muted", "panel"],
      ["muted", "page"],
      ["subtle", "panel-muted"],
      ["accent", "selected"],
      ["primary-text", "primary-bg"],
      ["changed", "changed-bg"],
      ["added", "added-bg"],
      ["warning", "warning-bg"],
      ["before", "before-bg"],
      ["after", "after-bg"],
      ["mixed", "mixed-bg"],
      ["syntax-keyword", "source-bg"],
      ["syntax-string", "source-bg"],
      ["syntax-comment", "source-bg"],
      ["syntax-number", "source-bg"],
      ["ink", "graph-context"],
      ["nav-text", "nav"],
    ];
    const colors = await page.evaluate((pairs) => {
      const css = getComputedStyle(document.documentElement);
      return pairs.map(([a, b]) => [
        css.getPropertyValue(`--${a}`),
        css.getPropertyValue(`--${b}`),
      ]);
    }, pairs);
    colors.forEach(([a, b], i) =>
      expect(
        contrast(a, b),
        `${theme}: ${pairs[i].join(" / ")}`,
      ).toBeGreaterThanOrEqual(4.5),
    );
    const borders = await page.evaluate(() => {
      const css = getComputedStyle(document.documentElement);
      return [
        css.getPropertyValue("--border-strong"),
        css.getPropertyValue("--panel"),
      ];
    });
    expect(contrast(borders[0], borders[1])).toBeGreaterThanOrEqual(3);
    const search = page.getByRole("searchbox", { name: "Search tests" });
    await search.focus();
    expect(
      await search.evaluate((el) => getComputedStyle(el).outlineStyle),
    ).toBe("solid");
  }
});

test("reduced motion, empty results and map recovery remain usable", async ({
  page,
}) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await loadDemo(page);
  await dark(page);
  expect(
    await themeButton(page).evaluate(
      (el) => getComputedStyle(el).transitionDuration,
    ),
  ).toBe("0s");
  await page
    .getByRole("searchbox", { name: "Search tests" })
    .fill("no matches");
  await expect(
    page.getByRole("heading", { name: "No matching tests" }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Clear filters", exact: true })
    .press("Enter");
  await expect(page.locator(".test-row")).toHaveCount(3);
  await page.getByRole("button", { name: "Map", exact: true }).click();
  await page.getByLabel("Search symbols").fill("missing");
  await page
    .getByRole("button", { name: "Show all symbols", exact: true })
    .press("Enter");
  await expect(page.locator(".react-flow__node")).toHaveCount(16);
  await page.getByRole("button", { name: "New analysis", exact: true }).click();
  await upload(page, {
    label: "Empty",
    base: { files: {} },
    head: { files: {} },
  });
  await expect(
    page.getByRole("heading", { name: "No tests recommended" }),
  ).toBeVisible();
  await expect(
    page.getByText(/No recommendation does not establish/),
  ).toBeVisible();
  await page.getByRole("button", { name: "Review changed code" }).click();
  await expect(
    page.getByText("No semantic changes in these snapshots."),
  ).toBeVisible();
  await noOverflow(page);
});

for (const caseId of ["slugify_ascii", "slugify_boundary", "cachetools_lfu"]) {
  test(`dark ${caseId} keeps large-report navigation and full exports`, async ({
    page,
  }) => {
    const fixture = JSON.parse(
      await readFile(
        new URL(`../../corpus/real-v2/cases/${caseId}.json`, import.meta.url),
        "utf8",
      ),
    );
    await page.goto("/");
    await dark(page);
    const report = await upload(page, fixture.request);
    const last = report.recommendations.at(-1)!;
    await page
      .getByRole("searchbox", { name: "Search tests" })
      .fill(last.symbol);
    await expect(page.locator(".test-row")).toHaveCount(1);
    await page.locator(".test-row").click();
    await page.getByRole("button", { name: "Focus path in Map" }).click();
    await expect(page.locator(".react-flow__node")).toHaveCount(
      last.evidence_path.length,
    );
    await page.getByRole("button", { name: "Fit view", exact: true }).click();
    await page
      .getByRole("button", { name: "Inspect test", exact: true })
      .click();
    await openChangedCode(page);
    await expect(
      page.getByRole("region", { name: "Selected changed code" }),
    ).toContainText(last.evidence_path.at(-1)!.split("::")[1]);
    expect(await exported(page)).toEqual(report);
    await noOverflow(page);
  });
}

test("dark mixed and deleted evidence stays explicit during source review", async ({
  page,
}) => {
  const request = JSON.parse(
    await readFile(
      new URL("../../tests/fixtures/mixed-revisions.json", import.meta.url),
      "utf8",
    ),
  );
  await page.goto("/");
  await dark(page);
  await upload(page, request);
  await showEvidence(page);
  await expect(page.locator(".detail-content")).toContainText(
    "Mixed revisions",
  );
  await page.getByRole("button", { name: "Focus path in Map" }).click();
  await expect(page.locator(".react-flow__node.removed")).toHaveCount(1);
  await page.getByRole("button", { name: "Inspect test", exact: true }).click();
  await openChangedCode(page);
  await expect(
    page.getByRole("region", { name: "After source" }),
  ).toContainText("Empty file");
  await expect(
    page.getByRole("region", { name: "Before source" }),
  ).toContainText("def f()");
});
