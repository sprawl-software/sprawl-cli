import unittest
import os
import shutil
import tempfile
import json
import sys
from io import StringIO
from src.sprawl.mcp.workspace_fs import WorkspaceFS, MCPServer, MCPError

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
        
        with open(os.path.join(self.root, "new.txt"), "r") as f:
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
            "params": {
                "name": "read_file",
                "arguments": {"path": "test.txt"}
            }
        }
        resp = self.server.handle_request(req)
        self.assertEqual(resp["result"]["content"][0]["text"], "content")

if __name__ == "__main__":
    unittest.main()
