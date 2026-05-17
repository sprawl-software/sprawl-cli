import unittest
import os
import shutil
import tempfile
import json
from src.sprawl.config import create_config
from src.sprawl.workspace import Workspace

class TestWorkspaceMigration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.workspace_path = os.path.join(self.test_dir, "my-project")
        os.makedirs(self.workspace_path)
        
        # Configure for test mode
        os.environ["SPRAWL_TEST_MODE"] = "1"
        from src.sprawl.config import config
        config.reinitialize()
        config.workspaces_dir = os.path.join(self.test_dir, ".sprawl", "workspaces")
        self.config = config

    def tearDown(self):
        shutil.rmtree(self.test_dir)
        if os.path.exists(self.config.workspaces_dir):
            shutil.rmtree(self.config.workspaces_dir)

    def test_workspace_mgt_dir_generation(self):
        ws = Workspace(self.workspace_path)
        self.assertTrue(ws.mgt_dir.startswith(self.config.workspaces_dir))
        # Ensure it's deterministic
        ws2 = Workspace(self.workspace_path)
        self.assertEqual(ws.mgt_dir, ws2.mgt_dir)

    def test_bind_dna_to_mgt_plane(self):
        ws = Workspace(self.workspace_path)
        ws.bind_dna("python-fastapi")
        
        self.assertTrue(os.path.exists(ws.dna_binding_path))
        with open(ws.dna_binding_path, "r") as f:
            data = json.load(f)
            self.assertEqual(data["alias"], "python-fastapi")
        
        self.assertEqual(ws.get_dna_alias(), "python-fastapi")
        # Ensure no .sprawl_dna in workspace
        self.assertFalse(os.path.exists(os.path.join(self.workspace_path, ".sprawl_dna")))

    def test_legacy_migration(self):
        # Create legacy .sprawl_dna
        legacy_path = os.path.join(self.workspace_path, ".sprawl_dna")
        with open(legacy_path, "w") as f:
            f.write("vanilla-js")
            
        ws = Workspace(self.workspace_path)
        # Should pick up legacy and migrate
        alias = ws.get_dna_alias()
        self.assertEqual(alias, "vanilla-js")
        
        # Verify it migrated to mgt plane
        self.assertTrue(os.path.exists(ws.dna_binding_path))
        with open(ws.dna_binding_path, "r") as f:
            data = json.load(f)
            self.assertEqual(data["alias"], "vanilla-js")

    def test_sync_state_tracking(self):
        ws = Workspace(self.workspace_path)
        ws.update_sync_state({"files_synced": 5})
        
        state = ws.get_sync_state()
        self.assertEqual(state["files_synced"], 5)
        self.assertIn("last_sync_timestamp", state)

if __name__ == "__main__":
    unittest.main()
