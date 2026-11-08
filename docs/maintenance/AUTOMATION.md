# Daily project health automation

[Current report](daily-health.md) · [Workflow runs](https://github.com/danielpan01/CodeImpact/actions/workflows/daily-health.yml)

This workflow performs real, lightweight maintenance checks and commits a dated observation to the repository's default branch. The report is explicitly automated. It does not alter application behavior or dependency versions.

## Checks

Checks required repository files, documentation targets, Python source syntax, and live PyPI metadata for the pinned development environment. Does not execute analyzed repositories, change analyzer code or report schemas, modify dependencies, or claim full application or browser test coverage. Feature work remains separate from this generated maintenance report.

Configure the input files and external URLs in `.github/daily-health.json`. The collector uses Python's standard library and the Ubuntu runner; it installs no project dependencies. External HTTP requests have 15-second timeouts. A blocked or unreachable external service is labeled WARN/unverified, never healthy. Missing files, invalid Python/SVG, and checksum mismatches are failures: the workflow publishes the diagnostic report and then fails visibly.

## Schedule

GitHub checks four daytime slots in **America/New_York**: 9:17 a.m., 10:43 a.m., 12:29 p.m., and 2:11 p.m. A deterministic hash of the repository name and local calendar date selects a slot within alternating pairs of times, so adjacent dates choose different slots. This varies the selected time across dates and projects without spending runner minutes sleeping. The other three invocations only evaluate the selector and skip report generation.

Daylight saving time follows the named timezone. GitHub can delay or skip scheduled runs, so a contribution every calendar day is not guaranteed. Manual **Run workflow** on the default branch bypasses the slot selector and runs immediately. If today's results are unchanged, rerunning will not create another commit. Public-repository schedules may be disabled by GitHub after 60 days without repository activity.

## Attribution and publishing

Daniel is the authorized commit author using the existing GitHub-linked address `146807695+danielpan01@users.noreply.github.com`. `github-actions[bot]` is the committer; commit messages explicitly identify automated reports. Commits land on the default branch of this standalone repository and therefore meet GitHub's commit-attribution criteria. GitHub controls profile indexing, which can take up to 24 hours.

Only the report job receives `contents: write` through the automatic `GITHUB_TOKEN`; no personal access token or extra secret is required. It stages only `docs/maintenance/daily-health.md`, uses an ordinary fast-forward push, and will fail rather than overwrite a concurrent change. Rerun manually if a concurrent push rejects publication. The workflow is restricted to `danielpan01/CodeImpact` and the default branch so forks do not automatically publish under this identity. Schedule/manual triggers prevent report commits from recursively launching this workflow.

To pause: Actions → Daily project health → menu → Disable workflow. To remove: delete `.github/workflows/daily-health.yml`.

## Local verification

```bash
python3 -m unittest discover -s scripts -p 'test_daily_health.py' -v
python3 scripts/daily_health.py
```

The report uses the actual check date in New York. Same-day identical observations are stable; Git history retains prior dates. The collector does not claim model accuracy, scientific reproduction, full application tests, dependency compatibility, or vulnerability scanning.
