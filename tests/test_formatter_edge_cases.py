"""Tests for TUI formatter edge cases — empty content, long lines, and multi-line wrapping."""

import re
import unittest

from src.sprawl.tui.formatter import format_panel, format_checklist_item


def strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences from text."""
    return re.sub(r'\033\[[0-9;]*m', '', text)


class TestFormatPanelEdgeCases(unittest.TestCase):
    """Edge-case tests for the TUI panel formatter."""

    def test_empty_content_produces_valid_panel(self):
        """format_panel with empty content produces a valid panel with correct width."""
        panel = format_panel("Empty", "")
        lines = panel.splitlines()
        self.assertTrue(len(lines) >= 3, "Panel must have at least top, content, bottom lines")
        for line in lines:
            stripped = strip_ansi(line)
            self.assertEqual(len(stripped), 100, f"Line width mismatch: '{stripped}' ({len(stripped)} chars)")

    def test_whitespace_only_content(self):
        """format_panel with whitespace-only content still produces valid 100-char lines."""
        panel = format_panel("Whitespace", "   \n\n  ")
        lines = panel.splitlines()
        for line in lines:
            stripped = strip_ansi(line)
            self.assertEqual(len(stripped), 100)

    def test_very_long_single_line_wraps(self):
        """format_panel correctly wraps a very long single line across multiple panel rows."""
        long_content = "x" * 300  # Much longer than 96-char inner width
        panel = format_panel("Long Line", long_content)
        lines = panel.splitlines()

        # Should produce more than just top + 1 content + bottom
        content_lines = lines[1:-1]
        self.assertGreater(len(content_lines), 1, "Long content should wrap to multiple lines")

        for line in lines:
            stripped = strip_ansi(line)
            self.assertEqual(len(stripped), 100)

    def test_multi_line_content(self):
        """format_panel correctly handles multi-line content with varying lengths."""
        content = "Short line.\nThis is a medium length line that should fit.\nAnother one."
        panel = format_panel("Multi-line", content)
        lines = panel.splitlines()

        for line in lines:
            stripped = strip_ansi(line)
            self.assertEqual(len(stripped), 100)

    def test_no_title_produces_valid_panel(self):
        """format_panel with an empty title produces a valid full-dash top border."""
        panel = format_panel("", "content goes here")
        lines = panel.splitlines()
        top = strip_ansi(lines[0])
        self.assertTrue(top.startswith("╭"))
        self.assertTrue(top.endswith("╮"))
        self.assertEqual(len(top), 100)

    def test_very_long_title_truncates(self):
        """format_panel truncates a title that exceeds the inner content width."""
        long_title = "T" * 200
        panel = format_panel(long_title, "body content")
        lines = panel.splitlines()
        for line in lines:
            stripped = strip_ansi(line)
            self.assertEqual(len(stripped), 100)

    def test_border_characters_present(self):
        """format_panel output contains all expected box-drawing characters."""
        panel = format_panel("Test", "content")
        self.assertIn("╭", panel)
        self.assertIn("╮", panel)
        self.assertIn("╰", panel)
        self.assertIn("╯", panel)
        self.assertIn("│", panel)
        self.assertIn("─", panel)

    def test_custom_border_color(self):
        """format_panel accepts a custom border color ANSI sequence."""
        custom_color = "\033[38;2;255;0;0m"  # Red
        panel = format_panel("Colored", "body", border_color=custom_color)
        self.assertIn(custom_color, panel)


class TestFormatChecklistItemEdgeCases(unittest.TestCase):
    """Edge-case tests for the checklist item formatter."""

    def test_success_item_contains_emerald(self):
        """Success checklist item uses the Emerald color code."""
        item = format_checklist_item(True, "All good")
        self.assertIn("\033[38;2;16;185;129m", item)  # Emerald

    def test_failure_item_contains_crimson(self):
        """Failure checklist item uses the Crimson color code."""
        item = format_checklist_item(False, "Failed check")
        self.assertIn("\033[38;2;239;68;68m", item)  # Crimson

    def test_empty_label(self):
        """Checklist item with empty label still produces a valid string."""
        item = format_checklist_item(True, "")
        stripped = strip_ansi(item)
        self.assertIn("✓", stripped)

    def test_long_label(self):
        """Checklist item with a very long label does not crash."""
        label = "A" * 500
        item = format_checklist_item(False, label)
        stripped = strip_ansi(item)
        self.assertIn("✗", stripped)
        self.assertIn("A" * 500, stripped)


if __name__ == "__main__":
    unittest.main()
