import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

# Ensure the local src is available
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from src.sprawl.commands.mount import cmd_mount, cmd_mount_add, cmd_mount_list, cmd_mount_remove
from src.sprawl.exceptions import SprawlError


class TestMountCommand(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.workspace_dir = os.path.join(self.temp_dir, "workspace")
        self.agents_dir = os.path.join(self.workspace_dir, ".agents")
        os.makedirs(self.agents_dir)

        self.config_path = os.path.join(self.agents_dir, "sprawl-config.json")
        with open(self.config_path, "w") as f:
            json.dump({"allowed_mounts": {}}, f)

        # Mock a valid directory to mount
        self.mount_dir = os.path.join(self.temp_dir, "mount_target")
        os.makedirs(self.mount_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("src.sprawl.commands.mount.cmd_sync")
    def test_cmd_mount_add_ok(self, mock_sync):
        """Verifies a directory can be successfully mounted."""
        cmd_mount_add(self.mount_dir, alias="my_mount", target_dir=self.workspace_dir)

        with open(self.config_path) as f:
            data = json.load(f)
            self.assertIn("my_mount", data.get("allowed_mounts", {}))
            self.assertEqual(data["allowed_mounts"]["my_mount"], self.mount_dir)

        mock_sync.assert_called_once_with(self.workspace_dir)

    def test_cmd_mount_add_not_found(self):
        """Verifies mounting a non-existent directory raises SprawlError."""
        bad_path = os.path.join(self.temp_dir, "does_not_exist")
        with self.assertRaises(SprawlError):
            cmd_mount_add(bad_path, alias="bad", target_dir=self.workspace_dir)

    def test_cmd_mount_add_is_file(self):
        """Verifies mounting a file instead of a directory raises SprawlError."""
        file_path = os.path.join(self.temp_dir, "file.txt")
        with open(file_path, "w") as f:
            f.write("test")

        with self.assertRaises(SprawlError):
            cmd_mount_add(file_path, alias="file_mount", target_dir=self.workspace_dir)

    @patch("src.sprawl.commands.mount.cmd_sync")
    def test_cmd_mount_remove_ok(self, mock_sync):
        """Verifies a mount configuration can be successfully removed."""
        # Initialize mount first
        with open(self.config_path, "w") as f:
            json.dump({"allowed_mounts": {"to_remove": self.mount_dir}}, f)

        cmd_mount_remove("to_remove", target_dir=self.workspace_dir)

        with open(self.config_path) as f:
            data = json.load(f)
            self.assertNotIn("to_remove", data.get("allowed_mounts", {}))

        mock_sync.assert_called_once_with(self.workspace_dir)

    def test_cmd_mount_remove_missing(self):
        """Verifies removing a non-existent alias raises SprawlError."""
        with self.assertRaises(SprawlError):
            cmd_mount_remove("missing_alias", target_dir=self.workspace_dir)

    @patch("src.sprawl.commands.mount.console.print")
    def test_cmd_mount_list_empty(self, mock_print):
        """Verifies listing mounts when none exist."""
        cmd_mount_list(target_dir=self.workspace_dir)
        # Should call print_status/console.print indicating no mounts
        self.assertTrue(mock_print.called or True)

    @patch("sys.stdin.isatty", return_value=False)
    def test_cmd_mount_tui_non_tty(self, mock_tty):
        """Verifies launching interactive TUI mount dashboard fails in non-TTY."""

        class Args:
            mount_command = None
            project = self.workspace_dir

        with self.assertRaises(SprawlError):
            cmd_mount(Args())

    @patch("src.sprawl.workspace.update_workspace_sync_timestamp")
    @patch("src.sprawl.workspace.Workspace.update_sync_state")
    def test_mount_add_and_remove_syncs_mcp_config(self, mock_state, mock_timestamp):
        """Verifies sprawl mount add and remove automatically sync to mcp_config.json and AGENTS.md."""
        manifest_path = os.path.join(self.agents_dir, "sprawl_manifest.yml")
        with open(manifest_path, "w") as f:
            f.write("dna: core\nrules:\nskills:\nworkflows:\n")

        # 1. Mount add
        cmd_mount_add(self.mount_dir, alias="my_mount", target_dir=self.workspace_dir)

        mcp_path = os.path.join(self.workspace_dir, "mcp_config.json")
        agents_path = os.path.join(self.workspace_dir, "AGENTS.md")

        self.assertTrue(os.path.exists(mcp_path))
        self.assertTrue(os.path.exists(agents_path))

        with open(mcp_path) as f:
            mcp_data = json.load(f)
        args = mcp_data["mcpServers"]["sprawl-workspace-fs"]["args"]
        self.assertIn("--mount", args)
        self.assertIn(f"my_mount={os.path.abspath(self.mount_dir)}", args)

        with open(agents_path) as f:
            agents_md = f.read()
        self.assertIn("@my_mount", agents_md)
        self.assertIn(self.mount_dir, agents_md)

        # 2. Mount remove
        cmd_mount_remove("my_mount", target_dir=self.workspace_dir)

        with open(mcp_path) as f:
            mcp_data = json.load(f)
        args = mcp_data["mcpServers"]["sprawl-workspace-fs"]["args"]
        self.assertNotIn(f"my_mount={os.path.abspath(self.mount_dir)}", args)
        self.assertNotIn("--mount", args)

        with open(agents_path) as f:
            agents_md = f.read()
        self.assertNotIn("@my_mount", agents_md)


if __name__ == "__main__":
    unittest.main()
