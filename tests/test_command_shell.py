import unittest
import os
import shutil
import tempfile
from unittest.mock import patch, MagicMock
from src.sprawl.commands.shell import cmd_shell

class TestCommandShell(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.agents_dir = os.path.join(self.test_dir, ".agents")
        self.venv_dir = os.path.join(self.agents_dir, ".venv")
        os.makedirs(os.path.join(self.venv_dir, "bin"))

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch('subprocess.run')
    def test_cmd_shell_env_setup(self, mock_run):
        # We don't want to actually run a shell
        mock_run.return_value = MagicMock()
        
        with patch.dict(os.environ, {"SHELL": "/bin/zsh", "PATH": "/usr/bin"}):
            cmd_shell(self.test_dir)
            
            self.assertTrue(mock_run.called)
            args, kwargs = mock_run.call_args
            
            env = kwargs.get("env")
            self.assertEqual(env.get("SHELL"), "/bin/zsh")
            self.assertEqual(env.get("VIRTUAL_ENV"), self.venv_dir)
            self.assertEqual(env.get("SPRAWL_WORKSPACE"), os.path.abspath(self.test_dir))
            self.assertTrue(env.get("PATH").startswith(os.path.join(self.venv_dir, "bin")))

    @patch('subprocess.run')
    def test_cmd_shell_missing_venv(self, mock_run):
        shutil.rmtree(self.venv_dir)
        from src.sprawl.exceptions import SprawlError
        with self.assertRaises(SprawlError) as cm:
            cmd_shell(self.test_dir)
        self.assertIn("No virtual environment found", str(cm.exception))

if __name__ == "__main__":
    unittest.main()
