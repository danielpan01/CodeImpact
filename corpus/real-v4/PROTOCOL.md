# Fresh evaluation v4 selection protocol

Established November 17, 2026, before candidate inspection. Reference analyzer:
`ed728a0851e87308c0ed454071ded12adb37eda8` (merged PR #22).

Use a purposive sample of three public repositories absent from prior datasets.
In order, consider `madzak/python-json-logger` (logging serialization),
`pydanny/cached-property` (descriptor/cache behavior), and
`python-humanize/humanize` (formatting). If one cannot supply two eligible
changes, use `wimglenn/oyaml` then `gruns/icecream` in that order. Use the
first 20 commits in the default-branch commit listing at or before
2020-01-01T00:00:00Z for the first three projects and
2022-01-01T00:00:00Z for reserves. Consider candidates in the order returned
by GitHub's commit listing, newest first, until two eligible changes per
repository are found. Record the prefix considered and any exclusions.

A candidate must have an exact head and first parent, a functional change
to production Python, a supported ordinary root MIT or BSD-3-Clause license
at both revisions, and complete supported Python trees that the existing
bounded reader can capture. Exclude merges, duplicates, packaging, CI,
documentation, test-only and whitespace-only edits, and broad unrelated
refactors. Require a parseable head with at least one test-shaped source
definition, including definitions outside current discovery. Source maps are
captured whole, with no size-based trimming. Determine eligibility from pinned
metadata and source only. Preserve every final choice once analysis starts.

Inventory head test-shaped definitions under the current static policy.
Label each discovered definition affected, unaffected or uncertain. A
changed or new test is affected. Unchanged tests are affected when pinned
source establishes dependence on a changed behavior, initialization or
binding. Keep unproved fixture, dispatch, indirect state and setup paths
uncertain. Use an explicit rationale for each test. Parameter expansions,
inherited executions and runtime collection are outside this count.
Record excluded definition IDs and reasons separately.

Freeze the selection, candidate decisions, protocol, source, provenance,
licenses, inventory, labels, source-only review pack and reference engine
hashes before the first v4 recommendation run. Preserve the first full
stable result and record discrepancies separately after measurement.
No analyzer tuning, relabeling or case selection may use that result in
this milestone. Labels remain drafts pending actual independent review.
Upstream files are data only. Never check them out, import them, execute
them or install upstream dependencies. This small historical sample measures
agreement with source labels for these changes. It has no runtime outcomes.

## Pre-analysis eligibility amendment

The initial windows yielded too few eligible repositories. JSON Logger's first
functional candidate has a BSD-2-Clause license, outside the allowlist. The
initial Cached Property and Humanize windows contain too few production
changes. The first reserve, oyaml, has qualifying candidates. The second
reserve, IceCream, has one in its initial window. Before final selection or
analysis, extend IceCream's window to the first 60 entries at the same cutoff.
For the remaining slot, apply the same first-20 rule to Humanize at
2021-01-01T00:00:00Z, then Cached Property at that cutoff if needed. These extra
windows respond to source eligibility only. No recommendations have been run.

The two reserve projects supply four changes. The second Humanize/Cached
Property window still lacks a third complete pair. Before final selection,
continue the later Humanize window through its first 60 commits, retaining
the original order. The ordinary root filename `LICENCE` is eligible when
its pinned text is an allowed license.

## Source labeling clarification before measurement

For discovery coverage, include conventional unittest-style `testCamelCase`
functions in the test-shaped inventory. They currently fall outside the
function-name rule even inside a supported filename. The analyzer policy is
unchanged. IceCream's two cases stay in the sample with zero discovered tests.

A test is affected when source establishes that it reaches the edited code or
binding, even if a particular input would still produce the same output.
A source-visible early exit before the edit can be unaffected. For external
loader registration, retain uncertainty where the runtime callback depends on a
library or interpreter version absent from the snapshot.
