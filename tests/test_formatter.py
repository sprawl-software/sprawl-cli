"""Tests for styled TUI console formatter."""

import unittest
from src.sprawl.tui.formatter import format_panel, format_checklist_item


class TestTUIFormatter(unittest.TestCase):
    def test_format_panel_width(self):
        """format_panel produces output lines that are exactly 100 characters long (excluding ANSI escape codes)."""
        title = "Test Title"
        content = "This is a simple test content that should be wrapped nicely inside a panel."
        panel = format_panel(title, content)
        
        # Check that it returns a string with unicode borders
        self.assertIn("╭", panel)
        self.assertIn("╮", panel)
        self.assertIn("╰", panel)
        self.assertIn("╯", panel)
        
        # Strip ANSI escape sequences to check line lengths
        import re
        def strip_ansi(text: str) -> str:
            return re.sub(r'\033\[[0-9;]*m', '', text)
            
        lines = panel.splitlines()
        for line in lines:
            stripped = strip_ansi(line)
            self.assertEqual(len(stripped), 100)

    def test_format_checklist_item(self):
        """format_checklist_item formats checklist items with styled checkmark icons."""
        success_item = format_checklist_item(True, "Healthy environment")
        fail_item = format_checklist_item(False, "Missing dependencies")
        
        self.assertIn("✓", success_item)
        self.assertIn("✗", fail_item)


if __name__ == "__main__":
    unittest.main()
