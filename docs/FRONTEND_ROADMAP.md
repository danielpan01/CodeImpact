# CodeImpact frontend redesign roadmap

Status: milestones 1 and 2 merged in [PR #7](https://github.com/danielpan01/CodeImpact/pull/7)
and [PR #8](https://github.com/danielpan01/CodeImpact/pull/8) after CI passed on
November 12, 2026. Milestone 3 merged in [PR #9](https://github.com/danielpan01/CodeImpact/pull/9)
after CI passed. New analyzer work follows the active [build plan](BUILD_PLAN.md).
The owner waived the separate developer walkthrough. A built local pilot service
subsequently merged in PR #12; live hosting and the human pilot remain deferred.
No independent review or usability study is claimed. See [VALIDATION.md](VALIDATION.md)
for observed checks and [REPOSITORY_REVIEW.md](REPOSITORY_REVIEW.md) for the November 15 audit.

Milestone **8A merged in [PR #13](https://github.com/danielpan01/CodeImpact/pull/13)**,
including the CI timeout correction; its post-merge checks passed. It supplies the
rounded controls, entry composition, connected-node identity and coordinated surfaces.
See [the visual receipt](FRONTEND_MILESTONE8A.md). **8B merged in [PR #14](https://github.com/danielpan01/CodeImpact/pull/14)**:
lossless category/file diagnostics, full-text search, filters, explicit paging and
retained review state. See [the diagnostics receipt](FRONTEND_MILESTONE8B.md).
**8C merged in [PR #15](https://github.com/danielpan01/CodeImpact/pull/15)**, with
[post-merge CI passing](https://github.com/danielpan01/CodeImpact/actions/runs/43808633061):
16 canonical image comparisons and 48 rendered WCAG A/AA scans. See the
[gate receipt](FRONTEND_MILESTONE8C.md). Milestone 7 now adds explicit discovery-scope
communication while preserving these gates and all original screenshots.
Two new expected images replace active empty/zero-discovery captures; the old files
are retained. [Scope, review evidence and results](TEST_DISCOVERY.md) explain the
new positive `test.py` and authored zero-discovery browser cases. Milestone 9A is next.

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

**Owner direction, November 15: make the interface feel less generic and less
AI-generated, with rounder buttons and more visual character.** The foundation is
refined in merged milestone 8A. The direction below records the starting design
brief; milestone 8B carries these styles into the diagnostics workflow.

Aim for a carefully designed developer workbench: soft controls, confident type,
clear surface depth and a recognizable CodeImpact identity. Keep the warm light
canvas and graphite dark theme, then give navigation, actions, results and evidence
distinct visual roles. Use cobalt deliberately for the primary action and selected
path; let quieter tinted surfaces connect related information. Semantic
change/evidence colors must work in both themes with text or shape cues.

| Element | Direction |
| --- | --- |
| Buttons and inputs | Replace the current 6 px control corners with shared 10–12 px radii as the starting target. Give primary actions a confident filled treatment, secondary actions a quieter surface, and tertiary actions a clear text treatment. Keep touch targets at least 44 px |
| Panels and badges | Start with 14–16 px outer panel corners and 6–8 px compact badges; use fully rounded pills selectively for filters. Keep dense code and list interiors aligned and compact |
| Surfaces | Warm page canvas, crisp results surface and a subtly tinted inspector; use fine dividers within lists and restrained elevation for floating controls. Reduce repeated nested borders and identical boxes |
| Typography | A distinctive, compact wordmark/header; stronger section titles; 14–16 px primary UI text; readable secondary labels. Reserve monospace for code, paths and revisions, and replace unnecessary uppercase labels with sentence case |
| Spacing | Shared 4/8 px spacing scale with deliberate grouping: closer related controls, more separation between tasks. Preserve the phone first-result layout while giving desktop content room |
| Color | More purposeful contrast between navigation, canvas, results and selected evidence. Cobalt connects actions and dependency paths; coral/amber/teal remain meaningful change states. Validate the palette independently in both themes |
| Identity and icons | Refine the CodeImpact wordmark and a small connected-node motif derived from its dependency graph. Use one consistent SVG icon family, paired with clear labels; carry the same motif into useful empty/demo states |
| Graph and evidence | Give the dependency trail a clear visual rhythm, coordinated node styling and readable revision badges. The selected path should be easy to follow across Map, Tests and the inspector |
| Motion | Brief, consistent hover/press/selection transitions, starting around 120–180 ms. Keep controls stable while interacting and respect reduced-motion preferences |
| Fonts/assets | Reliable system or locally bundled licensed fonts; no mandatory external font request for the primary experience |

These are starting design decisions to refine against real screens and contrast
checks. Rounded corners alone do not complete the refresh: typography, composition,
surface contrast and interaction states must improve together. Avoid a grid of
identical metric cards, excessive pill badges, decorative gradient blobs, oversized
marketing headings or a border around every fragment. Add character through the
actual code-review workflow; do not invent activity or product capabilities.

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

**Merged in PR #7.** The application now has shared semantic light-theme tokens,
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

**Merged in PR #8.** Tests has literal test/file search, explanation categories,
deterministic sorts, filtered/total counts and reset/reveal-selection actions. Map
focuses exact evidence paths, retains module fallback and revision context, jumps to
individual symbols at readable scale, fits/resets and preserves pan/zoom across views.
The inspector numbers trail steps and opens a focused map without discarding expanded
source locations. Changes retains file/symbol navigation and adds safe lexical source
coloring within the existing preview limits. Reports/exports and all analyzer data
remain unchanged. No dependencies or virtualization were added after local rendering
observations on the 150-recommendation, 585-visible-node LFU case.

Original milestone scope (delivered):

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

**Merged in PR #9 after CI passed.** Both themes cover inputs, Tests, Map, source and revision
evidence with shared tokens and a saved appearance preference. Responsive focus,
touch targets, Escape/back navigation and graph framing have cross-browser coverage.
Error recovery distinguishes invalid input, limits, network and unreadable responses;
retry preserves the submitted snapshot in memory. The README and usage walkthrough
have current screenshots. Analyzer behavior and all baseline outputs remain unchanged.
The separate developer walkthrough was explicitly waived by the owner and was not
performed; agent browser/visual checks do not substitute for a user study.

Original milestone scope (delivered, except the waived walkthrough):

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
`make evaluate-real-v2`, `make evaluate-real-v3`, `make verify-pilot`, and
`cd web && npm run test:e2e`. Add coverage for behavior
introduced by that slice. Preserve the existing desktop and mobile tests; test new
themes and responsive interactions explicitly as they arrive.

Compare stable report results to the merged reference. Analyzer source, scores,
selected IDs, graph direction, revision evidence, input limits, all corpus data and
all historical v2/v3 measurements stay unchanged during frontend work. Document
actual outcomes and inspect screenshots; green tests alone do not establish good
visual design. Keep changes unstaged/uncommitted for the owner to review and publish.

## Subsequent roadmap

The original follow-up work has advanced: bounded mapping refinement merged in
PR #10, fresh v3 evaluation in PR #11, and local deployment preparation in PR #12.
Use the active [build plan](BUILD_PLAN.md) for milestones 7–13. The frontend's next
substantial work is milestone 8: visual character, large-report diagnostics and
quality gates, in that order. It can proceed independently of analyzer milestone 7.

The 284 v2 false positives present at frontend release became 273 after mapping
refinement. V3 records 43 more false positives and 30 definitions outside discovery;
the two authored misses and independent label review remain open. This UI review
does not change those analyzer measurements.

## Ongoing professional UI quality

The November 15 review confirms the functional visual foundation is implemented:
shared light and dark tokens, coherent typography, aligned controls, coordinated
evidence and responsive layouts. The owner's subsequent feedback makes a more
distinctive, less bland appearance an explicit next deliverable. The local refinement
reduces excess phone spacing and removes the redundant phone-only table heading.
It keeps labels, scores, export disclosure,
44-pixel controls and all report data. A regression verifies the first complete demo
recommendation without scrolling at 360×844 and 390×844 in both themes across all
five browser configurations. This is not a guarantee that arbitrarily long test
names or real PR metadata fit the same first screen.

### Milestone 8A: visual character and component refinement — merged in PR #13

1. Capture the current entry screen, loaded Tests workspace, evidence, Map and
   Changes with the demo and a large pinned report. Apply the visual direction
   above to the working application, starting with shared controls and surfaces.
2. Round buttons and inputs consistently, improve primary/secondary action
   hierarchy, and refine the wordmark, typography and selected states. Carry these
   decisions through theme, export, graph and source-navigation controls.
3. Recompose the entry screen around one clear input task with supporting demo and
   upload options. Give the loaded workspace a stronger identity through its
   compact header, integrated summary, readable test rows and distinctive evidence
   trail. Keep useful content near the top on phones.
4. Finish the quiet states as carefully as the main screen: loading, no results,
   errors, disabled actions and empty evidence. Use specific, concise copy and
   small relevant SVG details where useful. Show only real progress and counts.
5. Inspect before/after screens at 1440×900, 1280×800, 768×1024, 390×844 and
   360×844 in both themes. Refine the result in the browser before recording new
   screenshot baselines; record actual owner feedback if it is provided.

Acceptance: the change is visibly broader than a radius adjustment. Buttons feel
consistent and rounded, primary actions are obvious, headings and surfaces create
a clear hierarchy, and CodeImpact has a recognizable identity across all three
views. Long names, code, semantic colors and evidence remain readable. Preserve
the existing first-result regression, keyboard/focus behavior, 44 px touch targets,
reduced-motion support and all report/export data. Include before/after evidence
and explain specific visual decisions; passing tests alone cannot demonstrate
that the result feels less generic.

### Milestone 8B: readable diagnostics — merged in PR #14

The working UI groups all original warning occurrences by supported category and
confirmed file, with full-text literal search, category/file filters where useful,
matching/total counts, expandable groups and 50-note pages. Unknown and ambiguous
formats stay in General / unclassified. Duplicates have distinct original-order
identities. Empty notes and no filter matches are distinct states. Controls and
expansion survive view navigation; a new report resets them. Exports are unchanged.
See [rules, screenshots and verification](FRONTEND_MILESTONE8B.md).

### Milestone 8C: regression protection — merged in PR #15

Sixteen reviewed screenshots now form failing comparison gates in a pinned Linux
ARM64/Ubuntu/Chromium/font environment. Forty-eight full-page axe scans cover both
themes and desktop/phone workflows. Explicit defect probes fail and recovery runs
pass; normal CI cannot create or update expected images. Small accessible-name,
region/group and attribution fixes preserve the 8A design and 8B data/behavior.
See [coverage, commands, artifacts and limitations](FRONTEND_MILESTONE8C.md).
Historical documentation images remain unchanged. Publication checks are recorded
in Actions separately from these local results. Neither establishes accessibility
certification or independent user review.

Maintain these standards in every future UI change:

- Prioritize the user's next action and the actual evidence. Use consistent token
  spacing, readable type, meaningful selected/focus states and complete labels.
- Keep the first useful result accessible; long names wrap without losing identity.
  Preserve sticky view navigation and the return path from evidence on phones.
- Keep semantic colors and shape/text cues consistent in both themes. New UI must
  pass contrast/focus checks and respect reduced motion; do not infer certification.
- Maintain the bounded desktop/phone screenshot matrix in the pinned environment;
  retain tablet and narrow-phone behavioral checks. Add a new image only for a
  demonstrated coverage gap. Keep failure artifacts and review intended diffs.
- Test the full report, empty/zero-discovery/error states, mixed/deleted evidence,
  long lists and the pilot access flow. Exports must preserve full underlying data.
- Make large diagnostics manageable through display-only grouping and filtering.
  The inspected Cachetools LFU report has 3,128 notes; individual entries must remain
  discoverable and exports unchanged in the 8B implementation.
- Measure real rendering bottlenecks before adopting virtualization or a new layout
  engine. Preserve stable symbol/edge identity and exact selected evidence paths.

The visual refresh and grouped diagnostics are merged. Milestone 8C now implements
pixel comparisons and scoped rendered-accessibility gates in CI and locally. Existing semantic
color, focus, theme, touch-target and cross-browser workflow checks are retained.
Some graph/clipped-content contrast checks still require manual assessment; no
comprehensive accessibility audit is claimed.
Agent visual inspection does not substitute for independent user feedback.
