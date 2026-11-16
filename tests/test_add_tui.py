import os
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

# Ensure the local src is available
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from src.sprawl.commands.artifacts import cmd_add


class TestAddTUI(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.workspace_dir = os.path.join(self.test_dir, "workspace")
        self.manifest_dir = os.path.join(self.workspace_dir, ".agents")
        os.makedirs(self.manifest_dir)
        self.manifest_path = os.path.join(self.manifest_dir, "sprawl_manifest.yml")

        # Create a mock global DNA vault
        self.dna_dir = os.path.join(self.test_dir, "dna")
        os.makedirs(os.path.join(self.dna_dir, "atoms"))
        os.makedirs(os.path.join(self.dna_dir, "skills"))

        # Add initial manifest
        with open(self.manifest_path, "w") as f:
            f.write("""dna: core
rules:
skills:
workflows:
""")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def _run_add_with_selection(self, menu_selection):
        """Runs cmd_add([]) with mocked TUI selection and real RegistryScanner."""
        os.makedirs(os.path.join(self.dna_dir, "skills", "skill1"), exist_ok=True)
        with (
            patch(
                "src.sprawl.commands.artifacts.get_active_dna_context", return_value=self.dna_dir
            ),
            patch("src.sprawl.utils.tui.show_checkbox_menu", return_value=menu_selection),
            patch("src.sprawl.commands.artifacts.cmd_sync") as mock_sync,
        ):
            cmd_add([], target_dir=self.workspace_dir)
            return mock_sync

    def test_cmd_add_tui_cancel(self):
        """Verify cmd_add exits cleanly and does not modify manifest if TUI is cancelled."""
        with open(self.manifest_path) as f:
            initial_content = f.read()

        mock_sync = self._run_add_with_selection(None)

        with open(self.manifest_path) as f:
            self.assertEqual(f.read(), initial_content)
        mock_sync.assert_not_called()

    def test_cmd_add_tui_success(self):
        """Verify cmd_add saves selection and triggers sync on successful TUI confirmation."""
        mock_sync = self._run_add_with_selection(
            {
                "skills": ["skill1"],
                "rules": [],
                "workflows": [],
            }
        )

        with open(self.manifest_path) as f:
            content = f.read()
            self.assertIn("skill1", content)
            self.assertIn("dna: core", content)

        mock_sync.assert_called_once_with(self.workspace_dir)


if __name__ == "__main__":
    unittest.main()
