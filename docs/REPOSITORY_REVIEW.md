# Repository and UI review — November 15, 2026

## Conclusion and scope

The repository matches the **implemented technical scope** of roadmap milestones
1–6. The three frontend milestones, bounded mapping refinement, v3 evaluation and
local pilot service are present. Live hosting and the human pilot remain explicitly
owner-deferred. Independent source-label review is pending. Those are separate
release gates, not completed features or failing automated checks.

Reviewed reference: `8d9661f1640619741ed25e570911bea838198666`, merged in
[PR #12](https://github.com/danielpan01/CodeImpact/pull/12). GitHub `main` matched the
local reference and its [post-merge CI](https://github.com/danielpan01/CodeImpact/actions/runs/43778102565)
completed successfully during this review. The working tree was clean at the start.
The new documentation and phone-layout refinement below are local changes, not part
of that remote CI result. No commit, push or PR was made for this review.

Review covered the current README, architecture, active and frontend roadmaps,
evaluation/discovery results, deployment boundaries, CI commands, UI components and
styles, plus live visual inspection and the automated suites. It is not a complete
security audit, independent label review, usability study or accessibility certification.

## Roadmap reconciliation

| Area | Present in the repository | Finding |
| --- | --- | --- |
| Analysis engine and evidence | AST comparison, stable IDs, typed edges, deleted/base/head evidence and bounded resolution/filtering | Matches documented scope; static-analysis limitations remain |
| Frontend foundation | Shared tokens, light/dark themes, compact workspace, public PR/demo/upload/export workflows | Implemented; inspected desktop and phone states are visually coherent |
| Review interactions | Search/filter/sort, path-focused Map, source coloring, coordinated evidence and phone back navigation | Implemented; large-case and cross-browser regressions pass |
| Evaluation | 25 authored cases plus three six-case real datasets, frozen source/provenance and explicit baselines | All four replays match; labels are draft and discovery coverage is incomplete |
| Local pilot | Built single-origin server, access key, bounded workers, admission/deadline controls and readiness | Real local verification passes; no live deployment is claimed |
| Design quality assurance | Theme/token contrast, focus/touch/recovery tests and saved screenshots | Useful coverage; no screenshot-diff gate or comprehensive rendered-accessibility scan yet |
| Human and hosted validation | Prepared walkthrough/review packs and deployment guide | Human pilot/live host deferred; source-label review still pending |

The former frontend follow-up list still described mapping, v3 and worker deployment
as future work. It now points to the current plan. Its check list now includes v3
and built-pilot verification. The build plan records PR #12 as merged and defines
milestones 7–13 rather than stopping at the original six.

## Findings and priorities

1. **Test-discovery coverage is the next analyzer priority.** In v3, 30 source
   definitions in `test.py` sit outside the current filename rule, including a
   direct `test_pop` call. They are correctly shown separately in evaluation and
   the empty-discovery UI, but they are not covered by the reported recall. Define
   bounded discovery support and preserve the original denominator/result in a new
   versioned measurement; do not silently broaden discovery or relabel the corpus.
2. **Keep improving recommendation precision in separate scopes.** V2 retains
   273 false positives: 125 LFU, 31 descriptor and 117 Slugify case/test pairs.
   V3 retains 43: 37 Inflection and six ISO validator pairs. The two authored
   fixture/runtime-import misses also remain. Passing replay intentionally preserves
   these results; these counts are not independent runtime failures or production
   accuracy. Prioritize one evidenced mechanism per milestone.
3. **Make large diagnostics easier to review.** The inspected LFU report exposes
   3,128 notes. Grouping/filtering these in the UI would improve navigation while
   retaining every raw warning and original export. This is planned, not implemented
   as part of the current review.
4. **Protect the professional visual baseline.** Screenshot artifacts and behavioral
   checks exist, but no `toHaveScreenshot` comparison gate is configured. Add stable
   visual baselines in a pinned environment and rendered-accessibility checks, while
   keeping human review status explicit.
5. **Keep local readiness distinct from hosting.** The pilot uses a shared key and
   process-local quotas. Its workers have resource/process limits, not an OS security
   sandbox. Deployment needs exact-host verification and authorization when the owner
   resumes that work; no database or queue is justified merely by this roadmap.

## Professional UI review and implemented refinement

The existing visual design uses restrained blue actions, neutral surfaces, consistent
system typography, clear selection states and readable light/dark themes. Desktop
Tests, focused Map and before/after Changes were inspected. Tablet layout was checked
at 768×1024; phone evidence navigation and the 139-recommendation Cachetools case
were also inspected. Observed desktop/tablet/phone states did not overflow the page.
The browser console reported no JavaScript errors in the inspected session.

One concrete usability problem was reproduced before changing CSS: the first demo
recommendation was mostly below the initial phone viewport. The new failing browser
test observed only about 6% of that row at 360×844. The refinement reduces excess
spacing in the phone header/summary/panels and removes the redundant mobile table
heading. Every control, label, score, warning, export disclosure and report value is
retained; control hit areas remain at least 44 px under the existing touch rules.

The new test verifies the entire first demo recommendation without scrolling at
360×844 and 390×844 in both themes, across Chromium desktop/phone, Firefox, WebKit
desktop and WebKit phone. All five configurations passed. Live inspection at 390×844
showed the first row bottom move from approximately 896 px to 780 px. This is an
observed fixed-demo layout improvement, not a claim that long real PR metadata or
every test name fits in one screen.

No JavaScript behavior, dependencies, report contracts, backend source or corpus
data changed. The existing design remains the baseline; milestone 8 defines the next
professional UI work instead of repeating the completed redesign.

## Observed verification

| Check | Result |
| --- | --- |
| `make check` | Ruff lint/format, strict mypy, **810 Python tests passed**, one expected Linux-only skip, TypeScript/Vite build passed |
| `make evaluate` | Baseline matches: 23 TP / 0 FP / 2 FN / 32 TN; two uncertain recommendations |
| `make evaluate-real` | Baseline matches: 45 TP / 0 FP / 0 FN / 123 TN; 11/33 uncertain selected |
| `make evaluate-real-v2` | Baseline matches: 109 TP / 273 FP / 0 FN / 177 TN; 395/581 selected, 13/22 uncertain selected |
| `make evaluate-real-v3` | Baseline matches: 41 TP / 43 FP / 0 FN / 6 TN; 84/90 discovered selected, 30 outside discovery |
| `make verify-pilot` | Readiness, built assets, public demo, access rejection, exact frozen authorized report and no report storage passed |
| `npm run test:e2e` | **164 passed**, including the new phone-layout check in all five browser configurations; final CSS rebuilt by the suite |
| `npm run format:check` | Passed |
| Preservation | All 106 corpus files, 21 backend source files, two benchmark receipts and ten existing report artifacts byte-identical to the pre-review manifest |

The existing Starlette/httpx deprecation and Node color-environment notices remain
non-failing. Linux's address-space integration test is skipped locally on macOS;
the merged-commit Linux CI passed. The current local review changes have not run
remote CI. Full checks cover behavior, not all possible source dependencies.

Local evidence is ignored under `reports/`: `repository-review-{check,evaluations,
pilot,browser,mobile-red,mobile-green}.log`, `repository-review-before.json`, and
`review-{desktop-light,desktop-dark,desktop-changes,desktop-final,tablet-light,
phone-before,phone-after}.jpg`. The review used fresh development servers on
ports 5180/8010 because an older service already occupied port 8000; no unrelated
service was stopped. Reload after restarting the review server to avoid stale Vite
styles when inspecting the refinement.

## Next work

The [active build plan](BUILD_PLAN.md) gives the ordered milestones, acceptance
criteria and decision gates. Start with bounded discovery coverage; UI quality gates
and diagnostics can proceed alongside source-label review. Keep future fallback
work isolated, reserve fresh evaluation cases before tuning, and keep the deferred
human pilot and live hosting explicit. All review edits remain unstaged/uncommitted.
