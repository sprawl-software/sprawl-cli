"""Generator for mcp_config.json — Clean Room architecture compliant."""

import json
import os
import tempfile
from typing import Any

from ..utils import get_mcp_command_executable, is_compiled_binary


def _merge_mcp_file(target_path: str, servers: dict[str, Any]) -> None:
    """Non-destructively merges Sprawl MCP server definitions into an IDE mcp json file."""
    existing: dict[str, Any] = {}
    if os.path.isfile(target_path):
        try:
            with open(target_path, encoding="utf-8") as f:
                loaded = json.load(f)
                if isinstance(loaded, dict):
                    existing = loaded
        except (OSError, json.JSONDecodeError):
            existing = {}

    mcp_servers = existing.get("mcpServers")
    if not isinstance(mcp_servers, dict):
        mcp_servers = {}
    mcp_servers.update(servers)
    existing["mcpServers"] = mcp_servers

    os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)
    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=4)


def _provision_antigravity_plugin(local_agents_dir: str, mcp_config: dict[str, Any]) -> None:
    """Provisions .agents/plugins/sprawl-mcp/{plugin.json,mcp_config.json} for Antigravity auto-discovery."""
    plugin_dir = os.path.join(local_agents_dir, "plugins", "sprawl-mcp")
    os.makedirs(plugin_dir, exist_ok=True)
    plugin_manifest_path = os.path.join(plugin_dir, "plugin.json")
    with open(plugin_manifest_path, "w", encoding="utf-8") as f:
        json.dump({"name": "sprawl-mcp"}, f, indent=2)

    plugin_mcp_path = os.path.join(plugin_dir, "mcp_config.json")
    with open(plugin_mcp_path, "w", encoding="utf-8") as f:
        json.dump(mcp_config, f, indent=4)


def _build_workspace_fs_args(
    app_dir: str, allowed_mounts: dict[str, str] | None, compiled: bool
) -> list[str]:
    """Builds CLI argument list for the sprawl-workspace-fs MCP server."""
    base_arg = os.path.abspath(app_dir)
    args = (
        ["mcp", "workspace-fs", base_arg]
        if compiled
        else ["-m", "sprawl.mcp.workspace_fs", base_arg]
    )
    if allowed_mounts:
        for alias, target_path in sorted(allowed_mounts.items()):
            resolved = os.path.abspath(os.path.expanduser(target_path))
            args.extend(["--mount", f"{alias}={resolved}"])
    return args


def _sync_global_antigravity_mcp(
    mcp_servers: dict[str, Any], app_dir: str, global_agy_mcp_path: str | None
) -> None:
    """Non-destructively merges Sprawl MCP servers into Antigravity global mcp_config.json."""
    if global_agy_mcp_path is not None:
        _merge_mcp_file(global_agy_mcp_path, mcp_servers)
        return
    if not os.path.isdir(app_dir):
        return
    temp_root = os.path.abspath(tempfile.gettempdir())
    abs_app = os.path.abspath(app_dir)
    if abs_app != temp_root and not abs_app.startswith(temp_root + os.sep):
        default_agy_mcp = os.path.join(
            os.path.expanduser("~"), ".gemini", "config", "mcp_config.json"
        )
        _merge_mcp_file(default_agy_mcp, mcp_servers)


def _sync_workspace_ide_mcp_files(
    app_dir: str, mcp_servers: dict[str, Any], allowed_mounts: dict[str, str] | None
) -> None:
    """Provisions .mcp.json (Claude Code) and .cursor/mcp.json (Cursor) in the workspace."""
    if not os.path.isdir(app_dir):
        return
    claude_mcp_path = os.path.join(app_dir, ".mcp.json")
    if (
        allowed_mounts
        or os.path.exists(claude_mcp_path)
        or os.path.exists(os.path.join(app_dir, "CLAUDE.md"))
    ):
        _merge_mcp_file(claude_mcp_path, mcp_servers)

    cursor_dir = os.path.join(app_dir, ".cursor")
    if (
        allowed_mounts
        or os.path.isdir(cursor_dir)
        or os.path.exists(os.path.join(app_dir, ".cursorrules"))
    ):
        _merge_mcp_file(os.path.join(cursor_dir, "mcp.json"), mcp_servers)


def generate_mcp_config(
    output_path: str,
    reqs: dict[str, list[str]],
    app_dir: str,
    local_agents_dir: str,
    venv_python: str,
    vault_path: str | None = None,
    allowed_mounts: dict[str, str] | None = None,
    global_agy_mcp_path: str | None = None,
) -> None:
    """Generates standardized MCP configurations for the workspace and active IDEs."""
    cmd_exe = get_mcp_command_executable()
    compiled = is_compiled_binary()
    mcp_config: dict[str, dict[str, Any]] = {
        "mcpServers": {
            "sprawl-workspace-fs": {
                "command": cmd_exe,
                "args": _build_workspace_fs_args(app_dir, allowed_mounts, compiled),
            }
        }
    }

    if vault_path:
        resolved_vault = os.path.abspath(os.path.expanduser(vault_path))
        vault_args = (
            ["mcp", "vault", resolved_vault]
            if compiled
            else ["-m", "sprawl.mcp.vault", resolved_vault]
        )
        mcp_config["mcpServers"]["sprawl-vault"] = {
            "command": cmd_exe,
            "args": vault_args,
        }

    from .antigravity_schemas import provision_schemas

    provision_schemas(os.path.join(os.path.expanduser("~"), ".gemini", "antigravity", "mcp"))
    _sync_global_antigravity_mcp(mcp_config["mcpServers"], app_dir, global_agy_mcp_path)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(mcp_config, f, indent=4)

    if os.path.isdir(local_agents_dir):
        agents_mcp_path = os.path.join(local_agents_dir, "mcp_config.json")
        if os.path.abspath(agents_mcp_path) != os.path.abspath(output_path):
            with open(agents_mcp_path, "w", encoding="utf-8") as f:
                json.dump(mcp_config, f, indent=4)
        _provision_antigravity_plugin(local_agents_dir, mcp_config)

    _sync_workspace_ide_mcp_files(app_dir, mcp_config["mcpServers"], allowed_mounts)
