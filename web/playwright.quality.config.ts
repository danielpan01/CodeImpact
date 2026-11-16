import { defineConfig } from "@playwright/test";
import { existsSync } from "node:fs";

const mode = process.env.QUALITY_MODE ?? "visual";
if (mode === "update" && (process.env.CI || process.env.QUALITY_PROBE)) {
  throw new Error("No updates in CI or defect probes.");
}
const suite =
  mode === "a11y" ? "a11y" : mode === "preview" ? "preview" : "visual";
const environment = existsSync("/etc/codeimpact-quality.json")
  ? "canonical"
  : "local";
const output = `test-results/quality/${environment}/${suite}`;
export default defineConfig({
  testDir: "./tests/quality",
  testMatch: "*.spec.ts",
  fullyParallel: false,
  workers: 1,
  retries: 0,
  forbidOnly: !!process.env.CI,
  updateSnapshots: mode === "update" ? "all" : "none",
  snapshotPathTemplate: "{testDir}/baselines/{arg}{ext}",
  outputDir: `${output}/results`,
  reporter: [
    ["list"],
    ["html", { outputFolder: `${output}/html`, open: "never" }],
    ["json", { outputFile: `${output}/results.json` }],
  ],
  expect: {
    toHaveScreenshot: {
      animations: "disabled",
      caret: "hide",
      scale: "css",
      threshold: 0.1,
      maxDiffPixels: 0,
    },
  },
  use: {
    baseURL: "http://127.0.0.1:5176",
    browserName: "chromium",
    channel: "chromium",
    launchOptions: { args: ["--disable-gpu"] },
    locale: "en-US",
    timezoneId: "UTC",
    deviceScaleFactor: 1,
    reducedMotion: "reduce",
    serviceWorkers: "block",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  webServer: {
    command: "npm run dev",
    env: { CODEIMPACT_WEB_PORT: "5176" },
    url: "http://127.0.0.1:5176",
    reuseExistingServer: false,
  },
});
