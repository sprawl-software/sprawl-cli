"""Sprawl CLI Commands Package — Decomposed from the core.py monolith.

Each submodule contains logically grouped command functions:
- init_cmd: DNA initialization and fetching
- workspace: Workspace creation and grafting
- sync_cmd: Sync orchestration and IDE binding
- artifacts: Artifact discovery, injection, scaffolding, and removal
- diagnostics: Update, cleanup, manual, and demo engine
"""

# Re-export all command functions for backward compatibility
from .artifacts import cmd_add, cmd_list, cmd_remove, cmd_scaffold
from .diagnostics import cmd_clean_demo, cmd_clean_test, cmd_demo, cmd_update
from .diff import cmd_diff
from .doctor import cmd_doctor
from .init_cmd import cmd_fetch_dna, cmd_init
from .man import cmd_man
from .shell import cmd_shell
from .status import cmd_status
from .sync_cmd import cmd_bind, cmd_sync
from .wipe import cmd_wipe
from .workspace import cmd_create, cmd_graft

__all__ = [
    "cmd_init",
    "cmd_fetch_dna",
    "cmd_create",
    "cmd_graft",
    "cmd_sync",
    "cmd_bind",
    "cmd_diff",
    "cmd_list",
    "cmd_add",
    "cmd_scaffold",
    "cmd_remove",
    "cmd_update",
    "cmd_clean_test",
    "cmd_clean_demo",
    "cmd_man",
    "cmd_demo",
    "cmd_doctor",
    "cmd_shell",
    "cmd_status",
    "cmd_wipe",
]
