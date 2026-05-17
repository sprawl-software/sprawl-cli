"""Tests for sprawl bind adapter engine."""

import unittest
import os
import json
import shutil
import tempfile
from src.sprawl.bind import bind_adapters


class TestBind(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.agents_dir = os.path.join(self.test_dir, ".agents")
        os.makedirs(self.agents_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_bind_creates_cursorrules(self):
        """bind_adapters creates .cursorrules with correct content."""
        self.assertTrue(bind_adapters(self.test_dir))
        cursor_file = os.path.join(self.test_dir, ".cursorrules")
        self.assertTrue(os.path.exists(cursor_file))
        with open(cursor_file, "r") as f:
            content = f.read()
        self.assertIn("# Agentic Workspace Directives", content)
        self.assertIn("AGENTS.md", content)

    def test_bind_creates_clinerules(self):
        """bind_adapters creates .clinerules."""
        bind_adapters(self.test_dir)
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, ".clinerules")))

    def test_bind_creates_windsurfrules(self):
        """bind_adapters creates .windsurfrules."""
        bind_adapters(self.test_dir)
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, ".windsurfrules")))

    def test_bind_creates_copilot_instructions(self):
        """bind_adapters creates .github/copilot-instructions.md."""
        bind_adapters(self.test_dir)
        copilot = os.path.join(self.test_dir, ".github", "copilot-instructions.md")
        self.assertTrue(os.path.exists(copilot))

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

        with open(cursor_file, "r") as f:
            content = f.read()
        self.assertEqual(content, original)

    def test_bind_with_force_overwrites_existing(self):
        """bind_adapters overwrites existing files when force=True."""
        cursor_file = os.path.join(self.test_dir, ".cursorrules")
        with open(cursor_file, "w") as f:
            f.write("OLD CONTENT")

        bind_adapters(self.test_dir, force=True)

        with open(cursor_file, "r") as f:
            content = f.read()
        self.assertIn("# Agentic Workspace Directives", content)
        self.assertNotIn("OLD CONTENT", content)

    def test_bind_no_agents_dir_returns_false(self):
        """bind_adapters returns False when .agents/ doesn't exist."""
        empty_dir = tempfile.mkdtemp()
        try:
            result = bind_adapters(empty_dir)
            self.assertFalse(result)
        finally:
            shutil.rmtree(empty_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
