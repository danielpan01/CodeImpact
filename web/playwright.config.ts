import { defineConfig, devices } from "@playwright/test";

// Isolated servers ensure tests exercise this checkout, not stale user processes.
const apiPort = 8002;
const webPort = 5174;

export default defineConfig({
  testDir: "./tests",
  use: {
    baseURL: `http://127.0.0.1:${webPort}`,
    channel: "chromium",
    launchOptions: { args: ["--disable-gpu"] },
    trace: "retain-on-failure",
  },
  webServer: [
    {
      command: `../.venv/bin/python -m uvicorn browser_api:app --app-dir ../tests --host 127.0.0.1 --port ${apiPort}`,
      url: `http://127.0.0.1:${apiPort}/health`,
      reuseExistingServer: false,
    },
    {
      command: "npm run dev",
      env: {
        CODEIMPACT_API_PORT: String(apiPort),
        CODEIMPACT_WEB_PORT: String(webPort),
      },
      url: `http://127.0.0.1:${webPort}`,
      reuseExistingServer: false,
    },
  ],
  projects: [
    { name: "desktop", use: { ...devices["Desktop Chrome"] } },
    { name: "mobile", use: { ...devices["Pixel 7"] } },
  ],
});
