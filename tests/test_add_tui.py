import unittest
import os
import shutil
import tempfile
from unittest.mock import patch, MagicMock

from sprawl.commands.artifacts import cmd_add
from sprawl.exceptions import SprawlError


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
atoms:
molecules:
workflows:
""")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch("sprawl.commands.artifacts.get_active_dna_context")
    @patch("sprawl.utils.tui.show_checkbox_menu")
    @patch("sprawl.utils.registry_scanner.RegistryScanner")
    @patch("sprawl.commands.artifacts.cmd_sync")
    def test_cmd_add_tui_cancel(self, mock_sync, mock_scanner_cls, mock_show_menu, mock_get_context):
        """Verify cmd_add exits cleanly and does not modify manifest if TUI is cancelled."""
        mock_get_context.return_value = self.dna_dir
        mock_scanner = MagicMock()
        mock_scanner.scan.return_value = {"atoms": [("atom1.json", False)]}
        mock_scanner_cls.return_value = mock_scanner
        mock_show_menu.return_value = None  # Cancelled

        # Verify initial manifest state
        with open(self.manifest_path, "r") as f:
            initial_content = f.read()

        cmd_add([], target_dir=self.workspace_dir)

        # Content should be completely unchanged
        with open(self.manifest_path, "r") as f:
            self.assertEqual(f.read(), initial_content)
        mock_sync.assert_not_called()

    @patch("sprawl.commands.artifacts.get_active_dna_context")
    @patch("sprawl.utils.tui.show_checkbox_menu")
    @patch("sprawl.utils.registry_scanner.RegistryScanner")
    @patch("sprawl.commands.artifacts.cmd_sync")
    def test_cmd_add_tui_success(self, mock_sync, mock_scanner_cls, mock_show_menu, mock_get_context):
        """Verify cmd_add saves selection and triggers sync on successful TUI confirmation."""
        mock_get_context.return_value = self.dna_dir
        mock_scanner = MagicMock()
        mock_scanner.scan.return_value = {
            "atoms": [("atom1.json", False)],
            "skills": [("skill1", False)],
        }
        mock_scanner_cls.return_value = mock_scanner
        mock_show_menu.return_value = {
            "atoms": ["atom1.json"],
            "skills": [],
            "rules": [],
            "molecules": [],
            "workflows": [],
        }

        cmd_add([], target_dir=self.workspace_dir)

        # Check if sprawl_manifest.yml got updated correctly
        with open(self.manifest_path, "r") as f:
            content = f.read()
            self.assertIn("atom1.json", content)
            self.assertIn("dna: core", content)

        mock_sync.assert_called_once_with(self.workspace_dir)


if __name__ == "__main__":
    unittest.main()
