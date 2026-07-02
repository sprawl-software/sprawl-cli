"""Generator for mcp_config.json — Clean Room architecture compliant."""

import os
import sys
import json
from typing import Any, Dict, List, Optional


def generate_mcp_config(
    output_path: str,
    reqs: Dict[str, List[str]],
    app_dir: str,
    local_agents_dir: str,
    venv_python: str,
    vault_path: Optional[str] = None
) -> None:
    """Generates a standardized mcp_config.json for the workspace.

    Args:
        output_path: Path where mcp_config.json will be written.
        reqs: Dictionary of required artifacts by category.
        app_dir: Absolute path to the workspace root.
        local_agents_dir: Path to the local .agents/ directory.
        venv_python: Path to the workspace virtual environment python.
        vault_path: Optional path to the global Obsidian vault.
    """
    mcp_config = {"mcpServers": {}}

    # 1. Inject Workspace Filesystem (The Hard Fence)
    mcp_config["mcpServers"]["sprawl-workspace-fs"] = {
        "command": sys.executable,
        "args": [
            "-m",
            "sprawl.mcp.workspace_fs",
            os.path.abspath(app_dir)
        ]
    }

    # 2. Inject Vault (Global Knowledge)
    if vault_path:
        mcp_config["mcpServers"]["sprawl-vault"] = {
            "command": sys.executable,
            "args": [
                "-m",
                "sprawl.mcp.vault",
                os.path.abspath(os.path.expanduser(vault_path))
            ]
        }

    # 3. Process Molecules (Deprecated, skipped)

    with open(output_path, "w") as f:
        json.dump(mcp_config, f, indent=4)
