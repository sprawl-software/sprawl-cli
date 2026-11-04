"""Generator for mcp_config.json — Clean Room architecture compliant."""

import json
import os
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


def generate_mcp_config(
    output_path: str,
    reqs: dict[str, list[str]],
    app_dir: str,
    local_agents_dir: str,
    venv_python: str,
    vault_path: str | None = None,
    allowed_mounts: dict[str, str] | None = None,
) -> None:
    """Generates standardized MCP configurations for the workspace and active IDEs.

    Args:
        output_path: Path where mcp_config.json will be written.
        reqs: Dictionary of required artifacts by category.
        app_dir: Absolute path to the workspace root.
        local_agents_dir: Path to the local .agents/ directory.
        venv_python: Path to the workspace virtual environment python.
        vault_path: Optional path to the global Obsidian vault.
        allowed_mounts: Optional dictionary mapping mount aliases to target paths.
    """
    mcp_config: dict[str, dict[str, Any]] = {"mcpServers": {}}
    cmd_exe = get_mcp_command_executable()
    compiled = is_compiled_binary()

    # 1. Inject Workspace Filesystem (The Hard Fence)
    if compiled:
        args = ["mcp", "workspace-fs", os.path.abspath(app_dir)]
    else:
        args = ["-m", "sprawl.mcp.workspace_fs", os.path.abspath(app_dir)]
    if allowed_mounts:
        for alias, target_path in sorted(allowed_mounts.items()):
            args.extend(["--mount", f"{alias}={os.path.abspath(os.path.expanduser(target_path))}"])

    mcp_config["mcpServers"]["sprawl-workspace-fs"] = {
        "command": cmd_exe,
        "args": args,
    }

    # 2. Inject Vault (Global Knowledge)
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

    # 3. Provision Antigravity MCP Schemas (legacy path) & Workspace Plugin (Antigravity 2.0)
    user_home = os.path.expanduser("~")
    mcp_base_dir = os.path.join(user_home, ".gemini", "antigravity", "mcp")
    from .antigravity_schemas import provision_schemas

    provision_schemas(mcp_base_dir)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(mcp_config, f, indent=4)

    if os.path.isdir(local_agents_dir):
        agents_mcp_path = os.path.join(local_agents_dir, "mcp_config.json")
        if os.path.abspath(agents_mcp_path) != os.path.abspath(output_path):
            with open(agents_mcp_path, "w", encoding="utf-8") as f:
                json.dump(mcp_config, f, indent=4)
        _provision_antigravity_plugin(local_agents_dir, mcp_config)

    # 4. Provision IDE-native MCP discovery files (.mcp.json for Claude Code, .cursor/mcp.json for Cursor)
    if os.path.isdir(app_dir):
        claude_mcp_path = os.path.join(app_dir, ".mcp.json")
        if (
            allowed_mounts
            or os.path.exists(claude_mcp_path)
            or os.path.exists(os.path.join(app_dir, "CLAUDE.md"))
        ):
            _merge_mcp_file(claude_mcp_path, mcp_config["mcpServers"])

        cursor_dir = os.path.join(app_dir, ".cursor")
        if (
            allowed_mounts
            or os.path.isdir(cursor_dir)
            or os.path.exists(os.path.join(app_dir, ".cursorrules"))
        ):
            _merge_mcp_file(os.path.join(cursor_dir, "mcp.json"), mcp_config["mcpServers"])
