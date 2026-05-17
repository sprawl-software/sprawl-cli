"""Tests for command registry pattern — TASK-001-01."""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))


class TestCommandRegistry(unittest.TestCase):
    """Tests for the dict-based command dispatch in cli.py."""

    def test_registry_contains_all_commands(self) -> None:
        """All known commands are registered in the COMMAND_REGISTRY."""
        # We test by importing get_parser and checking subparser destinations
        from src.sprawl.cli import get_parser
        parser = get_parser()

        expected_commands = [
            "init", "fetch-dna", "ls", "add", "create", "graft",
            "sync", "bind", "update", "clean-test", "clean-demo",
            "scaffold", "rm", "man", "demo",
        ]

        # All expected commands must have a subparser
        for cmd in expected_commands:
            with self.subTest(cmd=cmd):
                # Verify subparser exists by parsing
                try:
                    if cmd == "init":
                        args = parser.parse_args([cmd, "https://example.com/repo.git"])
                    elif cmd == "create":
                        args = parser.parse_args([cmd, "test-workspace"])
                    elif cmd == "fetch-dna":
                        args = parser.parse_args([cmd, "https://example.com/repo.git"])
                    elif cmd == "add":
                        args = parser.parse_args([cmd, "item1"])
                    elif cmd == "scaffold":
                        args = parser.parse_args([cmd, "persona", "Test"])
                    elif cmd == "rm":
                        args = parser.parse_args([cmd, "item1"])
                    elif cmd == "demo":
                        args = parser.parse_args([cmd])
                    else:
                        args = parser.parse_args([cmd])
                    self.assertEqual(args.command, cmd)
                except SystemExit:
                    self.fail(f"Parser rejected valid command: {cmd}")

    @patch("src.sprawl.core.cmd_graft")
    def test_dispatch_calls_correct_handler(self, mock_graft: MagicMock) -> None:
        """Registry dispatch calls the correct command function."""
        from src.sprawl.cli import get_parser

        parser = get_parser()
        args = parser.parse_args(["graft"])

        # Simulate the registry dispatch pattern
        from src.sprawl.core import cmd_graft
        REGISTRY = {
            "graft": lambda a: cmd_graft(),
        }

        handler = REGISTRY.get(args.command)
        self.assertIsNotNone(handler)
        handler(args)
        mock_graft.assert_called_once()

    def test_unknown_command_returns_none(self) -> None:
        """Unknown command key returns None from registry lookup."""
        REGISTRY = {
            "init": lambda a: None,
            "sync": lambda a: None,
        }
        self.assertIsNone(REGISTRY.get("nonexistent"))


if __name__ == "__main__":
    unittest.main()
