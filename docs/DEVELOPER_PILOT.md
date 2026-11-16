# Developer walkthrough

**Status: deferred by the owner on November 14, 2026.** No developer participant,
completion time, feedback, satisfaction score or independent usability evidence
has been recorded. The automated browser checks exercise the tasks below; they
are not a human pilot. Source-label review remains a separate pending activity.

## Prepare

From the repository root, with the existing development dependencies installed:

```sh
make pilot
make dev
```

Open `http://127.0.0.1:5173`. `make pilot` validates the frozen v3 inputs and writes
two JSON snapshot pairs under `reports/developer-pilot/`. It does not run analysis
or execute upstream code. Existing output is preserved: reuse those files or use
`--output` with a new directory when running `scripts/prepare_pilot.py` directly.
There are no credentials or upstream dependency installations in this walkthrough.
Stop the development servers with Ctrl-C when finished.

## Tasks for a future participant

Use your own words to explain the evidence; record confusion before asking the
facilitator for help. Try the same tasks on a narrow viewport if practical.

1. Choose **Load demo**. Select `test_create_order`, inspect the dependency path,
   use **Focus path in Map**, and then **Open changed code**. Explain why a test
   can deserve attention even when its own file was not edited.
2. Choose **New analysis** and upload `inflection_title.json`. Search Tests for
   `test_titleize`, select it, and inspect the resolved call explanation. Follow
   the path into Map and open changed code. Find the `.title()` implementation.
   Compare a different recommended test's conservative module/import explanation.
   Explain why a recommendation does not prove an assertion will fail. Clear the
   search and export the full report; filtering should not trim the export.
3. Upload `ordered_set_pop.json`. Milestone 7 discovers its 30 `test.py` definitions
   and recommends `test_pop`. Open **Test discovery scope**, then inspect the
   conservative module/import evidence and **Open changed code**. Select
   **modified OrderedSet.pop** to see the new `index=-1` argument. Explain why
   unselected tests are not proven safe to skip; 12 new source labels remain uncertain.
   Whole-module previews are bounded; use the individual method or full JSON export.
   For zero discovery, separately upload `tests/fixtures/unsupported-discovery.json`
   from this checkout. Explain the unsupported filename and conditional-definition
   boundaries, then use **Review changed code**. The old Ordered Set zero-discovery
   walkthrough remains a historical milestone 5 result, not current behavior.
4. Switch light/dark themes, return to Tests and use **New analysis**. Record any
   confusing navigation, lost context, clipping or unreadable evidence.

## Blank feedback record

Leave these blank until a person actually participates. Record observations in a
new dated file, outside the immutable corpus; do not fill them from automated tests.

- Participant and relevant development experience:
- Date, device, browser and viewport:
- Task completed independently / with help / not completed:
- Participant's explanation of resolved versus conservative evidence:
- Participant's interpretation of the zero-discovery result:
- Where they hesitated, with the exact action or wording:
- What they expected and what happened:
- Suggested improvement and priority:
- Follow-up change and verification, if any:

Do not publish personal feedback or contact another person without the owner's
instruction. A future label reviewer should use the separate
[source-only review pack](../corpus/real-v3/REVIEW.md), before viewing evaluation
results. Neither walkthrough completion nor a passing replay establishes accuracy.
