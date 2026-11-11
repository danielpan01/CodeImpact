# CodeImpact project context

Owner: GitHub **danielpan01**. Goal: a memorable, practical SWE portfolio project
with an original analysis component the owner can defend in an interview.

Origin: the “Vibe Coding Ideas” conversation proposed a Python-first PR impact
explorer: changed functions, potential downstream effects and relevant tests.

## Locations and ownership

- GitHub: https://github.com/danielpan01/CodeImpact — private. On November 5, 2026,
  local `main` and remote `main` were verified at
  `0d5c06fbf7f168bac27eada6f4d2f56a67414c7f` (`Initialize CodeImpact starter`).
- Active local Codex project: **CodeImpact**, attached to
  `/Users/danny/Documents/ChatGPT/CodeImpact`.
- Original local working tree created by setup, retained unchanged:
  `/Users/danny/Documents/Codex/2026-11-05/referenced-chatgpt-conversation-this-is-an/outputs/codeimpact`
- ChatGPT project: **CodeImpact** (`g-p-6aed253d2ef88191b129b52d050ea7b7`).
- Cloud Work chat: **CodeImpact Project Orientation**:
  https://chatgpt.com/c/6aed2816-95c0-83e8-9ff8-682f88b76275

The local Codex project initially pointed at an empty folder. The existing clean
checkout and its Git history were copied there on November 5, 2026, and pinned
dependencies were installed in that folder. Continue local work in the active Codex
project; the original checkout is a separate copy and does not receive these edits.
No repository was created on GitHub during this milestone.

The cloud chat was created inside the existing project and its context reply was
verified. Phone access itself was not tested. Open the same ChatGPT account on web
or phone and find the chat in CodeImpact. A cloud conversation does not automatically
mirror this Mac folder. The user must push reviewed changes before GitHub can serve
as the shared source of truth. GitHub connector access to the new private repository
was verified during setup for this new private repo. After the first push, verify
that the cloud chat can retrieve the actual files; account connection alone does
not guarantee that every execution environment can clone them.

The setup agent does not stage, commit or push the project. User Git identity is
left unchanged. Test fixtures create synthetic commits in temporary directories
using an explicitly fictional fixture identity, never in this project repository.

## Current scope

Working local vertical slice: AST graph, semantic snapshot comparison, deleted-node
preservation, conservative impact traversal, ranked evidence paths, Git CLI,
FastAPI, responsive React graph, demo, upload/export, pinned dependencies, tests,
lint/type checking and CI configuration. Consult VALIDATION.md for actual results.

Public GitHub PR ingestion was implemented locally on November 8, 2026, starting
from `34eb6b05d193468df3903f8cccaf056ec688b8f5` on `main`. It uses pinned merge-base/head
snapshots, supports public forks, preserves evidence paths and reports explicit input
and network failures. It has a PR URL form and exportable revision provenance. A live
MarkupSafe PR and deterministic HTTP/browser tests are recorded in VALIDATION.md.
The existing analyzer and empty-module fix were preserved. The November 10 milestone
started with this work present in clean local commit `2604fd7` on `main`.

Inspectable changes and revision-aware evidence were implemented locally November
10, 2026. Report schema 2.0 adds shared source files, per-symbol before/after ranges,
per-revision dependency evidence, exact typed recommendation edges and mixed-path
labels. The Changes view opens directly from a test recommendation while preserving
its explanation. Map, Tests, demo, uploads and public PR analysis remain available.
Exports contain full source for changed files; previews are bounded and escaped.
Snapshot input is unchanged; old reports must be re-analyzed. See ARCHITECTURE.md
for the contract and VALIDATION.md for observed regression-first and final results.
These new task edits remain unstaged and uncommitted; only the user may commit/push.

Not implemented: GitHub App auth, durable jobs, cross-request source caching,
database, public hosted app, production abuse controls or a real-repository accuracy
benchmark. Do not present those as existing features.

## Model and cross-device settings

User preference: **GPT-6 Astra, Extra high**. The cloud creation tool does not accept
model or reasoning overrides, so setup did not switch or verify those settings.
Choose Astra in the chat's model selector and Extra high in its reasoning controls
if offered by the account. Availability varies by client and workspace.

Official guidance describes cloud Work and eligible synced conversations across
devices. Local access through a synced conversation depends on the workspace setting
and a connected computer. This setup uses a cloud chat plus a separate local working
tree; no local-computer sync setting was changed or verified.

Sources checked during setup:
[Work and cross-device behavior](https://learn.chatgpt.com/docs/get-started-with-work),
[model and effort selection](https://learn.chatgpt.com/docs/model-selection).

## Build strategy

Use Codex to implement bounded slices. Review and understand each before making your
own commit. Sequence: own the engine → labeled correctness corpus → real public PR
ingestion → durable jobs/private authorization/deployment → measured evaluation.

Most impressive evidence: show a real change, traverse its dependency path to a test,
retain deleted dependencies, label uncertainty, compare against known affected tests,
and report honest measurements. Avoid invented resume metrics and unsupported claims
that selected tests can safely replace the complete suite.
