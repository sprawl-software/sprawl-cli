"""Antigravity-specific bindings, workspace manifest, and MCP schema provisioning."""

import os
import json
import shutil
from ..output import console
from .adapters import _write_binding, _prune_empty_dirs


def _write_antigravity_gemini_json(target_dir: str, force: bool) -> bool:
    """Generates .gemini/antigravity/gemini.json for Antigravity workspace detection."""
    gemini_dir = os.path.join(target_dir, ".gemini", "antigravity")
    gemini_json_path = os.path.join(gemini_dir, "gemini.json")

    agents_abs = os.path.abspath(os.path.join(target_dir, ".agents"))

    manifest = {
        "sprawl": {
            "version": "2.0",
            "agents_dir": agents_abs,
            "managed": True,
        }
    }

    content = json.dumps(manifest, indent=2)
    return _write_binding("Antigravity gemini.json", gemini_json_path, content, force)


def _provision_antigravity_schemas() -> bool:
    """Provisions Antigravity MCP tool schema files and instructions.md."""
    user_home = os.path.expanduser("~")
    mcp_base_dir = os.path.join(user_home, ".gemini", "antigravity", "mcp")
    from ..generators.antigravity_schemas import provision_schemas
    success = provision_schemas(mcp_base_dir)
    if success:
        console.print("  [success]✔ Antigravity MCP Schemas:[/success] Provisioned → ~/.gemini/antigravity/mcp/")
        return True
    else:
        console.print("  [error]✗ Antigravity MCP Schemas:[/error] Failed to provision schemas")
        return False


def _remove_antigravity_schemas() -> None:
    """Removes Antigravity MCP tool schema files."""
    try:
        user_home = os.path.expanduser("~")
        mcp_base_dir = os.path.join(user_home, ".gemini", "antigravity", "mcp")
        for server in ("sprawl-workspace-fs", "sprawl-vault"):
            server_dir = os.path.join(mcp_base_dir, server)
            if os.path.exists(server_dir):
                shutil.rmtree(server_dir)
                console.print(f"  [info][-] Antigravity MCP Schemas:[/info] Removed → {server}")
    except Exception:
        pass
