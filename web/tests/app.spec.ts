import { test, expect } from "@playwright/test";

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
