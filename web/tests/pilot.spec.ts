import { test, expect } from "@playwright/test";
import { readFile } from "node:fs/promises";

const KEY = "browser-test-only-pilot-key-with-32-characters";
test.use({ baseURL: "http://127.0.0.1:8003" });

test("built pilot keeps demo public and protects snapshot analysis with a memory-only key", async ({
  page,
}, testInfo) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto("/");
  await expect(page.getByLabel("Pilot access key")).toBeVisible();
  expect(
    (await page.getByLabel("Pilot access key").boundingBox())!.height,
  ).toBeGreaterThanOrEqual(44);
  await expect(page.getByText("Pilot service", { exact: true })).toHaveCount(1);
  await page.getByRole("button", { name: "Load demo", exact: true }).click();
  await expect(page.locator(".test-row")).toHaveCount(3);
  await page.getByRole("button", { name: "New analysis", exact: true }).click();
  const request = JSON.parse(
    await readFile(
      new URL(
        "../../corpus/real-v3/cases/inflection_title.json",
        import.meta.url,
      ),
      "utf8",
    ),
  ).request;
  const response = page.waitForResponse("**/api/analyze");
  await page.getByLabel("Upload snapshot JSON").setInputFiles({
    name: "pilot.json",
    mimeType: "application/json",
    buffer: Buffer.from(JSON.stringify(request)),
  });
  expect((await response).status()).toBe(401);
  await expect(
    page.getByText("Pilot access required", { exact: true }),
  ).toBeVisible();
  await page.getByLabel("Pilot access key").fill(KEY);
  const authorized = page.waitForResponse("**/api/analyze");
  await page
    .getByRole("button", { name: "Retry snapshots", exact: true })
    .click();
  const result = await authorized;
  expect(result.status()).toBe(200);
  expect(result.headers()["cache-control"]).toBe("no-store");
  expect(await result.text()).not.toContain(KEY);
  await expect(page.locator(".test-row")).toHaveText([/test_titleize/]);
  await page.getByRole("button", { name: "New analysis", exact: true }).click();
  await expect(page.getByLabel("Pilot access key")).toHaveValue(KEY);
  expect(await page.getByLabel("Pilot access key").getAttribute("type")).toBe(
    "password",
  );
  expect(
    await page.evaluate(() =>
      JSON.stringify({
        local: { ...localStorage },
        session: { ...sessionStorage },
      }),
    ),
  ).not.toContain(KEY);
  expect(page.url()).not.toContain(KEY);
  await page.getByRole("button", { name: "Clear key", exact: true }).click();
  await expect(page.getByLabel("Pilot access key")).toHaveValue("");
  await expect(page.getByLabel("Pilot access key")).toBeFocused();
  await page
    .getByRole("region", { name: "New analysis", exact: true })
    .screenshot({
      path: testInfo.outputPath("pilot-access-light.png"),
    });
  await page.getByRole("button", { name: "Switch to dark theme" }).click();
  await page
    .getByRole("region", { name: "New analysis", exact: true })
    .screenshot({
      path: testInfo.outputPath("pilot-access-dark.png"),
    });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await page.getByLabel("Pilot access key").fill(KEY);
  await page.reload();
  await expect(page.getByLabel("Pilot access key")).toHaveValue("");
  expect(errors).toEqual([]);
});

test("built pilot rejects missing or incorrect credentials and remains healthy", async ({
  request,
}) => {
  const credentials: Record<string, string>[] = [
    {},
    { Authorization: "Bearer wrong" },
  ];
  for (const headers of credentials) {
    const result = await request.post("/api/analyze", {
      headers,
      data: "not valid JSON",
    });
    expect(result.status()).toBe(401);
  }
  expect((await request.get("/ready")).status()).toBe(200);
  expect((await request.get("/api/reports/missing")).status()).toBe(404);
  expect((await request.get("/api/demo")).status()).toBe(200);
});
