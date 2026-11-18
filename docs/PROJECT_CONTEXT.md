# CodeImpact project context

## Current priority — November 17, 2026

The 9C literal-table and validator/export slices merged through PRs #20 and #21.
The test parameter-table slice is implemented. Inflection titleize
selects 2/22 with one resolved call and one conservative mutation/cleanup path.
Expanded v3 is 47/120, with 42 TP / 5 FP / 0 FN / 61 TN and all 12 uncertain
definitions unselected. New `parameter-tables-v1` receipts preserve the
additive-export and literal-table records. Labels await independent review.
[Titleize source and evidence review](PARAMETER_TABLE_REVIEW.md)

## Preserved milestone context

The measurements below describe their named milestones; the current 9C result
is above.

The 9B descriptor slice merged through PR #18 at
`383b819667f91e3bcf6a39e23c1cf5a7b6b3554e`. The 9B Slugify slice is implemented.
A known literal dispatch into an unchanged legacy module removes
66 Boundary false positives. Boundary now selects 42/133, with 28 TP, 14 FP,
0 FN and 88 TN. All three uncertain definitions remain unselected. V2 selects
327/581 with 109 TP, 205 FP, 0 FN and 245 TN. The ASCII case and the other four
v2 analyses retain their hashes. New `legacy-dispatch-v1` receipts preserve
the descriptor and earlier baselines. [Exact Slugify results](SLUGIFY_FALLBACK_REVIEW.md)

Milestone 9A merged at `41753b3522246fe8c947a27326ada95b1c285dce` through PR #17.
Milestone 9B implements ordinary zero-argument descriptor binding.
One descriptor false positive is removed, leaving 35/154 selected and
0 TP / 30 FP / 0 FN / 116 TN. The five selected and three unselected uncertain
definitions retain their outcomes. V2 becomes 393/581 selected with
109 TP / 271 FP / 0 FN / 179 TN, and the other cases retain their analysis hashes.
The new `descriptor-binding-v1` receipts preserve milestone 9A and all earlier
records. [Descriptor proof and measurements](DESCRIPTOR_REFINEMENT_REVIEW.md)

Milestone 7 merged through PR #16 at
`a4d29a7c7c462c32f0bb7978e45708166b0106b0`. All final PR and post-merge checks passed.
Milestone **9A** is implemented; the owner authorized publication on November 16. It permits
only direct literal-raising callbacks in the existing mapping exclusion proof.
Exactly `tests/test_rr.py::RRCacheTest.test_rr_bad_choice` is removed: LFU
138/156, 6 TP / 124 FP / 0 FN / 18 TN; all six affected and eight uncertain
selections remain. V2 is 394/581, 109 TP / 272 FP / 0 FN / 178 TN, with 13/22
uncertain selected. Retained recommendations and all five other v2 analyses are
identical. V3's full expanded measurement is unchanged. New `lfu-callback-v1`
receipts link the untouched milestone 7 receipts; see [scope and evidence](LFU_CALLBACK_REVIEW.md).
The paragraphs below describe the preserved earlier milestones.

Milestones 8A, 8B and 8C are merged in PRs #13, #14 and
[#15](https://github.com/danielpan01/CodeImpact/pull/15). 8C’s merge commit is
`7084ab04dd60881a6dde6e91986911f1d9f6ece2`; its
[post-merge quality jobs passed](https://github.com/danielpan01/CodeImpact/actions/runs/43808633061).
The owner authorized that merge, followed by local milestone 7 implementation,
then requested publication of milestone 7 on November 16. There were no starting
user edits. The implementation and publication checks are recorded in VALIDATION.md.

Milestone 7 adds literal `test.py` to the existing case-sensitive filename policy.
It preserves direct class/nested discovery and excludes arbitrary production files,
compound-statement definitions and runtime collection. A source-only draft labeled
30 newly eligible Ordered Set definitions before expanded analysis: 1 affected,
17 unaffected, 12 uncertain. Only `test_pop` is newly selected, conservatively.
Milestone 7 v3 was 85/120 selected, 42 TP / 43 FP / 0 FN / 23 TN, with 12 uncertain
unselected definitions. Original v3 remains 84/90 plus 30 excluded definitions;
all original corpus/labels/provenance/freezes/first runs/baselines are unchanged.
Authored/v1 stable reports and v2’s full mapping measurement are unchanged.
New current receipts/output filenames are separate. Application/export 2.0 stays.

Tests has a keyboard-accessible discovery-scope disclosure and distinct zero-test,
zero-recommendation and filtered-empty states. A separate authored fixture retains
zero-discovery coverage. 8A styling, 8B lossless diagnostics and 8C’s 16 canonical
comparisons/48 accessibility scans remain; two intentionally changed screenshots
have new filenames, preserving the old 16. Read [TEST_DISCOVERY.md](TEST_DISCOVERY.md)
and [VALIDATION.md](VALIDATION.md) for the exact results and remaining findings.

**Next evaluation milestone: 10, with new frozen inputs and reviewed labels.**
The 124 remaining LFU false positives are a separate scope. Live
hosting and the human pilot remain owner-deferred; independent source-label review
remains pending. Automated/agent review is not accessibility certification or
independent usability testing. The owner-approved local Colima runtime supplies
8C’s pinned Linux ARM64 environment; it does not host CodeImpact.

Evaluation v2, bounded module-level partial calls and argument-sensitive filtering
are merged in [PR #6](https://github.com/danielpan01/CodeImpact/pull/6), commit
`f06f72350a552722d91bd529a5ffd0b1d48cc2b5`. Earlier implementation-status paragraphs
below are historical records, not descriptions of uncommitted work today.

Frontend milestones 1–3 are merged. Foundation landed in [PR #7](https://github.com/danielpan01/CodeImpact/pull/7),
interaction refinement in [PR #8](https://github.com/danielpan01/CodeImpact/pull/8),
and themes/responsive recovery in [PR #9](https://github.com/danielpan01/CodeImpact/pull/9),
commit `1dbec1bd1051b2ced15a5bd10aa980e768f07cca`, after CI passed. The owner waived
milestone 3's separate developer walkthrough; it was not performed.

The bounded mapping milestone merged in [PR #10](https://github.com/danielpan01/CodeImpact/pull/10),
commit `25b58040ede56918755a6a83277de98408f3dcb9`, with post-merge CI passing. Bounded mapping
fallback removes 11 unrelated FIFO/LRU/RR recommendations from the LFU case while
retaining every affected and uncertain selection. V2 is 109 TP / 273 FP / 0 FN / 177 TN,
395/581 selected, including 13/22 uncertain definitions. Authored/v1 reports and
all five other v2 analyses remain unchanged. `mapping-fallback-v1` records current
behavior separately; all three prior v2 baselines and original corpus files remain
intact. Analysis report 2.0 and dashboard contracts are unchanged; only the separate
fresh evaluation wrapper advances to 4.0.

Human source-label review remains pending; [review notes](MAPPING_FALLBACK_REVIEW.md)
record the source-only controls without claiming approval. Milestone 5 merged in
[PR #11](https://github.com/danielpan01/CodeImpact/pull/11), commit
`02598a155bda061b56d03a0fcee161e13df10e89`, with post-merge CI passing:
six unused changes, frozen draft labels and first measurements, an offline v3
replay gate and reproducible walkthrough inputs. V3 selects 84/90 discovered tests:
41 TP / 43 FP / 0 FN / 6 TN; 30 more test-shaped functions are outside discovery.
The analyzer and all 72 historical corpus files/three report outputs are unchanged.
The dashboard distinguishes no discovered tests from no recommendations.
The owner deferred the human developer pilot on November 14; materials are prepared,
with no participant feedback claimed. See REAL_EVALUATION_V3.md and DEVELOPER_PILOT.md.

Milestone 6's local scope is complete: disposable
analysis workers, wall/CPU/RSS/output limits, admission before body buffering,
shared-key access for submitted code, a public demo, readiness and source-free logs.
The built UI and API run from one origin; keys stay in browser memory only. Six-case
measurements and local deployment verification are documented in PERFORMANCE.md,
DEPLOYMENT.md and VALIDATION.md. All 106 historical corpus files and the 16 existing
engine/model/ingestion/evaluation modules apart from the API remain byte-identical.
The owner authorized publication in [PR #12](https://github.com/danielpan01/CodeImpact/pull/12)
on November 15 while reaffirming the November 14
live-hosting deferral: prepare and verify locally. There is no deployed URL,
database, queue, durable-job layer, individual-account system or new human feedback.
Remaining LFU, descriptor, Slugify, fixture and runtime-import limitations stay open.
See VALIDATION.md for observed checks. Hosting and infrastructure follow a demonstrated
pilot need.

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
