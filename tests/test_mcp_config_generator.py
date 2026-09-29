import json
import os
import shutil
import sys
import tempfile
import unittest

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

        generate_mcp_config(
            self.output_path, reqs, app_dir, self.local_agents_dir, self.venv_python
        )

        self.assertTrue(os.path.exists(self.output_path))
        with open(self.output_path) as f:
            config = json.load(f)

        self.assertIn("sprawl-workspace-fs", config["mcpServers"])
        self.assertEqual(config["mcpServers"]["sprawl-workspace-fs"]["command"], sys.executable)
        self.assertIn(os.path.abspath(app_dir), config["mcpServers"]["sprawl-workspace-fs"]["args"])
        self.assertNotIn("sprawl-vault", config["mcpServers"])

    def test_generate_with_vault(self):
        reqs = {"molecules": []}
        app_dir = "/my/app"
        vault_path = "~/MyVault"

        generate_mcp_config(
            self.output_path, reqs, app_dir, self.local_agents_dir, self.venv_python, vault_path
        )

        with open(self.output_path) as f:
            config = json.load(f)

        self.assertIn("sprawl-vault", config["mcpServers"])
        self.assertIn(
            os.path.abspath(os.path.expanduser(vault_path)),
            config["mcpServers"]["sprawl-vault"]["args"],
        )

    def test_generate_with_allowed_mounts(self):
        reqs = {"molecules": []}
        app_dir = "/my/app"
        allowed_mounts = {
            "shared_lib": "/path/to/shared",
            "assets": "/path/to/assets",
        }

        generate_mcp_config(
            self.output_path,
            reqs,
            app_dir,
            self.local_agents_dir,
            self.venv_python,
            allowed_mounts=allowed_mounts,
        )

        with open(self.output_path) as f:
            config = json.load(f)

        args = config["mcpServers"]["sprawl-workspace-fs"]["args"]
        self.assertIn("-m", args)
        self.assertIn("sprawl.mcp.workspace_fs", args)
        self.assertIn(os.path.abspath(app_dir), args)
        self.assertIn("--mount", args)
        self.assertIn(f"assets={os.path.abspath('/path/to/assets')}", args)
        self.assertIn(f"shared_lib={os.path.abspath('/path/to/shared')}", args)


if __name__ == "__main__":
    unittest.main()
