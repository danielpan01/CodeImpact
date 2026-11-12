# Real-repository evaluation v1 — observed results

Observed locally on 2026-11-12, after bounded constructor/factory argument tracking.
Six source changes across three public repositories; **agent-drafted labels,
zero independently reviewed cases**. Sources and labels are unchanged. Upstream
source/tests were never executed, imported, installed or checked out.

The initial evaluation did not tune the analyzer. The follow-up fix used these
cases to diagnose mistakes, so these are now **development/regression inputs,
not an unseen benchmark**. A fresh evaluation set and independent label review
are needed before making broader claims.

[Review pack](../corpus/real/REVIEW.md) · [Protocol and provenance](../corpus/real/README.md) · [Attribution](../corpus/real/ATTRIBUTION.md) · [Archived initial baseline](../corpus/selection-baseline-v1.json)

## Current results

CodeImpact selects **56/201 definition IDs (27.9%)**, down from 171 initially and
60 after class/module selection refinement. Against the frozen draft labels:
**TP 45, FP 0, FN 0, TN 123**. Precision and recall are both **45/45 (100%)** for
these classified drafts. Initial precision was 45/147 (30.6%); the intermediate
refinement yielded 45/49 (91.8%). These are development/regression measurements,
not production accuracy or evidence that omitted tests are safe.

**33 tests remain unclassified: 11 selected and 22 unselected.** They stay in all
inventories and selection totals but outside labeled metric denominators. The
45 classified selections plus 11 uncertain selections equal 56. Definition counts
do not expand parametrization/inherited contexts; repeated IDs across cases are
correlated case-test pairs, not independent observations.

| Case | Tests | Selected | TP | FP | FN | TN | Unclassified tests | Unclassified selected |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| itsdangerous_fips | 37 | 29 | 29 | 0 | 0 | 8 | 0 | 0 |
| itsdangerous_future | 44 | 18 | 7 | 0 | 0 | 19 | 18 | 11 |
| markupsafe_format_map | 23 | 1 | 1 | 0 | 0 | 14 | 8 | 0 |
| markupsafe_striptags | 23 | 1 | 1 | 0 | 0 | 15 | 7 | 0 |
| schedule_repr | 38 | 3 | 3 | 0 | 0 | 35 | 0 | 0 |
| schedule_tags | 36 | 4 | 4 | 0 | 0 | 32 | 0 | 0 |
| **Overall** | 201 | 56 | 45 | 0 | 0 | 123 | 33 | 11 |

| Repository | Selected / tests | TP | FP | FN | TN | Unclassified tests / selected |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| dbader/schedule | 7 / 74 | 7 | 0 | 0 | 67 | 0 / 0 |
| pallets/itsdangerous | 47 / 81 | 36 | 0 | 0 | 27 | 18 / 11 |
| pallets/markupsafe | 2 / 46 | 2 | 0 | 0 | 29 | 15 / 0 |

## What changed and what the explanations establish

Body edits remain visible as full AST changes, but an unrelated method edit no
longer makes every constructor user affected. Aggregate module fallback requires
bounded possible references to changed declarations. Supported class-default changes now receive a bounded argument query; other
initialization effects retain fallback. These checks do not add
resolved calls or change scoring, IDs, report schema or dashboard design.

| Case | Resolved call path | Conservative module/import | Test itself changed |
| --- | ---: | ---: | ---: |
| itsdangerous_fips | 4 | 24 | 1 |
| itsdangerous_future | 0 | 17 | 1 |
| markupsafe_format_map | 0 | 0 | 1 |
| markupsafe_striptags | 0 | 0 | 1 |
| schedule_repr | 0 | 2 | 1 |
| schedule_tags | 2 | 0 | 2 |
| **Overall** | 6 | 43 | 7 |

Every recommendation passes typed-edge direction/identity, changed endpoint,
source-location and before/head evidence checks. All graph nodes/edges, changed
symbols, removed symbols and source evidence are identical to the initial run;
selection/impact propagation changed. These checks establish report consistency,
not runtime execution. Seven selections are changed tests themselves and do not
show discovery of unchanged dependent tests. Most remaining recommendations still
use conservative fallback; “resolved” is never a correctness guarantee.

Concrete fixes:

- **MarkupSafe `striptags`:** `test_format_map` and the other 14 unrelated labeled
  tests are no longer selected merely for constructing `Markup`. The edited
  `test_striptags` remains. The seven uncertain native/C-variant tests remain
  unclassified and are unselected, without a safety claim.
- **MarkupSafe `format_map`:** `test_unescape` and the other 13 unrelated labeled
  tests are excluded; the edited `test_format_map` remains. Eight uncertain
  variants stay in the denominator inventory, unselected.
- **Schedule representation:** selection falls from 38 to 3; all 35 unaffected
  controls are excluded. `test_to_string` uses the separate `__str__`, while
  `test_time_units` does not depend on every method of the constructed class.
- **Schedule tagged lookup:** selection falls from 36 to 4, removing 32 FPs.
  The bounded receiver checks distinguish the stored `Job.next_run` field from
  the changed `Scheduler.next_run` property. Getter normalization avoids treating
  a `@property` to `property(getter)` rewrite as wholesale initialization impact.
- **ItsDangerous timestamps:** the two unrelated ordinary-serializer selections
  are removed, including `test_digests`. All 18 inherited-definition uncertainties
  remain explicitly uncertain, with 11 selected.

### Four constructor/factory false positives fixed

All four previous `itsdangerous_fips` false positives are now excluded, with their
source and unaffected labels unchanged:

- `tests/test_itsdangerous/test_signer.py::TestSigner.test_digest_method`: the local
  partial factory forwards explicit MD5 through `Signer` into `HMACAlgorithm`, so
  neither changed default is read.
- `tests/test_itsdangerous/test_serializer.py::TestSerializer.test_fallback_signers`:
  explicit signer options and fallback dictionaries are tracked through the source
  serializer factory, stored fields, `make_signer` and `iter_unsigners`. All visible
  variants supply their digest. The newly added passive helper import does not
  independently select every test in the already-importing module.
- `tests/test_itsdangerous/test_signer.py::TestSigner.test_invalid_separator`:
  literal argument/byte conversion and membership in the fixed alphabet suffix
  establish a source-level early `raise` before the default lookup.
- `tests/test_itsdangerous/test_signer.py::test_abstract_algorithm`: the constructed
  abstract algorithm and its method do not reference the changed defaults.

These are bounded AST dependency deductions, not observed upstream test execution.
No repository names, test IDs or case-specific suppression lists occur in the
implementation. Unknown options, factories, iteration counts and protocols retain
recommendations. Direct literal fixture values and simple local fixture factories
are supported; general injection, setup effects, arbitrary dispatch/descriptors,
reflection, runtime imports and complex mutation remain incomplete. The
[architecture boundary](ARCHITECTURE.md#bounded-constructor-and-factory-arguments)
details eligibility, API shapes and resource limits.

No FN is observed among the 45 affected drafts. The 33 uncertain definitions,
C behavior, edited tests, unsupported dispatch/discovery and purposive sample
prevent extrapolation. The authored corpus still records fixture-injection and
runtime-import misses. Full tests remain the merge gate; no upstream assertion
failure, FIPS runtime, performance, deployed CI or production accuracy is claimed.

## Exact sources and supported coverage

Each linked change is compared with the exact first parent below. All supported
Python files are preserved as source strings, with complete tree inventories,
Git blob hashes, SHA-256 hashes and license bytes in `corpus/real/provenance/`.

| Case / change | Before SHA | After SHA | Python files base/head | Python bytes base/head |
| --- | --- | --- | ---: | ---: |
| [itsdangerous_fips](https://github.com/pallets/itsdangerous/commit/2f69e841d2a979c616a55b226e444694f5d9c962) | `93ae366874bbd4f69d90495c45b2cd336387496c` | `2f69e841d2a979c616a55b226e444694f5d9c962` | 15/15 | 59896/60224 |
| [itsdangerous_future](https://github.com/pallets/itsdangerous/commit/c30678d19e37011890e2374cca04f7789e101793) | `1a9b8d1f9968eb248bda69f39d373a6330b692ba` | `c30678d19e37011890e2374cca04f7789e101793` | 18/18 | 56299/56763 |
| [markupsafe_format_map](https://github.com/pallets/markupsafe/commit/391aa07d3c68d4d0888b31fdea62516df9e19cb8) | `60e7eb97e65947a83fa290010f3dde71be8fed84` | `391aa07d3c68d4d0888b31fdea62516df9e19cb8` | 15/15 | 25065/25410 |
| [markupsafe_striptags](https://github.com/pallets/markupsafe/commit/60a6512315d0ce05e6788808f80be526f2084b3f) | `73e6a4886564a554c4a19983d29c97f9fc95457d` | `60a6512315d0ce05e6788808f80be526f2084b3f` | 15/15 | 26340/26371 |
| [schedule_repr](https://github.com/dbader/schedule/commit/3863effe15ec8239ba88c65a4231a67e43b116df) | `a3ecd3548aff70bef15a61baee0d2d7f22f57992` | `3863effe15ec8239ba88c65a4231a67e43b116df` | 4/4 | 77399/77705 |
| [schedule_tags](https://github.com/dbader/schedule/commit/c883af0229143285cf38e1c7733aaf36656c8744) | `64f83981b2a55136ea3737b8c35cf3da7b270055` | `c883af0229143285cf38e1c7733aaf36656c8744` | 4/4 | 72803/73776 |

All 12 trees were untruncated and within existing source limits. No captured tree
contained an excluded Python path, symlink or submodule. Non-Python inventory is
retained but non-Python contents (apart from license text) are outside this dataset.
Pallets sources use BSD-3-Clause; Schedule uses MIT. Original license/copyright
notices are retained. See the protocol for the offline provenance trust boundary.

## Reproduce and interpret the baseline

```sh
make evaluate-real
make evaluate
make check
cd web && npm run test:e2e
```

`reports/real-evaluation.json` contains full snapshots, labels, selected IDs,
TP/FP/FN/TN lists, uncertainty inventories and typed paths. The initial run and the
refinement both produced nonzero baseline-drift results before annotations were
deliberately updated. Sources, frozen labels, provenance, draft review statuses
and the source-only review pack stayed unchanged. Passing now records zero FP/FN against the classified drafts, while preserving
all uncertainties and the stated semantic limitations.

The [archived baseline](../corpus/selection-baseline-v1.json) retains the original
selected IDs, counts and discrepancy explanations for both datasets, plus
source/label hashes. The initial real selection was 171 (48 resolved, 116 fallback,
7 changed tests); the intermediate selection was 60 (6 resolved, 47 fallback,
7 changed). The current selection is 56 (6 resolved, 43 fallback, 7 changed).
The authored corpus moves from TP 23 / FP 6 / FN 2 / TN 26 to TP 23 / FP 0 / FN 2 /
TN 32; its two uncertain selections and all source/label data are unchanged.

Verification: **481 Python tests**, Ruff lint/format, strict mypy and frontend
production build pass in `make check`; **267 focused regressions** and **32
desktop/mobile Playwright tests** pass. Both evaluations exit 0. Repeated reports
are byte-identical, and reversing snapshot file order produces identical analysis.
Only embedded `stats.elapsed_ms` is excluded, as documented by the evaluator.

- Dataset SHA-256: `bcc3c986a75f83baacfd7348e4ed2d7394cfb03a299b147138010a0ea0c69bec`.
- Real corpus SHA-256: `cc295683bb432a32bc554cfc2dd3b31dd1ac6dbc83ea4e1e2eb417c5060c67f3`.
- Report SHA-256: `258ab743f6af677e714d238e9e1f3fd099f090a7e65ec3bd0c61b1e144992cae`.

See [VALIDATION.md](VALIDATION.md) for the verification record and local artifacts.

## Selected test IDs by case

### itsdangerous_fips (29 selected)

| Selected definition ID | Classification | Explanation |
| --- | --- | --- |
| `tests/test_itsdangerous/test_serializer.py::TestSerializer.test_iter_unsigners` | TP | Test itself changed |
| `tests/test_itsdangerous/test_signer.py::TestSigner.test_secret_keys` | TP | Resolved call path |
| `tests/test_itsdangerous/test_timed.py::TestTimestampSigner.test_malformed_timestamp` | TP | Resolved call path |
| `tests/test_itsdangerous/test_timed.py::TestTimestampSigner.test_timestamp_missing` | TP | Resolved call path |
| `tests/test_itsdangerous/test_signer.py::TestSigner.test_algorithm` | TP | Resolved call path |
| `tests/test_itsdangerous/test_serializer.py::TestSerializer.test_alt_salt` | TP | Conservative module/import dependency |
| `tests/test_itsdangerous/test_serializer.py::TestSerializer.test_bad_payload_exception` | TP | Conservative module/import dependency |
| `tests/test_itsdangerous/test_serializer.py::TestSerializer.test_bad_signature_exception` | TP | Conservative module/import dependency |
| `tests/test_itsdangerous/test_serializer.py::TestSerializer.test_changed_value` | TP | Conservative module/import dependency |
| `tests/test_itsdangerous/test_serializer.py::TestSerializer.test_file` | TP | Conservative module/import dependency |
| `tests/test_itsdangerous/test_serializer.py::TestSerializer.test_loads_unsafe` | TP | Conservative module/import dependency |
| `tests/test_itsdangerous/test_serializer.py::TestSerializer.test_serializer` | TP | Conservative module/import dependency |
| `tests/test_itsdangerous/test_serializer.py::TestSerializer.test_serializer_kwargs` | TP | Conservative module/import dependency |
| `tests/test_itsdangerous/test_serializer.py::TestSerializer.test_signer_cls` | TP | Conservative module/import dependency |
| `tests/test_itsdangerous/test_serializer.py::TestSerializer.test_signer_kwargs` | TP | Conservative module/import dependency |
| `tests/test_itsdangerous/test_serializer.py::test_digests` | TP | Conservative module/import dependency |
| `tests/test_itsdangerous/test_signer.py::TestSigner.test_broken_signature` | TP | Conservative module/import dependency |
| `tests/test_itsdangerous/test_signer.py::TestSigner.test_changed_value` | TP | Conservative module/import dependency |
| `tests/test_itsdangerous/test_signer.py::TestSigner.test_invalid_key_derivation` | TP | Conservative module/import dependency |
| `tests/test_itsdangerous/test_signer.py::TestSigner.test_key_derivation` | TP | Conservative module/import dependency |
| `tests/test_itsdangerous/test_signer.py::TestSigner.test_no_separator` | TP | Conservative module/import dependency |
| `tests/test_itsdangerous/test_signer.py::TestSigner.test_signer` | TP | Conservative module/import dependency |
| `tests/test_itsdangerous/test_timed.py::TestTimedSerializer.test_max_age` | TP | Conservative module/import dependency |
| `tests/test_itsdangerous/test_timed.py::TestTimedSerializer.test_return_payload` | TP | Conservative module/import dependency |
| `tests/test_itsdangerous/test_timed.py::TestTimestampSigner.test_future_age` | TP | Conservative module/import dependency |
| `tests/test_itsdangerous/test_timed.py::TestTimestampSigner.test_malformed_future_timestamp` | TP | Conservative module/import dependency |
| `tests/test_itsdangerous/test_timed.py::TestTimestampSigner.test_max_age` | TP | Conservative module/import dependency |
| `tests/test_itsdangerous/test_timed.py::TestTimestampSigner.test_return_timestamp` | TP | Conservative module/import dependency |
| `tests/test_itsdangerous/test_timed.py::TestTimestampSigner.test_sig_error_date_signed` | TP | Conservative module/import dependency |

### itsdangerous_future (18 selected)

| Selected definition ID | Classification | Explanation |
| --- | --- | --- |
| `tests/test_itsdangerous/test_timed.py::TestTimestampSigner.test_future_age` | TP | Test itself changed |
| `tests/test_itsdangerous/test_timed.py::TestTimedSerializer.test_max_age` | TP | Conservative module/import dependency |
| `tests/test_itsdangerous/test_timed.py::TestTimedSerializer.test_return_payload` | TP | Conservative module/import dependency |
| `tests/test_itsdangerous/test_timed.py::TestTimestampSigner.test_malformed_timestamp` | TP | Conservative module/import dependency |
| `tests/test_itsdangerous/test_timed.py::TestTimestampSigner.test_max_age` | TP | Conservative module/import dependency |
| `tests/test_itsdangerous/test_timed.py::TestTimestampSigner.test_return_timestamp` | TP | Conservative module/import dependency |
| `tests/test_itsdangerous/test_timed.py::TestTimestampSigner.test_timestamp_missing` | TP | Conservative module/import dependency |
| `tests/test_itsdangerous/test_serializer.py::TestSerializer.test_alt_salt` | Unclassified | Conservative module/import dependency |
| `tests/test_itsdangerous/test_serializer.py::TestSerializer.test_bad_payload_exception` | Unclassified | Conservative module/import dependency |
| `tests/test_itsdangerous/test_serializer.py::TestSerializer.test_bad_signature_exception` | Unclassified | Conservative module/import dependency |
| `tests/test_itsdangerous/test_serializer.py::TestSerializer.test_changed_value` | Unclassified | Conservative module/import dependency |
| `tests/test_itsdangerous/test_serializer.py::TestSerializer.test_fallback_signers` | Unclassified | Conservative module/import dependency |
| `tests/test_itsdangerous/test_serializer.py::TestSerializer.test_file` | Unclassified | Conservative module/import dependency |
| `tests/test_itsdangerous/test_serializer.py::TestSerializer.test_loads_unsafe` | Unclassified | Conservative module/import dependency |
| `tests/test_itsdangerous/test_serializer.py::TestSerializer.test_serializer` | Unclassified | Conservative module/import dependency |
| `tests/test_itsdangerous/test_serializer.py::TestSerializer.test_serializer_kwargs` | Unclassified | Conservative module/import dependency |
| `tests/test_itsdangerous/test_serializer.py::TestSerializer.test_signer_cls` | Unclassified | Conservative module/import dependency |
| `tests/test_itsdangerous/test_serializer.py::TestSerializer.test_signer_kwargs` | Unclassified | Conservative module/import dependency |

### markupsafe_format_map (1 selected)

| Selected definition ID | Classification | Explanation |
| --- | --- | --- |
| `tests/test_markupsafe.py::test_format_map` | TP | Test itself changed |

### markupsafe_striptags (1 selected)

| Selected definition ID | Classification | Explanation |
| --- | --- | --- |
| `tests/test_markupsafe.py::test_escaping` | TP | Test itself changed |

### schedule_repr (3 selected)

| Selected definition ID | Classification | Explanation |
| --- | --- | --- |
| `test_schedule.py::SchedulerTests.test_to_repr` | TP | Test itself changed |
| `test_schedule.py::SchedulerTests.test_repr_functools_partial_job_func` | TP | Conservative module/import dependency |
| `test_schedule.py::SchedulerTests.test_time_range_repr` | TP | Conservative module/import dependency |

### schedule_tags (4 selected)

| Selected definition ID | Classification | Explanation |
| --- | --- | --- |
| `test_schedule.py::SchedulerTests.test_idle_seconds` | TP | Test itself changed |
| `test_schedule.py::SchedulerTests.test_next_run_with_tag` | TP | Test itself changed |
| `test_schedule.py::SchedulerTests.test_next_run_property` | TP | Resolved call path |
| `test_schedule.py::SchedulerTests.test_next_run_time` | TP | Resolved call path |


## Separate fresh evaluation

[Fresh-repository evaluation v2](REAL_EVALUATION_V2.md) now measures six additional
changes on the unchanged post-fix engine. It finds 284 false positives and 44
false negatives against its draft labels. These results are kept separate from
v1; the original six snapshots, labels, provenance and baseline remain unchanged.
They demonstrate why the perfect classified v1 regression score is not a general
accuracy claim. Both datasets still await independent human label review.
