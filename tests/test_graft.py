"""Tests for universal workspace harvesting adapter framework."""

import os
import shutil
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from src.sprawl.commands.workspace import cmd_graft
from src.sprawl.sync import sync_app_directory, parse_sprawl_manifest
from src.sprawl.commands.diff import diff_files
from src.sprawl.config import config


class TestGraftHarvesting(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)

        # Redirect config to a temp folder inside test_dir
        self.global_dir = os.path.join(self.test_dir, "global_sprawl")
        os.makedirs(self.global_dir)
        self.config_file = os.path.join(self.global_dir, "config.json")
        with open(self.config_file, "w") as f:
            f.write("{}")
        self.original_config_path = config.config_path
        config.config_path = self.config_file

        # Create some legacy configs
        self.cursorrules = os.path.join(self.test_dir, ".cursorrules")
        with open(self.cursorrules, "w") as f:
            f.write("legacy cursor rules")

        self.prompts_dir = os.path.join(self.test_dir, ".github", "prompts")
        os.makedirs(self.prompts_dir)
        self.prompt_file = os.path.join(self.prompts_dir, "test.prompt.md")
        with open(self.prompt_file, "w") as f:
            f.write("legacy custom prompt")

        # Set mock config attributes
        config.dry_run = False

    def tearDown(self):
        config.config_path = self.original_config_path
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_graft_harvests_legacy_files(self):
        """cmd_graft harvests .cursorrules and .github/prompts/ into local_rules in manifest."""
        cmd_graft()

        local_agents_dir = os.path.join(self.test_dir, ".agents")
        manifest_path = os.path.join(local_agents_dir, "sprawl_manifest.yml")
        self.assertTrue(os.path.exists(manifest_path))

        # Check harvested rules files exist in .agents/rules/
        self.assertTrue(os.path.exists(os.path.join(local_agents_dir, "rules", "local_cursor.md")))
        self.assertTrue(os.path.exists(os.path.join(local_agents_dir, "rules", "local_test.md")))

        # Check manifest contents
        reqs = parse_sprawl_manifest(manifest_path)
        self.assertIn("local_cursor.md", reqs.get("local_rules", []))
        self.assertIn("local_test.md", reqs.get("local_rules", []))

    @patch("src.sprawl.utils.get_active_dna_context")
    def test_sync_retains_local_rules(self, mock_get_dna):
        """sync does not prune harvested local rules from local rules folder."""
        cmd_graft()
        local_agents_dir = os.path.join(self.test_dir, ".agents")
        
        # Mock global dna directory
        global_dna = tempfile.mkdtemp()
        os.makedirs(os.path.join(global_dna, "rules"))
        mock_get_dna.return_value = global_dna

        try:
            stats = sync_app_directory(self.test_dir)
            # Ensure local_cursor.md is not pruned
            self.assertTrue(os.path.exists(os.path.join(local_agents_dir, "rules", "local_cursor.md")))
        finally:
            shutil.rmtree(global_dna, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
