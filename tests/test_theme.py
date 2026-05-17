"""Unit tests for the Sprawl Theme system."""

import unittest
from src.sprawl.theme import SDS_THEME

class TestTheme(unittest.TestCase):
    def test_theme_keys(self):
        """Verify that all required semantic token names are present in the theme."""
        required_keys = ["info", "accent", "success", "warning", "error", "muted", "debug"]
        for key in required_keys:
            self.assertIn(key, SDS_THEME.styles)
