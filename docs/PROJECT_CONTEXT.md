# CodeImpact project context

## Current priority — November 12, 2026

Evaluation v2, bounded module-level partial calls and argument-sensitive filtering
are merged in [PR #6](https://github.com/danielpan01/CodeImpact/pull/6), commit
`f06f72350a552722d91bd529a5ffd0b1d48cc2b5`. Earlier implementation-status paragraphs
below are historical records, not descriptions of uncommitted work today.

The owner has prioritized a substantial frontend redesign next. Follow the active
sequence in [BUILD_PLAN.md](BUILD_PLAN.md) and the detailed [frontend roadmap](FRONTEND_ROADMAP.md):
visual foundation/complete workspace, graph/test/code interaction refinement, then
responsive/accessibility/theme polish. These are planned features. Keep the analyzer,
report contracts and all evaluation baselines fixed during this work. Human label
review and bounded Cachetools fallback improvements remain subsequent work; hosting
and infrastructure follow a demonstrated pilot need.

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
That work is present in clean starting commit `546ee8e` for the corpus milestone.

The bounded analyzer correctness corpus was implemented locally November 10, 2026,
starting on `main` at `546ee8e295c513d3137c4446c7ddde0b63e3075a`. It adds 25 complete
JSON cases (14 supported demonstrations, 11 known-limitation cases), strict label
validation, typed-path checks, exact discrepancy baselines and a deterministic
`make evaluate` workflow. Its initial authored-label agreement: TP 22, FN 3, FP 6, TN 26;
two unclassified recommendations remain separate. Precision 22/28, recall 22/25.
The analyzer and dashboard were not changed. See CORPUS.md and the separate
VALIDATION.md milestone for interpretation and observed checks. That corpus was
merged as `4b50d9f` before the local-import milestone.

Bounded function-local import resolution was implemented locally November 10, 2026,
starting on clean `main` at `4b50d9fd58d28809def15e753032595a66ba76ea`. Direct aliases
are scoped to a function and resolved only after the import. Competing bindings and
unsupported control-flow/closure cases suppress precise calls; direct import
fallback belongs to the function. The former `local_import` FN becomes a TP without
changing any authored label or snapshot. Counts at that milestone: TP 23, FN 2, FP 6, TN 26,
plus two unclassified recommendations; precision 23/29, recall 23/25. The other 24
case reports are unchanged. Schema versions, scoring, dashboard and input limits
remain unchanged. See ARCHITECTURE.md, CORPUS.md and the separate VALIDATION.md
entry for supported scope and actual checks.

That local-import work was merged as `68ae852` (PR #3). The next module-level
rebinding milestone starts from that commit on `codex/module-level-rebinding`.
Its local implementation suppresses ambiguous module import names without removing
conservative import edges. At that milestone the `module_rebinding` FP remained selected, with a
fallback path and priority 23 rather than a misleading resolved path and priority 72.
The directly affected test remains resolved with priority 81 instead of 82 after
removing one incorrect incoming edge. Selected IDs, all authored labels/snapshots
and overall metrics were unchanged at that milestone; the other 24 reports were identical.
Module rebinding was merged as `aca764e` (PR #4).

Real-repository evaluation v1 starts at `aca764e9e3205a612898e29b065230695667fc85`
on `codex/real-repository-evaluation`. It adds six changes across MarkupSafe,
ItsDangerous and Schedule, complete pinned Python snapshots, source/license/tree
provenance, a source-only label review pack and offline `make evaluate-real`.
Labels remain agent drafted: 45 affected, 123 unaffected, 33 uncertain. The initial
run selected 171/201 (45 TP, 102 FP, 0 FN, 21 TN, 24 uncertain selected).
The subsequent user-requested selection refinement separates aggregate body edits
from initialization changes and filters conservative fallback by bounded source
references. The initial selection refinement yielded 60/201 selections. Bounded constructor
and factory argument tracking now yields 56/201 selected, 45 TP, 0 FP, 0 FN, 123 TN,
11 uncertain selected. Authored results: 23 TP, 0 FP, 2 FN, 32 TN, 2 uncertain selected.
All source snapshots, labels, graph evidence and report contracts are preserved;
discrepancy annotations were deliberately updated and the original baseline archived.
The four default-initialization FPs are fixed; the two authored misses remain. Independent
label review and an unseen evaluation set are next; these six cases informed the fix.
Dashboard design and scoring are unchanged. Changes remain unstaged/uncommitted;
see REAL_EVALUATION.md and VALIDATION.md for verification.

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
own commit. Engine, public PR ingestion, revision evidence and the authored corpus
are present locally, with bounded function-local imports and module import rebinding.
The current next step is the frontend program above. Independent review of real-source
labels and bounded fallback improvements remain on the roadmap. Durable jobs, private
authorization and deployment need their own demonstrated requirements.

Most impressive evidence: show a real change, traverse its dependency path to a test,
retain deleted dependencies, label uncertainty, compare against known affected tests,
and report honest measurements. Avoid invented resume metrics and unsupported claims
that selected tests can safely replace the complete suite.
