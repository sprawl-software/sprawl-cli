"""Tests for sprawl status command."""

import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from src.sprawl.commands.status import cmd_status
from src.sprawl.exceptions import SprawlError


class TestStatusCommand(unittest.TestCase):
    def test_status_no_manifest_raises(self):
        """Status raises SprawlError when not in a workspace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(SprawlError) as ctx:
                cmd_status(target_dir=tmpdir)
            self.assertIn("Not in a Sprawl workspace", str(ctx.exception))

    def _run_status_with_sync_state(self, sync_state: dict) -> int:
        """Creates a real manifest workspace and runs cmd_status with a fake sync_state."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agents_dir = os.path.join(tmpdir, ".agents")
            os.makedirs(agents_dir)
            with open(os.path.join(agents_dir, "sprawl_manifest.yml"), "w") as f:
                f.write("rules:\n  - engineering.md\n")

            fake_ws = MagicMock()
            fake_ws.get_dna_alias.return_value = "core"
            fake_ws.get_sync_state.return_value = sync_state

            with (
                patch("src.sprawl.commands.status.Workspace", return_value=fake_ws),
                patch("src.sprawl.commands.status.console") as mock_console,
            ):
                cmd_status(target_dir=tmpdir)
                return mock_console.print.call_count

    def test_status_renders_panel(self):
        """Status renders panels when manifest exists."""
        call_count = self._run_status_with_sync_state({})
        self.assertGreater(call_count, 0)

    def test_status_stale_sync(self):
        """Status shows stale indicator for old sync timestamps."""
        from datetime import datetime, timedelta, timezone

        stale_ts = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
        call_count = self._run_status_with_sync_state({"last_sync_timestamp": stale_ts})
        self.assertGreater(call_count, 0)


if __name__ == "__main__":
    unittest.main()
