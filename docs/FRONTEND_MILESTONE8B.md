# Milestone 8B — readable, searchable analysis diagnostics

Implemented on November 15, 2026, from clean `main` at
`e7e4c37aa149381c3a92324040337ee50d5e7a00` (merged PR #13). There were no preexisting
uncommitted edits. Milestone 8A and its CI timeout correction are preserved. This
milestone adds no backend or report-schema changes,
dependencies, hosting, authentication, report storage or analyzer tuning.

## Working interface

Analysis scope & limitations retains its compact disclosure and always shows the
**total original note count**, even when its contents are closed or filtered.
Opening it reveals the static-analysis caveat, search, optional category/file filters,
matching/total counts and category/file disclosures. The caveat stays visible while
filtering: a missing dependency path does not establish safety, and the full suite
remains the gate. Fewer visible notes do not mean greater accuracy.

Small reports omit dropdowns that offer only one category/file choice. Search and
reset remain available. Empty warning arrays say “No analysis notes”; a filter with
no results says “No matching notes” and retains the original total. Known limitation
categories such as Parse failures and Conservative fallback remain explicit.

Search uses `trim().toLowerCase()` and literal substring matching against each
**complete original string**, before any group is collapsed or paginated. It does
not interpret regexes or split the query into tokens. Category and file filters
combine with search; dropdown counts describe the whole current report, not just
matches. Report-wide/unconfirmed-file notes have an explicit filter option.

- **Total notes:** every occurrence in the original `report.warnings` array.
- **Matching notes:** occurrences matching all active controls across all pages.
- **Group count:** matching / total occurrences in that category or category/file;
  when all match, the label is simply the total. This does not count distinct strings.
- **Page count:** the displayed range out of matching occurrences in that group.
- **Note number:** the original, one-based report-array position. Identical strings
  keep different zero-based occurrence IDs internally and remain separate entries.

Categories use the fixed order below. Confirmed files use locale-independent
code-point ordering, with report-wide entries first. Original array order is kept
within each category/file. Neither helper mutates the warning array or report.

An expanded file/report-wide group displays at most **50 complete notes per page**,
with explicit Previous/Next controls and a displayed range. No note text is clipped,
shortened or interpreted as HTML. Keyboard paging moves focus to the new list.
All entries remain reachable, including repeated messages and empty strings.
Search/filter/expansion/page state survives Tests → Map → Changes navigation and
closing/reopening diagnostics. Filter edits reset pages to the first match while
retaining disclosure choices; a new analysis resets all diagnostics state, including
the outer disclosure. Diagnostics never change test selection, graph content,
evidence, metrics or JSON exports.

## Conservative classification contract

`web/src/diagnostics.ts` is a presentation allowlist, based on the current producers
in `analyzer.py`, `selection.py` and `github.py`. It does not infer severity or
upgrade a fallback to a resolved dependency. Every row retains its exact raw text.

| Category, in display order | Supported full message format | File association |
| --- | --- | --- |
| Analysis scope | The exact existing static-analysis caveat; the exact risk-score caveat; `No Python files were found in the supported analysis scope.` | Report-wide |
| Analysis scope | `base` or `head`: `skipped N symlinks`, `submodules`, or `excluded Python files`, followed by the producer's parenthesized examples and final period; positive integer N | Always report-wide, even with a single example; multiple files are never forced into one file |
| Parse failures | `Cannot parse PATH: SyntaxError`, `ValueError`, or `RecursionError` | PATH must exactly match a report node path or source-file path |
| Unresolved imports | `Wildcard import is unresolved: PATH:LINE` | Confirmed PATH; positive safe-integer LINE syntax |
| Unresolved imports | `Wildcard local import is unresolved: SYMBOL` | Exact indexed function/test symbol and matching node path |
| Unresolved imports | `Ambiguous module import binding: SYMBOL: NAMES` or `Ambiguous or unsupported local import binding: SYMBOL: NAMES` | Exact module symbol for the first form, exact function/test symbol for the second; comma-space-separated Unicode identifier names |
| Unresolved calls | `Unresolved call NAME: PATH:LINE` | NAME is an identifier or dotted identifier chain; confirmed PATH and positive safe-integer LINE syntax |
| Dynamic calls | `Dynamic call: PATH:LINE` | Confirmed PATH and positive safe-integer LINE syntax |
| Conservative fallback | `Conservative fallback retained: unmodeled protocol change in PATH` | Confirmed PATH |
| Conservative fallback | `Conservative fallback retained: reference budget exceeded for SYMBOL` | Exact indexed symbol and matching node path |
| General / unclassified | Everything else, including unfamiliar prefixes, unsupported exception types, malformed suffixes, missing/ambiguous file or symbol references, and multiline messages | No confirmed file |

The parser does not infer a file from arbitrary substrings or choose a file when a
message mentions several. Symbol matching uses the report's indexed identity and
path, not a guessed split. These are grouping labels, not new report facts. Backend
warnings may already have been deduplicated by their producer; the UI preserves
**exactly the occurrences it receives**, without inventing missing occurrences.

No warning-derived location links are created: a string does not establish which
revision or available source preview to open. Locations remain verbatim text;
existing evidence/source navigation is unchanged. Future producers fall back to
General / unclassified until their exact formats and identity checks are documented
and regression-tested. There is no generic severity parser or external auto-linking.

## Before/after evidence and observed scale

Fresh API analysis of the pinned Cachetools LFU snapshot confirmed **3,128 notes**
and **139 recommendations**. Its notes group into 2 analysis-scope entries,
3 import entries, 2,988 unresolved calls and 135 dynamic calls. No entries are lost
or unclassified in that specific report. The demo has 2 analysis-scope notes.

| View | Before | After |
| --- | --- | --- |
| Large LFU report, desktop light | [Flat list](media/milestone8b/before-desktop-light-large-expanded.png) | [Category overview](media/milestone8b/after-desktop-light-large-overview.png) |
| Demo, phone dark | [Original notes](media/milestone8b/before-phone-dark-demo-expanded.png) | [Complete grouped notes](media/milestone8b/after-phone-dark-demo-expanded.png) |

Additional inspected captures: [desktop dark filtered imports](media/milestone8b/after-desktop-dark-large-expanded.png),
[tablet dark file disclosure](media/milestone8b/after-tablet-dark-large-expanded.png),
[unknown multiline text on phone](media/milestone8b/after-phone-light-unknown.png),
[no matches on phone](media/milestone8b/after-phone-dark-no-match.png), and
[empty diagnostics](media/milestone8b/after-desktop-light-empty.png).
The unknown/empty/no-match examples use synthetic display-test reports; demo/LFU
captures use real API analysis of trusted local inputs, with upstream source read
only as data.

Before, the open LFU diagnostics measured 90,210 CSS pixels tall at 1440×900 and
115,312 pixels at 390×844. The final **category overview** measures 543 and 865 pixels
respectively; expanding files adds their full note page. This compares browsing
surfaces, not reduced data. Across the final local capture matrix, classification
plus grouping took about 1–3 ms for LFU (20 iterations per capture in Node on this
Mac); these are local observations, not a browser latency SLO or capacity benchmark.
There was no demonstrated need for virtualization or a new dependency. Paging
addresses the observed navigation length and bounds mounted note entries.

The visual review covered 1440×900, 768×1024, 390×844 and 360×844, both themes, demo
and LFU, plus empty/unknown/long/no-match states and reduced-motion captures. All
16 demo/LFU size/theme/report records and 12 synthetic edge-state records have no
page overflow or JavaScript errors. Stable demo/LFU reports matched the before
captures exactly after excluding only `stats.elapsed_ms`. Screenshots were inspected;
small-report controls were simplified and sticky-navigation scroll clearance added.
The 8A colors, shared radii, visible focus and phone first-result layout are retained.

## Verification and boundaries

The first browser regression failed against the flat-list UI because diagnostics
search did not exist. Pure helper coverage exercises exact categories/file checks,
unknown/malformed/ambiguous formats, duplicates, immutability, deterministic order,
literal punctuation/regex-like queries, Unicode, long/multiline messages and empty
arrays. Browser coverage checks combined controls/counts, paging beyond the first
50 notes, keyboard/focus/touch sizes, retained view state, new-report reset, safe
text rendering, no matches/reset and exact full JSON exports, including real LFU.

Initial browser runs caught dropdown accessible names that included option text and
WebKit rendering selects below 44 px. Explicit labels and 48 px select heights fix
those failures without relaxing assertions. The final focused diagnostics run
passed **40 checks** across the five existing browser projects; the full suite
passed **248 checks**. See [the validation record](VALIDATION.md) for all required
commands, expected skips and preservation receipts.

This is agent visual/keyboard inspection and existing browser testing, not independent
usability review, a screen-reader study or accessibility certification. File links,
severity inference and cross-revision guessing are deliberately absent. Very long
notes still require vertical reading; all raw content remains available. Milestone
**8C: pinned screenshot-comparison and rendered-accessibility gates** is the next
frontend step. Analyzer milestone 7, source-label review, human pilot and live
hosting remain separate; the latter two remain owner-deferred.

## Local preview

From `/Users/danny/Documents/ChatGPT/CodeImpact`:

```sh
CODEIMPACT_WEB_PORT=5183 CODEIMPACT_API_PORT=8013 make dev
```

Open http://127.0.0.1:5183, choose **Load demo**, then open **Analysis scope &
limitations** below the workspace. For LFU, upload the `request` object from
`corpus/real-v2/cases/cachetools_lfu.json` as a snapshot JSON file (the corpus wrapper
itself is not an upload). No upstream checkout or dependency installation is needed.
Stop both local services with Ctrl-C. Live hosting is deferred.
