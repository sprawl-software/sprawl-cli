import unittest
from unittest.mock import patch
from datetime import datetime, timezone, timedelta

from src.sprawl.config import config
from src.sprawl.registry import update_dna_registry, get_dna_registry, check_dna_staleness

class TestDNARegistry(unittest.TestCase):
    def setUp(self):
        import os
        import tempfile
        self.temp_dir = tempfile.TemporaryDirectory()
        # Ensure we are in test mode
        os.environ["SPRAWL_TEST_MODE"] = "1"
        config.reinitialize()
        config.config_path = os.path.join(self.temp_dir.name, "config.json")
        # Reset the test config file
        config.update({"dna_source": None})
        
    def tearDown(self):
        self.temp_dir.cleanup()
        
    def test_update_dna_registry(self):
        source_url = "https://github.com/test/dna.git"
        update_dna_registry(source_url)
        
        data = get_dna_registry()
        self.assertIsNotNone(data)
        self.assertEqual(data["url"], source_url)
        self.assertEqual(data["local_path"], config.agents_dir_global)
        self.assertIn("last_pulled", data)

    @patch('src.sprawl.registry.print_warning')
    def test_staleness_no_registry(self, mock_warn):
        check_dna_staleness()
        mock_warn.assert_not_called()

    @patch('src.sprawl.registry.print_warning')
    def test_staleness_recent(self, mock_warn):
        recent_time = datetime.now(timezone.utc) - timedelta(days=2)
        config.update({
            "dna_source": {
                "last_pulled": recent_time.isoformat()
            }
        })
        check_dna_staleness()
        mock_warn.assert_not_called()

    @patch('src.sprawl.registry.print_warning')
    def test_staleness_stale(self, mock_warn):
        stale_time = datetime.now(timezone.utc) - timedelta(days=8)
        config.update({
            "dna_source": {
                "last_pulled": stale_time.isoformat()
            }
        })
        check_dna_staleness()
        mock_warn.assert_called_once()
        warning_msg = mock_warn.call_args[0][0]
        self.assertIn("DNA source is stale", warning_msg)

    @patch('src.sprawl.registry.print_warning')
    def test_staleness_invalid_date(self, mock_warn):
        config.update({
            "dna_source": {
                "last_pulled": "not-a-valid-date"
            }
        })
        # Should catch ValueError and pass silently
        check_dna_staleness()
        mock_warn.assert_not_called()

if __name__ == "__main__":
    unittest.main()
