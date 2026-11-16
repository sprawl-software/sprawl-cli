"""sprawl-vault — Python-native MCP server for Obsidian vault.

Global vault access limited to configured vault_path. Pure stdlib + rich.
"""

import json
import os
import sys
from typing import Any

from . import (
    MCPError,
    dispatch_mcp_tool_call,
    format_mcp_text_result,
    handle_common_mcp_method,
    read_safe_utf8_file,
    require_path_and_content_arguments,
    require_path_argument,
    write_jsonrpc_error,
    write_safe_utf8_file,
)


class VaultManager:
    """Core logic for sandboxed Obsidian vault operations."""

    def __init__(self, vault_path: str) -> None:
        self.root = os.path.abspath(os.path.expanduser(vault_path))
        if not os.path.isdir(self.root):
            raise ValueError(f"Vault path {self.root} is not a directory.")

    def _get_safe_path(self, rel_path: str) -> str:
        """Resolves relative path and ensures it stays within vault root."""
        if not rel_path.endswith(".md") and not os.path.isdir(os.path.join(self.root, rel_path)):
            rel_path += ".md"

        abs_path = os.path.abspath(os.path.join(self.root, rel_path))
        real_path = os.path.realpath(abs_path)
        real_root = os.path.realpath(self.root)

        if real_path != real_root and not real_path.startswith(real_root + os.sep):
            raise MCPError(
                -32602, f"Security Violation: Path '{rel_path}' resolves outside vault root."
            )
        return real_path

    def read_note(self, path: str) -> str:
        return read_safe_utf8_file(self._get_safe_path(path), path, kind_label="Note")

    def write_note(self, path: str, content: str) -> str:
        return write_safe_utf8_file(self._get_safe_path(path), path, content)

    def list_notes(self, path: str = ".") -> list[str]:
        safe_path = self._get_safe_path(path)
        if not os.path.isdir(safe_path):
            raise MCPError(-32602, f"Directory not found: {path}")
        return sorted(item for item in os.listdir(safe_path) if not item.startswith("."))

    def search_notes(self, query: str) -> list[dict[str, str]]:
        """Simple keyword search across notes."""
        results: list[dict[str, str]] = []
        lowered_query = query.lower()
        for root, _dirs, files in os.walk(self.root):
            if ".obsidian" in root:
                continue
            for file in files:
                if file.endswith(".md"):
                    self._match_note_file(root, file, lowered_query, results)
        return results

    def _match_note_file(
        self,
        root: str,
        file: str,
        lowered_query: str,
        results: list[dict[str, str]],
    ) -> None:
        """Reads a markdown note and appends a preview if it matches lowered_query."""
        path = os.path.join(root, file)
        rel_path = os.path.relpath(path, self.root)
        try:
            with open(path, encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except OSError:
            return
        if lowered_query in content.lower() or lowered_query in file.lower():
            preview = content[:200] + "..." if len(content) > 200 else content
            results.append({"path": rel_path, "preview": preview})


class MCPServer:
    """JSON-RPC 2.0 Server for MCP over stdio."""

    def __init__(self, vault_mgr: VaultManager) -> None:
        self.vault = vault_mgr
        self.tools = {
            "read_note": self._tool_read_note,
            "write_note": self._tool_write_note,
            "list_notes": self._tool_list_notes,
            "search_notes": self._tool_search_notes,
        }

    def _tool_read_note(self, arguments: dict[str, Any]) -> dict[str, Any]:
        return format_mcp_text_result(self.vault.read_note(require_path_argument(arguments)))

    def _tool_write_note(self, arguments: dict[str, Any]) -> dict[str, Any]:
        path, content = require_path_and_content_arguments(arguments)
        return format_mcp_text_result(self.vault.write_note(path, content))

    def _tool_list_notes(self, arguments: dict[str, Any]) -> dict[str, Any]:
        path = arguments.get("path", ".")
        return format_mcp_text_result("\n".join(self.vault.list_notes(path)))

    def _tool_search_notes(self, arguments: dict[str, Any]) -> dict[str, Any]:
        query = arguments.get("query")
        if not query:
            raise MCPError(-32602, "Missing 'query' argument.")
        results = self.vault.search_notes(query)
        return format_mcp_text_result(json.dumps(results, indent=2))

    def run(self) -> None:
        """Main loop reading from stdin."""
        for line in sys.stdin:
            if not line.strip():
                continue
            try:
                request = json.loads(line)
                response = self.handle_request(request)
                if response:
                    sys.stdout.write(json.dumps(response) + "\n")
                    sys.stdout.flush()
            except json.JSONDecodeError:
                self.send_error(None, -32700, "Parse error")
            except (OSError, ValueError, TypeError, KeyError) as e:
                self.send_error(None, -32603, f"Internal error: {e}")

    def handle_request(self, request: dict[str, Any]) -> dict[str, Any] | None:
        msg_id = request.get("id")
        method = request.get("method")
        params = request.get("params", {})

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {"listChanged": True}},
                    "serverInfo": {"name": "sprawl-vault", "version": "1.0.0"},
                },
            }

        handled, common_resp = handle_common_mcp_method(msg_id, method)
        if handled:
            return common_resp

        if method == "tools/list":
            return {"jsonrpc": "2.0", "id": msg_id, "result": {"tools": self._get_tool_schemas()}}

        if method == "tools/call":
            return self._handle_tool_call(msg_id, params)

        if msg_id is not None:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"},
            }
        return None

    @staticmethod
    def _get_tool_schemas() -> list[dict[str, Any]]:
        """Returns the static MCP tool definitions for sprawl-vault."""
        return [
            {
                "name": "read_note",
                "description": "Read the content of a note from the Obsidian vault.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Relative path to the note (e.g. 'Work/Meeting.md' or 'ProjectX')",
                        }
                    },
                    "required": ["path"],
                },
            },
            {
                "name": "write_note",
                "description": "Create or update a note in the Obsidian vault.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "content": {"type": "string"},
                    },
                    "required": ["path", "content"],
                },
            },
            {
                "name": "list_notes",
                "description": "List notes and folders in the vault.",
                "inputSchema": {
                    "type": "object",
                    "properties": {"path": {"type": "string", "description": "Subfolder to list"}},
                    "required": [],
                },
            },
            {
                "name": "search_notes",
                "description": "Search for notes containing a specific keyword.",
                "inputSchema": {
                    "type": "object",
                    "properties": {"query": {"type": "string"}},
                    "required": ["query"],
                },
            },
        ]

    def _handle_tool_call(self, msg_id: Any, params: dict[str, Any]) -> dict[str, Any]:
        return dispatch_mcp_tool_call(msg_id, params, self.tools)

    def send_error(self, msg_id: Any, code: int, message: str) -> None:
        write_jsonrpc_error(msg_id, code, message)


def run_vault_cli(argv: list[str] | None = None) -> None:
    """CLI entrypoint for launching the sprawl-vault MCP stdio server."""
    args_list = sys.argv[1:] if argv is None else list(argv)
    if not args_list:
        print("Usage: sprawl mcp vault <vault_path>", file=sys.stderr)
        sys.exit(1)

    root = args_list[0]
    try:
        mgr = VaultManager(root)
        server = MCPServer(mgr)
        server.run()
    except (OSError, ValueError) as e:
        print(f"Failed to start server: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    run_vault_cli()
