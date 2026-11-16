# Security and analysis boundaries

The development launcher binds to 127.0.0.1. The built pilot launcher also defaults
to loopback and requires a shared access key for submitted-code analysis. It adds
admission/rate limits, disposable worker processes, deadlines and resource budgets.
Live hosting is deferred; there are no individual accounts, persisted reports or
distributed quotas. See [deployment boundaries](docs/DEPLOYMENT.md) before choosing
a host. Process limits do not provide an OS filesystem/network security sandbox.

Sources are parsed with Python's AST library and never executed. The CLI reads Git
objects directly, resolves refs with `--end-of-options`, avoids shell interpolation,
skips symlinks and submodules, and uses subprocess timeouts. Only UTF-8 Python files
are accepted by the Git importer. No uploaded paths are written to disk.

Per snapshot: at most 300 files, 200,000 UTF-8 bytes per file, 2,000,000 total source
bytes. HTTP bodies are limited to 6,000,000 bytes, including chunked requests. Complex
AST input can still consume CPU and memory. The API applies wall/CPU/output limits,
a sampled RSS watchdog and a Linux address-space cap, and reaps workers on timeout,
cancellation or disconnect. Admission happens before buffering source. RSS sampling
is not a hard allocation cap. Linux-specific enforcement still needs validation on
the eventual host; local verification was on macOS. CLI/evaluation calls use the
engine directly and do not inherit the API's worker budgets.

The API does not send source code to an LLM or external service. The dashboard uses
system fonts and performs no external font request. Access keys stay in page memory
and are absent from reports, URLs and browser storage. API responses use no-store;
request logs omit source, keys and user-supplied URLs. Exports include changed-file
source, so the user controls where exported files are stored or shared.

Public GitHub ingestion validates exact PR URLs, reads only fixed GitHub API hosts,
pins immutable merge-base/head SHAs, verifies blob hashes, bounds downloads and
rejects truncated trees. It never runs hooks, imports upstream source or installs
upstream dependencies. Optional GitHub credentials stay server-side and are omitted
from the analysis worker environment. Private repositories remain unsupported even
with a token. A future private integration must authorize every job/report access;
the shared pilot key is not repository authorization. Never use `pull_request_target`
to execute untrusted PR code with secrets.

