# Authored analyzer correctness corpus

This corpus measures agreement with **authored dependency labels** on 25 small
Python changes. It is not externally validated ground truth, production accuracy,
proof of runtime test failures, or evidence that unselected tests can safely be
skipped. The full test suite remains the merge gate.

The labels were written from each fixture's intended dependencies before running
the evaluator, independently of the analyzer's recommendations. Sources and labels
are inspectable in `corpus/cases/*.json`. No fixture source or fixture test is
executed, imported, installed, or checked out. JSON is parsed into bounded snapshot
models, and Python is read only through `ast.parse`.

## Run and inspect

From the repository root, using the existing pinned environment (`make setup` on a
fresh checkout):

```sh
make evaluate
```

This prints every case's selected/missed affected tests, selected/unselected
unaffected tests, unclassified recommendations, ratios and limitation notes. It
writes `reports/corpus-evaluation.json`, which is ignored by Git and can be
regenerated. The explicit equivalent is:

```sh
.venv/bin/python -m codeimpact.evaluate \
  --corpus corpus/cases --output reports/corpus-evaluation.json

# Inspect one example; use a separate output so the full report stays available.
.venv/bin/python -m codeimpact.evaluate --case module_overselection \
  --output reports/module-overselection.json

.venv/bin/pytest tests/test_corpus.py tests/test_evaluation.py --no-cov
# Scope, ordering and ambiguity regressions for the local-import extension:
.venv/bin/pytest tests/test_local_imports.py --no-cov
.venv/bin/pytest tests/test_module_rebinding.py tests/test_selection_precision.py --no-cov
make check
```

Exit status **0** means every observed discrepancy matches its explicit baseline;
it does **not** mean the analyzer has no mistakes. Status **1** means a false
positive, false negative or unclassified selection changed; the report is still
written for review. Status **2** means invalid input, a broken evidence contract or
an input/output error; the diagnostic goes to stderr. A previous output can remain
after a status-2 error, so do not mistake it for a new successful evaluation.
Unknown `--case` IDs fail. Output inside the corpus directory is refused.

To read actual source with physical newlines instead of JSON escape sequences:

```sh
.venv/bin/python - <<'PY'
import json
from pathlib import Path
case = json.loads(Path("corpus/cases/local_import.json").read_text())
print(case["description"])
for side in ("base", "head"):
    for path, source in sorted(case["request"][side]["files"].items()):
        print(f"\n{side}: {path}\n{source}")
for group in ("expected_affected", "expected_unaffected", "unclassified"):
    print(group, json.dumps(case[group], indent=2))
PY
```

This prints strings only. Do not copy fixture files into an importable package or
run pytest against extracted snapshots. The application tests above test the
analyzer using strings; they do not run the tests inside those strings.

## Case contract and discovery

Each version-1.0 JSON case contains:

| Field | Meaning |
| --- | --- |
| `id`, `description` | Unique stable snake-case ID and plain-English purpose |
| `category` | `supported` or `known_limitation`; both enter overall metrics |
| `features` | Unique nonempty tags describing the language behavior |
| `request` | Complete `base.files` and `head.files`, plus a label; ordinary `AnalysisRequest` input |
| `expected_affected` | Map of head test IDs to independently authored dependency rationales |
| `expected_unaffected` | Map of head test IDs to rationales for independence from this change |
| `unclassified` | Explicit map of head test IDs whose dependency labels are deliberately withheld, with reasons |
| `known_discrepancies.false_positives` | Exact unaffected IDs currently selected, each with an explanation |
| `known_discrepancies.false_negatives` | Exact affected IDs currently missed, each with an explanation |
| `expected_unclassified_recommendations` | Exact selected unclassified IDs; excluded from precision/recall |
| `limitations` | Explanation list, required for `known_limitation`, empty for `supported` |

Every map/list is explicit, including empty ones. The three label maps must be
disjoint and cover **every discoverable head test**. An unlisted test is an error,
never automatically unaffected. Removed tests belong only to the base snapshot
and cannot be head labels or recommendations. All cases include an independent
unchanged control subsystem.

Discovery follows CodeImpact's documented rule, **not full pytest collection**:
the file basename starts with `test_` or ends with `_test.py`; a function or async
function's name starts with `test_`. Direct definitions inside functions/classes
are visited recursively, producing IDs such as `tests/test_x.py::TestGroup.test_x`.
Definitions nested under `if`, loops or `try` are not collected. Class names
themselves are not tests. Unparseable test files contribute no discovered tests.
Duplicate discovered test IDs are rejected as ambiguous. The corpus validator
implements this rule separately from analyzer recommendation generation.

The loader rejects duplicate JSON keys, duplicate case IDs, unknown fields, blank
descriptions/rationales, overlapping labels, invalid discrepancy membership and
inconsistent categories. Supported cases may not record false positives/negatives
or limitation notes. A limitation case may have no selection mistakes: `reexports`
is rescued by a fallback, yet still lacks precise call resolution.

Bounds: at most 100 case files, 1,000,000 bytes per JSON file and 20,000,000 aggregate
JSON bytes. Directory/case-file symlinks are rejected. Each snapshot also retains
the existing 300 Python files, 200,000 bytes/file and 2,000,000 total source-byte
limits and normalized relative Python paths. This is a local bounded corpus
workflow, not adversarial parsing isolation or a performance benchmark.

## Results and metric definitions

Observed November 11, 2026, after scoped aggregate-fallback selection. All 25
cases match their deliberately updated discrepancy annotations. All source
snapshots and authored affected/unaffected/unclassified labels are unchanged.
The [pre-refinement baseline](../corpus/selection-baseline-v1.json) preserves original
annotations, selected IDs, counts and source/label hashes. Earlier milestone
results also remain in [VALIDATION.md](VALIDATION.md).
Counts are **case/test pairs**, not independent real-world observations.

| Population | Cases | TP | FN | FP | TN | Selected unclassified | Precision | Recall |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| Overall | 25 | 23 | 2 | 0 | 32 | 2 | 23/23 = 100% | 23/25 = 92.0% |
| Supported demonstrations | 18 | 19 | 0 | 0 | 23 | 0 | 19/19 = 100% | 19/19 = 100% |
| Known limitations | 7 | 4 | 2 | 0 | 9 | 2 | 4/4 = 100% | 4/6 = 66.7% |

The initial corpus had TP 22 / FN 3 / FP 6 / TN 26. Local imports fixed one miss;
module rebinding removed a misleading resolved edge without changing selections.
The current refinement removes all six recorded false positives while preserving
TP 23, FN 2 and both uncertain selections. `module_overselection`, `module_rebinding`
and `shadowed_names` become supported demonstrations. Conditional definitions and
inherited dispatch remain limitation cases because their retained evidence is
conservative, not newly resolved calls. This is agreement with these fixtures,
not general language support or a safe test-skipping guarantee.

- **TP:** labeled affected and selected.
- **FN:** labeled affected and missed.
- **FP:** labeled unaffected and selected.
- **TN:** labeled unaffected and unselected.
- **Precision:** TP / (TP + FP), considering only labeled recommendations.
- **Recall:** TP / (TP + FN), considering only labeled affected tests.

Aggregate ratios use summed counts, not an average of per-case ratios. Each ratio
stores its numerator, denominator and value. A zero denominator produces JSON
`null` and readable “not applicable.” All difficult cases remain in overall totals.
There are 57 labeled case/test pairs and two unclassified pairs; both unclassified
tests are currently recommended. Their selections are neither TP nor FP.

`invalid_revisions` withholds a dependency label because both source versions are
unparseable. `mixed_revisions` withholds one because it is a provenance example with
changing dependency topology and equal literal outputs; a path assembled from two
revisions is not by itself a runtime relevance label. Their unchanged independent
controls remain labeled unaffected. These choices are authored upfront, not a way
to move observed false positives or misses out of the denominator.

### Case inventory

All cases are in `corpus/cases/<id>.json`. “No discrepancy” describes selection
against these labels, not complete language support.

| ID | Category | Behavior / observed discrepancy |
| --- | --- | --- |
| `direct_call` | supported | Direct call, absolute import, independent control |
| `transitive_calls` | supported | Test → wrapper → changed function |
| `import_aliases` | supported | Module and function aliases |
| `relative_src` | supported | Relative alias inside a `src/` package |
| `package_initialization` | supported | Package initialization value reached by fallback |
| `module_constant` | supported | Changed global value reached by fallback |
| `module_overselection` | supported | Former sibling-function FP removed |
| `deleted_function` | supported | Before-only call retained; removed test excluded |
| `renamed_module` | supported | Removal plus addition; old importer remains affected |
| `cycles` | supported | Finite recursive cycle; traversal terminates |
| `nested_functions` | supported | Nested call; enclosing fingerprint also changes |
| `shadowed_names` | supported | Both shadowed-call FPs removed; graph suppression preserved |
| `changed_test` | supported | Modified/new tests have singleton paths |
| `empty_comments_movement` | supported | Empty/comment-only and moved code cause no semantic changes |
| `valid_to_invalid` | supported | Broken syntax retains old dependency evidence |
| `invalid_to_valid` | supported | Repaired syntax creates after-only evidence |
| `invalid_revisions` | known_limitation | 1 unclassified selection; unavailable function semantics |
| `reexports` | known_limitation | No selection discrepancy; fallback rescues unresolved alias |
| `local_import` | supported | Previous FN fixed: direct local import resolves `test_read → read → price` |
| `module_rebinding` | supported | Stale call remains suppressed; unrelated fallback selection removed |
| `conditional_definitions` | known_limitation | No selection discrepancy; affected conditional name still uses fallback |
| `pytest_fixtures` | known_limitation | 1 FN: injected fixture has no test-to-fixture edge |
| `inherited_dispatch` | known_limitation | No selection discrepancy; bounded inherited-member references remain conservative |
| `runtime_import` | known_limitation | 1 FN: string import and `getattr` hide a call target |
| `mixed_revisions` | known_limitation | 1 unclassified selection with mixed path provenance |

### Fixed selections and remaining mistakes

In `module_overselection`, only `core.price` changes. The unchanged constant-return
`core.healthy` no longer selects `test_health` through the aggregate module. The
module/class AST change remains visible; graph edges and their revision evidence
are preserved. Filtering changes propagation, not the graph's factual inventory.

In `module_rebinding`, `worker` imports `price` then replaces it with a lambda.
The earlier binding scan removed the false `worker.read → core.price` resolved call,
but still selected `test_read` by fallback (priority 23). The current filter removes
that unrelated recommendation entirely. The affected direct `test_price` remains
resolved with priority 81. Neither the graph nor the scoring formula changed in
this refinement. The historical baseline records both the FP and its explanation.

`shadowed_names` loses two fallback FPs; `conditional_definitions` and
`inherited_dispatch` each lose one. Their affected selections remain. Possible
method/name references justify conservative module paths only: no new precise
dispatch edge is invented. Every resulting recommendation passes typed path and
before/head evidence validation. Tests reject stale baseline annotations rather
than silently accepting improvements.

Two misses remain. In `pytest_fixtures`, `test_quote` receives `quoted` through
pytest injection; the test has no explicit call/import to that fixture. In
`runtime_import`, a string import and reflective call hide the dependency.
Their affected labels and exact FN IDs remain unchanged. Fixture injection and
runtime-import analysis are outside this change. The earlier local-import miss
stays fixed with `test_read → worker.read → price` resolved in both revisions.

Initialization changes still propagate conservatively. The separate real-source
pilot previously recorded four default-digest initialization FPs. Bounded
constructor/factory argument and early-exit tracking now removes those four. Unmodeled special
methods and exhausted reference budgets retain broad fallback with a warning.
See [the implementation boundary](ARCHITECTURE.md#scoped-aggregate-fallback) and
[real-source results](REAL_EVALUATION.md). All limitations remain in reported
totals without skips, xfails or relabeling controls to make results look better.

## Evaluation report 1.0

This is a separate schema from the unchanged analyzer/API report **2.0**.

| Field | Meaning |
| --- | --- |
| `schema_version`, `analysis_schema_version` | `"1.0"` evaluator / `"2.0"` analyzer |
| `interpretation` | Explicit authored-label qualification |
| `corpus_sha256` | SHA-256 of sorted validated cases serialized as canonical JSON; includes snapshots, labels and baseline annotations, not analyzer code |
| `case_count`, `group_case_counts` | Number of cases overall and per category |
| `totals`, `groups` | `counts` (`tp`, `fn`, `fp`, `tn`, `unclassified_recommendations`), `precision`, `recall` |
| `cases[].case` | Full validated case metadata, labels and snapshots for inspection |
| `cases[].results` | Five sorted ID lists and that case's metrics |
| `cases[].analysis` | Analyzer report, retaining nodes, typed edges, revision evidence, sources, changes, warnings and recommendations; only `stats.elapsed_ms` removed |
| `cases[].regressions`, `regressions` | Per-case and flattened exact-baseline differences, including unexpected improvements |

The file sorts JSON object keys and cases by ID. It contains no timestamps, timings
or host paths supplied by the evaluator. Full snapshots and changed source remain
in it. The CLI's displayed output filename is outside stable JSON. Repeated runs
and reordered case/snapshot inputs are checked for identical stable JSON. Reproduce
with the same corpus, analyzer code, Python and pinned dependencies; the corpus
digest alone does not identify the analyzer version.

Every recommendation is checked for a unique valid head test, correct start/end,
distance, matching typed edge IDs and caller-to-dependency direction, cycle-free
path and correct resolved/fallback reason. Before/after edge evidence is compared
with each snapshot index; locations are bounded by that revision's source. Revision
labels must agree with edge evidence and the intersection of all path hops. Node
and edge union, stable edge IDs, removed symbols and ordering are checked too.

Re-indexing is a structural consistency check, not an independent semantic oracle:
an index bug could occur in both runs. Authored labels, independent discovery,
negative tests that corrupt reports, targeted evidence examples and existing engine
regressions provide separate checks. Existing scoring and stable-ID regressions
remain in the full suite. The local-import extension changes resolution and adds
function-to-module import edges, using the existing schema, IDs and evidence types.
The analyzer report and evaluation schema versions remain 2.0 and 1.0.
The subsequent module-rebinding correction suppresses unjustified call edges.
The selection refinement filters propagation while preserving all graph edges,
source/label data and report contracts; only discrepancy metadata is updated.

## Add a case or review a changed baseline

1. Create `corpus/cases/<unique_id>.json` with both complete snapshots and an
   independent control. Keep it small enough to understand by inspection.
2. **Before evaluating**, read the source and write affected/unaffected rationales.
   Explicitly classify every discovered head test; use unclassified only with a
   substantive reason. Never derive labels by copying recommendations.
3. Explain the language behavior with feature tags. Begin with empty discrepancy
   maps and, if needed, a known-limitation explanation. Run the single case.
4. Inspect any difference and its typed evidence. If it is an analyzer limitation,
   preserve the authored labels, record the exact FP/FN IDs with explanations, and
   use `known_limitation`. Do not change labels merely to make the test green.
5. Run the focused tests, `make evaluate`, then `make check`. Add an evidence-specific
   assertion if the example relies on a particular resolution/provenance limitation.
6. Update this guide and `VALIDATION.md` with actual totals. A change to known
   discrepancies in either direction must fail until deliberately reviewed. If a
   fix removes a limitation, update its baseline/category/explanation and related
   evidence assertion in the same review; keep affected/unaffected labels intact
   unless the fixture itself or its independently justified interpretation changes.

Statement coverage measures executed lines, not correctness. Passing regression
tests does not establish general analyzer accuracy. Small authored fixtures are not
representative of every repository. Dependency relevance differs from whether a
test actually fails; even the assertion examples here have not been executed.

## Interview walkthrough and next milestone

1. **Strength:** open `transitive_calls.json`. Predict `test_total → total → price`
   and explain why caller-to-dependency edges are traversed in reverse. Evaluate
   this case and inspect the resolved path and the unselected control.
2. **False positive and fix:** open `module_overselection.json` and the archived
   baseline. `healthy` never calls `price`; the old conservative module hop selected
   its test. The current body-change filter removes that FP while retaining the
   direct affected test and all graph evidence.
3. **Miss and fix:** open `local_import.json`. Its unchanged affected label moved
   from FN to TP after adding scoped aliases. Contrast it with the still-missed
   `pytest_fixtures` case; passing a baseline is not complete dependency coverage.
4. **Evidence, then selection:** `module_rebinding` first lost a false resolved
   edge but retained an FP through fallback. This follow-up removes the unrelated
   selection; the unaffected label and source stay fixed. The affected direct
   caller remains resolved with priority 81.

Next: independently review real-source labels and reserve fresh changes for an
unseen evaluation set. Keep controls, uncertain tests and misses in the reports;
reducing recommendation counts alone does not establish correctness.

## Separate real-repository pilot

`corpus/real` contains six pinned changes across MarkupSafe, ItsDangerous and
Schedule. Run `make evaluate-real` offline. It reuses this evaluator and evidence
checks, adding complete-tree/source/license integrity and label review status.
The two datasets stay separate. All original snapshots and labels are preserved;
the selection refinement deliberately updates discrepancy baselines and archives
the previous annotations in `corpus/selection-baseline-v1.json`.

The real labels were drafted before initial analysis: 45 affected, 123 unaffected,
33 uncertain definitions. All remain agent drafted, with no independent review or
upstream execution. Initial selection was 171/201, with 102 FPs. Current selection
is 56/201: TP 45, FP 0, FN 0, TN 123, plus 11 selected uncertain tests. Precision and
recall are both 45/45, conditional on the drafts. All six cases retain limitation
status. Class/module fixes removed 98 FPs and bounded argument tracking removed the
remaining four, without modifying the source or labels. These cases informed the fix and are regression data,
not an unseen benchmark. Edited tests also make selection easier.

The [protocol](../corpus/real/README.md) explains sampling, exclusions, complete
supported Python scope, limits, provenance trust, label semantics, uncertainties
and deliberate baseline updates. The [review pack](../corpus/real/REVIEW.md)
contains every label/rationale with pinned source links and full Python diffs.
[REAL_EVALUATION.md](REAL_EVALUATION.md) records per-case/aggregate measurements,
selected IDs, concrete false positives and reproducible report hashes.
