import unittest
from unittest.mock import patch, MagicMock
import os

from src.sprawl.commands.dna import cmd_dna_update, cmd_dna_inspect
from src.sprawl.exceptions import SprawlError
from src.sprawl.config import config

class TestDNACommands(unittest.TestCase):
    def setUp(self):
        import os
        import tempfile
        self.temp_dir = tempfile.TemporaryDirectory()
        os.environ["SPRAWL_TEST_MODE"] = "1"
        config.reinitialize()
        config.config_path = os.path.join(self.temp_dir.name, "config.json")
        config.update({"dna_source": None})
        
    def tearDown(self):
        self.temp_dir.cleanup()

    @patch('src.sprawl.commands.dna.get_dna_registry', return_value=None)
    def test_cmd_dna_update_no_registry(self, mock_get_registry):
        with self.assertRaises(SprawlError) as context:
            cmd_dna_update()
        self.assertIn("No Global DNA is registered", str(context.exception))

    @patch('src.sprawl.commands.dna.get_dna_registry', return_value={"url": "test-url"})
    @patch('src.sprawl.commands.dna.os.path.exists', return_value=False)
    def test_cmd_dna_update_no_git_repo(self, mock_exists, mock_get_registry):
        with self.assertRaises(SprawlError) as context:
            cmd_dna_update()
        self.assertIn("not found or not a git repository", str(context.exception))

    @patch('src.sprawl.commands.dna.get_dna_registry', return_value={"url": "test-url"})
    @patch('src.sprawl.commands.dna.os.path.exists', return_value=True)
    @patch('src.sprawl.commands.dna.subprocess.check_output', return_value="main")
    @patch('src.sprawl.commands.dna.subprocess.run')
    @patch('src.sprawl.commands.dna.update_dna_registry')
    def test_cmd_dna_update_success(self, mock_update_registry, mock_run, mock_check_output, mock_exists, mock_get_registry):
        config.dry_run = False
        cmd_dna_update()
        mock_run.assert_called_once_with(["git", "-C", config.agents_dir_global, "pull", "origin", "main"], check=True)
        mock_update_registry.assert_called_once_with("test-url")

    @patch('src.sprawl.commands.dna.get_dna_registry', return_value=None)
    def test_cmd_dna_inspect_no_registry(self, mock_get_registry):
        with self.assertRaises(SprawlError) as context:
            cmd_dna_inspect()
        self.assertIn("No Global DNA is registered", str(context.exception))

    @patch('src.sprawl.commands.dna.get_dna_registry', return_value={"url": "test-url"})
    @patch('src.sprawl.commands.dna.os.path.exists', side_effect=lambda x: False if x == config.agents_dir_global else True)
    def test_cmd_dna_inspect_no_dir(self, mock_exists, mock_get_registry):
        with self.assertRaises(SprawlError) as context:
            cmd_dna_inspect()
        self.assertIn("Global DNA not found", str(context.exception))

if __name__ == "__main__":
    unittest.main()
