import unittest
import os
import tempfile
import json
import shutil
from unittest.mock import patch

from sprawl.config import config
from sprawl.sync import sync_app_directory
from sprawl.commands.workspace import cmd_create
from sprawl.exceptions import SprawlError


class TestSyncPathsAndRootPollution(unittest.TestCase):
    """Test suite to verify workspace generation paths and root pollution prevention (TASK-012-04)."""

    def setUp(self):
        self.original_cwd = os.getcwd()
        self.temp_dir = tempfile.mkdtemp()
        os.chdir(self.temp_dir)
        config.dry_run = False
        config.verbose = False
        config.agents_dir_global = os.path.join(self.temp_dir, "global_dna")
        os.makedirs(config.agents_dir_global, exist_ok=True)
        # Create global DNA dummy contents
        os.makedirs(os.path.join(config.agents_dir_global, "rules"), exist_ok=True)
        os.makedirs(os.path.join(config.agents_dir_global, "skills"), exist_ok=True)
        os.makedirs(os.path.join(config.agents_dir_global, "workflows"), exist_ok=True)
        
        with open(os.path.join(config.agents_dir_global, "DESIGN.md"), "w") as f:
            f.write("# Global Design Specs")
        with open(os.path.join(config.agents_dir_global, "rules", "engineering.md"), "w") as f:
            f.write("# Engineering Rules")

    def tearDown(self):
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch('sprawl.workspace.WorkspaceRegistry.register')
    def test_workspace_creation_paths(self, mock_register):
        """Verifies sprawl create scaffolds config files inside .agents/ and not in root."""
        cmd_create("MyWorkspace", path=self.temp_dir)
        ws_path = os.path.join(self.temp_dir, "MyWorkspace")
        
        self.assertTrue(os.path.exists(ws_path))
        self.assertTrue(os.path.exists(os.path.join(ws_path, ".agents", "sprawl_manifest.yml")))
        self.assertTrue(os.path.exists(os.path.join(ws_path, ".agents", "sprawl-config.json")))
        
        # Verify no root pollution from creation
        self.assertFalse(os.path.exists(os.path.join(ws_path, "sprawl_manifest.yml")))
        self.assertFalse(os.path.exists(os.path.join(ws_path, "sprawl-config.json")))
        
        # Verify JSON validity of sprawl-config.json
        with open(os.path.join(ws_path, ".agents", "sprawl-config.json"), "r") as f:
            data = json.load(f)
            self.assertIn("allowed_mounts", data)

    @patch('sprawl.workspace.WorkspaceRegistry.update_sync_timestamp')
    @patch('sprawl.workspace.Workspace.update_sync_state')
    def test_sync_paths_and_root_cleanup(self, mock_state, mock_timestamp):
        """Verifies sprawl sync generates root-level files and cleans up stray root directories."""
        # 1. Create a workspace
        ws_path = os.path.join(self.temp_dir, "SyncWorkspace")
        os.makedirs(ws_path)
        local_agents_dir = os.path.join(ws_path, ".agents")
        os.makedirs(local_agents_dir)
        
        # Write sprawl_manifest.yml
        manifest_content = """# SyncWorkspace
dna: core
rules:
  - engineering.md
skills:
workflows:
"""
        with open(os.path.join(local_agents_dir, "sprawl_manifest.yml"), "w") as f:
            f.write(manifest_content)
            
        # Write default sprawl-config.json
        with open(os.path.join(local_agents_dir, "sprawl-config.json"), "w") as f:
            json.dump({"allowed_mounts": {"my_custom_mount": "/tmp/custom_mount"}}, f)

        # 2. Add some stray/polluted folders in the workspace root
        os.makedirs(os.path.join(ws_path, "atoms"))
        os.makedirs(os.path.join(ws_path, "molecules"))
        os.makedirs(os.path.join(ws_path, "rules"))
        os.makedirs(os.path.join(ws_path, "skills"))
        os.makedirs(os.path.join(ws_path, "workflows"))
        
        # Also add deprecated categories in .agents/
        os.makedirs(os.path.join(local_agents_dir, "atoms"))
        os.makedirs(os.path.join(local_agents_dir, "molecules"))

        # 3. Execute sync
        sync_app_directory(ws_path)

        # 4. Verify Root-Level Exclusions (Human-Agent Interfaces)
        self.assertTrue(os.path.exists(os.path.join(ws_path, "AGENTS.md")), "AGENTS.md should be in root")
        self.assertTrue(os.path.exists(os.path.join(ws_path, "DESIGN.md")), "DESIGN.md should be in root")
        self.assertTrue(os.path.exists(os.path.join(ws_path, "mcp_config.json")), "mcp_config.json should be in root")

        # Verify mounts documentation inside AGENTS.md
        with open(os.path.join(ws_path, "AGENTS.md"), "r") as f:
            agents_md_content = f.read()
            self.assertIn("@my_custom_mount", agents_md_content)
            self.assertIn("/tmp/custom_mount", agents_md_content)
            self.assertIn("except through the allowed mounts mapped via the MCP server", agents_md_content)

        # Verify JSON validity of mcp_config.json
        with open(os.path.join(ws_path, "mcp_config.json"), "r") as f:
            mcp_data = json.load(f)
            self.assertIn("sprawl-workspace-fs", mcp_data["mcpServers"])

        # 5. Verify Hidden Directory Containment (rules, skills, workflows strictly inside .agents/)
        self.assertTrue(os.path.exists(os.path.join(local_agents_dir, "rules", "engineering.md")))
        self.assertTrue(os.path.exists(os.path.join(local_agents_dir, "skills")))
        self.assertTrue(os.path.exists(os.path.join(local_agents_dir, "workflows")))

        # Verify stray root folders were deleted
        self.assertFalse(os.path.exists(os.path.join(ws_path, "atoms")))
        self.assertFalse(os.path.exists(os.path.join(ws_path, "molecules")))
        self.assertFalse(os.path.exists(os.path.join(ws_path, "rules")))
        self.assertFalse(os.path.exists(os.path.join(ws_path, "skills")))
        self.assertFalse(os.path.exists(os.path.join(ws_path, "workflows")))

        # Verify deprecated folders in .agents/ were deleted
        self.assertFalse(os.path.exists(os.path.join(local_agents_dir, "atoms")))
        self.assertFalse(os.path.exists(os.path.join(local_agents_dir, "molecules")))


if __name__ == "__main__":
    unittest.main()
