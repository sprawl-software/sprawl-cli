"""Backward-compatible shim — re-exports all commands from the commands/ package.

This file exists solely for backward compatibility with existing imports.
All command logic has been decomposed into src/sprawl/commands/*.py.
New code should import from src.sprawl.commands directly.
"""

# Re-export everything for backward compatibility
from .commands import (
    cmd_add,
    cmd_bind,
    cmd_clean_demo,
    cmd_clean_test,
    cmd_create,
    cmd_demo,
    cmd_fetch_dna,
    cmd_graft,
    cmd_init,
    cmd_list,
    cmd_man,
    cmd_remove,
    cmd_scaffold,
    cmd_sync,
    cmd_update,
)

__all__ = [
    "cmd_init",
    "cmd_fetch_dna",
    "cmd_create",
    "cmd_graft",
    "cmd_sync",
    "cmd_bind",
    "cmd_list",
    "cmd_add",
    "cmd_scaffold",
    "cmd_remove",
    "cmd_update",
    "cmd_clean_test",
    "cmd_clean_demo",
    "cmd_man",
    "cmd_demo",
]
