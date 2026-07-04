import os
import json
import unittest
import tempfile
import shutil
from unittest.mock import patch

from src.sprawl.config import create_config, config
from src.sprawl.workspace import (
    register_workspace, deregister_workspace, get_workspace_info,
    get_all_workspaces, update_workspace_sync_timestamp,
    load_workspace_registry, WorkspaceError
)


class TestWorkspaceRegistry(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        self.workspace_registry_path = os.path.join(self.test_dir, "workspaces.json")
        
        # Mock the config's workspace_registry_path
        self.patcher = patch("src.sprawl.workspace.config.workspace_registry_path", self.workspace_registry_path)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        shutil.rmtree(self.test_dir)

    def test_load_empty(self):
        data = load_workspace_registry()
        self.assertEqual(data, {})

    def test_register_new_workspace(self):
        register_workspace("test-ws", "/tmp/test-ws", "github.com/test/dna")
        data = load_workspace_registry()
        self.assertIn("test-ws", data)
        self.assertEqual(data["test-ws"]["path"], os.path.abspath("/tmp/test-ws"))
        self.assertEqual(data["test-ws"]["dna_source"], "github.com/test/dna")
        self.assertIsNone(data["test-ws"]["last_sync_timestamp"])

    def test_register_update_existing(self):
        register_workspace("test-ws", "/tmp/test-ws")
        register_workspace("test-ws", "/tmp/test-ws-2", "new-dna")
        
        data = load_workspace_registry()
        self.assertEqual(data["test-ws"]["path"], os.path.abspath("/tmp/test-ws-2"))
        self.assertEqual(data["test-ws"]["dna_source"], "new-dna")

    def test_deregister(self):
        register_workspace("test-ws", "/tmp/test-ws")
        self.assertIn("test-ws", get_all_workspaces())
        
        deregister_workspace("test-ws")
        self.assertNotIn("test-ws", get_all_workspaces())
        
        with self.assertRaises(WorkspaceError):
            deregister_workspace("nonexistent")

    def test_get(self):
        register_workspace("test-ws", "/tmp/test-ws")
        ws = get_workspace_info("test-ws")
        self.assertIsNotNone(ws)
        self.assertEqual(ws["path"], os.path.abspath("/tmp/test-ws"))
        
        self.assertIsNone(get_workspace_info("missing"))

    def test_update_sync_timestamp(self):
        register_workspace("test-ws", "/tmp/test-ws")
        ws_before = get_workspace_info("test-ws")
        self.assertIsNone(ws_before["last_sync_timestamp"])
        
        update_workspace_sync_timestamp("test-ws")
        
        ws_after = get_workspace_info("test-ws")
        self.assertIsNotNone(ws_after["last_sync_timestamp"])

        with self.assertRaises(WorkspaceError):
            update_workspace_sync_timestamp("missing")

if __name__ == "__main__":
    unittest.main()
