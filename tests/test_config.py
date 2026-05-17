"""Tests for SprawlConfig dataclass — TASK-001-03."""

import os
import sys
import json
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from src.sprawl.config import SprawlConfig, create_config


class TestSprawlConfig(unittest.TestCase):
    """Tests for the SprawlConfig dataclass refactor."""

    def test_default_construction(self) -> None:
        """Config initializes with sane defaults."""
        cfg = SprawlConfig(test_mode=False)
        self.assertFalse(cfg.dry_run)
        self.assertFalse(cfg.verbose)
        self.assertFalse(cfg.json_logging)
        self.assertFalse(cfg.test_mode)
        self.assertIn(".sprawl/core", cfg.agents_dir_global)
        self.assertIn(".sprawl/dna", cfg.dna_registry_dir)

    def test_test_mode_paths(self) -> None:
        """Test mode resolves to isolated paths."""
        cfg = SprawlConfig(test_mode=True)
        self.assertIn("sprawl_test", cfg.agents_dir_global)
        self.assertIn("sprawl_test", cfg.dna_registry_dir)
        self.assertIn("Sprawl_Test", cfg.sprawl_dir)
        self.assertIn("sprawl_test", cfg.config_path)

    def test_production_paths(self) -> None:
        """Production mode resolves to standard paths."""
        cfg = SprawlConfig(test_mode=False)
        self.assertIn(".sprawl/core", cfg.agents_dir_global)
        self.assertNotIn("test", cfg.agents_dir_global.lower())

    def test_reinitialize_switches_modes(self) -> None:
        """reinitialize() picks up environment changes."""
        cfg = SprawlConfig(test_mode=False)
        original_global = cfg.agents_dir_global

        os.environ["SPRAWL_TEST_MODE"] = "1"
        try:
            cfg.reinitialize()
            self.assertTrue(cfg.test_mode)
            self.assertNotEqual(cfg.agents_dir_global, original_global)
            self.assertIn("sprawl_test", cfg.agents_dir_global)
        finally:
            del os.environ["SPRAWL_TEST_MODE"]

    def test_create_config_factory(self) -> None:
        """create_config() factory produces correctly configured instances."""
        cfg = create_config(test_mode=True)
        self.assertTrue(cfg.test_mode)
        self.assertIn("sprawl_test", cfg.agents_dir_global)

        cfg2 = create_config(test_mode=False)
        self.assertFalse(cfg2.test_mode)
        self.assertNotIn("test", cfg2.agents_dir_global.lower())

    def test_from_env_factory(self) -> None:
        """from_env() reads SPRAWL_TEST_MODE from environment."""
        os.environ["SPRAWL_TEST_MODE"] = "1"
        try:
            cfg = SprawlConfig.from_env()
            self.assertTrue(cfg.test_mode)
        finally:
            del os.environ["SPRAWL_TEST_MODE"]

    def test_load_missing_config(self) -> None:
        """load() returns empty dict when config file doesn't exist."""
        cfg = SprawlConfig(test_mode=False)
        cfg.config_path = "/nonexistent/path/config.json"
        self.assertEqual(cfg.load(), {})

    def test_update_and_load_roundtrip(self) -> None:
        """update() persists data that load() can retrieve."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = SprawlConfig(test_mode=False)
            cfg.config_path = os.path.join(tmpdir, "config.json")

            cfg.update({"remote_dna_url": "https://example.com/dna.git"})

            loaded = cfg.load()
            self.assertEqual(loaded["remote_dna_url"], "https://example.com/dna.git")

    def test_update_merges_existing(self) -> None:
        """update() merges with existing config, not replaces."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = SprawlConfig(test_mode=False)
            cfg.config_path = os.path.join(tmpdir, "config.json")

            cfg.update({"key1": "value1"})
            cfg.update({"key2": "value2"})

            loaded = cfg.load()
            self.assertEqual(loaded["key1"], "value1")
            self.assertEqual(loaded["key2"], "value2")

    def test_di_injection_override(self) -> None:
        """Config supports direct field override for DI in tests."""
        cfg = SprawlConfig(test_mode=False)
        cfg.agents_dir_global = "/custom/test/path"
        self.assertEqual(cfg.agents_dir_global, "/custom/test/path")

    def test_dataclass_is_not_singleton(self) -> None:
        """Multiple instances are independent — no shared mutable state."""
        cfg1 = SprawlConfig(test_mode=False)
        cfg2 = SprawlConfig(test_mode=True)

        self.assertFalse(cfg1.test_mode)
        self.assertTrue(cfg2.test_mode)
        self.assertNotEqual(cfg1.agents_dir_global, cfg2.agents_dir_global)


if __name__ == "__main__":
    unittest.main()
