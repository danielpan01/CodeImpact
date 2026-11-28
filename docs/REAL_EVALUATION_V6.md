# Fresh real-repository evaluation v6

V6 measures CodeImpact at merged revision `060547c3375a999eb4bc8d582cff9883f7c39ef5`
on six source changes from XMLtodict, python-dotenv, and tokenize-rt.
All three repositories are new to the measured v1–v5 samples. Those earlier
datasets remain regression gates. The v6 run uses the reference engine's
default analysis, discovery, and scoring.

```sh
make evaluate-real-v6
```

The offline replay writes `reports/real-v6-evaluation.json` with exact test IDs,
typed evidence and revision ranges. It checks the first report and discrepancy
baseline after validating the captured Git trees, blobs, licenses, and draft
labels. Its only excluded report field is analysis elapsed time.
[Source and selection records](../datasets/real-v6/README.md) · [Engine hashes](../datasets/real-v6/analyzer.json) · [Frozen inputs](../datasets/real-v6/frozen-inputs.json) · [First measurement](../datasets/real-v6/first-run.json) · [Discrepancy baseline](../datasets/real-v6/baseline.json)

## First measurement

TP, FP, FN, and TN are agreement with the frozen source-based draft labels.
Uncertain definitions are tracked separately. The six cases have 399 discovered
head definitions and 379 discovered base definitions, with zero outside
discovery on either side. A parametrized definition contributes one ID.
The counts treat each change and definition as a pair. Nearby commits can
include the same test. Independent label review is pending.

| Case | Selected / discovered | TP | FP | FN | TN | Uncertain selected / total |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| XMLtodict allows DOCTYPE without entities | 59 / 102 | 5 | 53 | 0 | 43 | 1 / 1 |
| XMLtodict rejects entity declarations | 58 / 101 | 3 | 54 | 0 | 43 | 1 / 1 |
| python-dotenv disables loading by environment flag | 40 / 75 | 5 | 33 | 0 | 30 | 2 / 7 |
| python-dotenv detects interactive shells | 31 / 70 | 10 | 21 | 0 | 36 | 0 / 3 |
| tokenize-rt handles template-string middle tokens | 26 / 26 | 1 | 25 | 0 | 0 | 0 / 0 |
| tokenize-rt preserves named Unicode escapes | 25 / 25 | 3 | 22 | 0 | 0 | 0 / 0 |
| **Overall** | **239 / 399** | **27** | **208** | **0** | **152** | **4 / 12** |

| Case | Resolved call | Conservative module/import | Changed test |
| --- | ---: | ---: | ---: |
| XMLtodict allows DOCTYPE without entities | 55 | 0 | 4 |
| XMLtodict rejects entity declarations | 55 | 0 | 3 |
| python-dotenv disables loading by environment flag | 0 | 35 | 5 |
| python-dotenv detects interactive shells | 0 | 21 | 10 |
| tokenize-rt handles template-string middle tokens | 18 | 7 | 1 |
| tokenize-rt preserves named Unicode escapes | 17 | 6 | 2 |
| **Overall** | **145** | **69** | **25** |

Precision is **27/235 (11.49%)**, and recall is **27/27 (100%)** within this
frozen sample. Twenty-five of the 27 draft true positives are changed or
added test definitions. The two unchanged ones have resolved evidence.
The four selected uncertain definitions include the two XML streaming memory
cases and two python-dotenv cases whose relevant runtime environment is
unproved. Eight uncertain definitions are unselected. This is a purposive
static sample with no upstream test executions.
[Source-only labels and rationales](../datasets/real-v6/REVIEW.md)

## Where precision breaks down

- **XMLtodict contributes 107 of the 208 draft false positives.** All 107
  have resolved paths ending at `xmltodict.py::parse`. For example,
  `test_simple` uses an ordinary element with text, and
  `test_disable_entities_false_returns_xmlbomb` explicitly bypasses the edited
  handler setup. The call edge is valid in both cases. It establishes entry to
  `parse` while leaving the behavior of its edited declaration handlers open.
- **python-dotenv contributes 54 false positives, all conservative.** The
  flag change sends 27 of them through the changed test module and six
  through the production module. The interactive change sends all 21
  through the production module. Explicit-file `dotenv_values` calls and
  `find_dotenv(usecwd=True)` are source-visible controls that avoid the
  edited behavior.
- **tokenize-rt selects all 51 definitions across its two cases.** Of its
  47 draft false positives, 34 resolve to `src_to_tokens` and 13 use
  changed-test-module fallback. Ordinary source and empty f-string fixtures
  avoid the changed middle-token behavior. Offset defaults have no path
  through the tokenizer.

## Next precision milestone

Start with **bounded reachability of XML parser declaration handlers**.
The first control is an explicit `disable_entities=False` call in both
revisions. Then audit calls with a statically bound parser and literal XML
whose events cannot reach any changed handler. Check registration effects
as well as callback invocation before excluding an evidence path. Retain
independent evidence, the default-comment regression, affected declaration
tests, and uncertain streaming or parser bindings. This target addresses
the largest measured group of false positives with concrete source
controls. Keep the v6 engine and draft measurements as the baseline for
that separate work.
