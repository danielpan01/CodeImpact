# Milestone 8A — visual character and component refinement

Implemented locally on November 15, 2026, on top of PR #12 and the existing
uncommitted roadmap/phone-spacing review. Publication remains the owner's task.
This is a presentation change to the working React application. Analyzer behavior,
API/report contracts, evidence paths, source limits and evaluation baselines are
unchanged. No dependencies, hosting or authentication features were added.

## Visual decisions

Before inspection found a single undifferentiated entry card, identical results and
inspector surfaces, small square controls, and uppercase supporting labels that
competed with test names. The change carries one direction across the workflow:

- A compact connected-node mark and a two-weight CodeImpact wordmark. The entry
  screen separates workflow orientation from the primary PR form, with snapshot
  upload and demo actions below it. On smaller screens it becomes one column.
- Shared 12 px control corners, 16 px outer panels and 7 px compact badges. Primary
  actions retain cobalt; secondary actions use quiet outlines; tertiary actions
  gain a restrained hover surface. Buttons, graph controls and inputs keep at
  least 44 px targets; the pilot key field uses 48 px.
- Warm canvas/results surfaces, a separate slate evidence surface, graphite dark
  theme and fine dividers/shadows. Navigation is one coordinated control group.
  The redundant results-heading count was removed; summary, view and visible-result
  counts remain. Tablet summaries use two columns to accommodate large values.
- Stronger page and section headings, sentence-case supporting labels, and larger
  desktop test identifiers. System fonts serve interface text; code/paths remain
  monospace. The phone spacing regression and complete first demo row are retained.
- Numbered connected dependency steps, a square changed endpoint, explicit revision
  labels and coordinated graph/source colors. Before/After source headings include
  direction icons; removed symbols still have their text labels and dashed graph
  outline. Nothing promotes conservative fallback to resolved evidence.
- Consistent empty/loading/error details, visible focus, pressed/hover feedback and
  150 ms color/border/shadow transitions. Reduced motion disables transitions;
  feedback changes no geometry.

## Before and after

These are captures of running applications using real demo/pinned snapshot inputs,
not mockups or comparison-test baselines. Before images include the preexisting
phone-spacing fix. Timing values are real per-request measurements and vary.

| View | Before | After |
| --- | --- | --- |
| Entry, 1440×900 light | [Before](media/milestone8a/before-desktop-light-entry.png) | [After](media/milestone8a/after-desktop-light-entry.png) |
| Tests, 1440×900 light | [Before](media/milestone8a/before-desktop-light-tests.png) | [After](media/milestone8a/after-desktop-light-tests.png) |
| Tests, 1440×900 dark | [Before](media/milestone8a/before-desktop-dark-tests.png) | [After](media/milestone8a/after-desktop-dark-tests.png) |
| Tests, 390×844 light | [Before](media/milestone8a/before-phone-light-tests.png) | [After](media/milestone8a/after-phone-light-tests.png) |

Additional reviewed views: [focused Map](media/milestone8a/after-desktop-dark-map.png),
[Changes](media/milestone8a/after-laptop-light-changes.png),
[phone evidence](media/milestone8a/after-phone-dark-evidence.png),
[large pinned Cachetools report on tablet](media/milestone8a/after-tablet-dark-large-tests.png).

## Inspection and regression coverage

Before/after capture matrix: **1440×900, 1280×800, 768×1024, 390×844 and 360×844**,
in light and dark, with entry, demo Tests/evidence/Map/Changes and uploaded pinned
Cachetools LFU Tests/evidence/Map/Changes. There was no page-level horizontal
overflow or JavaScript page error in these captures. The 139-recommendation LFU
report retains its 3,128 raw notes; grouping is future milestone 8B.

Further inspected captures cover pinned Slugify reports, deleted and mixed-revision
paths, empty recommendations, Ordered Set zero discovery, long names/paths and code
scrolling, loading and invalid input. Existing browser checks exercise PR ingestion
through the test transport, retrying the same request, search/filter/sort/counts,
selection/expansion persistence, map fit/reset/pan/zoom, source clipping, full JSON
exports and source disclosure, Back/Escape/focus restoration and the built pilot.
No additional live GitHub import was required for this display-only milestone.

Added browser coverage checks entry keyboard order/close focus at all five sizes,
desktop target sizes across all three views and reduced-motion source focus. The
existing phone first-result test is unchanged. Contrast checks now also include
ink, supporting text and accent against the inspector surface. WebKit uses its
native Option-Tab navigation to include buttons on macOS. This is targeted testing,
not a comprehensive rendered-accessibility audit or certification.

Zoom checks used a 720×450 CSS viewport at 2× pixel density (200%-equivalent reflow
of a 1440×900 display), plus 2× page-scale zoom. Keyboard navigation into evidence
and source remained usable with no horizontal page overflow in either theme.
Native browser-menu zoom was not independently certified. No independent developer
usability review, screen-reader study or owner design approval is claimed.

The first full browser run passed 173 checks and caught Firefox reporting the pilot
field at 43.9999847 px. The field was enlarged to 48 px without relaxing the test;
the focused pilot rerun passed all 10 checks. The final full run passed **174 checks**.
The new keyboard check initially used Tab on WebKit; correcting the test to its
native Option-Tab behavior made all 10 new focused checks pass.

Final command results and preservation receipts are recorded in [VALIDATION.md](VALIDATION.md).
Local evidence lives in ignored `reports/milestone8a-before/`, `milestone8a-after/`,
`milestone8a-*.log` and `milestone8a-preservation.json`. Capture scripts there use the
existing Playwright installation; no screenshot-comparison pipeline was introduced.

## Preview and remaining scope

From the repository root:

```sh
CODEIMPACT_WEB_PORT=5181 CODEIMPACT_API_PORT=8011 make dev
```

Open http://127.0.0.1:5181 and choose **Load demo**. Default `make dev` still uses
5173/8000. These alternative ports avoid unrelated existing local services. Stop
both services with Ctrl-C. If a development server shows stale styles, restart it
and reload; final inspection used a fresh server. The pilot deployment remains local.

Dense whole-repository maps still need focus/zoom; very long identifiers wrap and
source panes scroll. The first-row guarantee applies to the fixed demo at the
specified phone sizes, not arbitrary report labels. Raw diagnostics remain long.
The next frontend slice is **8B: diagnostics grouping**, then **8C: pinned visual
comparison and rendered-accessibility checks**. Analyzer milestone 7 remains a
separate task. Human pilot, label review and live-hosting decisions remain unchanged.
