"""Tests for graft.py edge cases — directive skipping, individual adapters, and unified interface."""

import os
import shutil
import tempfile
import unittest

from src.sprawl.graft import (
    FileHarvestAdapter,
    PromptsFolderAdapter,
    HarvestAdapter,
    harvest_legacy_rules,
)


class TestFileHarvestAdapterEdgeCases(unittest.TestCase):
    """Edge-case tests for the FileHarvestAdapter (formerly BaseHarvestAdapter)."""

    def setUp(self):
        self.root_dir = tempfile.mkdtemp()
        self.dest_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.root_dir, ignore_errors=True)
        shutil.rmtree(self.dest_dir, ignore_errors=True)

    def test_skips_sprawl_generated_directives(self):
        """Adapter skips files containing Sprawl's own 'Agentic Workspace Directives' sentinel."""
        with open(os.path.join(self.root_dir, ".cursorrules"), "w") as f:
            f.write("# Agentic Workspace Directives\nThese are generated.\n")

        adapter = FileHarvestAdapter(".cursorrules", "cursor")
        self.assertTrue(adapter.matches(self.root_dir))
        result = adapter.harvest(self.root_dir, self.dest_dir)
        self.assertEqual(result, [])

    def test_skips_sprawl_generated_behavior_sentinel(self):
        """Adapter skips files containing the 'behavior and knowledge base' sentinel."""
        with open(os.path.join(self.root_dir, ".clinerules"), "w") as f:
            f.write("Your behavior and knowledge base for this workspace are defined here.\n")

        adapter = FileHarvestAdapter(".clinerules", "cline")
        result = adapter.harvest(self.root_dir, self.dest_dir)
        self.assertEqual(result, [])

    def test_skips_empty_file(self):
        """Adapter skips empty or whitespace-only files."""
        with open(os.path.join(self.root_dir, ".windsurfrules"), "w") as f:
            f.write("   \n\n  \t  \n")

        adapter = FileHarvestAdapter(".windsurfrules", "windsurf")
        result = adapter.harvest(self.root_dir, self.dest_dir)
        self.assertEqual(result, [])

    def test_harvests_clinerules(self):
        """Adapter harvests .clinerules content correctly."""
        with open(os.path.join(self.root_dir, ".clinerules"), "w") as f:
            f.write("cline custom rules")

        adapter = FileHarvestAdapter(".clinerules", "cline")
        result = adapter.harvest(self.root_dir, self.dest_dir)
        self.assertEqual(result, ["rules/local_cline.md"])
        with open(os.path.join(self.dest_dir, "rules", "local_cline.md")) as f:
            self.assertEqual(f.read(), "cline custom rules")

    def test_harvests_windsurfrules(self):
        """Adapter harvests .windsurfrules content correctly."""
        with open(os.path.join(self.root_dir, ".windsurfrules"), "w") as f:
            f.write("windsurf config")

        adapter = FileHarvestAdapter(".windsurfrules", "windsurf")
        result = adapter.harvest(self.root_dir, self.dest_dir)
        self.assertEqual(result, ["rules/local_windsurf.md"])

    def test_harvests_claude_md(self):
        """Adapter harvests CLAUDE.md content correctly."""
        with open(os.path.join(self.root_dir, "CLAUDE.md"), "w") as f:
            f.write("claude memory rules")

        adapter = FileHarvestAdapter("CLAUDE.md", "claude")
        result = adapter.harvest(self.root_dir, self.dest_dir)
        self.assertEqual(result, ["rules/local_claude.md"])

    def test_harvests_agents_md(self):
        """Adapter harvests AGENTS.md content correctly."""
        with open(os.path.join(self.root_dir, "AGENTS.md"), "w") as f:
            f.write("agent instructions")

        adapter = FileHarvestAdapter("AGENTS.md", "agent")
        result = adapter.harvest(self.root_dir, self.dest_dir)
        self.assertEqual(result, ["rules/local_agent.md"])

    def test_nonexistent_file_returns_empty(self):
        """Adapter returns empty list for a file that doesn't exist on disk."""
        adapter = FileHarvestAdapter(".cursorrules", "cursor")
        self.assertFalse(adapter.matches(self.root_dir))
        result = adapter.harvest(self.root_dir, self.dest_dir)
        self.assertEqual(result, [])


class TestAdapterInterfaceConsistency(unittest.TestCase):
    """Tests that all adapters implement the HarvestAdapter ABC consistently."""

    def test_file_adapter_is_harvest_adapter(self):
        """FileHarvestAdapter must be a subclass of HarvestAdapter."""
        adapter = FileHarvestAdapter(".cursorrules", "cursor")
        self.assertIsInstance(adapter, HarvestAdapter)

    def test_prompts_folder_adapter_is_harvest_adapter(self):
        """PromptsFolderAdapter must be a subclass of HarvestAdapter."""
        adapter = PromptsFolderAdapter()
        self.assertIsInstance(adapter, HarvestAdapter)

    def test_all_adapters_return_list(self):
        """harvest() must always return a list (never None or a string)."""
        root = tempfile.mkdtemp()
        dest = tempfile.mkdtemp()
        try:
            adapters = [
                FileHarvestAdapter(".cursorrules", "cursor"),
                FileHarvestAdapter("CLAUDE.md", "claude"),
                PromptsFolderAdapter(),
            ]
            for adapter in adapters:
                result = adapter.harvest(root, dest)
                self.assertIsInstance(result, list,
                    f"{adapter.__class__.__name__}.harvest() returned {type(result).__name__}, expected list")
        finally:
            shutil.rmtree(root, ignore_errors=True)
            shutil.rmtree(dest, ignore_errors=True)


class TestHarvestLegacyRulesIntegration(unittest.TestCase):
    """Integration test for the full harvest_legacy_rules() orchestrator."""

    def setUp(self):
        self.root_dir = tempfile.mkdtemp()
        self.dest_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.root_dir, ignore_errors=True)
        shutil.rmtree(self.dest_dir, ignore_errors=True)

    def test_harvests_multiple_formats(self):
        """harvest_legacy_rules collects files from multiple adapter formats."""
        with open(os.path.join(self.root_dir, ".cursorrules"), "w") as f:
            f.write("cursor rules")
        with open(os.path.join(self.root_dir, "CLAUDE.md"), "w") as f:
            f.write("claude rules")
        with open(os.path.join(self.root_dir, ".windsurfrules"), "w") as f:
            f.write("windsurf rules")

        result = harvest_legacy_rules(self.root_dir, self.dest_dir)
        self.assertIn("rules/local_cursor.md", result)
        self.assertIn("rules/local_claude.md", result)
        self.assertIn("rules/local_windsurf.md", result)
        self.assertEqual(len(result), 3)

    def test_empty_project_returns_empty(self):
        """harvest_legacy_rules returns empty list for a project with no legacy configs."""
        result = harvest_legacy_rules(self.root_dir, self.dest_dir)
        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
