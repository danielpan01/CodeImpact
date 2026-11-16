import { readFileSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const root = fileURLToPath(new URL("../", import.meta.url));
const [mode, ...args] = process.argv.slice(2);
const environment = JSON.parse(
  readFileSync(new URL("../quality-environment.json", import.meta.url), "utf8"),
);
const installed = JSON.parse(
  readFileSync(
    new URL("../node_modules/@playwright/test/package.json", import.meta.url),
    "utf8",
  ),
);
if (installed.version !== environment.playwright)
  throw new Error(
    "Playwright must match quality-environment.json; reinstall with npm ci.",
  );
if (
  process.env.QUALITY_PROBE &&
  !["visual", "a11y"].includes(process.env.QUALITY_PROBE)
)
  throw new Error("Unknown defect probe.");
if (!["visual", "update", "preview", "a11y"].includes(mode)) {
  throw new Error("Choose visual, update, preview or a11y.");
}
if (args.some((arg) => /update-snapshots|ignore-snapshots/.test(arg))) {
  throw new Error(
    "Use the explicit test:visual:update command for reviewed updates.",
  );
}
if (mode === "update" && (process.env.CI || process.env.QUALITY_PROBE)) {
  throw new Error("Baseline updates are forbidden in CI and defect probes.");
}
if (["visual", "update"].includes(mode)) {
  const expected = readFileSync(
    new URL("../quality-environment.json", import.meta.url),
    "utf8",
  );
  let actual = "";
  try {
    actual = readFileSync("/etc/codeimpact-quality.json", "utf8");
  } catch {
    /* Noncanonical host. */
  }
  if (
    process.platform !== "linux" ||
    process.arch !== "arm64" ||
    actual !== expected
  ) {
    throw new Error(
      "Canonical comparisons require the pinned container: npm run quality:container -- " +
        mode +
        ". Use test:visual:preview for noncanonical captures.",
    );
  }
}
const result = spawnSync(
  process.execPath,
  [
    "node_modules/@playwright/test/cli.js",
    "test",
    "--config=playwright.quality.config.ts",
    mode === "a11y" ? "accessibility.spec.ts" : "visual.spec.ts",
    ...args,
  ],
  {
    cwd: root,
    stdio: "inherit",
    env: {
      ...process.env,
      QUALITY_MODE: mode,
      PLAYWRIGHT_BROWSERS_PATH: process.env.PLAYWRIGHT_BROWSERS_PATH ?? "0",
    },
  },
);
if (result.error) throw result.error;
process.exit(result.status ?? 1);
