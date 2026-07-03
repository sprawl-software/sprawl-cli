"""Tests for the P0 security fix in workspace_fs path containment.

Tests the sibling-directory prefix escape that was patched in the
startswith() path containment check.
"""

import os
import shutil
import tempfile
import json
import unittest

from src.sprawl.mcp.workspace_fs import WorkspaceFS, MCPError


class TestWorkspaceFSSiblingDirectoryEscape(unittest.TestCase):
    """Tests for the patched sibling-directory prefix escape vulnerability."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

        # Create workspace root: /tmp/xxx/mount
        self.workspace_root = os.path.join(self.temp_dir, "mount")
        os.makedirs(self.workspace_root)

        # Create a sibling dir that shares a prefix: /tmp/xxx/mount-secrets
        self.sibling_dir = os.path.join(self.temp_dir, "mount-secrets")
        os.makedirs(self.sibling_dir)
        with open(os.path.join(self.sibling_dir, "secret.txt"), "w") as f:
            f.write("top secret data")

        # Create mount root: /tmp/xxx/mnt
        self.mount_root = os.path.join(self.temp_dir, "mnt")
        os.makedirs(self.mount_root)

        # Create a sibling of mount root: /tmp/xxx/mnt-private
        self.mount_sibling = os.path.join(self.temp_dir, "mnt-private")
        os.makedirs(self.mount_sibling)
        with open(os.path.join(self.mount_sibling, "private.txt"), "w") as f:
            f.write("private data")

        # Scaffold sprawl-config.json with allowed_mounts
        agents_dir = os.path.join(self.workspace_root, ".agents")
        os.makedirs(agents_dir)
        config_data = {
            "allowed_mounts": {
                "lib": self.mount_root
            }
        }
        with open(os.path.join(agents_dir, "sprawl-config.json"), "w") as f:
            json.dump(config_data, f)

        self.fs = WorkspaceFS(self.workspace_root)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_workspace_root_sibling_escape_blocked(self):
        """A workspace named 'mount' must not allow access to sibling 'mount-secrets'."""
        # The old startswith("/tmp/xxx/mount") would match "/tmp/xxx/mount-secrets/secret.txt"
        # This must now raise MCPError
        with self.assertRaises(MCPError) as context:
            # Construct a relative path that would resolve to mount-secrets
            # We need to go up from workspace root and into mount-secrets
            self.fs._get_safe_path("../mount-secrets/secret.txt")
        self.assertIn("resolves outside workspace root", context.exception.message)

    def test_mount_sibling_escape_blocked(self):
        """A mount alias 'lib' pointing to 'mnt' must not allow access to sibling 'mnt-private'."""
        with self.assertRaises(MCPError) as context:
            self.fs._get_safe_path("@lib/../mnt-private/private.txt")
        self.assertIn("resolves outside mount root", context.exception.message)

    def test_exact_root_path_still_works(self):
        """Accessing the workspace root directory itself (path '.') must still work."""
        safe_path = self.fs._get_safe_path(".")
        self.assertEqual(os.path.realpath(safe_path), os.path.realpath(self.workspace_root))

    def test_exact_mount_root_still_works(self):
        """Accessing the mount root directory itself (path '@lib') must still work."""
        safe_path = self.fs._get_safe_path("@lib")
        self.assertEqual(os.path.realpath(safe_path), os.path.realpath(self.mount_root))

    def test_normal_mount_subpath_still_works(self):
        """Normal sub-paths inside the mount root must still resolve correctly."""
        # Create a file inside the mount root
        os.makedirs(os.path.join(self.mount_root, "src"), exist_ok=True)
        with open(os.path.join(self.mount_root, "src", "main.py"), "w") as f:
            f.write("print('hello')")

        safe_path = self.fs._get_safe_path("@lib/src/main.py")
        self.assertEqual(
            os.path.realpath(safe_path),
            os.path.realpath(os.path.join(self.mount_root, "src", "main.py"))
        )


class TestWorkspaceFSRootSiblingWithIO(unittest.TestCase):
    """Tests that actual I/O operations on workspace sibling dirs are blocked."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

        self.workspace_root = os.path.join(self.temp_dir, "project")
        os.makedirs(self.workspace_root)

        self.sibling = os.path.join(self.temp_dir, "project-private")
        os.makedirs(self.sibling)
        with open(os.path.join(self.sibling, "data.txt"), "w") as f:
            f.write("sensitive")

        agents_dir = os.path.join(self.workspace_root, ".agents")
        os.makedirs(agents_dir)
        with open(os.path.join(agents_dir, "sprawl-config.json"), "w") as f:
            json.dump({"allowed_mounts": {}}, f)

        self.fs = WorkspaceFS(self.workspace_root)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_read_file_sibling_blocked(self):
        """read_file must block reads from workspace root sibling directories."""
        with self.assertRaises(MCPError):
            self.fs.read_file("../project-private/data.txt")

    def test_write_file_sibling_blocked(self):
        """write_file must block writes to workspace root sibling directories."""
        with self.assertRaises(MCPError):
            self.fs.write_file("../project-private/injected.txt", "pwned")
        # Verify file was NOT written
        self.assertFalse(os.path.exists(os.path.join(self.sibling, "injected.txt")))

    def test_list_directory_sibling_blocked(self):
        """list_directory must block listing of workspace root sibling directories."""
        with self.assertRaises(MCPError):
            self.fs.list_directory("../project-private")


if __name__ == "__main__":
    unittest.main()
