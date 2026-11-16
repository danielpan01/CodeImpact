import { expect, type Page } from "@playwright/test";
import { readFileSync } from "node:fs";
import { createHash } from "node:crypto";
import type { Report } from "../../src/types";
import { showEvidence } from "../helpers";

export const states = [
  "entry",
  "tests",
  "evidence",
  "map",
  "changes",
  "mixed",
  "deleted",
  "diagnostics",
  "empty",
  "zero-discovery",
  "error",
  "pilot",
] as const;
export type State = (typeof states)[number] | "loading";
export type Theme = "light" | "dark";
export const layouts = {
  desktop: { width: 1440, height: 900 },
  phone: { width: 390, height: 844 },
};

const manifest = JSON.parse(
  readFileSync(new URL("./fixtures/manifest.json", import.meta.url), "utf8"),
);
const reports = Object.fromEntries(
  ["demo", "mixed", "large", "unsupported-discovery"].map((name) => [
    name,
    readReport(name),
  ]),
);
function readReport(name: string): Report {
  const data = readFileSync(
    new URL(`./fixtures/${name}.json`, import.meta.url),
    "utf8",
  );
  expect(
    createHash("sha256").update(data).digest("hex"),
    `${name} fixture integrity`,
  ).toBe(manifest[name].report_sha256);
  const input = readFileSync(
    new URL(`../../../${manifest[name].input}`, import.meta.url),
  );
  expect(
    createHash("sha256").update(input).digest("hex"),
    `${name} input integrity`,
  ).toBe(manifest[name].input_sha256);
  return JSON.parse(data) as Report;
}

export async function renderState(page: Page, state: State, theme: Theme) {
  await page.emulateMedia({ colorScheme: theme });
  const fixture = ["mixed", "deleted"].includes(state)
    ? "mixed"
    : state === "diagnostics"
      ? "large"
      : state === "zero-discovery"
        ? "unsupported-discovery"
        : "demo";
  const report = reports[fixture];
  let attempts = 0;
  let release: () => void = () => {};
  const held = new Promise<void>((resolve) => {
    release = resolve;
  });
  // All API inputs are local. Unexpected API/external requests fail the test.
  await page.route("**/*", async (route) => {
    const url = new URL(route.request().url());
    if (url.origin !== "http://127.0.0.1:5176")
      throw new Error(`Unexpected external request: ${url.origin}`);
    if (url.pathname === "/api/config")
      return route.fulfill({ json: { access_required: state === "pilot" } });
    if (
      url.pathname === "/api/demo" ||
      (fixture !== "demo" && url.pathname === "/api/analyze")
    ) {
      if (state === "loading") await held;
      if (state === "error" && attempts++ === 0)
        return route.fulfill({
          status: 503,
          json: {
            detail: {
              code: "upstream_unavailable",
              message:
                "The analysis service is temporarily unavailable. Try again.",
              retryable: true,
            },
          },
        });
      return route.fulfill({ json: report });
    }
    if (url.pathname.startsWith("/api/"))
      throw new Error(`Unexpected API request: ${url.pathname}`);
    return route.continue();
  });
  await page.goto("/");
  await expect(page.locator("html")).toHaveAttribute("data-theme", theme);
  await expect(
    page.getByRole("button", { name: "Analyze PR", exact: true }),
  ).toBeVisible();
  if (state === "pilot")
    await expect(page.getByLabel("Pilot access key")).toBeVisible();
  if (["entry", "pilot"].includes(state)) return { release };
  if (fixture === "demo") {
    await page.getByRole("button", { name: "Load demo", exact: true }).click();
  } else {
    const input = JSON.parse(
      readFileSync(
        new URL(`../../../${manifest[fixture].input}`, import.meta.url),
        "utf8",
      ),
    );
    await page.getByLabel("Upload snapshot JSON").setInputFiles({
      name: `${fixture}.json`,
      mimeType: "application/json",
      buffer: Buffer.from(JSON.stringify(input.request ?? input)),
    });
  }
  if (state === "loading") {
    await expect(page.getByRole("status")).toContainText("Loading analysis");
    return { release };
  }
  if (state === "error") {
    await expect(page.getByRole("alert")).toContainText(
      "temporarily unavailable",
    );
    await expect(
      page.getByRole("button", { name: "Retry demo", exact: true }),
    ).toBeVisible();
    return { release };
  }
  await expect(
    page.getByRole("button", { name: /^Tests \d+$/ }),
  ).toHaveAttribute("aria-pressed", "true");
  await expect(page.locator(".test-row")).toHaveCount(
    report.recommendations.length,
  );
  if (["tests", "evidence", "map", "changes"].includes(state)) {
    await page
      .getByRole("button", { name: /test_create_order.*Heuristic/ })
      .click();
  }
  if (state === "tests") {
    const back = page.getByRole("button", { name: "Back to results" });
    if (await back.isVisible()) await back.click();
    await expect(page.locator(".test-row.selected")).toContainText(
      "test_create_order",
    );
  }
  if (state === "zero-discovery") {
    await page.locator(".discovery-scope summary").click();
    const scopeEnd = page.locator(".discovery-scope p").last();
    await scopeEnd.scrollIntoViewIfNeeded();
    await expect(scopeEnd).toBeInViewport({ ratio: 1 });
  }
  if (["evidence", "mixed", "map", "changes", "deleted"].includes(state)) {
    await showEvidence(page);
    if (["evidence", "mixed"].includes(state))
      await page.locator(".revision-evidence summary").first().click();
    if (state === "mixed")
      await expect(page.locator(".detail-panel")).toContainText(
        "Mixed revisions",
      );
    if (state === "map") {
      await page.getByRole("button", { name: "Focus path in Map" }).click();
      await expect(page.locator(".react-flow__node")).toHaveCount(4);
      await page.getByRole("button", { name: "Fit view", exact: true }).click();
    }
    if (["changes", "deleted"].includes(state)) {
      await page.getByRole("button", { name: "Open changed code" }).click();
      await expect(
        page.getByRole("region", { name: "Before source" }),
      ).toBeVisible();
      await expect(
        page.getByRole("region", { name: "After source" }),
      ).toBeVisible();
      if (state === "deleted")
        await expect(
          page.getByRole("region", { name: "After source" }),
        ).toContainText("Empty file");
    }
  }
  if (state === "diagnostics") {
    await page.locator(".diagnostics > summary").click();
    await page
      .getByLabel("Note category", { exact: true })
      .selectOption("imports");
    await page.getByRole("button", { name: /^Unresolved imports/ }).click();
    for (const button of await page
      .locator(".diagnostic-file > h4 > button")
      .all())
      await button.click();
    await expect(page.getByRole("status", { name: "Note results" })).toHaveText(
      "3 matching notes of 3128 total",
    );
    await expect(page.locator(".diagnostic-text")).toHaveCount(3);
  }
  if (state === "empty") {
    await page
      .getByRole("searchbox", { name: "Search tests" })
      .fill("no_matching_test");
    await expect(page.locator(".test-row")).toHaveCount(0);
  }
  if (state === "zero-discovery")
    await expect(
      page.getByRole("heading", { name: "No tests discovered" }),
    ).toBeVisible();
  return { release };
}

export async function settle(page: Page) {
  await page.evaluate(() => document.fonts.ready);
  // Measured layout (including graph framing) must agree across animation frames.
  // No fixed sleeps, report masks, frozen application clocks or hidden controls.
  await page.evaluate(async () => {
    let previous = "";
    let equal = 0;
    for (let frame = 0; frame < 120; frame++) {
      await new Promise(requestAnimationFrame);
      const current = JSON.stringify(
        [
          ...document.querySelectorAll(
            "main, .explorer-layout, .react-flow__viewport, .react-flow__node, .diagnostics",
          ),
        ].map((el) => {
          const r = el.getBoundingClientRect();
          return [r.x, r.y, r.width, r.height, getComputedStyle(el).transform];
        }),
      );
      equal = current === previous ? equal + 1 : 0;
      if (equal >= 4) return;
      previous = current;
    }
    throw new Error("Layout did not stabilize");
  });
}
