import { mkdirSync, readFileSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const web = fileURLToPath(new URL("../", import.meta.url));
const repo = fileURLToPath(new URL("../../", import.meta.url));
const [mode = "visual", ...args] = process.argv.slice(2);
if (!["visual", "update", "a11y"].includes(mode))
  throw new Error("Choose visual, update or a11y.");
if (mode === "update" && (process.env.CI || process.env.QUALITY_PROBE))
  throw new Error("No baseline updates in CI/probes.");
const spec = JSON.parse(
  readFileSync(new URL("../quality-environment.json", import.meta.url)),
);
if (
  !readFileSync(
    new URL("../quality.Dockerfile", import.meta.url),
    "utf8",
  ).includes(`FROM ${spec.baseImage}\n`)
)
  throw new Error("Dockerfile must match the pinned environment manifest.");
const docker = process.env.CODEIMPACT_DOCKER_CONTEXT
  ? ["--context", process.env.CODEIMPACT_DOCKER_CONTEXT]
  : [];
function run(args) {
  const result = spawnSync("docker", [...docker, ...args], {
    stdio: "inherit",
  });
  if (result.error)
    throw new Error(
      `Docker is required: ${result.error.message}. See docs/FRONTEND_MILESTONE8C.md.`,
    );
  if (result.status !== 0) process.exit(result.status ?? 1);
}
// Fresh checkouts need the mountpoint before the repository becomes read-only.
// The volume still supplies Linux dependencies from the image, not the host.
mkdirSync(`${web}node_modules`, { recursive: true });
mkdirSync(`${web}test-results`, { recursive: true });
mkdirSync(`${web}${spec.baselineDirectory}`, { recursive: true });
run([
  "build",
  "--platform",
  spec.platform,
  "-f",
  `${web}quality.Dockerfile`,
  "-t",
  "codeimpact-ui-quality:local",
  web,
]);
const env = ["CI", "QUALITY_PROBE"].flatMap((name) =>
  process.env[name] ? ["-e", `${name}=${process.env[name]}`] : [],
);
run([
  "run",
  "--rm",
  "--init",
  "--platform",
  spec.platform,
  "--network",
  "none",
  "--ipc=host",
  ...env,
  "--mount",
  `type=bind,source=${repo},target=/work,readonly`,
  "--mount",
  "type=volume,target=/work/web/node_modules",
  "--mount",
  `type=bind,source=${web}test-results,target=/work/web/test-results`,
  ...(mode === "update"
    ? [
        "--mount",
        `type=bind,source=${web}${spec.baselineDirectory},target=/work/web/${spec.baselineDirectory}`,
      ]
    : []),
  "codeimpact-ui-quality:local",
  "node",
  "scripts/quality.mjs",
  mode,
  ...args,
]);
