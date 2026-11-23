# PyISO8601 Hypothesis validator audit

**Decision.** Keep both wrapped tests' package-initializer fallback. The
captured source establishes the decorator expressions and unchanged parser
calls. The installed Hypothesis, pytest and pytz execution environment is
unproved. Even the locked Hypothesis release has import-time entry-point
loading and pytest hooks whose active environment is outside the snapshots.

## Captured test and package bindings

`iso8601_validator` compares `406db6f23ffbf6815a320c30be070b89d28e2974`
and `21f536815328987631d374421d928aab2255e3da`. Each test module binds
`hypothesis` with `import hypothesis` and loads its `extra.pytz` and
`strategies` submodules. Its relative import binds `iso8601` to the direct
child module. There are no competing source bindings for these imports.
Both decorators supply keyword `s` for the function's single
`datetime.datetime` parameter.
[Pinned snapshots](../corpus/real-v3/cases/iso8601_validator.json) ·
[Capture provenance](../corpus/real-v3/provenance/iso8601_validator.json)

| Test | Decorator lines before / after | Source body in both revisions |
| --- | --- | --- |
| `test_hypothesis_valid_naive_datetimes` | 264 / 266 | `hypothesis.strategies.datetimes()` supplies the value. The test formats it with `s.isoformat()`, calls `iso8601.parse_date` with `default_timezone=None`, prints values and checks equality. |
| `test_hypothesis_valid_datetimes_with_timezone` | 272–274 / 274–276 | The datetime strategy takes `hypothesis.extra.pytz.timezones()`. The body formats, prints and compares the values, using the parser's default timezone argument. |

The unchanged parser reads the same compiled regex and timezone helpers.
The head adds `is_iso8601` to that child module and explicitly imports it
in the package initializer. The existing named imports still bind
`parse_date`, `ParseError`, `UTC`, and `FixedOffset`. The head's adjacent
`"is_iso8601" "ParseError"` literals form one `__all__` entry,
`is_iso8601ParseError`. That changes the wildcard and introspection surface.
The two Hypothesis test bodies use the child parser and contain no wildcard
imports or validator calls. The two directly edited parser tests add the
validator assertions and remain independent seeds.
[Base test source](https://github.com/micktwomey/pyiso8601/blob/406db6f23ffbf6815a320c30be070b89d28e2974/iso8601/test_iso8601.py#L264-L279) ·
[Head test source](https://github.com/micktwomey/pyiso8601/blob/21f536815328987631d374421d928aab2255e3da/iso8601/test_iso8601.py#L266-L281) ·
[Additive-export review](VALIDATOR_EXPORT_REVIEW.md)

## What the workflows establish

The two trees share the same `poetry.lock`, `pyproject.toml`, `noxfile.py`,
`.envrc`, and workflow file. The lock pins Hypothesis **6.27.1**, pytz
**2021.3**, and pytest **6.2.5**. Both the wheel and source-distribution
SHA-256 entries for Hypothesis and pytz match the corresponding published
PyPI metadata. The lock is Git blob `98e05623c78b6fa401e9f2ff9f5bbb4195260be6`.
[Pinned lock](https://github.com/micktwomey/pyiso8601/blob/21f536815328987631d374421d928aab2255e3da/poetry.lock) ·
[Hypothesis release metadata](https://pypi.org/pypi/hypothesis/6.27.1/json) ·
[pytz release metadata](https://pypi.org/pypi/pytz/2021.3/json)

| Workflow | Supported conclusion |
| --- | --- |
| `poetry install` followed by pytest in that environment | The lock identifies the intended dependency versions and candidate artifacts when Poetry installs the development environment from it. The source contains no installed-environment inventory or execution result. |
| `poetry install` followed by `poetry run nox` | Poetry can supply the outer Nox executable. Its test session installs the project and requests pytest, Hypothesis and pytz by bare name in a separate, reusable environment. The Poetry development lock does not constrain those requests. |
| GitHub Actions | The shared workflow installs Nox without a version pin and runs the same `test` session for Python 3.6 through 3.10. The committed commands do not identify which package builds ran. Exact-SHA Actions queries returned zero runs for each revision, so they supplied no installed-version record. |

[Documented commands](https://github.com/micktwomey/pyiso8601/blob/21f536815328987631d374421d928aab2255e3da/README.rst#L74-L86) ·
[Nox session](https://github.com/micktwomey/pyiso8601/blob/21f536815328987631d374421d928aab2255e3da/noxfile.py#L25-L29) ·
[GitHub Actions workflow](https://github.com/micktwomey/pyiso8601/blob/21f536815328987631d374421d928aab2255e3da/.github/workflows/python-app.yml#L3-L27) ·
[Base run query](https://api.github.com/repos/micktwomey/pyiso8601/actions/runs?head_sha=406db6f23ffbf6815a320c30be070b89d28e2974&per_page=1) ·
[Head run query](https://api.github.com/repos/micktwomey/pyiso8601/actions/runs?head_sha=21f536815328987631d374421d928aab2255e3da&per_page=1)

## Collection and execution boundary

The upstream Hypothesis 6.27.1 tag resolves to
`2fa6d0a55df31ddffde4098b7eb7c7d9991b8dff`. In that source, `given` comes
from `hypothesis.core`. It builds a wrapper with a revised signature and
an `inner_test` handle. Generated inputs reach the test through the wrapper
and its settings and execution machinery. The datetime strategy defaults
to a `None` timezone. The aware form draws from the external pytz zone
catalog and attaches timezone information through pytz's localization API.
[Release source](https://github.com/HypothesisWorks/hypothesis/commit/2fa6d0a55df31ddffde4098b7eb7c7d9991b8dff) ·
[Wrapper](https://github.com/HypothesisWorks/hypothesis/blob/2fa6d0a55df31ddffde4098b7eb7c7d9991b8dff/hypothesis-python/src/hypothesis/core.py#L958-L1044) ·
[Datetime strategy](https://github.com/HypothesisWorks/hypothesis/blob/2fa6d0a55df31ddffde4098b7eb7c7d9991b8dff/hypothesis-python/src/hypothesis/strategies/_internal/datetime.py#L142-L232) ·
[pytz adapter](https://github.com/HypothesisWorks/hypothesis/blob/2fa6d0a55df31ddffde4098b7eb7c7d9991b8dff/hypothesis-python/src/hypothesis/extra/pytz.py#L28-L56)

The same release calls its entry-point loader on import. The loader can
load and invoke providers registered in the installed environment. The
distribution also registers a pytest plugin. The plugin can set profiles,
mark collected wrappers, inspect fixtures and handle wrapped execution
and reporting. The captured PyISO8601 tree has no `conftest.py` or pytest
configuration, and its two test definitions declare only Hypothesis's
generated argument. The installed entry-point registry, active plugins and
execution settings are still unknown. The source provides no evidence
that a specific plugin observed the changed export. It also provides no
closed audit of their effects on the package in either workflow.
[Import entry point](https://github.com/HypothesisWorks/hypothesis/blob/2fa6d0a55df31ddffde4098b7eb7c7d9991b8dff/hypothesis-python/src/hypothesis/__init__.py) ·
[Entry-point loader](https://github.com/HypothesisWorks/hypothesis/blob/2fa6d0a55df31ddffde4098b7eb7c7d9991b8dff/hypothesis-python/src/hypothesis/entry_points.py#L24-L71) ·
[Plugin registration](https://github.com/HypothesisWorks/hypothesis/blob/2fa6d0a55df31ddffde4098b7eb7c7d9991b8dff/hypothesis-python/setup.py#L129-L136) ·
[pytest hooks](https://github.com/HypothesisWorks/hypothesis/blob/2fa6d0a55df31ddffde4098b7eb7c7d9991b8dff/hypothesis-python/src/hypothesis/extra/pytestplugin.py)

The existing analyzer recognizes the two decorator constructions when
auditing a plain sibling. It still stops before modeling a decorated
test's execution. The new regressions use both recognized strategy
shapes with an otherwise simple parser call. The plain sibling sheds its
package fallback, and the wrapped test keeps its exact conservative path.
The pinned regression also checks both wrapped paths, their revision and
score, and the complete stable analysis hash.

## Replay result

`finite-string-guards-v1` still selects **4/8** for the validator case,
with **2 draft TP / 2 FP / 0 FN / 4 TN**. Each wrapped test retains
`test → iso8601/test_iso8601.py::<module> → iso8601/__init__.py::<module>`,
with distance 2, score 32 and evidence in both revisions. Both edited
tests retain their exact changed-test evidence. The existing receipt and
engine remain active. Independent review is pending.

The external bytes and blob and SHA-256 records are in the ignored local
`reports/hypothesis-validator-audit/` directory. The 18 PyISO8601 entries
match the frozen trees by blob ID and size. The eight Hypothesis source and
license files match the provider's blob IDs at the exact release commit.
All upstream material was read as data.
[Verification](VALIDATION.md#pyiso8601-hypothesis-wrapper-audit)
