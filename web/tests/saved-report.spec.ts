import { test, expect, type Page } from "@playwright/test";
import { readFile } from "node:fs/promises";
import { readFileSync } from "node:fs";
import { openAnalysis, openChangedCode, showEvidence } from "./helpers";
import type { Report } from "../src/types";

const demo: Report = JSON.parse(
  readFileSync(
    new URL("./quality/fixtures/demo.json", import.meta.url),
    "utf8",
  ),
);
const file = (contents: string, name = "review.json") => ({
  name,
  mimeType: "application/json",
  buffer: Buffer.from(contents),
});

async function exportJSON(page: Page) {
  const download = page.waitForEvent("download");
  await page
    .getByRole("button", { name: "Export report", exact: true })
    .click();
  return readFile((await (await download).path())!, "utf8");
}

async function chooseByKeyboard(page: Page, contents: string) {
  const choosing = page.waitForEvent("filechooser");
  await page
    .getByRole("button", { name: "Open saved report", exact: true })
    .press("Enter");
  await (await choosing).setFiles(file(contents));
  await expect(
    page.getByRole("region", { name: "Change explorer" }),
  ).toBeFocused();
}

test("a pilot export reopens offline and resumes only its own review decisions", async ({
  page,
  context,
}) => {
  await page.goto("http://127.0.0.1:8003/");
  await expect(page.getByLabel("Pilot access key")).toBeVisible();
  await page.getByRole("button", { name: "Load demo", exact: true }).click();
  const launch = page.getByRole("button", { name: "Review plan", exact: true });
  const plan = page.getByRole("dialog", { name: "Review plan" });
  const close = plan.getByRole("button", { name: "Close review plan" });
  await launch.click();
  await plan.getByRole("button", { name: "Mark reviewed" }).click();
  await expect(plan.getByRole("status")).toHaveText("1 of 3 reviewed");
  await close.click();
  const saved = await exportJSON(page);

  await page.reload();
  await expect(page.getByLabel("Pilot access key")).toBeVisible();
  await context.setOffline(true);
  const requests: string[] = [];
  page.on("request", (req) => {
    if (/^https?:/.test(req.url())) requests.push(req.url());
  });
  await chooseByKeyboard(page, saved);
  await expect(
    page.getByText("Opened from file", { exact: true }),
  ).toBeVisible();
  await expect(page.getByText(/review.json · Schema 2.0/)).toBeVisible();
  await expect(page.getByRole("button", { name: /^Tests 3$/ })).toBeVisible();
  await page.getByRole("button", { name: "Map", exact: true }).click();
  await expect(page.locator(".react-flow__node").first()).toBeVisible();
  await openChangedCode(page);
  await expect(
    page.getByRole("region", { name: "Before source" }),
  ).toContainText("def discount");
  await expect(
    page.getByRole("region", { name: "After source" }),
  ).toContainText("def discount");
  expect(await exportJSON(page)).toBe(saved);
  await launch.click();
  await expect(plan.getByRole("status")).toHaveText("1 of 3 reviewed");
  await close.click();

  const other: Report = JSON.parse(saved);
  const markup = '<img src="https://invalid.example/image" onerror="alert(1)">';
  other.warnings.push(markup);
  await openAnalysis(page);
  // The first reopen exercises the native keyboard chooser. For the following
  // replacements, select files on the same input to test report identity
  // independently of the browser's handling of rapid successive dialogs.
  const input = page.getByLabel("Saved report JSON");
  await input.setInputFiles(file(JSON.stringify(other)));
  await expect(
    page.getByRole("region", { name: "Change explorer" }),
  ).toBeFocused();
  await page.locator(".diagnostics > summary").click();
  await page.getByRole("button", { name: /^General \/ unclassified/ }).click();
  await expect(page.locator(".diagnostic-text")).toContainText(markup);
  await launch.click();
  await expect(
    plan.getByText("Decisions are saved in this browser."),
  ).toBeVisible();
  await expect(plan.getByRole("status")).toHaveText("0 of 3 reviewed");
  await plan.getByRole("button", { name: "Flag follow-up" }).click();
  await close.click();
  await openAnalysis(page);
  const later: Report = JSON.parse(saved);
  later.stats.elapsed_ms += 1;
  await input.setInputFiles(file(JSON.stringify(later)));
  await expect(
    page.getByRole("region", { name: "Change explorer" }),
  ).toBeFocused();
  await launch.click();
  await expect(plan.getByRole("status")).toHaveText("1 of 3 reviewed");
  await expect(plan.getByText("2 pending · 0 follow-up")).toBeVisible();
  expect(requests).toEqual([]);
});

test("file errors retain the active view and return keyboard users to the local picker", async ({
  page,
}) => {
  await page.goto("/");
  await chooseByKeyboard(page, JSON.stringify(demo));
  await page.getByRole("button", { name: "Map", exact: true }).click();
  await openAnalysis(page);
  const invalid = structuredClone(demo);
  invalid.recommendations[0].evidence_edges = ["bad"];
  const alert = page.getByRole("alert");
  for (const [contents, message] of [
    ["{", "not valid JSON"],
    ['{"schema_version":"1.0"}', "Unsupported report version"],
    [JSON.stringify(invalid), "recorded edges"],
  ]) {
    await page.getByLabel("Saved report JSON").setInputFiles(file(contents));
    await expect(alert).toContainText(message);
    await expect(
      page.getByRole("button", { name: "Open saved report" }),
    ).toBeFocused();
    await expect(
      page.getByRole("button", { name: "Map", exact: true }),
    ).toHaveAttribute("aria-pressed", "true");
  }
  await page.keyboard.press("Escape");
  await expect(
    page.getByRole("button", { name: "New analysis" }),
  ).toBeFocused();
  await expect(alert).toBeHidden();
  await openAnalysis(page);
  await chooseByKeyboard(page, JSON.stringify(demo));
  await expect(page.locator(".test-row")).toHaveCount(3);
});

test("reopens real fixture and PR exports when the analysis API is unavailable", async ({
  page,
  request,
}) => {
  const corpus = JSON.parse(
    readFileSync(
      new URL("../../corpus/cases/pytest_fixtures.json", import.meta.url),
      "utf8",
    ),
  );
  const fixture = await request.post("/api/analyze", { data: corpus.request });
  const github = await request.post("/api/github/pr", {
    data: { url: "https://github.com/acme/widget/pull/7" },
  });
  expect(fixture.ok() && github.ok()).toBe(true);
  const analyzed: Report = await fixture.json();
  expect(analyzed.schema_version).toBe("2.1");
  const pr: Report = await github.json();
  const requests: string[] = [];
  await page.route("**/api/**", (route) => {
    requests.push(new URL(route.request().url()).pathname);
    return route.abort();
  });
  await page.goto("/");
  await chooseByKeyboard(page, JSON.stringify(analyzed));
  await page.getByRole("button", { name: /test_quote.*Heuristic/ }).click();
  await showEvidence(page);
  await expect(page.locator(".edge-evidence").first()).toContainText(
    "Pytest fixture injection",
  );
  await openAnalysis(page);
  await chooseByKeyboard(page, JSON.stringify(pr));
  await expect(
    page.getByText("Opened from file", { exact: true }),
  ).toBeVisible();
  const source = page.getByRole("region", { name: "GitHub analysis source" });
  await expect(source.getByRole("link")).toHaveAttribute(
    "href",
    pr.source!.pr_url,
  );
  await source.getByText("Exact analyzed revisions").click();
  for (const sha of [
    pr.source!.head_sha,
    pr.source!.base_sha,
    pr.source!.merge_base_sha,
  ])
    await expect(source).toContainText(sha);
  expect(requests.every((url) => url === "/api/config")).toBe(true);
});
