"""Tests for sprawl bind adapter engine."""

import unittest
import os
import json
import shutil
import tempfile
from unittest.mock import patch, MagicMock
from src.sprawl.bind import bind_adapters


class TestBind(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.agents_dir = os.path.join(self.test_dir, ".agents")
        os.makedirs(self.agents_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_bind_creates_cursorrules(self):
        """bind_adapters creates .cursorrules as a symlink to AGENTS.md."""
        self.assertTrue(bind_adapters(self.test_dir))
        cursor_file = os.path.join(self.test_dir, ".cursorrules")
        self.assertTrue(os.path.islink(cursor_file))
        self.assertEqual(os.readlink(cursor_file), "AGENTS.md")

    def test_bind_creates_clinerules(self):
        """bind_adapters creates .clinerules."""
        bind_adapters(self.test_dir)
        self.assertTrue(os.path.islink(os.path.join(self.test_dir, ".clinerules")))

    def test_bind_creates_windsurfrules(self):
        """bind_adapters creates .windsurfrules."""
        bind_adapters(self.test_dir)
        self.assertTrue(os.path.islink(os.path.join(self.test_dir, ".windsurfrules")))

    def test_bind_creates_copilot_instructions(self):
        """bind_adapters creates .github/copilot-instructions.md as relative symlink."""
        bind_adapters(self.test_dir)
        copilot = os.path.join(self.test_dir, ".github", "copilot-instructions.md")
        self.assertTrue(os.path.islink(copilot))
        self.assertEqual(os.readlink(copilot), "../AGENTS.md")

    def test_bind_creates_antigravity_gemini_json(self):
        """bind_adapters creates .gemini/antigravity/gemini.json."""
        bind_adapters(self.test_dir)
        gemini = os.path.join(self.test_dir, ".gemini", "antigravity", "gemini.json")
        self.assertTrue(os.path.exists(gemini))
        with open(gemini, "r") as f:
            data = json.load(f)
        self.assertIn("sprawl", data)
        self.assertTrue(data["sprawl"]["managed"])

    def test_bind_without_force_skips_existing(self):
        """bind_adapters skips existing files when force=False."""
        # Write existing file with unique content
        cursor_file = os.path.join(self.test_dir, ".cursorrules")
        original = "MY ORIGINAL RULES"
        with open(cursor_file, "w") as f:
            f.write(original)

        bind_adapters(self.test_dir, force=False)

        self.assertFalse(os.path.islink(cursor_file))
        with open(cursor_file, "r") as f:
            content = f.read()
        self.assertEqual(content, original)

    def test_bind_with_force_overwrites_existing(self):
        """bind_adapters overwrites existing files when force=True."""
        cursor_file = os.path.join(self.test_dir, ".cursorrules")
        with open(cursor_file, "w") as f:
            f.write("OLD CONTENT")

        bind_adapters(self.test_dir, force=True)

        self.assertTrue(os.path.islink(cursor_file))
        self.assertEqual(os.readlink(cursor_file), "AGENTS.md")

    def test_bind_no_agents_dir_returns_false(self):
        """bind_adapters returns False when .agents/ doesn't exist."""
        empty_dir = tempfile.mkdtemp()
        try:
            result = bind_adapters(empty_dir)
            self.assertFalse(result)
        finally:
            shutil.rmtree(empty_dir, ignore_errors=True)

    def test_bind_adapters_selective_filtering(self):
        """bind_adapters writes only files matched in target keys list."""
        self.assertTrue(bind_adapters(self.test_dir, targets=["cursor"]))
        self.assertTrue(os.path.islink(os.path.join(self.test_dir, ".cursorrules")))
        self.assertFalse(os.path.islink(os.path.join(self.test_dir, ".clinerules")))
        self.assertFalse(os.path.islink(os.path.join(self.test_dir, ".github", "copilot-instructions.md")))

    def test_bind_adapters_symmetric_cleanup(self):
        """bind_adapters removes excluded rules and directories when targets are updated."""
        # 1. Bind cursor and cline-roo
        self.assertTrue(bind_adapters(self.test_dir, targets=["cursor", "cline-roo"]))
        
        cursor_file = os.path.join(self.test_dir, ".cursorrules")
        cline_file = os.path.join(self.test_dir, ".clinerules")
        
        self.assertTrue(os.path.islink(cursor_file))
        self.assertTrue(os.path.islink(cline_file))
        
        # 2. Run bind targeting only cursor
        self.assertTrue(bind_adapters(self.test_dir, targets=["cursor"]))
        
        # 3. Assert cursor is kept, cline-roo is deleted
        self.assertTrue(os.path.islink(cursor_file))
        self.assertFalse(os.path.exists(cline_file))
        self.assertFalse(os.path.islink(cline_file))

    def test_bind_adapters_invalid_target_raises(self):
        """bind_adapters raises SprawlError when invalid target key is passed."""
        from src.sprawl.exceptions import SprawlError
        with self.assertRaises(SprawlError):
            bind_adapters(self.test_dir, targets=["invalid_target"])

    @patch("sys.stdin.isatty", return_value=False)
    @patch("src.sprawl.bind.bind_adapters")
    def test_cmd_bind_non_tty_defaults_to_all(self, mock_bind, mock_isatty):
        """cmd_bind defaults to all adapters when not in TTY mode."""
        from src.sprawl.commands.sync_cmd import cmd_bind
        from src.sprawl.bind import ADAPTER_MAP
        cmd_bind(self.test_dir)
        mock_bind.assert_called_once_with(self.test_dir, force=False, targets=list(ADAPTER_MAP.keys()))

    @patch("src.sprawl.bind.bind_adapters")
    def test_cmd_bind_only_flag(self, mock_bind):
        """cmd_bind parses and passes only list to bind_adapters."""
        from src.sprawl.commands.sync_cmd import cmd_bind
        cmd_bind(self.test_dir, only="cursor,copilot")
        mock_bind.assert_called_once_with(self.test_dir, force=False, targets=["cursor", "copilot"])


if __name__ == "__main__":
    unittest.main()
