"""Automated test suite for Windows cross-platform compatibility."""

import os
import sys
import shutil
import tempfile
import unittest
from unittest.mock import patch, MagicMock, ANY

from src.sprawl.utils import get_venv_executable
from src.sprawl.utils import tui
from src.sprawl.bind.adapters import _write_symlink
from src.sprawl.mcp.workspace_fs import WorkspaceFS, MCPError


class TestWindowsCompatibility(unittest.TestCase):
    """Verifies cross-platform behavior on Windows and POSIX."""

    def test_get_venv_executable_windows(self):
        """get_venv_executable must resolve to Scripts\\*.exe on Windows."""
        with patch("sys.platform", "win32"):
            python_exe = get_venv_executable("/fake/venv", "python3")
            self.assertEqual(python_exe, os.path.join("/fake/venv", "Scripts", "python.exe"))

            pip_exe = get_venv_executable("/fake/venv", "pip")
            self.assertEqual(pip_exe, os.path.join("/fake/venv", "Scripts", "pip.exe"))

            custom_exe = get_venv_executable("/fake/venv", "pytest")
            self.assertEqual(custom_exe, os.path.join("/fake/venv", "Scripts", "pytest.exe"))

    def test_get_venv_executable_posix(self):
        """get_venv_executable must resolve to bin/* on POSIX systems."""
        with patch("sys.platform", "linux"):
            python_exe = get_venv_executable("/fake/venv", "python3")
            self.assertEqual(python_exe, os.path.join("/fake/venv", "bin", "python3"))

            pip_exe = get_venv_executable("/fake/venv", "pip")
            self.assertEqual(pip_exe, os.path.join("/fake/venv", "bin", "pip"))

    def test_tui_read_key_windows_arrows(self):
        """tui.read_key must decode msvcrt arrow key escape sequences on Windows."""
        mock_msvcrt = MagicMock()
        with patch("sys.platform", "win32"), \
             patch("sys.stdin.isatty", return_value=True), \
             patch("src.sprawl.utils.tui.msvcrt", mock_msvcrt):

            # Up arrow: 0xe0 followed by 'H'
            mock_msvcrt.getch.side_effect = [b"\xe0", b"H"]
            self.assertEqual(tui.read_key(), "\x1b[A")

            # Down arrow: 0xe0 followed by 'P'
            mock_msvcrt.getch.side_effect = [b"\xe0", b"P"]
            self.assertEqual(tui.read_key(), "\x1b[B")

            # Left arrow: 0xe0 followed by 'K'
            mock_msvcrt.getch.side_effect = [b"\xe0", b"K"]
            self.assertEqual(tui.read_key(), "\x1b[D")

            # Right arrow: 0xe0 followed by 'M'
            mock_msvcrt.getch.side_effect = [b"\xe0", b"M"]
            self.assertEqual(tui.read_key(), "\x1b[C")

    def test_tui_read_key_windows_standard_keys(self):
        """tui.read_key must handle Enter, Space, and standard characters on Windows."""
        mock_msvcrt = MagicMock()
        with patch("sys.platform", "win32"), \
             patch("sys.stdin.isatty", return_value=True), \
             patch("src.sprawl.utils.tui.msvcrt", mock_msvcrt):

            mock_msvcrt.getch.return_value = b"\r"
            self.assertEqual(tui.read_key(), "\r")

            mock_msvcrt.getch.return_value = b" "
            self.assertEqual(tui.read_key(), " ")

            mock_msvcrt.getch.return_value = b"q"
            self.assertEqual(tui.read_key(), "q")

    def test_tui_raw_terminal_windows_enables_vt(self):
        """tui.raw_terminal context manager must enable VT mode on Windows."""
        with patch("sys.platform", "win32"), \
             patch("src.sprawl.utils.tui._enable_windows_vt") as mock_enable_vt:
            with tui.raw_terminal():
                pass
            mock_enable_vt.assert_called_once()

    def test_workspace_fs_mount_backslash_normalization(self):
        """workspace_fs must normalize Windows backslashes in @mount aliases."""
        temp_dir = tempfile.mkdtemp()
        try:
            workspace_root = os.path.join(temp_dir, "workspace")
            mount_dir = os.path.join(temp_dir, "shared_lib")
            os.makedirs(workspace_root)
            os.makedirs(mount_dir)

            # Create file inside mount
            secret_file = os.path.join(mount_dir, "code.py")
            with open(secret_file, "w") as f:
                f.write("print('hello windows')")

            # Configure allowed_mounts
            agents_dir = os.path.join(workspace_root, ".agents")
            os.makedirs(agents_dir)
            import json
            with open(os.path.join(agents_dir, "sprawl-config.json"), "w") as f:
                json.dump({"allowed_mounts": {"lib": mount_dir}}, f)

            fs = WorkspaceFS(workspace_root)

            # Test forward slash
            safe_path = fs._get_safe_path("@lib/code.py")
            self.assertEqual(safe_path, os.path.realpath(secret_file))

            # Test Windows backslash
            safe_path_bs = fs._get_safe_path("@lib\\code.py")
            self.assertEqual(safe_path_bs, os.path.realpath(secret_file))
        finally:
            shutil.rmtree(temp_dir)

    def test_symlink_fallback_to_copy_on_oserror(self):
        """_write_symlink must fall back to file or directory copy when os.symlink fails with OSError."""
        temp_dir = tempfile.mkdtemp()
        try:
            ws_root = os.path.join(temp_dir, "ws")
            os.makedirs(ws_root)
            agents_dir = os.path.join(ws_root, ".agents")
            os.makedirs(agents_dir)

            # Create test file in .agents
            with open(os.path.join(agents_dir, "test.txt"), "w") as f:
                f.write("test content")

            link_path = os.path.join(ws_root, ".agent")

            # Mock os.symlink to simulate Windows PermissionError (WinError 1314)
            with patch("os.symlink", side_effect=OSError(1314, "A required privilege is not held")):
                success = _write_symlink("Antigravity .agent", link_path, ".agents", force=True)
                self.assertTrue(success)
                self.assertTrue(os.path.exists(link_path))
                self.assertTrue(os.path.isdir(link_path))
                self.assertTrue(os.path.exists(os.path.join(link_path, "test.txt")))
        finally:
            shutil.rmtree(temp_dir)

    def test_validate_dna_directory_utf8_encoding(self):
        """validate_dna_directory must decode UTF-8 characters without charmap decoding errors."""
        from src.sprawl.validation import validate_dna_directory
        temp_dir = tempfile.mkdtemp()
        try:
            skills_dir = os.path.join(temp_dir, "skills", "test-skill")
            rules_dir = os.path.join(temp_dir, "rules")
            os.makedirs(skills_dir)
            os.makedirs(rules_dir)

            # Markdown with non-ASCII UTF-8 characters (emojis, em-dash, smart quotes)
            skill_content = (
                "---\n"
                "name: test-skill\n"
                "description: “Smart quotes and emojis 🚀 — dash”\n"
                "---\n"
                "# Test Skill 💡\n"
                "UTF-8 content: €100, bullet •, em-dash —\n"
            )
            with open(os.path.join(skills_dir, "SKILL.md"), "w", encoding="utf-8") as f:
                f.write(skill_content)

            rule_content = (
                "---\n"
                "description: “Rule description”\n"
                "---\n"
                "# Demo Security 🛡️\n"
                "Zero-trust check: ✓ passed\n"
            )
            with open(os.path.join(rules_dir, "demo_security.md"), "w", encoding="utf-8") as f:
                f.write(rule_content)

            # Should not raise any decoding error
            validate_dna_directory(temp_dir)
        finally:
            shutil.rmtree(temp_dir)

    @patch("src.sprawl.commands.diagnostics.resolve_repo_root", return_value=None)
    @patch("src.sprawl.commands.diagnostics.subprocess.run")
    @patch("src.sprawl.commands.diagnostics.os.path.exists", return_value=False)
    @patch("sys.platform", "win32")
    def test_cmd_update_windows_uses_pipx_upgrade(self, mock_exists, mock_run, mock_resolve):
        """cmd_update on Windows must use pipx upgrade to avoid python.exe file-locking PermissionError."""
        from src.sprawl.commands.diagnostics import cmd_update
        from src.sprawl.config import config
        config.dry_run = False
        mock_run.return_value = MagicMock(returncode=0)
        cmd_update()
        mock_run.assert_called_with(
            ["pipx", "upgrade", "sprawl-cli", "--pip-args=--no-cache-dir"],
            env=ANY
        )

    @patch("src.sprawl.commands.diagnostics.resolve_repo_root", return_value=None)
    @patch("src.sprawl.commands.diagnostics.subprocess.run")
    @patch("src.sprawl.commands.diagnostics.os.path.exists", return_value=False)
    @patch("sys.platform", "win32")
    def test_cmd_update_windows_falls_back_to_runpip(self, mock_exists, mock_run, mock_resolve):
        """cmd_update on Windows falls back to pipx runpip if pipx upgrade fails."""
        from src.sprawl.commands.diagnostics import cmd_update
        from src.sprawl.config import config
        config.dry_run = False
        mock_run.side_effect = [
            MagicMock(returncode=1),
            MagicMock(returncode=0)
        ]
        cmd_update()
        mock_run.assert_any_call(
            ["pipx", "runpip", "sprawl-cli", "install", "--upgrade", "--no-cache-dir", "git+https://github.com/sprawl-software/sprawl-cli.git"],
            env=ANY
        )


if __name__ == "__main__":
    unittest.main()
