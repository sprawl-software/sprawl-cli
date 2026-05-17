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

    # 3. Process Molecules (Additional servers)
    for molecule_file in reqs.get("molecules", []):
        molecule_path = os.path.join(local_agents_dir, "molecules", molecule_file)
        if os.path.exists(molecule_path):
            try:
                with open(molecule_path, "r") as f:
                    molecule_data = json.load(f)
                    
                for server_name, server_config in molecule_data.items():
                    if "command" in server_config:
                        cmd = server_config["command"]
                        
                        interpolated_args = []
                        for arg in server_config.get("args", []):
                            if arg == "$VENV_PYTHON":
                                interpolated_args.append(venv_python)
                            elif arg.startswith("$LOCAL_SKILL:"):
                                skill_name = arg.split(":", 1)[1]
                                interpolated_args.append(os.path.join(local_agents_dir, "skills", skill_name))
                            elif arg.startswith("$VENV_SKILL_BIN:"):
                                parts = arg.split(":", 2)
                                if len(parts) == 3:
                                    skill_name = parts[1]
                                    bin_name = parts[2]
                                    interpolated_args.append(os.path.join(local_agents_dir, ".venv", "bin", bin_name))
                                else:
                                    interpolated_args.append(arg) 
                            else:
                                interpolated_args.append(arg)
                        
                        mcp_config["mcpServers"][server_name] = {
                            "command": cmd,
                            "args": interpolated_args
                        }
                        if "env" in server_config:
                            mcp_config["mcpServers"][server_name]["env"] = server_config["env"]

            except (json.JSONDecodeError, IOError):
                # We skip malformed molecules in the generator; 
                # validation should happen elsewhere if needed.
                pass

    with open(output_path, "w") as f:
        json.dump(mcp_config, f, indent=4)
