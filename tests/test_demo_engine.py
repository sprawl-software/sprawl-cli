"""Tests for demo engine — verifies no os.chdir() mutations occur."""

import unittest
import os
from unittest.mock import patch, MagicMock, call


class TestDemoEngine(unittest.TestCase):

    def test_generate_dummy_dna_creates_tempdir(self):
        """generate_dummy_dna creates a temp directory with category subdirs."""
        import tempfile
        import shutil
        from src.sprawl.demo_engine import generate_dummy_dna
        from src.sprawl.utils import CATEGORIES

        dummy_path = None
        with patch('src.sprawl.demo_engine.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            dummy_path = generate_dummy_dna()

        try:
            self.assertTrue(os.path.isdir(dummy_path))
            for cat in CATEGORIES:
                self.assertTrue(os.path.isdir(os.path.join(dummy_path, cat)),
                                f"Category dir missing: {cat}")
        finally:
            if dummy_path and os.path.exists(dummy_path):
                shutil.rmtree(dummy_path, ignore_errors=True)

    def test_demo_engine_does_not_mutate_cwd(self):
        """run_interactive_demo must not change the process CWD."""
        from src.sprawl.demo_engine import run_interactive_demo

        original_cwd = os.getcwd()

        with patch('src.sprawl.demo_engine.cmd_init'), \
             patch('src.sprawl.demo_engine.cmd_clean_test'), \
             patch('src.sprawl.demo_engine.generate_dummy_dna', return_value="/tmp/fake_dna"), \
             patch('src.sprawl.demo_engine._provision_squad_workspace'), \
             patch('src.sprawl.demo_engine.config') as mock_config, \
             patch('src.sprawl.demo_engine.tempfile.TemporaryDirectory') as mock_td:

            mock_config.sprawl_dir = "/tmp/fake_sprawl"
            mock_td.return_value.__enter__ = lambda s: "/tmp/fake_demo"
            mock_td.return_value.__exit__ = MagicMock(return_value=False)

            run_interactive_demo(selected_key="1")

        # CWD must be unchanged
        self.assertEqual(os.getcwd(), original_cwd)

    def test_demo_invalid_key_returns_gracefully(self):
        """run_interactive_demo handles invalid selection without crashing."""
        from src.sprawl.demo_engine import run_interactive_demo

        with patch('src.sprawl.demo_engine.print_error') as mock_err:
            run_interactive_demo(selected_key="999")
            mock_err.assert_called_once()
            self.assertIn("Invalid selection", mock_err.call_args[0][0])

    def test_demo_quit_returns_gracefully(self):
        """run_interactive_demo handles 'q' selection gracefully."""
        from src.sprawl.demo_engine import run_interactive_demo

        with patch('src.sprawl.demo_engine.cmd_init') as mock_init:
            run_interactive_demo(selected_key="q")
            mock_init.assert_not_called()

    def test_provision_squad_uses_absolute_paths(self):
        """_provision_squad_workspace uses explicit paths, not os.chdir()."""
        import tempfile
        from src.sprawl.demo_engine import _provision_squad_workspace

        with tempfile.TemporaryDirectory() as demo_dir:
            with patch('src.sprawl.demo_engine.cmd_create') as mock_create, \
                 patch('src.sprawl.demo_engine.cmd_add') as mock_add, \
                 patch('src.sprawl.demo_engine.console'):

                _provision_squad_workspace(demo_dir, "my-squad", ["rule.md"])

                # cmd_create must be called with path=demo_dir
                mock_create.assert_called_once_with("my-squad", path=demo_dir)

                # cmd_add must be called with target_dir pointing to squad path
                expected_path = os.path.join(demo_dir, "my-squad")
                mock_add.assert_called_once_with(["rule.md"], target_dir=expected_path)

    def test_provision_squad_uses_sync_when_no_artifacts(self):
        """_provision_squad_workspace calls cmd_sync when no artifacts provided."""
        import tempfile
        from src.sprawl.demo_engine import _provision_squad_workspace

        with tempfile.TemporaryDirectory() as demo_dir:
            with patch('src.sprawl.demo_engine.cmd_create'), \
                 patch('src.sprawl.demo_engine.cmd_sync') as mock_sync, \
                 patch('src.sprawl.demo_engine.console'):

                _provision_squad_workspace(demo_dir, "empty-squad", [])

                expected_path = os.path.join(demo_dir, "empty-squad")
                mock_sync.assert_called_once_with(expected_path)


if __name__ == "__main__":
    unittest.main()
