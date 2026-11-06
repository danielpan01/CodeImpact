# CodeImpact working agreement

Read README.md and docs/ARCHITECTURE.md before changing the analyzer.

- The user owns all commits and pushes. Do not stage, commit, push, force-push,
  create remote file commits, change Git identity, or open a PR without an explicit
  new instruction authorizing that action. Local edits and tests are authorized.
- Do not execute, import, install dependencies from, or check out analyzed repositories.
  Read source as data. No `eval`, `exec`, pickle, shell interpolation or unsafe archives.
- Keep report schema changes explicit. Preserve stable IDs, deterministic ordering,
  deleted-symbol handling and caller-to-dependency edge direction.
- Every recommendation must have a valid evidence path. Distinguish resolved calls
  from conservative fallbacks. Never label heuristic scores as probabilities.
- Write tests for algorithmic behavior and failure modes. Run `make check` for code
  changes and `cd web && npm run test:e2e` for behavior changes in the dashboard.
- Keep README claims and docs/VALIDATION.md consistent with observed results.
  Do not invent benchmark numbers, deployed URLs or integration completion.
- Prefer a bounded milestone. Ask only when a product choice or missing credential
  blocks meaningful progress. Do not add infrastructure without a demonstrated need.
- Do not modify unrelated files or discard the user's changes.

