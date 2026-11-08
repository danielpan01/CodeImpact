import tempfile
import unittest
import urllib.error
from pathlib import Path

from daily_health import collect, local_path, markdown_targets


class DailyHealthTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name).resolve()
        self.config = {"project": "Fixture", "files": [], "scope": "Test fixture"}

    def test_missing_required_file_is_failure(self):
        self.config["files"] = ["missing.png"]
        report, failed = collect(self.root, self.config, "2026-11-08")
        self.assertTrue(failed)
        self.assertIn("Required file missing", report)

    def test_repository_escape_rejected(self):
        with self.assertRaises(ValueError):
            local_path(self.root, "../outside")

    def test_code_examples_are_not_links(self):
        text = "[real](README.md)\n```md\n[example](missing.md)\n```\n`[example](missing.md)`"
        self.assertEqual(markdown_targets(text), ["README.md"])

    def test_relative_links_and_missing_target(self):
        (self.root / "docs").mkdir()
        (self.root / "README.md").write_text("Readme")
        (self.root / "docs/notes.md").write_text("[ok](../README.md#section) [bad](missing.md)")
        self.config["markdown"] = ["docs/notes.md"]
        report, failed = collect(self.root, self.config, "2026-11-08")
        self.assertTrue(failed)
        self.assertIn("| PASS | Local target exists", report)
        self.assertIn("| FAIL | Local target missing", report)

    def test_network_failure_is_unverified_not_healthy(self):
        self.config["urls"] = ["https://example.com"]

        def unavailable(*args, **kwargs):
            raise urllib.error.URLError("offline")

        report, failed = collect(self.root, self.config, "2026-11-08", unavailable)
        self.assertFalse(failed)
        self.assertIn("| WARN | Unverified:", report)

    def test_syntax_and_checksum_failures(self):
        (self.root / "app.py").write_text("def broken(:")
        (self.root / "asset").write_bytes(b"modified")
        self.config.update(python=["app.py"], sha256={"asset": "0" * 64})
        report, failed = collect(self.root, self.config, "2026-11-08")
        self.assertTrue(failed)
        self.assertIn("2 failed checks", report)

    def test_release_watch_is_repeatable_and_day_changes(self):
        (self.root / "requirements.txt").write_text("numpy~=2.0.1\n")
        self.config["requirements"] = "requirements.txt"

        def metadata(*args, **kwargs):
            return {"info": {"version": "2.3.0", "requires_python": ">=3.11"}}

        first = collect(self.root, self.config, "2026-11-08", metadata)
        self.assertEqual(first, collect(self.root, self.config, "2026-11-08", metadata))
        self.assertNotEqual(first, collect(self.root, self.config, "2026-11-09", metadata))
        self.assertIn("| numpy | ~=2.0.1 | 2.3.0 | >=3.11 |", first[0])

    def test_unsupported_requirement_is_visible_failure(self):
        (self.root / "requirements.txt").write_text("-r other.txt\n")
        self.config["requirements"] = "requirements.txt"
        report, failed = collect(self.root, self.config, "2026-11-08")
        self.assertTrue(failed)
        self.assertIn("Unsupported requirement", report)


if __name__ == "__main__":
    unittest.main()
