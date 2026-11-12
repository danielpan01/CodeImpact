import { expect, type Page } from "@playwright/test";

export async function loadDemo(page: Page) {
  await page.goto("/");
  await page.getByRole("button", { name: "Load demo", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "Tests", exact: true }),
  ).toHaveAttribute("aria-pressed", "true");
}
export async function openAnalysis(page: Page) {
  if (
    !(await page
      .getByRole("button", { name: "Analyze PR", exact: true })
      .isVisible())
  ) {
    await page
      .getByRole("button", { name: "New analysis", exact: true })
      .click();
  }
}
export async function showEvidence(page: Page) {
  await page.getByRole("button", { name: "Tests", exact: true }).waitFor();
  const trigger = page.getByRole("button", {
    name: "View evidence",
    exact: true,
  });
  if (await trigger.isVisible()) await trigger.click();
}
export async function openChangedCode(page: Page) {
  await showEvidence(page);
  await page
    .getByRole("button", { name: "Open changed code", exact: true })
    .click();
}
