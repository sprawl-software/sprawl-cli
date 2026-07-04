"""Generator for Antigravity MCP schemas — DRY implementation."""

import os
import json


def provision_schemas(mcp_base_dir: str) -> bool:
    """Provisions Antigravity MCP tool schema files and instructions.md.

    Args:
        mcp_base_dir: Base directory where schema directories will be created.

    Returns:
        bool: True if schemas were provisioned successfully, False otherwise.
    """
    try:
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
        return True
    except Exception:
        return False
