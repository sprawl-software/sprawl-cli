import os
import sys
import unittest
from unittest.mock import patch

# Ensure both repo root and local src are available
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from src.sprawl.utils.tui import (
    is_tui_supported,
    prompt_numbered_selection,
    raw_terminal,
    read_key,
    show_checkbox_menu,
)


class TestTUI(unittest.TestCase):
    @unittest.skipIf(sys.platform == "win32", "POSIX-specific terminal test")
    def test_raw_terminal_non_tty(self):
        """Verify raw_terminal context manager handles non-TTY gracefully."""
        with (
            patch("sys.stdin.isatty", return_value=False),
            patch("sys.stdin.fileno", return_value=0),
            raw_terminal() as fd,
        ):
            self.assertEqual(fd, 0)

    @patch("sys.stdin.isatty", return_value=False)
    @patch("sys.stdin.read")
    def test_read_key_non_tty(self, mock_read, mock_isatty):
        """Verify read_key simply returns characters if not a TTY."""
        mock_read.return_value = "a"
        self.assertEqual(read_key(), "a")

    def _read_key_under_posix_tty(self, os_read_values, select_ready: bool = False) -> str:
        """Runs read_key() with simulated POSIX TTY stdin."""
        select_res = ([0], [], []) if select_ready else ([], [], [])
        with (
            patch("sys.stdin.fileno", return_value=0),
            patch("sys.stdin.isatty", return_value=True),
            patch("select.select", return_value=select_res),
            patch("os.read", side_effect=os_read_values),
        ):
            return read_key()

    @unittest.skipIf(sys.platform == "win32", "POSIX-specific terminal test")
    def test_read_key_tty_char(self):
        """Verify read_key reads single characters on TTY."""
        self.assertEqual(self._read_key_under_posix_tty([b"x"]), "x")

    @unittest.skipIf(sys.platform == "win32", "POSIX-specific terminal test")
    def test_read_key_tty_arrow(self):
        """Verify read_key parses escape sequences for arrow keys correctly."""
        self.assertEqual(
            self._read_key_under_posix_tty([b"\x1b", b"[B"], select_ready=True),
            "\x1b[B",
        )

    @patch("src.sprawl.utils.tui.read_key")
    @patch("sys.stdout.write")
    def test_show_checkbox_menu_cancel(self, mock_write, mock_read_key):
        """Verify show_checkbox_menu returns None when cancelled with Esc or q."""
        mock_read_key.return_value = "q"
        categories = {
            "atoms": [("atom1", False)],
            "skills": [("skill1", True)],
        }
        res = show_checkbox_menu("Test Menu", categories)
        self.assertIsNone(res)

    @patch("src.sprawl.utils.tui.read_key")
    @patch("sys.stdout.write")
    def test_show_checkbox_menu_toggle_and_confirm(self, mock_write, mock_read_key):
        """Verify show_checkbox_menu updates checked states and returns result on Enter."""
        # Key sequence:
        # 1. ' ' (Space) to check atom1
        # 2. '\x1b[B' (Arrow Down) to move to skill1 (actually header is skipped, so it goes to skill1)
        # 3. ' ' (Space) to uncheck skill1
        # 4. '\r' (Enter) to confirm
        mock_read_key.side_effect = [" ", "\x1b[B", " ", "\r"]

        categories = {
            "atoms": [("atom1", False)],
            "skills": [("skill1", True)],
        }

        res = show_checkbox_menu("Test Menu", categories)

        # Expected:
        # atom1: checked False -> space pressed -> checked True
        # skill1: checked True -> arrow down, space pressed -> checked False
        self.assertIsNotNone(res)
        self.assertEqual(res["atoms"], ["atom1"])
        self.assertEqual(res["skills"], [])

    @patch("sys.stdin.readline", return_value="\n")
    def test_prompt_numbered_selection_enter_default(self, mock_readline):
        """Pressing Enter in numbered prompt accepts current default checked items."""
        categories = {
            "integrations": [("cursor", True), ("vscode", False), ("windsurf", True)],
        }
        res = prompt_numbered_selection("Select Integrations", categories)
        self.assertIsNotNone(res)
        self.assertEqual(res["integrations"], ["cursor", "windsurf"])

    @patch("sys.stdin.readline", return_value="1, 2\n")
    def test_prompt_numbered_selection_numbers(self, mock_readline):
        """Entering comma-separated numbers selects precisely those items."""
        categories = {
            "integrations": [("cursor", True), ("vscode", False), ("windsurf", True)],
        }
        res = prompt_numbered_selection("Select Integrations", categories)
        self.assertIsNotNone(res)
        self.assertEqual(res["integrations"], ["cursor", "vscode"])

    @patch("sys.stdin.readline", return_value="vscode, windsurf\n")
    def test_prompt_numbered_selection_names(self, mock_readline):
        """Entering item names case-insensitively selects those items."""
        categories = {
            "integrations": [("cursor", True), ("vscode", False), ("windsurf", False)],
        }
        res = prompt_numbered_selection("Select Integrations", categories)
        self.assertIsNotNone(res)
        self.assertEqual(res["integrations"], ["vscode", "windsurf"])

    @patch("sys.stdin.readline", return_value="all\n")
    def test_prompt_numbered_selection_all(self, mock_readline):
        """Entering 'all' selects every item across categories."""
        categories = {
            "integrations": [("cursor", False), ("vscode", False)],
        }
        res = prompt_numbered_selection("Select Integrations", categories)
        self.assertIsNotNone(res)
        self.assertEqual(res["integrations"], ["cursor", "vscode"])

    @patch("sys.stdin.readline", return_value="none\n")
    def test_prompt_numbered_selection_none(self, mock_readline):
        """Entering 'none' clears all items."""
        categories = {
            "integrations": [("cursor", True), ("vscode", True)],
        }
        res = prompt_numbered_selection("Select Integrations", categories)
        self.assertIsNotNone(res)
        self.assertEqual(res["integrations"], [])

    @patch("sys.stdin.readline", return_value="q\n")
    def test_prompt_numbered_selection_cancel(self, mock_readline):
        """Entering 'q' cancels selection and returns None."""
        categories = {
            "integrations": [("cursor", True)],
        }
        res = prompt_numbered_selection("Select Integrations", categories)
        self.assertIsNone(res)

    def test_is_tui_supported_non_tty(self):
        """is_tui_supported returns False when stdin is not a tty."""
        with patch("sys.stdin.isatty", return_value=False):
            self.assertFalse(is_tui_supported())

    def _check_tui_support_under_platform(
        self,
        platform_name: str,
        msvcrt_val: object = None,
        termios_val: object = None,
        tty_val: object = None,
        select_val: object = None,
    ) -> bool:
        """Evaluates is_tui_supported() under a simulated platform and module state."""
        with (
            patch("sys.platform", platform_name),
            patch("sys.stdin.isatty", return_value=True),
            patch("sys.stdout.isatty", return_value=True),
            patch("src.sprawl.utils.tui.msvcrt", msvcrt_val),
            patch("src.sprawl.utils.tui.termios", termios_val),
            patch("src.sprawl.utils.tui.tty", tty_val),
            patch("src.sprawl.utils.tui.select", select_val),
        ):
            return is_tui_supported()

    def test_is_tui_supported_windows(self):
        """is_tui_supported checks msvcrt on win32."""
        self.assertTrue(self._check_tui_support_under_platform("win32", msvcrt_val=object()))
        self.assertFalse(self._check_tui_support_under_platform("win32", msvcrt_val=None))

    def test_is_tui_supported_posix(self):
        """is_tui_supported checks termios, tty, and select on POSIX."""
        dummy = object()
        self.assertTrue(
            self._check_tui_support_under_platform(
                "linux", termios_val=dummy, tty_val=dummy, select_val=dummy
            )
        )
        self.assertFalse(
            self._check_tui_support_under_platform(
                "linux", termios_val=None, tty_val=dummy, select_val=dummy
            )
        )


if __name__ == "__main__":
    unittest.main()
