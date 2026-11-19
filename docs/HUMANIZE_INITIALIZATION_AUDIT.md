# Humanize package initialization audit

**Decision.** Keep the existing conservative evidence for
`humanize.precisedelta`. Both revisions contain an explicit re-export, but
the pinned data cannot establish the behavior of the initializer's
`pkg_resources` import and distribution lookup.

## Revisions and dependency provenance

The `humanize_small_delta` fixture compares first parent
`9d9de69177154b41b2d6ef412d1487639e99833d` with head
`62706fd4cb90ebeb9bf85685bad8ab1fa9d0c742` from
`python-humanize/humanize`. Both frozen Git trees are complete, with 125
entries and 79 blobs each. Fifteen files fetched by exact Git revision,
including packaging, CI, release, documentation dependencies and `LICENCE`,
matched the blob IDs and byte lengths in **both** trees. The Humanize source
is MIT-licensed. The fetched bytes and their Git blob and SHA-256 manifest
are kept in the ignored local directory `reports/humanize-init-audit/`.
[Frozen provenance](../corpus/real-v4/provenance/humanize_small_delta.json) ·
[Base commit](https://github.com/python-humanize/humanize/commit/9d9de69177154b41b2d6ef412d1487639e99833d) ·
[Head commit](https://github.com/python-humanize/humanize/commit/62706fd4cb90ebeb9bf85685bad8ab1fa9d0c742) ·
[Pinned MIT license](https://github.com/python-humanize/humanize/blob/62706fd4cb90ebeb9bf85685bad8ab1fa9d0c742/LICENCE)

| Pinned source | What it establishes in both revisions |
| --- | --- |
| [Packaging declarations](https://github.com/python-humanize/humanize/blob/62706fd4cb90ebeb9bf85685bad8ab1fa9d0c742/setup.py#L28-L38) | Runtime `setuptools` and setup-time `setuptools_scm` are unpinned. The tests extra also leaves its dependencies unpinned. |
| [pyproject.toml](https://github.com/python-humanize/humanize/blob/62706fd4cb90ebeb9bf85685bad8ab1fa9d0c742/pyproject.toml) and [setup.cfg](https://github.com/python-humanize/humanize/blob/62706fd4cb90ebeb9bf85685bad8ab1fa9d0c742/setup.cfg) | The TOML is Black configuration with no build-system dependency declaration. The setuptools mention in `setup.cfg` is an import-sorting classification. |
| [Tox configuration](https://github.com/python-humanize/humanize/blob/62706fd4cb90ebeb9bf85685bad8ab1fa9d0c742/tox.ini#L1-L19) and [docs requirements](https://github.com/python-humanize/humanize/blob/62706fd4cb90ebeb9bf85685bad8ab1fa9d0c742/docs/requirements.txt) | The test environment uses the tests extra. The requirements file supplies documentation dependencies and has no setuptools entry. The full trees contain no dependency lock or constraints file. |
| [GitHub Actions test workflow](https://github.com/python-humanize/humanize/blob/62706fd4cb90ebeb9bf85685bad8ab1fa9d0c742/.github/workflows/test.yml#L8-L62), [Travis configuration](https://github.com/python-humanize/humanize/blob/62706fd4cb90ebeb9bf85685bad8ab1fa9d0c742/.travis.yml#L1-L23), and [release instructions](https://github.com/python-humanize/humanize/blob/62706fd4cb90ebeb9bf85685bad8ab1fa9d0c742/RELEASING.md#L16-L49) | CI selects Python environments and installs or upgrades tools before running Tox. The cache key and runner selection give no exact setuptools version. Release instructions also upgrade setuptools without a pin. |

GitHub's Actions runs endpoint returned zero runs for each exact SHA during
the audit. It supplied no installed-version evidence. The verified hashes
identify Humanize's metadata bytes. There is no verifiable setuptools
version, source revision, license receipt or artifact hash for these
fixtures. [Base Actions query](https://api.github.com/repos/python-humanize/humanize/actions/runs?head_sha=9d9de69177154b41b2d6ef412d1487639e99833d&per_page=100) ·
[Head Actions query](https://api.github.com/repos/python-humanize/humanize/actions/runs?head_sha=62706fd4cb90ebeb9bf85685bad8ab1fa9d0c742&per_page=100)

## Import, re-export and lookup

The initializer is byte-identical between the two revisions, with SHA-256
`a0a452062f9eed2065b9b4089ffff6689442fc6fc8212435c0439e5f73ea39cb`.
Its statements run in this order. [Base initializer](https://github.com/python-humanize/humanize/blob/9d9de69177154b41b2d6ef412d1487639e99833d/src/humanize/__init__.py#L1-L34) ·
[Head initializer](https://github.com/python-humanize/humanize/blob/62706fd4cb90ebeb9bf85685bad8ab1fa9d0c742/src/humanize/__init__.py#L1-L34)

1. **Line 2 imports `pkg_resources`.** The import runs before any explicit
   export binding. An import failure can prevent the package from reaching
   the binding. Its initialization and any transitive effects on the
   namespace are outside the captured source.
2. **Lines 3–12 import the captured child modules.** `filesize` and `number`
   load their source definitions and data. `i18n` also constructs
   `NullTranslations()` and thread-local state during import. `time` imports
   translation functions, defines the `Unit` enum with a
   `total_ordering` decorator, and defines `precisedelta`. If these imports
   complete, the explicit import assigns the child function to the root
   package's `precisedelta` attribute. The function's header matches in both
   revisions. Its edited body is deferred by the definition. The captured
   initializer contains no eager call to it. [Transitive i18n initialization](https://github.com/python-humanize/humanize/blob/62706fd4cb90ebeb9bf85685bad8ab1fa9d0c742/src/humanize/i18n.py#L1-L12) ·
   [Time initialization](https://github.com/python-humanize/humanize/blob/62706fd4cb90ebeb9bf85685bad8ab1fa9d0c742/src/humanize/time.py#L1-L42) ·
   [Base function](https://github.com/python-humanize/humanize/blob/9d9de69177154b41b2d6ef412d1487639e99833d/src/humanize/time.py#L378-L520) ·
   [Head function](https://github.com/python-humanize/humanize/blob/62706fd4cb90ebeb9bf85685bad8ab1fa9d0c742/src/humanize/time.py#L378-L534)
3. **Line 14 runs `get_distribution(__name__).version`.** This requests
   Humanize's distribution version and assigns it to `__version__` and
   `VERSION`. The code shows no direct reassignment of `precisedelta` here.
   The call and attribute access still execute after the export is bound.
   An uncaught failure can stop successful package initialization before
   the trailing literal `__all__` is set. The captured source supplies no
   effect proof for the lookup. `__all__` records export names without
   establishing the callable's identity.

The audit distinguishes a visible source binding from a verified surviving
binding. It found no direct write to the export in the captured initializer.
A different surviving value would require a write to the package namespace,
such as a reassignment or a mutation through a shared module object. The
uncaptured import and lookup leave both completion and indirect writes
unproved. In both snapshots the existing proof rejects the initializer
at the first opaque import.

## Separate i18n caller audit

`test_i18n.py` is byte-identical in both revisions. In `test_i18n`, the
qualified calls on lines 14, 20 and 26 use the module-scope `import humanize`.
They occur before locale activation, while the Russian locale is active,
and after deactivation in `finally`. Those calls work with child module
translation state. The test itself has no `importlib.import_module` call.
[Affected i18n test](https://github.com/python-humanize/humanize/blob/62706fd4cb90ebeb9bf85685bad8ab1fa9d0c742/tests/test_i18n.py#L1-L26) ·
[Locale state changes](https://github.com/python-humanize/humanize/blob/62706fd4cb90ebeb9bf85685bad8ab1fa9d0c742/src/humanize/i18n.py#L28-L60)

Five sibling tests use `importlib.import_module("humanize.i18n")`. One
reads from the returned module and four set or delete its `__file__`.
These are dynamic child-module lookups and observed mutations of module
metadata. The source shows no direct rebinding of `humanize.precisedelta`
through those aliases. These operations remain outside the bounded
caller proof. `freezegun` and pytest collection effects were outside the audit.
[Sibling tests](https://github.com/python-humanize/humanize/blob/62706fd4cb90ebeb9bf85685bad8ab1fa9d0c742/tests/test_i18n.py#L29-L66)

## Result and next candidate

`make evaluate-real-v4-reexports` reproduced 20 of 33 selected, with one
changed-test path and 19 conservative paths. The five draft true positives,
15 draft false positives, 0 false negatives and 13 true negatives are
unchanged. The replay matches the existing receipt byte for byte.
[Existing re-export receipt](../corpus/real-v4-successors/explicit-reexports-v1/baseline.json) ·
[Verification](VALIDATION.md#humanize-package-initialization-audit)

For the next analyzer slice, investigate the single remaining draft false
positive in the already captured v3 `inflection_title` fixture,
`test_inflection.py::test_uncountable_word_is_not_greedy`. Its sole evidence
ends at its own changed test module. The source adds one literal to
`inflection.UNCOUNTABLES`, calls the plural and singular helpers and
restores the set in `finally`. A focused source audit can test whether
that mutation is independent of the edited titleize parameter table and
production `titleize` body in both revisions. Preserve the `test_titleize`
edge and retain fallback if the set aliases, escapes or fails to restore.
[Pinned Inflection case](../corpus/real-v3/cases/inflection_title.json) ·
[Current titleize result](PARAMETER_TABLE_REVIEW.md#measured-change)
