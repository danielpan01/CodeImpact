import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { layouts, states, renderState, settle } from "./states";

// All enabled axe rules tagged WCAG 2.0/2.1/2.2 A/AA. No exclusions, disabled
// rules or accepted violation counts. Full page, including scrollable regions.
const tags = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"];
for (const layout of ["desktop", "phone"] as const) {
  for (const theme of ["light", "dark"] as const) {
    test.describe(`${layout}-${theme}`, () => {
      test.use({
        viewport: layouts[layout],
        isMobile: layout === "phone",
        hasTouch: layout === "phone",
      });
      for (const state of states) {
        test(state, async ({ page }, info) => {
          await renderState(page, state, theme);
          await settle(page);
          if (process.env.QUALITY_PROBE === "a11y" && state === "entry") {
            await page
              .getByRole("button", { name: "Analyze PR", exact: true })
              .evaluate((button) => {
                button.textContent = "";
                button.removeAttribute("aria-label");
                button.removeAttribute("aria-labelledby");
                button.removeAttribute("title");
              });
          }
          const results = await new AxeBuilder({ page })
            .withTags(tags)
            .analyze();
          await info.attach("axe-results", {
            body: JSON.stringify(results, null, 2),
            contentType: "application/json",
          });
          expect(
            results.violations,
            JSON.stringify(results.violations, null, 2),
          ).toEqual([]);
        });
      }
    });
  }
}
