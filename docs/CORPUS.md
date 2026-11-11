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
.venv/bin/pytest tests/test_module_rebinding.py --no-cov
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

Observed November 11, 2026, after bounded module-level rebinding,
starting from merged local-import commit `68ae852`. All 25 checked-in cases match their
explicitly recorded discrepancies. The original baseline is preserved in
[VALIDATION.md](VALIDATION.md#bounded-analyzer-correctness-corpus--november-10-2026).
Counts are **case/test pairs**: reused test IDs in different cases are distinct
observations, and repeated controls are not independent real-world samples.

| Population | Cases | TP | FN | FP | TN | Selected unclassified | Precision | Recall |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| Overall | 25 | 23 | 2 | 6 | 26 | 2 | 23/29 = 79.3% | 23/25 = 92.0% |
| Supported demonstrations | 15 | 16 | 0 | 0 | 16 | 0 | 16/16 = 100% | 16/16 = 100% |
| Known limitations | 10 | 7 | 2 | 6 | 10 | 2 | 7/13 = 53.8% | 7/9 = 77.8% |

The original corpus run had TP 22 and FN 3, precision 22/28 and recall 22/25.
`local_import` now selects its one affected test through a resolved call path,
reducing FN by one and increasing TP by one. All snapshots and authored
affected/unaffected/unclassified labels are identical to the original corpus;
only that case's category, feature tags, description and known-miss annotation
changed. At that milestone the other 24 per-case analysis reports and classifications
were identical. The subsequent module-rebinding correction changes evidence and
priority in one case, with **no changes to selected test IDs/order, classifications
or aggregate metrics**. Its other 24 complete case reports remain identical to the
pre-rebinding evaluation.

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
| `module_overselection` | known_limitation | 1 FP: unchanged sibling function in an imported module |
| `deleted_function` | supported | Before-only call retained; removed test excluded |
| `renamed_module` | supported | Removal plus addition; old importer remains affected |
| `cycles` | supported | Finite recursive cycle; traversal terminates |
| `nested_functions` | supported | Nested call; enclosing fingerprint also changes |
| `shadowed_names` | known_limitation | 2 FPs via fallback despite precise shadowing suppression |
| `changed_test` | supported | Modified/new tests have singleton paths |
| `empty_comments_movement` | supported | Empty/comment-only and moved code cause no semantic changes |
| `valid_to_invalid` | supported | Broken syntax retains old dependency evidence |
| `invalid_to_valid` | supported | Repaired syntax creates after-only evidence |
| `invalid_revisions` | known_limitation | 1 unclassified selection; unavailable function semantics |
| `reexports` | known_limitation | No selection discrepancy; fallback rescues unresolved alias |
| `local_import` | supported | Previous FN fixed: direct local import resolves `test_read → read → price` |
| `module_rebinding` | known_limitation | 1 FP remains via module/import fallback; stale resolved-call edge removed |
| `conditional_definitions` | known_limitation | 1 FP: unindexed conditional definition and broad fallback |
| `pytest_fixtures` | known_limitation | 1 FN: injected fixture has no test-to-fixture edge |
| `inherited_dispatch` | known_limitation | 1 FP: fallback cannot separate inherited methods |
| `runtime_import` | known_limitation | 1 FN: string import and `getattr` hide a call target |
| `mixed_revisions` | known_limitation | 1 unclassified selection with mixed path provenance |

### Concrete mistakes

In `module_overselection`, only `core.price` changes. `test_health` calls the
unchanged, constant-return `core.healthy`. It is labeled unaffected, but the
recommendation follows `test_health → core.healthy → core.<module>`. The final hop
is a conservative module edge. A module fingerprint includes changes to all its
definitions, so the import/module approximation overselects this sibling test.

In `pytest_fixtures`, `test_quote` receives `quoted` through pytest injection. The
fixture in `conftest.py` calls changed `core.price`, but no Python call or import in
the test links it to that fixture. The unchanged affected label remains a recorded
FN. `runtime_import` remains another FN because its string-based import and
reflective call do not create a static edge to the changed target.

The former `local_import` miss is now fixed: `worker.read` contains
`from core import price` and returns `price()`. Its test has the resolved path
`test_read → worker.read → core.price` with evidence in both revisions. The
independent control stays unselected. Before the old miss annotation was removed,
evaluation deliberately exited 1 because expected FN `[test_read]` became `[]`.
The regression suite still rejects reinstating that stale annotation and uses
the remaining fixture-injection miss to check the opposite drift direction.

Local-import support is bounded to direct statements in function/async-function
bodies, including methods and separately indexed nested functions. Aliases are
usable only after the import's end position. Rebinding, duplicate/conditional
imports and conflicting parameters/captures suppress precise resolution rather
than falling through to globals. Closure propagation and calls through local
aliases in lambda/comprehension scopes remain unsupported. A conservative import
edge belongs to the importing function, so module-constant changes do not
automatically select unrelated sibling functions. See the
[exact resolution boundary](ARCHITECTURE.md#bounded-function-local-imports).

In `module_rebinding`, `worker` imports `price`, then overwrites it with a lambda
returning 42. The wrapper calls that replacement. Before the correction, the
stale import-alias table produced a misleading **resolved call** to `core.price`.
The module-scope binding scan now removes that edge in both revisions and reports
the ambiguity. It retains the direct import dependency, so the unaffected wrapper
test is still a false positive, now explicitly explained as conservative fallback.

| Measurement | Before module-rebinding fix | After |
| --- | --- | --- |
| Selected IDs | `tests/test_price.py::test_price`, `tests/test_worker.py::test_read` | Same IDs and order |
| Classification | TP 1, FN 0, FP 1, TN 1 | Unchanged |
| Wrapper test path | `test_read → worker.read → core.price` | `test_read → tests/test_worker.<module> → worker.<module> → core.<module>` |
| Wrapper explanation | Resolved call path | Conservative module/import dependency |
| Wrapper priority | 72 | 23 |
| Directly affected test | Resolved path to `core.price`, priority 82 | Same resolved path, priority 81 |
| Path revision | Both | Both |

One call edge is removed: `worker.py::read → core.py::price`. No edge is added and
every retained edge, ID and per-revision evidence item is unchanged. The directly
affected test's priority decreases by one because the changed target has one fewer
incoming dependent. The wrapper uses a longer fallback path with the existing
lower fallback starting score. Neither change alters the ranking formula or measures
a failure probability.

The case stays `known_limitation`, and its exact FP ID remains recorded. Only the
FP explanation, limitation text and feature tag were updated to describe fallback
instead of stale resolved evidence. Existing snapshots, label maps and rationales
are unchanged. The evidence-specific regression deliberately changed its expected
reason after first failing on the corrected result; selection baselines were not
weakened. All 31 recommendations still pass structural evidence validation.

The correction requires a single direct module import with no competing binding.
It handles assignments/deletions, definitions and compound-statement bindings while
excluding separate function/class bodies and comprehension iteration targets.
Bare annotations do not reassign a module name. See the
[exact boundary](ARCHITECTURE.md#bounded-module-level-rebinding), including unsupported
runtime/global/object mutations and deliberately conservative repeated imports.

Fixture injection, runtime imports, conditional definitions, re-export aliases,
instance/inherited dispatch and conservative module over-selection remain limitations
in the aggregate results without skips or xfails.

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
The subsequent module-rebinding correction only suppresses unjustified call edges;
it preserves the existing import edges and report contracts.

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
2. **False positive:** open `module_overselection.json`. Show that `healthy` never
   calls `price`, then inspect its conservative module hop. Explain why the full
   result includes this mistake rather than silently dropping it from metrics.
3. **Measured fix:** open `local_import.json`. Show how the unchanged affected label
   moved from FN to TP after adding scope-aware local aliases. Then contrast it
   with the still-missed `pytest_fixtures` case; passing the baseline does not mean
   every dependency is resolved.

4. **Evidence correction:** open `module_rebinding.json`. Explain why replacing an
   imported callable invalidates the old resolved edge. Compare the corrected
   fallback path and priority against the prior resolved path, while keeping the
   test labeled unaffected and retaining the FP. This improves evidence without
   claiming an improvement in selection accuracy.

A next step is independently reviewed evaluation of conservative module fallback
before attempting to narrow it. Keep labeled controls and any misses in the
measurements; reducing recommendations alone does not establish better correctness.
