"""Tests for sprawl status command."""

import unittest
from unittest.mock import patch, MagicMock
import os
import tempfile

from src.sprawl.commands.status import cmd_status
from src.sprawl.exceptions import SprawlError


class TestStatusCommand(unittest.TestCase):

    def test_status_no_manifest_raises(self):
        """Status raises SprawlError when not in a workspace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(SprawlError) as ctx:
                cmd_status(target_dir=tmpdir)
            self.assertIn("Not in a Sprawl workspace", str(ctx.exception))

    @patch('src.sprawl.commands.status.console')
    @patch('src.sprawl.commands.status.Workspace')
    @patch('src.sprawl.commands.status.parse_sprawl_manifest')
    def test_status_renders_panel(self, mock_manifest, mock_ws_class, mock_console):
        """Status renders panels when manifest exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agents_dir = os.path.join(tmpdir, ".agents")
            os.makedirs(agents_dir)
            manifest_path = os.path.join(agents_dir, "sprawl_manifest.yml")
            with open(manifest_path, "w") as f:
                f.write("rules:\n  - engineering.md\n")

            mock_ws = MagicMock()
            mock_ws.get_dna_alias.return_value = "core"
            mock_ws.get_sync_state.return_value = {}
            mock_ws_class.return_value = mock_ws

            mock_manifest.return_value = {
                "rules": ["engineering.md"], "skills": [], "atoms": [],
                "molecules": [], "workflows": []
            }

            cmd_status(target_dir=tmpdir)

            # console.print should be called for info panels
            self.assertTrue(mock_console.print.called)

    @patch('src.sprawl.commands.status.console')
    @patch('src.sprawl.commands.status.Workspace')
    @patch('src.sprawl.commands.status.parse_sprawl_manifest')
    def test_status_stale_sync(self, mock_manifest, mock_ws_class, mock_console):
        """Status shows stale indicator for old sync timestamps."""
        from datetime import datetime, timezone, timedelta
        with tempfile.TemporaryDirectory() as tmpdir:
            agents_dir = os.path.join(tmpdir, ".agents")
            os.makedirs(agents_dir)
            with open(os.path.join(agents_dir, "sprawl_manifest.yml"), "w") as f:
                f.write("rules:\n  - engineering.md\n")

            mock_ws = MagicMock()
            mock_ws.get_dna_alias.return_value = "core"
            stale_ts = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
            mock_ws.get_sync_state.return_value = {"last_sync_timestamp": stale_ts}
            mock_ws_class.return_value = mock_ws
            mock_manifest.return_value = {cat: [] for cat in ["rules", "skills", "atoms", "molecules", "workflows"]}

            cmd_status(target_dir=tmpdir)
            self.assertTrue(mock_console.print.called)


if __name__ == "__main__":
    unittest.main()
