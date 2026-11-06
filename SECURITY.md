# Security and analysis boundaries

This starter binds to 127.0.0.1. It has no user authentication, quotas, job isolation,
durable storage or production abuse controls. Do not expose it as a public upload
service until those deployment requirements are implemented and tested.

Sources are parsed with Python's AST library and never executed. The CLI reads Git
objects directly, resolves refs with `--end-of-options`, avoids shell interpolation,
skips symlinks and submodules, and uses subprocess timeouts. Only UTF-8 Python files
are accepted by the Git importer. No uploaded paths are written to disk.

Per snapshot: at most 300 files, 200,000 UTF-8 bytes per file, 2,000,000 total source
bytes. HTTP bodies are limited to 6,000,000 bytes, including chunked requests. Complex
AST input can still consume CPU and memory; production parsing needs isolated workers,
resource budgets, cancellation and admission control.

The API does not send source code to an LLM or external service. The web dashboard's
Google Fonts stylesheet is an optional external presentation request; system fonts
are the fallback. Source contents are not sent to that font provider.

Before GitHub ingestion: allowlist GitHub API hosts, validate owner/repo/PR input,
pin immutable SHAs, handle pagination and truncation, cap downloads, never run PR
hooks, keep tokens server-side, avoid token/source logging, and verify repository
authorization on every job/report read. Never use `pull_request_target` to execute
untrusted PR code with secrets. These are upcoming implementation requirements.

