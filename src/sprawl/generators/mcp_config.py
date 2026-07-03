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

    # 4. Provision Antigravity MCP Schemas
    try:
        user_home = os.path.expanduser("~")
        mcp_base_dir = os.path.join(user_home, ".gemini", "antigravity", "mcp")

        # Provision sprawl-workspace-fs schemas
        ws_schema_dir = os.path.join(mcp_base_dir, "sprawl-workspace-fs")
        os.makedirs(ws_schema_dir, exist_ok=True)
        ws_schemas = {
            "read_file.json": {
              "name": "read_file",
              "description": "Read the content of a file within the workspace or mapped mounts using the '@alias/subpath' format.",
              "inputSchema": {
                "type": "object",
                "properties": {
                  "path": {
                    "type": "string",
                    "description": "The path to read. Can be relative to the workspace root or start with '@<alias>/<subpath>'."
                  }
                },
                "required": ["path"]
              }
            },
            "write_file.json": {
              "name": "write_file",
              "description": "Write content to a file within the workspace or mapped mounts using the '@alias/subpath' format.",
              "inputSchema": {
                "type": "object",
                "properties": {
                  "path": {
                    "type": "string",
                    "description": "The target path to write to. Can be relative to the workspace root or start with '@<alias>/<subpath>'."
                  },
                  "content": {
                    "type": "string",
                    "description": "The file content to write."
                  }
                },
                "required": ["path", "content"]
              }
            },
            "list_directory.json": {
              "name": "list_directory",
              "description": "List contents of a directory within the workspace or mapped mounts using the '@alias/subpath' format.",
              "inputSchema": {
                "type": "object",
                "properties": {
                  "path": {
                    "type": "string",
                    "description": "The path to list. Can be relative to the workspace root, start with '@<alias>/<subpath>', or '@<alias>' to list mount root."
                  }
                },
                "required": []
              }
            }
        }
        for filename, data in ws_schemas.items():
            with open(os.path.join(ws_schema_dir, filename), "w", encoding="utf-8") as sf:
                json.dump(data, sf, indent=2)

        with open(os.path.join(ws_schema_dir, "instructions.md"), "w", encoding="utf-8") as sf:
            sf.write(
                "# sprawl-workspace-fs MCP Server Best Practices\n\n"
                "You have secure access to the local workspace and allowed mount points via this MCP server.\n\n"
                "## Allowed Mounts Resolution\n"
                "* To list the root directory of a mount, use `list_directory` with `path` set to `@alias`.\n"
                "* To access files or subdirectories within a mount, prefix the path with `@alias/` (e.g. `read_file` with `path` set to `@alias/subfolder/file.py`).\n"
                "* All paths must be specified using the `@alias/` syntax when accessing files/folders outside the workspace. Direct absolute paths to these folders are blocked by design.\n"
            )

        # Provision sprawl-vault schemas
        vault_schema_dir = os.path.join(mcp_base_dir, "sprawl-vault")
        os.makedirs(vault_schema_dir, exist_ok=True)
        vault_schemas = {
            "read_note.json": {
              "name": "read_note",
              "description": "Read the content of a markdown note within the Obsidian vault.",
              "inputSchema": {
                "type": "object",
                "properties": {
                  "path": {
                    "type": "string",
                    "description": "The path to the note relative to the vault root (with or without .md)."
                  }
                },
                "required": ["path"]
              }
            },
            "write_note.json": {
              "name": "write_note",
              "description": "Write content to a markdown note within the Obsidian vault.",
              "inputSchema": {
                "type": "object",
                "properties": {
                  "path": {
                    "type": "string",
                    "description": "The path to the target note relative to the vault root."
                  },
                  "content": {
                    "type": "string",
                    "description": "The content to write into the note."
                  }
                },
                "required": ["path", "content"]
              }
            },
            "list_notes.json": {
              "name": "list_notes",
              "description": "List markdown notes and directories in the Obsidian vault.",
              "inputSchema": {
                "type": "object",
                "properties": {
                  "path": {
                    "type": "string",
                    "description": "The relative directory path to list. Defaults to the vault root."
                  }
                },
                "required": []
              }
            },
            "search_notes.json": {
              "name": "search_notes",
              "description": "Keyword search across all markdown notes in the Obsidian vault.",
              "inputSchema": {
                "type": "object",
                "properties": {
                  "query": {
                    "type": "string",
                    "description": "The search term or keyword."
                  }
                },
                "required": ["query"]
              }
            }
        }
        for filename, data in vault_schemas.items():
            with open(os.path.join(vault_schema_dir, filename), "w", encoding="utf-8") as sf:
                json.dump(data, sf, indent=2)

        with open(os.path.join(vault_schema_dir, "instructions.md"), "w", encoding="utf-8") as sf:
            sf.write(
                "# sprawl-vault MCP Server Best Practices\n\n"
                "You have secure access to the Obsidian vault via this MCP server.\n\n"
                "* To retrieve the contents of a note, use `read_note`.\n"
                "* To list the files/directories in the vault or a subdirectory, use `list_notes`.\n"
                "* To find notes containing a specific keyword, use `search_notes`.\n"
                "* Always use these vault-specific tools rather than generic workspace tools when interacting with the Obsidian vault files.\n"
            )
    except Exception:
        pass

    with open(output_path, "w") as f:
        json.dump(mcp_config, f, indent=4)
