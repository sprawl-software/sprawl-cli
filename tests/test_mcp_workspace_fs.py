import os
import shutil
import tempfile
import unittest

from src.sprawl.mcp.workspace_fs import MCPError, MCPServer, WorkspaceFS


class TestWorkspaceFS(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.root = os.path.join(self.test_dir, "workspace")
        os.makedirs(self.root)
        self.fs = WorkspaceFS(self.root)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_read_file_safe(self):
        path = os.path.join(self.root, "test.txt")
        with open(path, "w") as f:
            f.write("hello world")

        content = self.fs.read_file("test.txt")
        self.assertEqual(content, "hello world")

    def test_read_file_unsafe(self):
        with self.assertRaises(MCPError) as cm:
            self.fs.read_file("../outside.txt")
        self.assertEqual(cm.exception.code, -32602)
        self.assertIn("Security Violation", cm.exception.message)

    def test_write_file_safe(self):
        result = self.fs.write_file("new.txt", "data")
        self.assertIn("Successfully wrote", result)

        with open(os.path.join(self.root, "new.txt")) as f:
            self.assertEqual(f.read(), "data")

    def test_write_file_unsafe(self):
        with self.assertRaises(MCPError):
            self.fs.write_file("/etc/passwd", "evil")

    def test_symlink_outside(self):
        outside_file = os.path.join(self.test_dir, "outside.txt")
        with open(outside_file, "w") as f:
            f.write("secret")

        symlink_path = os.path.join(self.root, "link.txt")
        os.symlink(outside_file, symlink_path)

        with self.assertRaises(MCPError) as cm:
            self.fs.read_file("link.txt")
        self.assertEqual(cm.exception.code, -32602)
        self.assertIn("Security Violation", cm.exception.message)

    def test_list_directory(self):
        os.makedirs(os.path.join(self.root, "subdir"))
        with open(os.path.join(self.root, "file.txt"), "w") as f:
            f.write("test")

        items = self.fs.list_directory(".")
        self.assertIn("subdir", items)
        self.assertIn("file.txt", items)


class TestMCPServer(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.fs = WorkspaceFS(self.test_dir)
        self.server = MCPServer(self.fs)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_handle_initialize(self):
        req = {"jsonrpc": "2.0", "id": 1, "method": "initialize"}
        resp = self.server.handle_request(req)
        self.assertEqual(resp["id"], 1)
        self.assertEqual(resp["result"]["serverInfo"]["name"], "sprawl-workspace-fs")

    def test_handle_tools_list(self):
        req = {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
        resp = self.server.handle_request(req)
        tools = resp["result"]["tools"]
        tool_names = [t["name"] for t in tools]
        self.assertIn("read_file", tool_names)
        self.assertIn("write_file", tool_names)
        self.assertIn("list_directory", tool_names)

    def test_handle_tools_call_read(self):
        with open(os.path.join(self.test_dir, "test.txt"), "w") as f:
            f.write("content")

        req = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "read_file", "arguments": {"path": "test.txt"}},
        }
        resp = self.server.handle_request(req)
        self.assertEqual(resp["result"]["content"][0]["text"], "content")

    def test_cli_mounts_access(self):
        mount_dir = os.path.join(self.test_dir, "external_mount")
        os.makedirs(mount_dir)
        test_file = os.path.join(mount_dir, "mounted.txt")
        with open(test_file, "w") as f:
            f.write("from external mount")

        fs_with_mount = WorkspaceFS(self.test_dir, cli_mounts={"ext": mount_dir})
        content = fs_with_mount.read_file("@ext/mounted.txt")
        self.assertEqual(content, "from external mount")

        # Test writing via mount
        fs_with_mount.write_file("@ext/written.txt", "written content")
        with open(os.path.join(mount_dir, "written.txt")) as f:
            self.assertEqual(f.read(), "written content")

    def test_cli_mounts_tools_list(self):
        mount_dir = os.path.join(self.test_dir, "external_mount")
        os.makedirs(mount_dir)
        fs = WorkspaceFS(self.test_dir, cli_mounts={"ext_lib": mount_dir})
        server = MCPServer(fs)

        req = {"jsonrpc": "2.0", "id": 10, "method": "tools/list"}
        resp = server.handle_request(req)
        tools = resp["result"]["tools"]
        read_file_tool = next(t for t in tools if t["name"] == "read_file")
        self.assertIn("@ext_lib", read_file_tool["description"])

    def test_maybe_dispatch_mcp_stdio_routing(self):
        from unittest.mock import patch

        from src.sprawl.cli import maybe_dispatch_mcp_stdio

        with (
            patch("src.sprawl.mcp.workspace_fs.run_workspace_fs_cli") as mock_wfs,
            patch("src.sprawl.mcp.vault.run_vault_cli") as mock_vault,
        ):
            self.assertFalse(maybe_dispatch_mcp_stdio(["sync"]))
            self.assertTrue(
                maybe_dispatch_mcp_stdio(
                    ["-m", "sprawl.mcp.workspace_fs", self.test_dir, "--mount", "a=/tmp"]
                )
            )
            mock_wfs.assert_called_once_with([self.test_dir, "--mount", "a=/tmp"])

            mock_wfs.reset_mock()
            self.assertTrue(maybe_dispatch_mcp_stdio(["mcp", "workspace-fs", self.test_dir]))
            mock_wfs.assert_called_once_with([self.test_dir])

            self.assertTrue(maybe_dispatch_mcp_stdio(["-m", "sprawl.mcp.vault", self.test_dir]))
            mock_vault.assert_called_once_with([self.test_dir])

    def test_live_refresh_mounts_and_cwd_discovery(self):
        import json

        from src.sprawl.mcp.workspace_fs import discover_cwd_workspace

        agents_dir = os.path.join(self.test_dir, ".agents")
        os.makedirs(agents_dir, exist_ok=True)
        with open(os.path.join(agents_dir, "sprawl_manifest.yml"), "w", encoding="utf-8") as f:
            f.write("dna: core\n")
        cfg_path = os.path.join(agents_dir, "sprawl-config.json")
        with open(cfg_path, "w", encoding="utf-8") as f:
            json.dump({"allowed_mounts": {}}, f)

        self.assertEqual(discover_cwd_workspace(self.test_dir), os.path.abspath(self.test_dir))
        subdir = os.path.join(self.test_dir, "nested", "dir")
        os.makedirs(subdir, exist_ok=True)
        self.assertEqual(discover_cwd_workspace(subdir), os.path.abspath(self.test_dir))

        fs = WorkspaceFS(self.test_dir)
        server = MCPServer(fs)
        self.assertEqual(fs.allowed_mounts, {})

        # Dynamically add a mount to sprawl-config.json while server is already instantiated
        mount_dir = os.path.join(self.test_dir, "live_mount")
        os.makedirs(mount_dir, exist_ok=True)
        with open(os.path.join(mount_dir, "hello.txt"), "w", encoding="utf-8") as f:
            f.write("live reloaded")
        with open(cfg_path, "w", encoding="utf-8") as f:
            json.dump({"allowed_mounts": {"live": mount_dir}}, f)

        self.assertEqual(fs.read_file("@live/hello.txt"), "live reloaded")
        resp = server.handle_request({"jsonrpc": "2.0", "id": 99, "method": "tools/list"})
        self.assertIn("@live", resp["result"]["tools"][0]["description"])


if __name__ == "__main__":
    unittest.main()
