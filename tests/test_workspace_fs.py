"""Tests for secure dynamic MCP directory mounting in workspace_fs."""

import os
import shutil
import tempfile
import json
import unittest

from src.sprawl.mcp.workspace_fs import WorkspaceFS, MCPError


class TestWorkspaceFSMounting(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.workspace_root = os.path.join(self.temp_dir, "workspace")
        os.makedirs(self.workspace_root)
        
        self.mount_root = os.path.join(self.temp_dir, "shared_library")
        os.makedirs(self.mount_root)
        
        # Scaffold sprawl-config.json with allowed_mounts
        agents_dir = os.path.join(self.workspace_root, ".agents")
        os.makedirs(agents_dir)
        
        self.config_data = {
            "allowed_mounts": {
                "shared_lib": self.mount_root
            }
        }
        
        with open(os.path.join(agents_dir, "sprawl-config.json"), "w") as f:
            json.dump(self.config_data, f)
            
        self.fs = WorkspaceFS(self.workspace_root)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_read_write_mounted_directory(self):
        """WorkspaceFS correctly reads and writes files inside the mounted directory."""
        content = "print('hello')"
        res = self.fs.write_file("@shared_lib/hello.py", content)
        self.assertIn("Successfully wrote to", res)
        
        # Assert file was written to the mount root
        real_file = os.path.join(self.mount_root, "hello.py")
        self.assertTrue(os.path.exists(real_file))
        
        # Read file back via MCP
        read_content = self.fs.read_file("@shared_lib/hello.py")
        self.assertEqual(read_content, content)

    def test_list_mounted_directory(self):
        """WorkspaceFS correctly lists directories inside the mounted directory."""
        self.fs.write_file("@shared_lib/a.py", "a")
        self.fs.write_file("@shared_lib/b.py", "b")
        
        items = self.fs.list_directory("@shared_lib")
        self.assertIn("a.py", items)
        self.assertIn("b.py", items)

    def test_unconfigured_mount_throws(self):
        """Accessing a mount alias that is not configured throws MCPError."""
        with self.assertRaises(MCPError) as context:
            self.fs.read_file("@not_configured/file.py")
        self.assertIn("Mount alias 'not_configured' is not allowed", context.exception.message)

    def test_mount_containment_violation_throws(self):
        """Directory traversal escaping the mount root is blocked and throws MCPError."""
        # Write a file outside the mount root
        outside_file = os.path.join(self.temp_dir, "secret.txt")
        with open(outside_file, "w") as f:
            f.write("secret data")
            
        with self.assertRaises(MCPError) as context:
            # Attempt to traverse up out of the mount
            self.fs.read_file("@shared_lib/../secret.txt")
        self.assertIn("resolves outside mount root", context.exception.message)


if __name__ == "__main__":
    unittest.main()
