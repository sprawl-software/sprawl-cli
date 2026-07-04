"""Sovereign Mount Engine — Configures allowed directory mounts for the sandboxed MCP server.

Includes CLI subcommands (add, remove, list) and routes to interactive TUI menus.
"""

import os
import re
import sys
import json
from typing import Any
from rich.table import Table
from ..exceptions import SprawlError
from ..output import console, print_status, print_error
from .sync_cmd import cmd_sync


def slugify(name: str) -> str:
    """Helper to convert folder name into a clean, safe alphanumeric alias."""
    s = name.lower()
    s = re.sub(r"[^a-z0-9_-]", "_", s)
    s = re.sub(r"_+", "_", s)
    return s.strip("_")


def _get_workspace_paths(target_dir: str = None) -> tuple[str, str, str]:
    """Helper to verify workspace root and return config paths."""
    workspace_root = os.path.abspath(target_dir) if target_dir else os.getcwd()
    agents_dir = os.path.join(workspace_root, ".agents")
    if not os.path.exists(agents_dir):
        raise SprawlError(
            f"Cannot configure mounts: {agents_dir} not found. Is this an agentic workspace?\n"
            "Run 'sprawl init <URL>' or 'sprawl graft' first."
        )
    config_path = os.path.join(agents_dir, "sprawl-config.json")
    return workspace_root, agents_dir, config_path


def _load_config(config_path: str) -> dict[str, Any]:
    """Helper to read sprawl-config.json safely."""
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except Exception:
            pass
    return {"allowed_mounts": {}}


def _write_config(config_path: str, data: dict[str, Any]) -> None:
    """Helper to write sprawl-config.json cleanly."""
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def cmd_mount_add(path: str, alias: str = None, target_dir: str = None) -> None:
    """Directly configures a path into the allowed mounts config."""
    workspace_root, _, config_path = _get_workspace_paths(target_dir)
    cfg = _load_config(config_path)

    if "allowed_mounts" not in cfg or not isinstance(cfg["allowed_mounts"], dict):
        cfg["allowed_mounts"] = {}

    abs_path = os.path.abspath(os.path.expanduser(path))
    if not os.path.exists(abs_path):
        raise SprawlError(f"Directory path '{path}' does not exist.")
    if not os.path.isdir(abs_path):
        raise SprawlError(f"Path '{path}' is a file, not a directory.")

    if not alias:
        alias = slugify(os.path.basename(abs_path))
        if not alias:
            alias = "mount"

    # Enforce safe alias formatting
    alias = slugify(alias)

    cfg["allowed_mounts"][alias] = abs_path
    _write_config(config_path, cfg)
    print_status(f"Added workspace mount: [accent]{alias}[/accent] → {abs_path}")

    # Immediately trigger sync to regenerate mcp_config.json
    print_status("Synchronizing workspace configurations...")
    cmd_sync(workspace_root)


def cmd_mount_remove(alias: str, target_dir: str = None) -> None:
    """Directly removes a mount configuration by alias."""
    workspace_root, _, config_path = _get_workspace_paths(target_dir)
    cfg = _load_config(config_path)

    mounts = cfg.get("allowed_mounts", {})
    if not isinstance(mounts, dict) or alias not in mounts:
        raise SprawlError(f"Mount alias '{alias}' not found in configuration.")

    removed_path = mounts.pop(alias)
    cfg["allowed_mounts"] = mounts
    _write_config(config_path, cfg)
    print_status(f"Removed workspace mount: [accent]{alias}[/accent] (was mapping to {removed_path})")

    # Immediately trigger sync to regenerate mcp_config.json
    print_status("Synchronizing workspace configurations...")
    cmd_sync(workspace_root)


def cmd_mount_list(target_dir: str = None) -> None:
    """Lists all configured directory mounts in a formatted table."""
    _, _, config_path = _get_workspace_paths(target_dir)
    cfg = _load_config(config_path)

    mounts = cfg.get("allowed_mounts", {})
    if not isinstance(mounts, dict) or not mounts:
        print_status("No directory mounts configured for this workspace.")
        return

    table = Table(show_header=True, border_style="#5D5CFF")
    table.add_column("Alias/Prefix", style="accent")
    table.add_column("Absolute Target Path", style="info")

    for alias in sorted(mounts.keys()):
        table.add_row(f"@{alias}", mounts[alias])

    console.print(table)


def cmd_mount(args: Any) -> None:
    """Core routing entrypoint for the sprawl mount command block."""
    target_dir = getattr(args, "project", None)
    
    if args.mount_command == "add":
        cmd_mount_add(args.path, getattr(args, "alias", None), target_dir)
    elif args.mount_command == "remove":
        cmd_mount_remove(args.alias, target_dir)
    elif args.mount_command == "list":
        cmd_mount_list(target_dir)
    elif args.mount_command is None:
        # Launch interactive TUI Dashboard
        if not sys.stdin.isatty() or not sys.stdout.isatty():
            raise SprawlError("Cannot launch interactive mount dashboard in a non-TTY environment.")
            
        workspace_root, _, _ = _get_workspace_paths(target_dir)
        from ..utils.tui import show_mount_dashboard
        show_mount_dashboard(workspace_root)
