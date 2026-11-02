"""In-process unit and integration tests for `sprawl ignore` (TASK-023-01)."""

import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from sprawl.analyzers.stack import (
    detect_stacks_from_entries,
    detect_workspace_stacks,
)
from sprawl.cli import get_parser
from sprawl.commands.ignore import cmd_ignore
from sprawl.config import config
from sprawl.exceptions import SprawlError
from sprawl.generators.ignore import (
    CUSTOM_SEPARATOR,
    IGNORE_TARGETS,
    MANAGED_HEADER,
    compile_managed_block,
    extract_custom_section,
    merge_ignore_content,
    sync_workspace_ignores,
)


class TestSprawlIgnore(unittest.TestCase):
    """Comprehensive in-process test suite for stack detection and multi-IDE ignore shields."""

    def setUp(self) -> None:
        self._orig_dry_run = config.dry_run
        self._orig_json_logging = config.json_logging
        config.dry_run = False
        config.json_logging = False

    def tearDown(self) -> None:
        config.dry_run = self._orig_dry_run
        config.json_logging = self._orig_json_logging

    def test_detect_stacks_pure_markers(self) -> None:
        """Verify detect_stacks_from_entries detects all 7 profiles in deterministic order."""
        empty_res = detect_stacks_from_entries(frozenset())
        self.assertEqual(empty_res.detected_stacks, ("base",))
        self.assertEqual(empty_res.matched_markers, {"base": ()})

        polyglot_entries = frozenset(
            {
                "pyproject.toml",
                "uv.lock",
                "package.json",
                "Cargo.toml",
                "go.mod",
                "manifest.md",
                ".obsidian",
                "Dockerfile",
                "README.md",
            }
        )
        res = detect_stacks_from_entries(polyglot_entries)
        self.assertEqual(
            res.detected_stacks,
            ("base", "python", "node", "rust", "go", "vault", "docker"),
        )
        self.assertEqual(res.matched_markers["python"], ("pyproject.toml", "uv.lock"))
        self.assertEqual(res.matched_markers["node"], ("package.json",))
        self.assertEqual(res.matched_markers["rust"], ("Cargo.toml",))
        self.assertEqual(res.matched_markers["go"], ("go.mod",))
        self.assertEqual(res.matched_markers["vault"], ("manifest.md", ".obsidian"))
        self.assertEqual(res.matched_markers["docker"], ("Dockerfile",))

    def test_compile_managed_block_deterministic(self) -> None:
        """Verify identical output order and zero duplicate patterns across repeated calls."""
        stacks = ("base", "python", "node", "vault")
        block_one = compile_managed_block(stacks)
        block_two = compile_managed_block(stacks)
        self.assertEqual(block_one, block_two)
        self.assertTrue(block_one.startswith(MANAGED_HEADER))
        self.assertIn("# [sprawl:base]", block_one)
        self.assertIn("# [sprawl:python]", block_one)
        self.assertIn("# [sprawl:node]", block_one)
        self.assertIn("# [sprawl:vault]", block_one)

        pattern_lines = [
            line.strip()
            for line in block_one.splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        self.assertEqual(len(pattern_lines), len(set(pattern_lines)))

    def test_merge_preserves_custom_rules_after_separator(self) -> None:
        """Verify custom lines below CUSTOM_SEPARATOR survive multiple sync runs untouched."""
        managed = compile_managed_block(("base", "python"))
        initial_existing = (
            f"{managed}\n\n{CUSTOM_SEPARATOR}\n"
            "# Team-specific ignores\n"
            "datasets/raw_dumps/\n"
            "*.sqlite3\n"
        )
        merged_once, count_once = merge_ignore_content(managed, initial_existing)
        self.assertEqual(count_once, 2)
        self.assertIn("datasets/raw_dumps/", merged_once)
        self.assertIn("*.sqlite3", merged_once)

        merged_twice, count_twice = merge_ignore_content(managed, merged_once)
        self.assertEqual(count_twice, 2)
        self.assertEqual(merged_once, merged_twice)

    def test_merge_migrates_legacy_unmanaged_ignore_file(self) -> None:
        """Verify pre-existing .cursorignore rules without a separator are migrated safely."""
        legacy_content = "# Hand-crafted cursor ignore\n.git/\nnode_modules/\nmy_private_notes/\n*.bak\n"
        managed = compile_managed_block(("base", "node"))
        merged, custom_count = merge_ignore_content(managed, legacy_content)

        self.assertEqual(custom_count, 2)
        self.assertIn(CUSTOM_SEPARATOR, merged)
        _, _, custom_part = merged.partition(CUSTOM_SEPARATOR)
        self.assertIn("# Hand-crafted cursor ignore", custom_part)
        self.assertIn("my_private_notes/", custom_part)
        self.assertIn("*.bak", custom_part)
        self.assertNotIn("node_modules/", custom_part)

    def test_sync_generates_all_five_targets_under_30ms(self) -> None:
        """Verify sync_workspace_ignores writes all 5 IDE targets identically in <30ms."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            ws_path = Path(tmp_dir)
            (ws_path / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")

            report = sync_workspace_ignores(ws_path)
            self.assertEqual(report.detected_stacks, ("base", "python"))
            self.assertLess(report.elapsed_ms, 30.0)
            self.assertFalse(report.has_drift)
            self.assertEqual(len(report.targets), 5)

            contents: set[str] = set()
            for target_name in IGNORE_TARGETS:
                target_file = ws_path / target_name
                self.assertTrue(target_file.is_file(), f"Missing {target_name}")
                contents.add(target_file.read_text(encoding="utf-8"))

            self.assertEqual(len(contents), 1)

    def test_sync_idempotent_second_run_unchanged(self) -> None:
        """Verify running sync_workspace_ignores twice marks all 5 targets as unchanged."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            ws_path = Path(tmp_dir)
            (ws_path / "package.json").write_text("{}", encoding="utf-8")

            first_report = sync_workspace_ignores(ws_path)
            self.assertTrue(all(t.status == "created" for t in first_report.targets))

            second_report = sync_workspace_ignores(ws_path)
            self.assertTrue(all(t.status == "unchanged" for t in second_report.targets))
            self.assertFalse(second_report.has_drift)

    def test_check_mode_detects_drift_and_raises_sprawl_error(self) -> None:
        """Verify check mode detects modified or missing ignore targets and raises SprawlError."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            ws_path = Path(tmp_dir)
            (ws_path / "Cargo.toml").write_text("[package]\n", encoding="utf-8")
            sync_workspace_ignores(ws_path)

            # Confirm clean check passes without raising
            cmd_ignore("check", str(ws_path))

            # Tamper with .claudeignore above the separator
            claude_file = ws_path / ".claudeignore"
            tampered = "# Tampered header\n"
            claude_file.write_text(tampered, encoding="utf-8")

            with self.assertRaises(SprawlError):
                cmd_ignore("check", str(ws_path))

            # Ensure check mode did not overwrite the tampered file
            self.assertEqual(claude_file.read_text(encoding="utf-8"), tampered)

    def test_cmd_ignore_json_and_dry_run_modes(self) -> None:
        """Verify --dry-run writes zero files and --json outputs valid JSON payloads."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            ws_path = Path(tmp_dir)
            (ws_path / "go.mod").write_text("module example.com/m\n", encoding="utf-8")

            config.dry_run = True
            config.json_logging = True

            stdout_buf = io.StringIO()
            with contextlib.redirect_stdout(stdout_buf):
                cmd_ignore("sync", str(ws_path))

            payload = json.loads(stdout_buf.getvalue().strip())
            self.assertEqual(payload["action"], "sync")
            self.assertTrue(payload["dry_run"])
            self.assertEqual(payload["detected_stacks"], ["base", "go"])
            for target_name in IGNORE_TARGETS:
                self.assertFalse((ws_path / target_name).exists())

            # Also verify detect action in JSON mode and CLI parser wiring
            detect_buf = io.StringIO()
            with contextlib.redirect_stdout(detect_buf):
                cmd_ignore("detect", str(ws_path))
            detect_payload = json.loads(detect_buf.getvalue().strip())
            self.assertEqual(detect_payload["action"], "detect")
            self.assertEqual(detect_payload["detected_stacks"], ["base", "go"])

            parser = get_parser()
            parsed = parser.parse_args(["ignore", "check", "--path", str(ws_path)])
            self.assertEqual(parsed.command, "ignore")
            self.assertEqual(parsed.ignore_action, "check")
            self.assertEqual(parsed.target_dir, str(ws_path))

            # Verify extract_custom_section on empty input and detect_workspace_stacks on valid dir
            self.assertEqual(extract_custom_section(None), ("", 0))
            self.assertEqual(detect_workspace_stacks(ws_path).detected_stacks, ("base", "go"))


if __name__ == "__main__":
    unittest.main()
