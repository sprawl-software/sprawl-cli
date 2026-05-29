"""Sprawl Registry Scanner.

Scans bound DNA registry categories (rules, skills, atoms, molecules, workflows)
and maps them against the local workspace sprawl_manifest.yml to determine selection states.
"""

import os
from typing import Dict, List, Tuple

from . import CATEGORIES, get_active_dna_context
from ..sync import parse_sprawl_manifest


class RegistryScanner:
    """Scans and maps global DNA registry items to local selection states."""

    def __init__(self, workspace_dir: str):
        """Initializes the scanner for a given workspace.

        Args:
            workspace_dir: Absolute path to the workspace root.
        """
        self.workspace_dir = os.path.abspath(os.path.expanduser(workspace_dir))
        self.manifest_path = os.path.join(self.workspace_dir, ".agents", "sprawl_manifest.yml")
        self.active_dna_dir = get_active_dna_context(self.workspace_dir)

    def scan(self) -> Dict[str, List[Tuple[str, bool]]]:
        """Scans the bound central DNA vault and identifies checked items.

        Returns:
            Dict mapping category name to list of tuples (item_name, is_checked).
        """
        # Parse manifest to identify currently checked items
        checked_items = parse_sprawl_manifest(self.manifest_path)

        result: Dict[str, List[Tuple[str, bool]]] = {}

        for category in CATEGORIES:
            result[category] = []
            category_dir = os.path.join(self.active_dna_dir, category)
            if not os.path.isdir(category_dir):
                continue

            try:
                entries = os.listdir(category_dir)
            except Exception:
                continue

            # Sort entries alphabetically, excluding hidden files
            sorted_entries = sorted(e for e in entries if not e.startswith("."))

            for entry in sorted_entries:
                is_checked = entry in checked_items.get(category, [])
                result[category].append((entry, is_checked))

        return result
