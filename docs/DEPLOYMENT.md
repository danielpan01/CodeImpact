# Local pilot deployment

Milestone 6 prepares and verifies a built, authenticated service locally. The owner
deferred live hosting on November 14, 2026. There is no deployed URL, hosting account,
container-build result or human pilot result to report.

## Run the built application

Use macOS or Linux with the pinned dependencies from `make setup`. From the repo root:

```sh
# Generate a local pilot key; this is separate from any GitHub credential.
export CODEIMPACT_ACCESS_KEY="$(.venv/bin/python -c 'import secrets; print(secrets.token_urlsafe(32))')"
# Display it locally to paste into the browser's Pilot access key field.
printf '%s\n' "$CODEIMPACT_ACCESS_KEY"
make serve
```

Open **http://127.0.0.1:8080**. This serves `web/dist` and the API from one origin,
without Vite or a proxy. The public demo works without the key. Snapshot and public
GitHub PR analysis require it. The password field holds the key in page memory only;
**Clear key** removes it and reload clears it. The key is never put in a report,
URL, cookie or browser storage. It is sent as an Authorization bearer header.

Ctrl-C stops the service and reaps active workers. Afterward,
`unset CODEIMPACT_ACCESS_KEY` clears the shell variable. The launcher fails if the key is
missing/invalid or the frontend build is absent. Keys must be 32–256 printable ASCII
characters without whitespace. Keep keys out of Git, `.env` files and `VITE_` settings.
To change the port after building, use `.venv/bin/python -m codeimpact.serve --port 8081`.

The development command `make dev` retains the two-server loopback workflow and
allows an unset key. Use `make serve` for the protected pilot configuration. An
optional `CODEIMPACT_GITHUB_TOKEN` remains server-side and is never inherited by an
analysis worker; it does not enable private repositories.

## Boundaries and operations

| Control | Default behavior |
| --- | --- |
| API process | One process; Uvicorn connection/task concurrency limit 16 |
| Analysis admission | Two concurrent requests, including GitHub ingestion and the public demo; busy requests receive 503 and `Retry-After` |
| Request rate | One service-wide token bucket: capacity 30, refill 30/minute; exhausted requests receive 429 and `Retry-After` |
| Input | 6,000,000-byte HTTP/worker JSON limit; existing 300 files, 200,000 bytes/file and 2,000,000 source bytes per revision |
| Deadlines | Body upload 10 seconds, application response 90 seconds after upload; GitHub import retains its 60-second deadline |
| Worker | Fresh Python process, JSON stdin/stdout, 20-second wall budget and 15-second CPU limit |
| Memory | 256 MiB RSS watchdog sampled every 20 ms; Linux additionally enforces 1 GiB virtual address space |
| Output | 32 MiB internal worker reply limit; oversized reports fail explicitly |
| Cleanup | Disconnect, timeout, cancellation and shutdown terminate and reap workers; no background retry |
| Data | No saved jobs, reports or source; API responses use `Cache-Control: no-store`; exports are user-controlled files |

Authorization and analysis admission occur **before** reading request bodies. The
rate bucket includes the public demo; unauthorized private requests do not consume
analysis capacity. Health, readiness and static assets do not consume analysis slots.
`CODEIMPACT_CONCURRENCY` accepts 1–8 and `CODEIMPACT_REQUESTS_PER_MINUTE` accepts 1–600.
Defaults target a small pilot, not measured multi-user capacity. Keep one API process:
these controls are process-local, not distributed quotas. Browser tests explicitly use
8/600 to accommodate parallel automation; production defaults have separate tests.

`GET /health` reports liveness. `GET /ready` becomes ready after a real demo worker
has spawned, been monitored and returned successfully. `GET /api/config` exposes only
whether access is required. JSON request logs contain request ID, known route, status
and duration; they omit source, request bodies, keys, PR URLs and query strings.
Generic access logs are disabled by the pilot launcher. Correlate failures with the
`X-Request-ID` response header. Source-bearing worker exceptions are not returned.

This is process/resource isolation, **not an OS security sandbox**: workers share the
host user and filesystem and have no network namespace restriction. The analyzed
repository is never executed or imported. RSS sampling can miss brief peaks; the
Linux address-space cap is a different metric from resident memory. macOS does not
use `RLIMIT_AS` here. The Linux-specific integration test is skipped on this Mac
and runs in Linux CI; see [PR #12 checks](https://github.com/danielpan01/CodeImpact/pull/12/checks)
for the publication result. No container runtime
was available for a local Linux/container deployment check.

## Verification and recovery

```sh
make check
make evaluate evaluate-real evaluate-real-v2 evaluate-real-v3
make verify-pilot
cd web && npm run test:e2e
```

`verify-pilot` starts the built server on an available loopback port with an ephemeral
key, checks readiness/assets/demo, rejects unauthorized input, verifies an authorized
v3 report against its frozen hash, rejects source/report-file URLs and stops the
server. It makes no GitHub request. Playwright also exercises the production build
on port 8003, including key errors, same-input retry, clearing/reloading and phone
layouts. Ports 8002, 8003 and 5174 must be free for browser checks.

A timeout, resource failure or interruption leaves no resumable job. A new request
starts from the submitted snapshots or reads the PR's current pinned revisions.
Tests verify that failures release capacity and the next request succeeds. Saved
report URLs do not exist. There is no per-user report authorization model to imply.

Before a future live pilot, choose the owner-controlled host, verify its Linux
resource behavior, put TLS and a host memory limit around the service, configure
secrets outside the repository, and repeat these checks against that exact deployment.
Share the pilot key only through the owner's chosen private channel. The key is
shared pilot access, not individual accounts or GitHub App authorization. Hosting,
identity and durable jobs remain separate decisions; no database or queue was added.

See [measured performance](PERFORMANCE.md), [architecture](ARCHITECTURE.md) and
[observed checks](VALIDATION.md).
