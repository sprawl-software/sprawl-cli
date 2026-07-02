"""Tests for sprawl wipe uninstall command."""

import os
import shutil
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from src.sprawl.commands.wipe import cmd_wipe
from src.sprawl.config import config
from src.sprawl.exceptions import SprawlError


class TestWipe(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.local_agents = os.path.join(self.test_dir, ".agents")
        os.makedirs(self.local_agents)

        # Create dummy rules files
        self.cursorrules = os.path.join(self.test_dir, ".cursorrules")
        self.clinerules = os.path.join(self.test_dir, ".clinerules")
        with open(self.cursorrules, "w") as f:
            f.write("dummy")
        with open(self.clinerules, "w") as f:
            f.write("dummy")

        # Create dummy global config directory
        self.global_dir = os.path.join(self.test_dir, "global_sprawl")
        os.makedirs(self.global_dir)
        self.config_file = os.path.join(self.global_dir, "config.json")
        with open(self.config_file, "w") as f:
            f.write("{}")

        # Create dummy ~/.sprawl_rc override
        self.sprawl_rc = os.path.join(self.test_dir, ".sprawl_rc")
        with open(self.sprawl_rc, "w") as f:
            f.write("dummy")

        # Patch config path
        self.original_config_path = config.config_path
        config.config_path = self.config_file

    def tearDown(self):
        config.config_path = self.original_config_path
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @patch("src.sprawl.commands.wipe.os.path.expanduser")
    @patch("src.sprawl.workspace.WorkspaceRegistry.get_all")
    def test_wipe_local_only(self, mock_get_all, mock_expanduser):
        """wipe local_only deletes .agents/ but leaves global registry and sprawl_rc intact."""
        mock_expanduser.return_value = self.sprawl_rc
        cmd_wipe(target_dir=self.test_dir, force=True, local_only=True)

        self.assertFalse(os.path.exists(self.local_agents))
        self.assertTrue(os.path.exists(self.global_dir))
        self.assertTrue(os.path.exists(self.sprawl_rc))
        self.assertTrue(os.path.exists(self.cursorrules))

    @patch("src.sprawl.commands.wipe.os.path.expanduser")
    @patch("src.sprawl.workspace.WorkspaceRegistry.get_all")
    def test_wipe_nuclear_purges_everything(self, mock_get_all, mock_expanduser):
        """wipe nuclear deletes local workspace, global registry, sprawl_rc, and cleans adapter files."""
        mock_expanduser.return_value = self.sprawl_rc
        mock_get_all.return_value = {
            "my_workspace": {
                "path": self.test_dir
            }
        }

        cmd_wipe(target_dir=self.test_dir, force=True, local_only=False)

        self.assertFalse(os.path.exists(self.local_agents))
        self.assertFalse(os.path.exists(self.global_dir))
        self.assertFalse(os.path.exists(self.sprawl_rc))
        self.assertFalse(os.path.exists(self.cursorrules))
        self.assertFalse(os.path.exists(self.clinerules))


if __name__ == "__main__":
    unittest.main()
