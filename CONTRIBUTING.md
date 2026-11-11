# Contributing

Use Python 3.12 and Node 24 for the documented baseline. `make setup` creates an
isolated environment and installs pinned Python/npm dependencies. `make dev` launches
the API and dashboard. `make check` runs Python lint/format, strict source typing,
backend tests with coverage, and the TypeScript production build.

Browser setup: `cd web && npm run install:browsers && npm run test:e2e`.
Playwright installs its browser under node_modules, without requiring a system install.
Use `npm run format:check` to check frontend formatting.

Analyzer changes need a minimal base/head fixture, expected changed symbols, an
evidence-path assertion, and an unaffected control. Add a regression case for a bug
before changing behavior. Preserve uncertainty rather than fabricating an edge.

The developer must personally review, stage, commit and push changes. An assistant
may edit and test but should not take over Git authorship or publishing.

Python pins are in requirements-dev.lock; project dependency ranges are in
pyproject.toml. The lock is a version-pinned development environment, not a
cryptographically hashed supply-chain lock. Update intentionally and verify on a
fresh environment. npm uses package-lock.json and `npm ci`.

Hosted validation runs through [Quality checks](https://github.com/danielpan01/CodeImpact/actions/workflows/ci.yml).
Check the run for the exact commit you are reviewing. Detailed setup and analysis
examples are in the [usage guide](docs/USAGE.md).

