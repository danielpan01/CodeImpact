"""Collect a small, explicitly scoped maintenance report without running the app."""

import ast
import hashlib
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


def cell(value):
    return str(value).replace("|", "&#124;").replace("\n", " ").replace("\r", " ")


def local_path(root, relative):
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError("path is outside the repository")
    return path


def fetch(url, *, as_json=False):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "DailyProjectHealth/1.0",
            "Accept": "application/json" if as_json else "*/*",
        },
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        if as_json:
            return json.load(response)
        # Opening the response checks HTTP reachability without downloading a dataset.
        return response.status


def markdown_targets(text):
    # Scope: inline Markdown links/images and HTML src/href attributes, not anchors.
    text = re.sub(r"```.*?```|~~~.*?~~~", "", text, flags=re.S)
    text = re.sub(r"`[^`\n]*`", "", text)
    targets = re.findall(r"\]\(<?([^\s)>]+)>?(?:\s+\"[^\"]*\")?\)", text)
    targets += re.findall(r"(?:src|href)=[\"']([^\"']+)[\"']", text)
    return sorted(set(targets))


def collect(root, config, day, fetcher=fetch):
    rows = []

    def add(check, status, detail):
        rows.append((check, status, detail))

    for name in config["files"]:
        path = local_path(root, name)
        add(
            name,
            "PASS" if path.is_file() and path.stat().st_size else "FAIL",
            "Required file exists and is nonempty"
            if path.is_file() and path.stat().st_size
            else "Required file missing or empty",
        )

    for name in config.get("markdown", []):
        path = local_path(root, name)
        if not path.is_file():
            add(f"Links in {name}", "FAIL", "Document is missing")
            continue
        for target in markdown_targets(path.read_text(encoding="utf-8")):
            parsed = urllib.parse.urlsplit(target)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            relative = path.parent.relative_to(root) / urllib.parse.unquote(parsed.path)
            try:
                exists = local_path(root, relative).exists()
                add(
                    f"{name}: {target}",
                    "PASS" if exists else "FAIL",
                    "Local target exists; fragment not checked"
                    if exists
                    else "Local target missing",
                )
            except ValueError:
                add(f"{name}: {target}", "FAIL", "Target escapes repository")

    for name in config.get("python", []):
        try:
            ast.parse(local_path(root, name).read_text(encoding="utf-8"), filename=name)
            add(
                f"Python syntax: {name}",
                "PASS",
                "Parsed without importing or executing the application",
            )
        except (OSError, SyntaxError, UnicodeError) as error:
            add(f"Python syntax: {name}", "FAIL", type(error).__name__)

    for name in config.get("svg", []):
        try:
            tag = ET.parse(local_path(root, name)).getroot().tag
            valid = tag in ("svg", "{http://www.w3.org/2000/svg}svg")
            add(
                f"SVG: {name}",
                "PASS" if valid else "FAIL",
                "SVG root and XML structure checked" if valid else "Root is not SVG",
            )
        except (OSError, ET.ParseError) as error:
            add(f"SVG: {name}", "FAIL", type(error).__name__)

    for name, expected in config.get("sha256", {}).items():
        path = local_path(root, name)
        actual = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else "missing"
        add(f"SHA-256: {name}", "PASS" if actual == expected else "FAIL", actual)

    for url in config.get("urls", []):
        try:
            status = fetcher(url)
            add(url, "PASS" if 200 <= status < 300 else "WARN", f"HTTP {status}; reachability only")
        except (urllib.error.URLError, OSError, TimeoutError, ValueError) as error:
            detail = (
                f"HTTP {error.code}"
                if isinstance(error, urllib.error.HTTPError)
                else type(error).__name__
            )
            add(url, "WARN", f"Unverified: {detail}; may be transient or automated-access blocking")

    dependencies = []
    requirements = config.get("requirements")
    if requirements:
        for raw in local_path(root, requirements).read_text(encoding="utf-8").splitlines():
            requirement = raw.partition("#")[0].strip()
            if not requirement:
                continue
            # Deliberately accept simple version constraints only. Fail visibly on other formats.
            match = re.fullmatch(
                r"([A-Za-z0-9][A-Za-z0-9._-]*)\s*([~=!<>][A-Za-z0-9.,*<>=!~+ -]+)", requirement
            )
            if not match:
                add("Dependency declaration", "FAIL", f"Unsupported requirement: {requirement}")
                continue
            name, constraint = match.groups()
            try:
                data = fetcher(
                    f"https://pypi.org/pypi/{urllib.parse.quote(name, safe='')}/json", as_json=True
                )
                info = data["info"]
                dependencies.append(
                    (
                        name,
                        constraint.strip(),
                        info["version"],
                        info.get("requires_python") or "Not declared",
                    )
                )
            except (
                urllib.error.URLError,
                OSError,
                TimeoutError,
                ValueError,
                KeyError,
                TypeError,
            ) as error:
                dependencies.append((name, constraint.strip(), "Unverified", "Unverified"))
                add(f"PyPI: {name}", "WARN", f"Metadata unavailable: {type(error).__name__}")

    failures = sum(status == "FAIL" for _, status, _ in rows)
    warnings = sum(status == "WARN" for _, status, _ in rows)
    lines = [
        f"# {config['project']} daily maintenance report",
        "",
        f"Checked on **{day}** (America/New_York).",
        "",
        (
            "Generated automatically by the daily project health workflow. This is a "
            "maintenance observation, not a new research result or application test run."
        ),
        "",
        f"**Summary:** {failures} failed checks; {warnings} unverified external checks.",
        "",
        "| Check | Status | Observation |",
        "| --- | --- | --- |",
        *["| " + " | ".join(cell(value) for value in row) + " |" for row in rows],
        "",
    ]
    if dependencies:
        lines += [
            "## Dependency release watch",
            "",
            (
                "Live PyPI metadata compared alongside the declared constraints. The "
                "reported latest release may be outside those constraints. This does not "
                "resolve installed versions, test compatibility, audit vulnerabilities, "
                "or upgrade packages."
            ),
            "",
            "| Package | Repository constraint | PyPI latest | Latest release requires Python |",
            "| --- | --- | --- | --- |",
            *["| " + " | ".join(cell(value) for value in row) + " |" for row in dependencies],
            "",
        ]
    lines += [
        "## Scope and history",
        "",
        config["scope"],
        "",
        (
            "Local link checks cover inline Markdown and HTML file targets; heading "
            "fragments and reference-style links are not validated. External checks "
            "verify HTTP responses only, not page content. WARN means unverified, not a "
            "confirmed broken link."
        ),
        "",
        (
            "The current report is replaced after each check; Git history preserves "
            "earlier observations. Same-day reruns with identical results produce no new "
            "commit."
        ),
        "",
        "[Workflow and attribution details](AUTOMATION.md)",
        "",
    ]
    return "\n".join(lines), bool(failures)


def main():
    root = Path(__file__).resolve().parents[1]
    config = json.loads((root / ".github/daily-health.json").read_text(encoding="utf-8"))
    day = datetime.now(ZoneInfo("America/New_York")).date().isoformat()
    report, failed = collect(root, config, day)
    output = root / "docs/maintenance/daily-health.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report, encoding="utf-8")
    print(report)
    return int(failed)


if __name__ == "__main__":
    sys.exit(main())
