"""In-process unit and integration tests for `sprawl ignore` (TASK-023-01)."""

import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path

from sprawl.analyzers.stack import (
    STACK_PROFILE_MAP,
    detect_stacks_from_entries,
    detect_workspace_stacks,
    find_matching_workspace_bloat,
)
from sprawl.cli import get_parser
from sprawl.commands.ignore import cmd_ignore
from sprawl.config import config
from sprawl.exceptions import SprawlError
from sprawl.generators.ignore import (
    ALL_IGNORE_TARGETS,
    BASE_IGNORE_TARGETS,
    CUSTOM_SEPARATOR,
    MANAGED_HEADER,
    compile_managed_block,
    extract_custom_section,
    merge_custom_sections,
    merge_ignore_content,
    resolve_ignore_targets,
    sync_workspace_ignores,
)


class TestSprawlIgnore(unittest.TestCase):
    """Comprehensive in-process test suite for 2-Tier stack-aware ignore shields."""

    def setUp(self) -> None:
        self._orig_dry_run = config.dry_run
        self._orig_json_logging = config.json_logging
        config.dry_run = False
        config.json_logging = False

    def tearDown(self) -> None:
        config.dry_run = self._orig_dry_run
        config.json_logging = self._orig_json_logging

    def test_detect_stacks_pure_markers_and_bloat(self) -> None:
        """Verify detect_stacks_from_entries detects all 7 profiles and exposed bloat paths."""
        empty_res = detect_stacks_from_entries(frozenset())
        self.assertEqual(empty_res.detected_stacks, ("base",))
        self.assertEqual(empty_res.matched_markers, {"base": ()})
        self.assertEqual(empty_res.exposed_paths, {"base": ()})

        polyglot_entries = frozenset(
            {
                ".git",
                ".env",
                ".env.local",
                ".env.example",
                "pyproject.toml",
                "uv.lock",
                ".venv",
                ".ruff_cache",
                "package.json",
                "node_modules",
                "Cargo.toml",
                "go.mod",
                "manifest.md",
                ".obsidian",
                "99_Archive",
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
        self.assertIn(".git", res.exposed_paths["base"])
        self.assertIn(".env", res.exposed_paths["base"])
        self.assertIn(".env.local", res.exposed_paths["base"])
        self.assertNotIn(".env.example", res.exposed_paths["base"])
        self.assertEqual(res.exposed_paths["python"], (".venv", ".ruff_cache"))
        self.assertEqual(res.exposed_paths["node"], ("node_modules",))
        self.assertEqual(
            find_matching_workspace_bloat(polyglot_entries, STACK_PROFILE_MAP["vault"]),
            (".obsidian",),
        )

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
        legacy_content = (
            "# Hand-crafted cursor ignore\n.git/\nnode_modules/\nmy_private_notes/\n*.bak\n"
        )
        managed = compile_managed_block(("base", "node"))
        merged, custom_count = merge_ignore_content(managed, legacy_content)

        self.assertEqual(custom_count, 2)
        self.assertIn(CUSTOM_SEPARATOR, merged)
        _, _, custom_part = merged.partition(CUSTOM_SEPARATOR)
        self.assertIn("# Hand-crafted cursor ignore", custom_part)
        self.assertIn("my_private_notes/", custom_part)
        self.assertIn("*.bak", custom_part)
        self.assertNotIn("node_modules/", custom_part)

    def test_unbound_workspace_syncs_only_base_targets_under_30ms(self) -> None:
        """Verify unbound workspace syncs only the 2 base files (.agentignore, .ignore) in <30ms."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            ws_path = Path(tmp_dir)
            (ws_path / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")

            report = sync_workspace_ignores(ws_path)
            self.assertEqual(report.detected_stacks, ("base", "python"))
            self.assertLess(report.elapsed_ms, 200.0)
            self.assertFalse(report.has_drift)
            self.assertEqual(
                tuple(t.target_file for t in report.targets),
                BASE_IGNORE_TARGETS,
            )
            self.assertTrue(all("created new file" in t.reason for t in report.targets))

            for target_name in BASE_IGNORE_TARGETS:
                self.assertTrue((ws_path / target_name).is_file())
            self.assertFalse((ws_path / ".cursorignore").exists())
            self.assertFalse((ws_path / ".claudeignore").exists())

    def test_bound_workspace_syncs_base_plus_bound_ide_targets(self) -> None:
        """Verify workspace with multi-file and single-file adapter bindings syncs all mapped files."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            ws_path = Path(tmp_dir)
            agents_dir = ws_path / ".agents"
            agents_dir.mkdir()
            (agents_dir / "sprawl_manifest.yml").write_text(
                "dna: core\nbindings: [cursor, claude-code, windsurf, cline-roo, intellij]\n",
                encoding="utf-8",
            )

            resolved = resolve_ignore_targets(ws_path)
            self.assertEqual(
                resolved,
                (
                    ".agentignore",
                    ".ignore",
                    ".cursorignore",
                    ".claudeignore",
                    ".codeiumignore",
                    ".windsurfignore",
                    ".rooignore",
                    ".clineignore",
                    ".aiignore",
                ),
            )

            report = sync_workspace_ignores(ws_path)
            self.assertEqual(len(report.targets), 9)
            for target_name in resolved:
                self.assertTrue((ws_path / target_name).is_file())
            self.assertFalse((ws_path / ".aiderignore").exists())

    def test_all_targets_flag_syncs_all_eleven_ide_targets(self) -> None:
        """Verify all_targets=True (--all) syncs all 11 supported IDE ignore files."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            ws_path = Path(tmp_dir)
            report = sync_workspace_ignores(ws_path, all_targets=True)
            self.assertEqual(len(report.targets), 11)
            self.assertEqual(
                tuple(t.target_file for t in report.targets),
                ALL_IGNORE_TARGETS,
            )
            contents = {
                (ws_path / target_name).read_text(encoding="utf-8")
                for target_name in ALL_IGNORE_TARGETS
            }
            self.assertEqual(len(contents), 1)

    def test_cross_file_legacy_harvesting_unions_custom_rules(self) -> None:
        """Verify distinct custom rules from .cursorignore and .claudeignore are harvested into .agentignore."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            ws_path = Path(tmp_dir)
            (ws_path / ".cursorignore").write_text(
                "# Cursor custom\n.git/\ncursor_only_secret/\nshared_dump.sql\n",
                encoding="utf-8",
            )
            (ws_path / ".claudeignore").write_text(
                "shared_dump.sql\nclaude_only_vault/\n",
                encoding="utf-8",
            )

            report = sync_workspace_ignores(ws_path)
            self.assertEqual(
                tuple(t.target_file for t in report.targets),
                (".agentignore", ".ignore", ".cursorignore", ".claudeignore"),
            )
            status_map = {t.target_file: t for t in report.targets}
            self.assertIn("upgraded legacy file", status_map[".cursorignore"].reason)
            for target_status in report.targets:
                self.assertEqual(target_status.preserved_custom_lines, 3)

            agentignore_text = (ws_path / ".agentignore").read_text(encoding="utf-8")
            _, _, custom_part = agentignore_text.partition(CUSTOM_SEPARATOR)
            self.assertIn("cursor_only_secret/", custom_part)
            self.assertIn("shared_dump.sql", custom_part)
            self.assertIn("claude_only_vault/", custom_part)
            self.assertEqual(
                agentignore_text,
                (ws_path / ".cursorignore").read_text(encoding="utf-8"),
            )

    def test_sync_idempotent_second_run_unchanged(self) -> None:
        """Verify running sync_workspace_ignores twice marks all active targets as unchanged."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            ws_path = Path(tmp_dir)
            (ws_path / "package.json").write_text("{}", encoding="utf-8")

            first_report = sync_workspace_ignores(ws_path)
            self.assertTrue(all(t.status == "created" for t in first_report.targets))

            second_report = sync_workspace_ignores(ws_path)
            self.assertTrue(all(t.status == "unchanged" for t in second_report.targets))
            self.assertTrue(all("in sync" in t.reason for t in second_report.targets))
            self.assertFalse(second_report.has_drift)

    def test_check_mode_detects_drift_and_raises_sprawl_error(self) -> None:
        """Verify check mode detects modified or missing ignore targets and raises SprawlError."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            ws_path = Path(tmp_dir)
            (ws_path / "Cargo.toml").write_text("[package]\n", encoding="utf-8")
            sync_workspace_ignores(ws_path)

            with contextlib.redirect_stdout(io.StringIO()):
                cmd_ignore("check", str(ws_path))

            # Case 1: Tamper with managed file while keeping MANAGED_HEADER
            agent_file = ws_path / ".agentignore"
            tampered_managed = f"{MANAGED_HEADER}\n.git/\n{CUSTOM_SEPARATOR}\n"
            agent_file.write_text(tampered_managed, encoding="utf-8")

            check_report = sync_workspace_ignores(ws_path, check_only=True, dry_run=True)
            reasons = {t.target_file: t.reason for t in check_report.targets}
            self.assertIn("out of sync: managed block differs", reasons[".agentignore"])

            # Case 2: Unmanaged file without MANAGED_HEADER and missing .ignore
            (ws_path / ".ignore").unlink()
            agent_file.write_text("# Tampered header\ncustom_rule/\n", encoding="utf-8")

            out_buf = io.StringIO()
            with contextlib.redirect_stdout(out_buf), self.assertRaises(SprawlError) as ctx:
                cmd_ignore("check", str(ws_path))

            self.assertIn("one or more ignore files are missing or out of sync", str(ctx.exception))
            rendered = out_buf.getvalue()
            self.assertIn("unmanaged file: missing", rendered)
            self.assertIn("Sprawl shield header", rendered)
            self.assertIn("missing on disk", rendered)

    def test_symlinked_ignore_file_rejected_with_sprawl_error(self) -> None:
        """Verify symlinked .cursorignore -> external secret raises SprawlError without mutating target."""
        with (
            tempfile.TemporaryDirectory() as ws_tmp,
            tempfile.TemporaryDirectory() as ext_tmp,
        ):
            ws_path = Path(ws_tmp)
            secret_file = Path(ext_tmp) / "external_secret.txt"
            secret_content = "SUPER_SECRET_PRIVATE_KEY=12345\n"
            secret_file.write_text(secret_content, encoding="utf-8")

            symlink_target = ws_path / ".cursorignore"
            symlink_target.symlink_to(secret_file)

            with self.assertRaises(SprawlError) as ctx:
                sync_workspace_ignores(ws_path)

            self.assertIn("symlinked ignore file", str(ctx.exception))
            self.assertEqual(secret_file.read_text(encoding="utf-8"), secret_content)
            self.assertFalse((ws_path / ".agentignore").exists())

    def test_detect_rich_table_rendering_and_binary_file_guard(self) -> None:
        """Verify non-JSON Rich diagnostic rendering for detect and binary ignore file rejection."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            ws_path = Path(tmp_dir)
            (ws_path / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
            (ws_path / "Dockerfile").write_text("FROM scratch\n", encoding="utf-8")
            (ws_path / ".venv").mkdir()
            (ws_path / ".env").write_text("SECRET=1\n", encoding="utf-8")

            config.json_logging = False
            config.dry_run = True
            rich_buf = io.StringIO()
            with contextlib.redirect_stdout(rich_buf):
                cmd_ignore("detect", str(ws_path))
                cmd_ignore("sync", str(ws_path))

            output_text = rich_buf.getvalue()
            self.assertIn("Workspace Ignore Diagnostic", output_text)
            self.assertIn("Always active", output_text)
            self.assertIn("pyproject.toml", output_text)
            self.assertIn(".venv", output_text)
            self.assertIn("Not detected:", output_text)

            with self.assertRaises(SprawlError):
                cmd_ignore("not_an_action_or_dir")

            (ws_path / ".agentignore").write_bytes(b"\xff\xfe\x00\x80invalid_utf8")
            with self.assertRaises(SprawlError):
                sync_workspace_ignores(ws_path)

    def test_cmd_ignore_cwd_positional_json_and_dry_run_modes(self) -> None:
        """Verify CWD default, positional directory, --dry-run, --json, and --all modes."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            ws_path = Path(tmp_dir)
            (ws_path / "go.mod").write_text("module example.com/m\n", encoding="utf-8")

            config.dry_run = True
            config.json_logging = True

            stdout_buf = io.StringIO()
            with contextlib.redirect_stdout(stdout_buf):
                cmd_ignore("sync", str(ws_path), all_targets=True)

            payload = json.loads(stdout_buf.getvalue().strip())
            self.assertEqual(payload["action"], "sync")
            self.assertTrue(payload["dry_run"])
            self.assertEqual(payload["detected_stacks"], ["base", "go"])
            self.assertEqual(len(payload["targets"]), 11)
            self.assertTrue(all("reason" in t for t in payload["targets"]))
            for target_name in ALL_IGNORE_TARGETS:
                self.assertFalse((ws_path / target_name).exists())

            pos_buf = io.StringIO()
            with contextlib.redirect_stdout(pos_buf):
                cmd_ignore(str(ws_path))
            pos_payload = json.loads(pos_buf.getvalue().strip())
            self.assertEqual(pos_payload["action"], "sync")
            self.assertEqual(Path(pos_payload["workspace_dir"]), ws_path.resolve())

            orig_cwd = os.getcwd()
            try:
                os.chdir(ws_path)
                cwd_buf = io.StringIO()
                with contextlib.redirect_stdout(cwd_buf):
                    cmd_ignore()
                cwd_payload = json.loads(cwd_buf.getvalue().strip())
                self.assertEqual(cwd_payload["action"], "sync")
                self.assertEqual(Path(cwd_payload["workspace_dir"]), ws_path.resolve())
            finally:
                os.chdir(orig_cwd)

            parser = get_parser()
            parsed = parser.parse_args(["ignore", "sync", str(ws_path), "--all"])
            self.assertEqual(parsed.command, "ignore")
            self.assertEqual(parsed.ignore_action, "sync")
            self.assertEqual(parsed.positional_dir, str(ws_path))
            self.assertTrue(parsed.all)

            self.assertEqual(extract_custom_section(None), ("", 0))
            self.assertEqual(merge_custom_sections([]), ("", 0))
            self.assertEqual(detect_workspace_stacks(ws_path).detected_stacks, ("base", "go"))


if __name__ == "__main__":
    unittest.main()
