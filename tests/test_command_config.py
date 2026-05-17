import unittest
import os
import tempfile
import json
from unittest.mock import patch


class TestCommandConfig(unittest.TestCase):
    """Tests for config subcommands.

    We create an isolated config instance and patch it into config_cmd
    so that both cmd_config_set and assertions share exactly one object.
    """

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def _make_isolated_config(self):
        """Returns a config instance fully isolated to temp_dir."""
        from src.sprawl.config import SprawlConfig
        cfg = SprawlConfig(test_mode=True)
        # Override the resolved path after construction
        cfg.config_path = os.path.join(self.temp_dir.name, "config.json")
        return cfg

    def test_config_set_persists_to_disk(self):
        """cmd_config_set writes key/value to config.json."""
        cfg = self._make_isolated_config()

        with patch("src.sprawl.commands.config_cmd.config", cfg):
            from src.sprawl.commands.config_cmd import cmd_config_set
            cmd_config_set("vault_path", "/path/to/my/vault")

        self.assertTrue(os.path.exists(cfg.config_path))
        with open(cfg.config_path, "r") as f:
            data = json.load(f)
        self.assertEqual(data["vault_path"], "/path/to/my/vault")

    def test_config_set_updates_vault_path_attribute(self):
        """cmd_config_set updates vault_path attribute on config singleton."""
        cfg = self._make_isolated_config()

        with patch("src.sprawl.commands.config_cmd.config", cfg):
            from src.sprawl.commands.config_cmd import cmd_config_set
            cmd_config_set("vault_path", "/my/new/vault")

        self.assertEqual(cfg.vault_path, "/my/new/vault")

    def test_config_list_does_not_crash(self):
        """cmd_config_list renders without errors."""
        cfg = self._make_isolated_config()

        with patch("src.sprawl.commands.config_cmd.config", cfg):
            from src.sprawl.commands.config_cmd import cmd_config_set, cmd_config_list
            cmd_config_set("key1", "val1")
            cmd_config_set("key2", "val2")
            cmd_config_list()  # Just check no exception raised


if __name__ == "__main__":
    unittest.main()
