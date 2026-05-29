import unittest
from unittest.mock import patch, MagicMock
import sys

from sprawl.utils.tui import raw_terminal, read_key, show_checkbox_menu


class TestTUI(unittest.TestCase):

    def test_raw_terminal_non_tty(self):
        """Verify raw_terminal context manager handles non-TTY gracefully."""
        with patch("sys.stdin.isatty", return_value=False):
            with raw_terminal() as fd:
                self.assertEqual(fd, sys.stdin.fileno())

    @patch("sys.stdin.isatty", return_value=False)
    @patch("sys.stdin.read")
    def test_read_key_non_tty(self, mock_read, mock_isatty):
        """Verify read_key simply returns characters if not a TTY."""
        mock_read.return_value = "a"
        self.assertEqual(read_key(), "a")

    @patch("sys.stdin.isatty", return_value=True)
    @patch("os.read")
    def test_read_key_tty_char(self, mock_os_read, mock_isatty):
        """Verify read_key reads single characters on TTY."""
        mock_os_read.return_value = b"x"
        self.assertEqual(read_key(), "x")

    @patch("sys.stdin.isatty", return_value=True)
    @patch("select.select")
    @patch("os.read")
    def test_read_key_tty_arrow(self, mock_os_read, mock_select, mock_isatty):
        """Verify read_key parses escape sequences for arrow keys correctly."""
        # os.read yields escape char, then the rest of the arrow sequence
        mock_os_read.side_effect = [b"\x1b", b"[B"]
        mock_select.return_value = ([sys.stdin.fileno()], [], [])

        self.assertEqual(read_key(), "\x1b[B")

    @patch("sprawl.utils.tui.read_key")
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

    @patch("sprawl.utils.tui.read_key")
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


if __name__ == "__main__":
    unittest.main()
