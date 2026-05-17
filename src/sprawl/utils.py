"""Sprawl CLI Utilities — Core constants and helper functions.

This module provides architecture constants and DNA context resolution.
Output functions have been moved to output.py.
"""

import os
from typing import Optional

from .config import config


# Core Architecture Constants
CATEGORIES: list[str] = ["rules", "skills", "atoms", "molecules", "workflows"]

DNA_ALIASES: dict[str, str] = {
    "@python-fastapi": "https://github.com/w3bwizart/aaf-python-fastapi.git",
    "@vanilla-js": "https://github.com/w3bwizart/aaf-vanilla-js.git",
    "@default": "https://github.com/w3bwizart/Atomic_Agentic_Fabric.git",
}

# Backward-compatible re-exports from output.py
# These allow existing imports like `from .utils import print_status` to keep working
# during the transition period. New code should import from output.py directly.


def get_active_dna_context(app_dir: Optional[str] = None) -> str:
    """Deterministically resolves the active DNA context directory.

    Checks the management plane for bound DNA, falling back to the global
    `~/.sprawl/core` hub.

    Args:
        app_dir: Optional directory to check for DNA binding. Defaults to cwd.

    Returns:
        Absolute path to the active DNA context directory.
    """
    if app_dir is None:
        app_dir = os.getcwd()

    from .workspace import Workspace
    workspace = Workspace(app_dir)
    alias_name = workspace.get_dna_alias()
    
    source_dna_dir = config.agents_dir_global

    if alias_name:
        source_dna_dir = os.path.join(config.dna_registry_dir, alias_name)

    return source_dna_dir
