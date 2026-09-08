"""Sprawl CLI Utilities — Core constants and helper functions.

This module provides architecture constants and DNA context resolution.
Output functions have been moved to output.py.
"""

import os
from typing import Optional

from ..config import config


# Core Architecture Constants
CATEGORIES: list[str] = ["rules", "skills", "workflows"]

DNA_ALIASES: dict[str, str] = {
    "@default": "https://github.com/sprawl-software/sprawl-demo-dna.git",
    "@demo": "https://github.com/sprawl-software/sprawl-demo-dna.git",
    "@python-fastapi": "https://github.com/sprawl-software/aaf-python-fastapi.git",
    "@vanilla-js": "https://github.com/sprawl-software/aaf-vanilla-js.git",
}

# Backward-compatible re-exports from output.py
# These allow existing imports like `from .utils import print_status` to keep working
# during the transition period. New code should import from output.py directly.


def get_active_dna_context(app_dir: Optional[str] = None) -> str:
    """Deterministically resolves the active DNA context directory.

    Checks the management plane for bound DNA, falling back to the global
    `~/.sprawl/core` hub or the registry default DNA.

    Args:
        app_dir: Optional directory to check for DNA binding. Defaults to cwd.

    Returns:
        Absolute path to the active DNA context directory.
    """
    if app_dir is None:
        app_dir = os.getcwd()

    from ..workspace import Workspace
    workspace = Workspace(app_dir)
    alias_name = workspace.get_dna_alias()

    if alias_name:
        alias_path = os.path.join(config.dna_registry_dir, alias_name)
        if os.path.exists(alias_path):
            return alias_path

    # Primary fallback to global hub (~/.sprawl/core)
    if os.path.exists(config.agents_dir_global):
        return config.agents_dir_global

    # Secondary fallback to registry default (~/.sprawl/registry/default)
    default_registry_path = os.path.join(config.dna_registry_dir, "default")
    if os.path.exists(default_registry_path):
        return default_registry_path

    return config.agents_dir_global


def get_git_env() -> dict[str, str]:
    """Returns a copy of the current environment with safe SSH options.

    Allows interactive terminal prompts for SSH key passphrases and Git credentials.
    """
    env = os.environ.copy()
    env["GIT_SSH_COMMAND"] = "ssh -o ConnectTimeout=10"
    env.pop("GIT_TERMINAL_PROMPT", None)
    return env
