"""Tests for interactive first-run onboarding flow."""

import os
import shutil
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from src.sprawl.onboarding import run_onboarding_wizard
from src.sprawl.config import config


class TestOnboarding(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.test_dir, "config.json")
        
        self.original_config_path = config.config_path
        config.config_path = self.config_path

    def tearDown(self):
        config.config_path = self.original_config_path
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @patch("builtins.input")
    def test_onboarding_questionnaire(self, mock_input):
        """Onboarding wizard captures responses and writes them to config.json."""
        # Mock inputs: Name, Email, Company Size (1), Use Case (1)
        mock_input.side_effect = ["John Doe", "john@example.com", "1", "1"]

        run_onboarding_wizard()

        cfg = config.load()
        self.assertTrue(cfg.get("onboarding_completed"))
        lead_info = cfg.get("lead_info", {})
        self.assertEqual(lead_info.get("name"), "John Doe")
        self.assertEqual(lead_info.get("email"), "john@example.com")
        self.assertEqual(lead_info.get("company_size"), "1-10")
        self.assertEqual(lead_info.get("primary_use_case"), "AST Compliance")

    @patch("builtins.input")
    def test_onboarding_already_completed(self, mock_input):
        """If onboarding is already marked completed, the wizard does not ask questions."""
        config.update({"onboarding_completed": True})

        run_onboarding_wizard()

        mock_input.assert_not_called()


if __name__ == "__main__":
    unittest.main()
