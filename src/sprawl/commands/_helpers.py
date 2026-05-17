"""Shared helpers used across command modules."""

import os
from typing import Optional

from ..utils import CATEGORIES


def resolve_item_in_dna(item: str, source_dna_dir: str) -> tuple[Optional[str], Optional[str]]:
    """Resolves a named item to its exact filename within the active DNA context.

    Checks for directory match, then .md, .yml, .yaml, .json extensions in order.

    Args:
        item: The artifact name to resolve.
        source_dna_dir: Path to the active DNA context directory.

    Returns:
        Tuple of (category, resolved_filename) or (None, None) if not found.
    """
    for category in CATEGORIES:
        cat_dir = os.path.join(source_dna_dir, category)
        if not os.path.exists(cat_dir):
            continue
        dir_contents = os.listdir(cat_dir)
        for candidate in [item, f"{item}.md", f"{item}.yml", f"{item}.yaml", f"{item}.json"]:
            if candidate in dir_contents:
                return category, candidate
    return None, None


def resolve_repo_root() -> Optional[str]:
    """Deterministically resolves the Sprawl CLI source repository root.

    Walks up from the installed script path, then falls back to known
    enterprise paths and environment variables.

    Returns:
        Absolute path to the repo root, or None if not found.
    """
    script_path = os.path.realpath(__file__)
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(script_path))))

    if os.path.exists(os.path.join(repo_root, ".git")):
        return repo_root

    # Check current working directory (dev mode)
    cwd = os.getcwd()
    if os.path.exists(os.path.join(cwd, ".git")) and os.path.exists(os.path.join(cwd, "src", "sprawl", "core.py")):
        return cwd

    # Fallback to environment variable if set
    env_path = os.environ.get("SPRAWL_DEV_MODE_PATH")
    if env_path and os.path.exists(os.path.join(env_path, ".git")):
        return env_path

    return None
