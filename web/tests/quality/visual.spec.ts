import { test, expect } from "@playwright/test";
import { readFileSync } from "node:fs";
import { layouts, renderState, settle, type State, type Theme } from "./states";

const cases: [State, keyof typeof layouts, Theme, string?][] = [
  ["entry", "desktop", "light"],
  ["entry", "phone", "dark"],
  ["saved-report", "desktop", "light"],
  ["saved-report", "phone", "dark"],
  ["tests", "desktop", "light"],
  ["tests", "desktop", "dark"],
  ["tests", "phone", "light"],
  ["review-plan", "desktop", "light", ".review-plan-dialog"],
  ["review-plan", "phone", "dark", ".review-plan-dialog"],
  ["evidence", "phone", "dark", ".detail-panel"],
  ["map", "desktop", "dark", ".explorer-layout"],
  ["changes", "desktop", "light", ".explorer-layout"],
  ["mixed", "phone", "dark", ".app-shell"],
  ["deleted", "phone", "light", ".graph-panel"],
  ["diagnostics", "desktop", "light", ".diagnostics"],
  ["diagnostics", "phone", "dark", ".diagnostics"],
  ["empty", "phone", "light", ".app-shell"],
  ["zero-discovery", "desktop", "dark"],
  ["error", "phone", "dark"],
  ["loading", "desktop", "light"],
];

for (const [state, layout, theme, selector] of cases) {
  test.describe(`${state}-${layout}-${theme}`, () => {
    test.use({
      viewport: layouts[layout],
      isMobile: layout === "phone",
      hasTouch: layout === "phone",
    });
    test("appearance", async ({ page, browser }, info) => {
      const environment = JSON.parse(
        readFileSync(
          new URL("../../quality-environment.json", import.meta.url),
          "utf8",
        ),
      );
      expect(browser.version()).toBe(environment.chromium);
      const errors: string[] = [];
      page.on("pageerror", (error) => errors.push(error.message));
      const { release } = await renderState(page, state, theme);
      if (state === "zero-discovery") {
        // Capture the empty-state heading and action. Browser/axe checks exercise
        // the expanded explanation, including scrolling to its final paragraph.
        await page.locator(".discovery-scope summary").click();
      }
      if (["mixed", "empty"].includes(state))
        await page.evaluate(() => window.scrollTo(0, 0));
      if (state === "tests" && layout === "phone") {
        await page.evaluate(() => window.scrollTo(0, 0));
        await expect(page.locator(".test-row").first()).toBeInViewport({
          ratio: 1,
        });
      }
      await settle(page);
      if (process.env.QUALITY_PROBE === "visual" && state === "entry") {
        // Explicit failure probe, isolated to test DOM. Updates refuse this flag.
        await page.addStyleTag({
          content:
            ".primary { border-radius: 0 !important; background: #ff00ff !important; }",
        });
      }
      const target = selector ? page.locator(selector) : page;
      // Preserve the earlier screenshots for report screens with a new toolbar.
      const prefix = ["tests", "mixed", "empty", "zero-discovery"].includes(
        state,
      )
        ? "review-workspace-"
        : "";
      // Entry, loading and server-error screens now include the offline picker.
      const entryPrefix = ["entry", "loading", "error"].includes(state)
        ? "offline-"
        : "";
      const name = `${entryPrefix}${prefix}${state}-${layout}-${theme}.png`;
      try {
        if (process.env.QUALITY_MODE === "preview") {
          await target.screenshot({
            path: info.outputPath(name),
            animations: "disabled",
            caret: "hide",
            scale: "css",
          });
        } else {
          await expect(target).toHaveScreenshot(name);
        }
      } finally {
        release();
      }
      if (state === "error") {
        await page
          .getByRole("button", { name: "Retry demo", exact: true })
          .click();
        await expect(page.locator(".test-row")).toHaveCount(3);
      }
      expect(errors).toEqual([]);
      expect(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= innerWidth,
        ),
      ).toBe(true);
    });
  });
}
