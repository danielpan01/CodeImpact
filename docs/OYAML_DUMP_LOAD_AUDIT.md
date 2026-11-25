# oyaml dump-versus-load dependency audit

The `explicit-reexports-v1` replay selects **18 of 18** definitions in
`oyaml_error_context` against the frozen draft labels. It records 3 true
positives, 8 false positives, 0 false negatives, 0 true negatives, and 7 selected
uncertain definitions. The six dump paths retain their conservative evidence.
The captured source leaves two separate initialization effects unresolved.
[Pinned snapshots](../corpus/real-v4/cases/oyaml_error_context.json) ·
[Capture provenance](../corpus/real-v4/provenance/oyaml_error_context.json)

## Exact evidence for the six dump tests

Every row is a `test_oyaml.py::` definition. Each recommendation has a single
typed `module` edge to `test_oyaml.py::<module>`, score 50, and path revision
`both`. The edge points from the definition span below to test-module lines
1–188 before and 1–194 after, with evidence about module initialization.

| Test | Calls in the two captured bodies | Definition span before | Definition span after |
| --- | --- | --- | --- |
| `test_dump` | `yaml.dump`, lines 15 / 16 | 14–15 | 15–16 |
| `test_dump_all` | `yaml.dump_all`, lines 24 / 25 | 22–26 | 23–27 |
| `test_dump_and_safe_dump_match` | `yaml.dump` and `yaml.safe_dump`, lines 32 / 33 | 29–32 | 30–33 |
| `test_safe_dump` | `yaml.safe_dump`, lines 19 / 20 | 18–19 | 19–20 |
| `test_safe_dump_all` | `yaml.safe_dump_all`, lines 37 / 38 | 35–39 | 36–40 |
| `test_subclass_dump` | `yaml.dump` and `yaml.safe_dump`, lines 92 and 94 / 93 and 95 | 90–94 | 91–95 |

The test module binds `yaml` with `import oyaml as yaml` on lines 7 / 8
and separately imports oyaml's dictionary-order guard on lines 8 / 9.
Both statements are evidence for a graph import edge from the test module
to `oyaml.py::<module>`. The displayed paths terminate one hop earlier.
The head adds a direct import of `ConstructorError` from the external
`yaml.constructor` module on line 5. Adding that import alone to a temporary
copy of the base snapshot reproduced all six dump recommendations with the
same test-module seed. Adding only the new test definition produced zero dump
recommendations. Changing only `oyaml.py` also produced zero dump recommendations
under the current analyzer. These source-only probes leave the frozen snapshots
intact.
[Base tests](https://github.com/wimglenn/oyaml/blob/425fd975c063aed8770826b98376a19b83a6c3de/test_oyaml.py) ·
[Head tests](https://github.com/wimglenn/oyaml/blob/6350d9de586f40014296b55427ccbc1d7f47269a/test_oyaml.py)

## Production registration and the external boundary

- **Dump side.** `map_representer` is unchanged on lines 14–15. Both revisions
  choose the two dumper classes by checking the identity of PyYAML's
  `safe_dump` and `dump` functions. The four calls from lines 31–34 before
  and 36–39 after register `dict` and `OrderedDict` with those dumper classes.
  The checked-in dump test bodies contain no observed load call.
- **Load side.** The body edit is in `map_constructor`, lines 18–20 before and
  18–25 after. The head asks the loader to construct the mapping on the error
  path so it can supply context after `OrderedDict(pairs)` raises
  `TypeError`. The dictionary-order guard is unchanged and depends on the
  Python version and implementation. It treats Python 3.7 or newer and
  CPython 3.6 or newer as ordered. When the guard permits registration,
  oyaml iterates external `pyyaml.loader.__all__`, looks up each class, and passes
  the edited callable to `pyyaml.add_constructor` during import, on line 41
  before and 46 after.
- **Re-export.** After registration, oyaml deletes the local callback and
  class bindings and uses `from yaml import *`, lines 48 / 53. The captured
  Python files contain no implementation of that export surface, the
  registration calls, the selected loader and dumper classes, or the four
  dump functions.
  [Base oyaml source](https://github.com/wimglenn/oyaml/blob/425fd975c063aed8770826b98376a19b83a6c3de/oyaml.py) ·
  [Head oyaml source](https://github.com/wimglenn/oyaml/blob/6350d9de586f40014296b55427ccbc1d7f47269a/oyaml.py)

Both `setup.py` revisions declare PyYAML by bare dependency name at line 13.
The pinned trees contain no lockfile. The identical Travis workflow requests
compatible releases starting at 3.13, 4.2b4, and 5.1 across several interpreter
variants. It asks the runner to print the installed versions, but the pinned
trees contain no such output or installed artifact receipt. The checked-in
matrix describes possible environments. It supplies no exact PyYAML identity
for either revision. The CI, packaging configuration, and README bytes fetched
for this audit matched their Git blob IDs in both capture receipts.
[Base dependency declaration](https://github.com/wimglenn/oyaml/blob/425fd975c063aed8770826b98376a19b83a6c3de/setup.py#L13) ·
[Head dependency declaration](https://github.com/wimglenn/oyaml/blob/6350d9de586f40014296b55427ccbc1d7f47269a/setup.py#L13) ·
[Pinned Travis matrix](https://github.com/wimglenn/oyaml/blob/6350d9de586f40014296b55427ccbc1d7f47269a/.travis.yml#L15-L30) ·
[Compatible release syntax](https://packaging.python.org/en/latest/specifications/version-specifiers/#compatible-release)

Exclusion would require a two-revision account of the effect of passing the
changed callback to external registration and of the callable actually exported
for each dump name. It would also require proving the separate new
`yaml.constructor` import cannot affect the test module's initialization or
the imported dump binding. The existing `yaml.representer` import could
initialize some of the same dependency modules. The captured source leaves
their initialization order and the redundancy of the new import unproved.
Separate registration names and unchanged dump bodies leave those effects
open. The audit reads upstream source and configuration only as data.

## Disposition

Zero IDs were added, removed, or given replacement evidence. All six dump
paths keep their exact typed evidence. The guarded `test_loads_to_ordered_dict`
and `test_safe_loads_to_ordered_dict` retain their conservative paths. The seven
uncertain definitions retain the same paths too. These are
`test_anchors_and_references`, `test_load`, `test_load_all`, `test_merge`,
`test_omap`, `test_omap_flow_style` and `test_safe_load`.
The new `test_unhashable_error_context` retains its exact after-only
changed-test evidence. The two guarded standard-dictionary paths also stay
as measured. Source-only regressions protect the pinned paths, the independent
test-module seed, and synthetic mixed load/dump and independently resolved
paths. The synthetic registration callback illustrates why an API name
alone does not establish separation. Its backend exposes the effect of
constructor registration through shared state read by a dump function.

The existing replay remains the baseline for this case. An exact dependency
and interpreter receipt, plus source for the imported constructor and
registration/export paths, would allow a future proof to be evaluated.
