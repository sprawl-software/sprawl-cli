import unittest
import os
import shutil
import tempfile
import json
from src.sprawl.mcp.vault import VaultManager, MCPServer, MCPError

class TestVaultManager(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.vault_root = os.path.join(self.test_dir, "my-vault")
        os.makedirs(self.vault_root)
        self.mgr = VaultManager(self.vault_root)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_read_note_with_extension(self):
        path = os.path.join(self.vault_root, "Idea.md")
        with open(path, "w") as f:
            f.write("brilliant idea")
        
        content = self.mgr.read_note("Idea.md")
        self.assertEqual(content, "brilliant idea")

    def test_read_note_without_extension(self):
        path = os.path.join(self.vault_root, "Idea.md")
        with open(path, "w") as f:
            f.write("brilliant idea")
        
        # Should auto-append .md
        content = self.mgr.read_note("Idea")
        self.assertEqual(content, "brilliant idea")

    def test_read_note_unsafe(self):
        with self.assertRaises(MCPError):
            self.mgr.read_note("../../etc/passwd")

    def test_write_note(self):
        self.mgr.write_note("Draft", "some content")
        path = os.path.join(self.vault_root, "Draft.md")
        self.assertTrue(os.path.exists(path))
        with open(path, "r") as f:
            self.assertEqual(f.read(), "some content")

    def test_search_notes(self):
        self.mgr.write_note("Note1", "The quick brown fox")
        self.mgr.write_note("Note2", "Jumps over the lazy dog")
        
        results = self.mgr.search_notes("fox")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["path"], "Note1.md")
        
        results = self.mgr.search_notes("the")
        self.assertEqual(len(results), 2)

class TestVaultMCPServer(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.mgr = VaultManager(self.test_dir)
        self.server = MCPServer(self.mgr)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_handle_initialize(self):
        req = {"jsonrpc": "2.0", "id": 1, "method": "initialize"}
        resp = self.server.handle_request(req)
        self.assertEqual(resp["result"]["serverInfo"]["name"], "sprawl-vault")

    def test_handle_tools_list(self):
        req = {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
        resp = self.server.handle_request(req)
        tool_names = [t["name"] for t in resp["result"]["tools"]]
        self.assertIn("read_note", tool_names)
        self.assertIn("write_note", tool_names)
        self.assertIn("search_notes", tool_names)

if __name__ == "__main__":
    unittest.main()
