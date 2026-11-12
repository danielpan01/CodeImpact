# CodeImpact frontend redesign roadmap

Status: milestone 1 implemented locally, November 12, 2026. Requested by the owner after the analyzer and
evaluation milestone merged in [PR #6](https://github.com/danielpan01/CodeImpact/pull/6).
Milestone 1 is implemented and locally verified below. Milestones 2–3 remain planned;
no deployment, independent review or usability study is claimed.

## Product goal

Make CodeImpact feel like a polished developer review workspace. A user should
immediately understand what changed, which tests deserve attention and why. The
visual experience should be substantially stronger across the whole workflow:
input, summary, graph, recommendations, changed code and evidence.

Keep the existing React/TypeScript/Vite application and working API. Apply the new
design to real analysis data from the first implementation slice. All existing
entry points remain usable: public PR URLs, snapshot upload and the local demo.

## Pre-redesign observations

Observed in the running application and current UI source on November 12:

- Dark green backgrounds, similar bordered panels and repeated cards give many
  elements equal visual weight. Separate navigation, inputs, results and evidence
  through clearer surfaces and hierarchy.
- The hero, input form, demo/upload panel and four large metrics precede the actual
  review workspace. In the observed narrow browser viewport, analysis content sits
  below the first screen. Give the review workspace priority once a report is loaded.
- Small secondary text and uppercase labels make useful information harder to scan.
  Promote file names, test names, evidence categories and revision context.
- At narrow widths, stacked code panes and evidence create a long page. Provide
  deliberate mobile navigation and an explicit route back from evidence to results.
- Test recommendations are a long button list. Large real cases need search,
  filters, sorting and visible result counts.
- The score occupies substantial space. Give the reason and actual dependency path
  greater prominence while retaining the numeric heuristic and its meaning.

These observations guide the redesign; they are not claims of measured usability
improvement. Capture before/after screenshots and review the completed implementation.

## Visual direction

Use a light, warm-neutral analysis canvas, dark ink navigation and a restrained
cobalt accent for primary actions and selection. Provide a coherent graphite dark
theme during the polish milestone. Semantic change/evidence colors must work in
both themes and include text or shape cues, not color alone.

| Element | Direction |
| --- | --- |
| Surfaces | Clear page, panel and selected-item levels; fine dividers; minimal nested boxes; subtle shadows only where they explain elevation |
| Typography | Strong, compact headings; 14–16 px primary UI text; comfortably readable secondary labels; monospace for code, paths and revisions |
| Spacing | Shared spacing tokens based on a 4/8 px scale; consistent control heights, panel padding and corner radii |
| Color | Neutral content surfaces; cobalt for actions; clearly labeled coral/amber/teal change states; distinct before/after/mixed evidence badges |
| Icons | One consistent SVG icon style with accessible labels; replace decorative Unicode control glyphs |
| Graph | Readable symbol cards, explicit direction, selected-path emphasis and muted surrounding context; fit-to-view and a compact legend |
| Motion | Brief state transitions and panel changes; no decorative continuous animation; respect reduced-motion preferences |
| Fonts/assets | Reliable system or locally bundled licensed fonts; no mandatory external font request for the primary experience |

These are starting design decisions. Refine exact colors and sizing against real
screenshots and contrast checks during implementation. Avoid giant decorative
headers, arbitrary gradients, unsupported product claims or fabricated activity.

## Workspace structure

Desktop: compact navigation, a slim report/context bar, a small summary strip and a
large review region with an evidence inspector. Keep the PR input prominent before
analysis; after loading, condense it into a clear “New analysis” action that can
reopen the form. Keep repository/revision context, demo status and export discoverable.

Use Tests as the initial review view after a successful analysis, with Map and
Changes adjacent and equally easy to open. Preserve selection while moving between
views. Present a zero-recommendation result explicitly, with a route to changed code
and the reminder that no recommendation does not establish safety.

Tablet: reduce navigation width and show evidence in a deliberate drawer or single
secondary panel instead of compressing three narrow columns.

Phone: one primary content pane at a time, persistent view navigation and a full-width
evidence panel with a clear back action. Show code revisions with Before/After controls
or a readable stacked layout. Keep horizontal scrolling inside code/graph regions,
not the page body. Desktop side-by-side code remains available where space permits.

## Milestone 1 — Visual foundation and complete workspace

**Implemented locally.** The application now has shared semantic light-theme tokens,
system fonts, SVG controls, compact dark navigation/report context and a summary strip.
Initial input offers PR analysis, snapshot upload and an explicit Load demo action.
Every successful analysis opens Tests and collapses input behind New analysis.
Tests preserve the entire recommendation list, original order and numeric priorities.
Map keeps the original layout algorithm, graph data and controls. Changes retains
source bounds and safely rendered before/after text, with collapsible file navigation.
The evidence inspector leads with reasons and dependency trails, preserves expansion
and selection across views, and provides Back/Escape navigation at tablet/phone widths.
Zero recommendations lead explicitly to changed code without a safety claim.

Observed checks: 653 Python tests, 50 browser tests, production build, formatting,
and all three unchanged offline evaluations. Screenshots were inspected at 1440×900,
1280×800, 768×1024, 390×844 and 360×844. Pinned Slugify ASCII/boundary and Cachetools LFU
reports, long names, deleted/mixed evidence, empty results, loading and errors were
also inspected. This is agent visual/keyboard verification in Chromium, not a user
study or a complete accessibility audit. See [VALIDATION.md](VALIDATION.md).

Original milestone scope (delivered):

Deliver a visibly redesigned, fully usable application shell and all existing views.

- Introduce shared typography, color, spacing, border and interaction tokens.
- Extract reusable controls, badges, panels and navigation from the large page
  component where this makes the redesign easier to maintain.
- Rebuild the analysis entry experience and compact loaded-report header.
- Restyle Map, Tests, Changes, code panes and evidence inspector consistently.
- Replace the large score display with a balanced priority/reason treatment.
- Preserve public PR analysis, snapshots, demo, export, scope warnings, exact
  revisions and before/head/deleted/mixed evidence throughout the new shell.
- Keep the current responsive behavior working while building the deliberate
  tablet/phone arrangements specified above; no desktop-only release.

Acceptance:

- At 1440×900 and 1280×800, a loaded report shows the report context, view controls
  and usable review content without scrolling past a marketing-sized introduction.
- At 390×844, users can analyze, choose a test, inspect evidence, open changed code
  and return without page-level horizontal overflow or obscured controls.
- A retained recommendation opens the same symbol and evidence as before; displayed
  priorities keep their current values and remain explicitly heuristic.
- All existing browser workflows pass with semantic selectors updated as needed;
  do not delete coverage simply because the layout changes.
- Before/after desktop and phone captures demonstrate the full redesign with real
  data. A static mockup alone does not complete this milestone.

## Milestone 2 — Refine graph, tests and code review

Deliver the interactions that make real reports easier to inspect.

- Tests: search by test/file name, filter by explanation category, deterministic
  sorting, visible filtered/total counts and a clear reset action. Filtering the UI
  never changes the analysis report or the set exported as recommendations.
- Graph: emphasize the selected evidence path, provide focus/fit/reset controls,
  distinguish calls from fallback edges, and make long paths readable. Any optional
  grouping must retain access to underlying symbols and original edge identities.
- Evidence: refine the delivered dependency trail, expandable source locations and
  revision badges for long paths and larger reports; preserve the existing selection
  and expansion behavior across graph, tests and changed-code navigation.
- Changes: a navigable file/symbol list, clear added/modified/deleted states, readable
  source with line numbers and safe syntax coloring. Keep before-only, after-only,
  empty-file and parse-error states explicit. Treat source as escaped data.
- Handle real 100+ recommendation lists and large graphs without clipped controls
  or unreadable labels. Measure rendering before adding virtualization or a new
  graph-layout dependency; preserve deterministic ordering.

Acceptance: the demo, both Slugify cases and a large Cachetools case can be reviewed
without losing selection or the route to changed code. Search/filter controls and
graph focus work by keyboard. Add meaningful browser regressions for the new
interactions. Displayed counts and exported report data remain consistent.

## Milestone 3 — Responsive polish and frontend release

- Complete both light and dark themes with shared semantic tokens and a saved
  local theme preference. Theme changes must not alter report data.
- Polish the delivered tablet/mobile single-pane navigation, touch targets, focus
  management and dismissal/back behavior across additional browsers and devices.
- Refine the delivered loading, empty, invalid input, rate-limit, network-error and retry states.
  Show only progress the API actually supplies; no invented percent-complete bars.
- Provide accessible names, visible focus, logical keyboard order, readable
  contrast and reduced-motion behavior. Verify these properties instead of claiming
  certification from a screenshot.
- Refresh the milestone-1 README/demo screenshots and walkthrough after subsequent changes.
- Ask another developer to complete the analyze → test → evidence → changed-code
  flow; record observations and actual review status without inventing a user study.

Visual review matrix: 1440×900, 1280×800, 768×1024 and 390×844; light and dark themes;
normal and reduced motion where relevant. Include long file names, many tests,
empty recommendations, deleted symbols, mixed revisions and loading/error states.
Automated visual comparisons should use stable fixture data and handle only
documented volatile display fields, such as elapsed time, without masking useful UI.

## Verification required for each frontend milestone

Run focused UI regressions, `make check`, `make evaluate`, `make evaluate-real`,
`make evaluate-real-v2`, and `cd web && npm run test:e2e`. Add coverage for behavior
introduced by that slice. Preserve the existing desktop and mobile tests; test new
themes and responsive interactions explicitly as they arrive.

Compare stable report results to the merged reference. Analyzer source, scores,
selected IDs, graph direction, revision evidence, input limits, all corpus data and
all three v2 measurements stay unchanged during this frontend program. Document
actual outcomes and inspect screenshots; green tests alone do not establish good
visual design. Keep changes unstaged/uncommitted for the owner to review and publish.

## Subsequent roadmap

1. Independent label review and bounded Cachetools fallback narrowing, starting with
   the 136 LFU-case false positives. Scope the 31 descriptor-case false positives
   separately; preserve unknown receivers, uncertain labels and historical baselines.
2. Fresh source changes selected and labeled before examining recommendations, plus
   a developer pilot to assess both analyzer usefulness and the redesigned workflow.
3. Performance/memory measurement, worker isolation and a small hosted pilot with
   explicit access and resource controls. Introduce jobs/storage/private authorization
   only when required by the pilot.

The 284 existing v2 false positives, two authored misses and outstanding label review
remain documented work. The frontend redesign does not change those measurements.
