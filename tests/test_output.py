"""Tests for output module — TASK-001-04."""

import io
import json
import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from src.sprawl.config import SprawlConfig


class TestOutputModule(unittest.TestCase):
    """Tests for the Rich output helpers with log levels and JSON mode."""

    def _get_output_module(self, cfg: SprawlConfig):
        """Import output module with a specific config injected."""
        import src.sprawl.output as output_mod
        original_config = output_mod.config
        output_mod.config = cfg
        return output_mod, original_config

    def test_json_mode_info(self) -> None:
        """JSON mode emits structured info log."""
        cfg = SprawlConfig(test_mode=False)
        cfg.json_logging = True
        output_mod, original = self._get_output_module(cfg)

        try:
            captured = io.StringIO()
            sys.stdout = captured
            output_mod.print_status("Test message")
            sys.stdout = sys.__stdout__

            log = json.loads(captured.getvalue().strip())
            self.assertEqual(log["level"], "info")
            self.assertEqual(log["message"], "Test message")
        finally:
            output_mod.config = original

    def test_json_mode_error(self) -> None:
        """JSON mode emits structured error log."""
        cfg = SprawlConfig(test_mode=False)
        cfg.json_logging = True
        output_mod, original = self._get_output_module(cfg)

        try:
            captured = io.StringIO()
            sys.stdout = captured
            output_mod.print_error("Something broke")
            sys.stdout = sys.__stdout__

            log = json.loads(captured.getvalue().strip())
            self.assertEqual(log["level"], "error")
            self.assertEqual(log["message"], "Something broke")
        finally:
            output_mod.config = original

    def test_json_mode_warning(self) -> None:
        """JSON mode emits structured warning log."""
        cfg = SprawlConfig(test_mode=False)
        cfg.json_logging = True
        output_mod, original = self._get_output_module(cfg)

        try:
            captured = io.StringIO()
            sys.stdout = captured
            output_mod.print_warning("Watch out")
            sys.stdout = sys.__stdout__

            log = json.loads(captured.getvalue().strip())
            self.assertEqual(log["level"], "warning")
            self.assertEqual(log["message"], "Watch out")
        finally:
            output_mod.config = original

    def test_json_mode_with_context(self) -> None:
        """JSON mode includes context fields."""
        cfg = SprawlConfig(test_mode=False)
        cfg.json_logging = True
        output_mod, original = self._get_output_module(cfg)

        try:
            captured = io.StringIO()
            sys.stdout = captured
            output_mod.print_status("Syncing", context={"command": "sync", "target": "/app"})
            sys.stdout = sys.__stdout__

            log = json.loads(captured.getvalue().strip())
            self.assertEqual(log["context"]["command"], "sync")
            self.assertEqual(log["context"]["target"], "/app")
        finally:
            output_mod.config = original

    def test_json_mode_success(self) -> None:
        """JSON mode emits success level."""
        cfg = SprawlConfig(test_mode=False)
        cfg.json_logging = True
        output_mod, original = self._get_output_module(cfg)

        try:
            captured = io.StringIO()
            sys.stdout = captured
            output_mod.print_success("Done")
            sys.stdout = sys.__stdout__

            log = json.loads(captured.getvalue().strip())
            self.assertEqual(log["level"], "success")
        finally:
            output_mod.config = original

    def test_debug_suppressed_without_verbose(self) -> None:
        """Debug messages are suppressed when verbose is False."""
        cfg = SprawlConfig(test_mode=False)
        cfg.json_logging = True
        cfg.verbose = False
        output_mod, original = self._get_output_module(cfg)

        try:
            captured = io.StringIO()
            sys.stdout = captured
            output_mod.print_debug("Should not appear")
            sys.stdout = sys.__stdout__

            self.assertEqual(captured.getvalue().strip(), "")
        finally:
            output_mod.config = original

    def test_debug_shown_with_verbose(self) -> None:
        """Debug messages appear when verbose is True."""
        cfg = SprawlConfig(test_mode=False)
        cfg.json_logging = True
        cfg.verbose = True
        output_mod, original = self._get_output_module(cfg)

        try:
            captured = io.StringIO()
            sys.stdout = captured
            output_mod.print_debug("Debug info")
            sys.stdout = sys.__stdout__

            log = json.loads(captured.getvalue().strip())
            self.assertEqual(log["level"], "debug")
            self.assertEqual(log["message"], "Debug info")
        finally:
            output_mod.config = original

    def test_rich_mode_does_not_crash(self) -> None:
        """Rich output mode (non-JSON) executes without errors."""
        cfg = SprawlConfig(test_mode=False)
        cfg.json_logging = False
        output_mod, original = self._get_output_module(cfg)

        try:
            # Just verify no exceptions — Rich writes to stderr/console
            output_mod.print_status("Rich status")
            output_mod.print_warning("Rich warning")
            output_mod.print_error("Rich error")
            output_mod.print_success("Rich success")
        finally:
            output_mod.config = original


if __name__ == "__main__":
    unittest.main()
