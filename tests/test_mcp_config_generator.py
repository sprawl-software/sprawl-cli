import unittest
import os
import shutil
import tempfile
import json
import sys
from src.sprawl.generators.mcp_config import generate_mcp_config

class TestMCPConfigGenerator(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.local_agents_dir = os.path.join(self.test_dir, ".agents")
        os.makedirs(self.local_agents_dir)
        self.output_path = os.path.join(self.local_agents_dir, "mcp_config.json")
        self.venv_python = "/path/to/venv/bin/python"

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_generate_basic_config(self):
        reqs = {"molecules": []}
        app_dir = "/my/app"
        
        generate_mcp_config(self.output_path, reqs, app_dir, self.local_agents_dir, self.venv_python)
        
        self.assertTrue(os.path.exists(self.output_path))
        with open(self.output_path, "r") as f:
            config = json.load(f)
            
        self.assertIn("sprawl-workspace-fs", config["mcpServers"])
        self.assertEqual(config["mcpServers"]["sprawl-workspace-fs"]["command"], sys.executable)
        self.assertIn(os.path.abspath(app_dir), config["mcpServers"]["sprawl-workspace-fs"]["args"])
        self.assertNotIn("sprawl-vault", config["mcpServers"])

    def test_generate_with_vault(self):
        reqs = {"molecules": []}
        app_dir = "/my/app"
        vault_path = "~/MyVault"
        
        generate_mcp_config(self.output_path, reqs, app_dir, self.local_agents_dir, self.venv_python, vault_path)
        
        with open(self.output_path, "r") as f:
            config = json.load(f)
            
        self.assertIn("sprawl-vault", config["mcpServers"])
        self.assertIn(os.path.abspath(os.path.expanduser(vault_path)), config["mcpServers"]["sprawl-vault"]["args"])

if __name__ == "__main__":
    unittest.main()
