"""Sprawl CLI Commands Package — Decomposed from the core.py monolith.

Each submodule contains logically grouped command functions:
- init_cmd: DNA initialization and fetching
- workspace: Workspace creation and grafting
- sync_cmd: Sync orchestration and IDE binding
- artifacts: Artifact discovery, injection, scaffolding, and removal
- diagnostics: Update, cleanup, manual, and demo engine
"""

# Re-export all command functions for backward compatibility
from .init_cmd import cmd_init, cmd_fetch_dna
from .workspace import cmd_create, cmd_graft
from .sync_cmd import cmd_sync, cmd_bind
from .diff import cmd_diff
from .artifacts import cmd_list, cmd_add, cmd_scaffold, cmd_remove
from .diagnostics import cmd_update, cmd_clean_test, cmd_clean_demo, cmd_demo
from .shell import cmd_shell
from .man import cmd_man
from .doctor import cmd_doctor
from .status import cmd_status
from .wipe import cmd_wipe

__all__ = [
    "cmd_init", "cmd_fetch_dna",
    "cmd_create", "cmd_graft",
    "cmd_sync", "cmd_bind", "cmd_diff",
    "cmd_list", "cmd_add", "cmd_scaffold", "cmd_remove",
    "cmd_update", "cmd_clean_test", "cmd_clean_demo", "cmd_man", "cmd_demo", "cmd_doctor",
    "cmd_shell",
    "cmd_status",
    "cmd_wipe",
]
