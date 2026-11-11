import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from codeimpact.cli import read_snapshot, revision


def test_cli_demo_json_and_snapshots():
    output = subprocess.check_output([sys.executable, "-m", "codeimpact.cli", "--demo"])
    report = json.loads(output)
    assert len(report["recommendations"]) == 3
    assert report["schema_version"] == "2.0"
    assert "0.10" in report["source_files"][0]["before"]["text"]
    assert "0.15" in report["source_files"][0]["after"]["text"]
    output = subprocess.check_output(
        [sys.executable, "-m", "codeimpact.cli", "--demo", "--snapshots"]
    )
    assert "base" in json.loads(output)


def test_real_git_comparison_uses_merge_base_and_skips_symlinks(tmp_path: Path):
    # Synthetic commits live only in pytest's temporary fixture repository.
    env = os.environ | {
        "GIT_AUTHOR_NAME": "CodeImpact Test Fixture",
        "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
        "GIT_COMMITTER_NAME": "CodeImpact Test Fixture",
        "GIT_COMMITTER_EMAIL": "fixture@example.invalid",
    }

    def git(*args: str) -> str:
        return (
            subprocess.check_output(["git", "-C", str(tmp_path), *args], env=env).decode().strip()
        )

    git("init", "-b", "main")
    (tmp_path / "a.py").write_text("def f(): return 1\n")
    (tmp_path / "test_a.py").write_text("from a import f\ndef test_f(): assert f() == 1\n")
    (tmp_path / "link.py").symlink_to("a.py")
    git("add", ".")
    git("commit", "-m", "fixture base")
    git("checkout", "-b", "feature")
    (tmp_path / "a.py").write_text("def f(): return 2\n")
    git("add", ".")
    git("commit", "-m", "fixture feature")
    head = revision(tmp_path, "HEAD")
    assert "link.py" not in read_snapshot(tmp_path, head).files
    git("checkout", "main")
    (tmp_path / "unrelated.py").write_text("def unrelated(): return 4\n")
    git("add", ".")
    git("commit", "-m", "fixture main divergence")
    output = subprocess.check_output(
        [
            sys.executable,
            "-m",
            "codeimpact.cli",
            "--repo",
            str(tmp_path),
            "--base",
            "main",
            "--head",
            "feature",
        ]
    )
    report = json.loads(output)
    assert report["changed"] == ["a.py::<module>", "a.py::f"]
    assert report["recommendations"][0]["symbol"] == "test_a.py::test_f"
    assert [f["path"] for f in report["source_files"]] == ["a.py"]
    assert report["source_files"][0]["before"]["text"] == "def f(): return 1\n"
    assert report["source_files"][0]["after"]["text"] == "def f(): return 2\n"
    assert git("branch", "--show-current") == "main"
    with pytest.raises(subprocess.CalledProcessError):
        revision(tmp_path, "--help")
