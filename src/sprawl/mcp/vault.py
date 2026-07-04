"""sprawl-vault — Python-native MCP server for Obsidian vault.

Global vault access limited to configured vault_path. Pure stdlib + rich.
"""

import os
import sys
import json
from typing import Any, Dict, List, Optional


class MCPError(Exception):
    def __init__(self, code: int, message: str, data: Any = None):
        self.code = code
        self.message = message
        self.data = data


class VaultManager:
    """Core logic for sandboxed Obsidian vault operations."""

    def __init__(self, vault_path: str):
        self.root = os.path.abspath(os.path.expanduser(vault_path))
        if not os.path.isdir(self.root):
            raise ValueError(f"Vault path {self.root} is not a directory.")

    def _get_safe_path(self, rel_path: str) -> str:
        """Resolves relative path and ensures it stays within vault root."""
        # Normalize note names if they don't have .md extension
        if not rel_path.endswith(".md") and not os.path.isdir(os.path.join(self.root, rel_path)):
             rel_path += ".md"
             
        abs_path = os.path.abspath(os.path.join(self.root, rel_path))
        real_path = os.path.realpath(abs_path)
        real_root = os.path.realpath(self.root)
        
        # Enforce strict directory boundary — prevent sibling-directory prefix escapes
        if real_path != real_root and not real_path.startswith(real_root + os.sep):
            raise MCPError(-32602, f"Security Violation: Path '{rel_path}' resolves outside vault root.")
        return real_path


    def read_note(self, path: str) -> str:
        safe_path = self._get_safe_path(path)
        if not os.path.isfile(safe_path):
            raise MCPError(-32602, f"Note not found: {path}")
        with open(safe_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    def write_note(self, path: str, content: str) -> str:
        safe_path = self._get_safe_path(path)
        os.makedirs(os.path.dirname(safe_path), exist_ok=True)
        with open(safe_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote to {path}"

    def list_notes(self, path: str = ".") -> List[str]:
        safe_path = self._get_safe_path(path)
        if not os.path.isdir(safe_path):
            raise MCPError(-32602, f"Directory not found: {path}")
        
        items = []
        for item in os.listdir(safe_path):
            if item.startswith("."):
                continue
            items.append(item)
        return sorted(items)

    def search_notes(self, query: str) -> List[Dict[str, str]]:
        """Simple keyword search across notes."""
        results = []
        query = query.lower()
        for root, dirs, files in os.walk(self.root):
            if ".obsidian" in root:
                continue
            for file in files:
                if file.endswith(".md"):
                    path = os.path.join(root, file)
                    rel_path = os.path.relpath(path, self.root)
                    try:
                        with open(path, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                            if query in content.lower() or query in file.lower():
                                results.append({
                                    "path": rel_path,
                                    "preview": content[:200] + "..." if len(content) > 200 else content
                                })
                    except Exception:
                        continue
        return results


class MCPServer:
    """JSON-RPC 2.0 Server for MCP over stdio."""

    def __init__(self, vault_mgr: VaultManager):
        self.vault = vault_mgr
        self.tools = {
            "read_note": self._tool_read_note,
            "write_note": self._tool_write_note,
            "list_notes": self._tool_list_notes,
            "search_notes": self._tool_search_notes,
        }

    def _tool_read_note(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        path = arguments.get("path")
        if not path:
            raise MCPError(-32602, "Missing 'path' argument.")
        content = self.vault.read_note(path)
        return {"content": [{"type": "text", "text": content}]}

    def _tool_write_note(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        path = arguments.get("path")
        content = arguments.get("content")
        if not path or content is None:
            raise MCPError(-32602, "Missing 'path' or 'content' argument.")
        result = self.vault.write_note(path, content)
        return {"content": [{"type": "text", "text": result}]}

    def _tool_list_notes(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        path = arguments.get("path", ".")
        items = self.vault.list_notes(path)
        return {"content": [{"type": "text", "text": "\n".join(items)}]}

    def _tool_search_notes(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        query = arguments.get("query")
        if not query:
            raise MCPError(-32602, "Missing 'query' argument.")
        results = self.vault.search_notes(query)
        return {"content": [{"type": "text", "text": json.dumps(results, indent=2)}]}

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
            except Exception as e:
                self.send_error(None, -32603, f"Internal error: {str(e)}")

    def handle_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        msg_id = request.get("id")
        method = request.get("method")
        params = request.get("params", {})

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "serverInfo": {"name": "sprawl-vault", "version": "1.0.0"}
                }
            }
        
        if method == "notifications/initialized":
            return None

        if method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "tools": [
                        {
                            "name": "read_note",
                            "description": "Read the content of a note from the Obsidian vault.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {"path": {"type": "string", "description": "Relative path to the note (e.g. 'Work/Meeting.md' or 'ProjectX')"}},
                                "required": ["path"]
                            }
                        },
                        {
                            "name": "write_note",
                            "description": "Create or update a note in the Obsidian vault.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
                                "required": ["path", "content"]
                            }
                        },
                        {
                            "name": "list_notes",
                            "description": "List notes and folders in the vault.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {"path": {"type": "string", "description": "Subfolder to list"}},
                                "required": []
                            }
                        },
                        {
                            "name": "search_notes",
                            "description": "Search for notes containing a specific keyword.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {"query": {"type": "string"}},
                                "required": ["query"]
                            }
                        }
                    ]
                }
            }

        if method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            if tool_name in self.tools:
                try:
                    result = self.tools[tool_name](arguments)
                    return {"jsonrpc": "2.0", "id": msg_id, "result": result}
                except MCPError as e:
                    return {
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "error": {"code": e.code, "message": e.message, "data": e.data}
                    }
                except Exception as e:
                    return {
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "error": {"code": -32603, "message": str(e)}
                    }
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {"code": -32601, "message": f"Tool not found: {tool_name}"}
                }

        return None

    def send_error(self, msg_id: Any, code: int, message: str):
        response = {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {"code": code, "message": message}
        }
        sys.stdout.write(json.dumps(response) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python vault.py <vault_path>", file=sys.stderr)
        sys.exit(1)
    
    root = sys.argv[1]
    try:
        mgr = VaultManager(root)
        server = MCPServer(mgr)
        server.run()
    except Exception as e:
        print(f"Failed to start server: {e}", file=sys.stderr)
        sys.exit(1)
