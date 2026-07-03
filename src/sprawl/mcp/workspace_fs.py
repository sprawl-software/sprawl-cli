"""sprawl-workspace-fs — Python-native MCP filesystem server.

Limited to the workspace root. Pure stdlib + rich.
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


class WorkspaceFS:
    """Core logic for sandboxed filesystem operations."""

    def __init__(self, root_path: str):
        self.root = os.path.abspath(os.path.expanduser(root_path))
        if not os.path.isdir(self.root):
            raise ValueError(f"Root path {self.root} is not a directory.")

        # Load allowed mounts from sprawl-config.json
        self.allowed_mounts = {}
        config_path = os.path.join(self.root, ".agents", "sprawl-config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                self.allowed_mounts = cfg.get("allowed_mounts", {})
            except Exception:
                pass
        if not isinstance(self.allowed_mounts, dict):
            self.allowed_mounts = {}

    def _get_safe_path(self, rel_path: str) -> str:
        """Resolves relative path and ensures it stays within root or allowed mounts."""
        if rel_path.startswith("@"):
            parts = rel_path.split("/", 1)
            alias = parts[0][1:]
            
            if alias in self.allowed_mounts:
                mount_root = os.path.abspath(os.path.expanduser(self.allowed_mounts[alias]))
                sub_path = parts[1] if len(parts) > 1 else ""
                
                # Prevent absolute paths or home expansion inside mount
                if os.path.isabs(sub_path) or sub_path.startswith("~"):
                    raise MCPError(-32602, "Security Violation: Absolute paths and home expansion are not allowed inside mounts.")
                
                abs_path = os.path.abspath(os.path.join(mount_root, sub_path))
                real_path = os.path.realpath(abs_path)
                real_mount_root = os.path.realpath(mount_root)
                
                # Enforce strict directory boundary — prevent sibling-directory prefix escapes
                # e.g. /home/user/mount vs /home/user/mount-secrets
                if real_path != real_mount_root and not real_path.startswith(real_mount_root + os.sep):
                    raise MCPError(-32602, f"Security Violation: Path '{rel_path}' resolves outside mount root '{alias}'.")
                return real_path
            else:
                raise MCPError(-32602, f"Security Violation: Mount alias '{alias}' is not allowed/configured.")

        # Prevent absolute paths or home expansion
        if os.path.isabs(rel_path) or rel_path.startswith("~"):
            raise MCPError(-32602, "Security Violation: Absolute paths and home expansion are not allowed.")
        
        abs_path = os.path.abspath(os.path.join(self.root, rel_path))
        real_path = os.path.realpath(abs_path)
        real_root = os.path.realpath(self.root)
        
        # Enforce strict directory boundary — prevent sibling-directory prefix escapes
        if real_path != real_root and not real_path.startswith(real_root + os.sep):
            raise MCPError(-32602, f"Security Violation: Path '{rel_path}' resolves outside workspace root.")
        return real_path

    def read_file(self, path: str) -> str:
        safe_path = self._get_safe_path(path)
        if not os.path.isfile(safe_path):
            raise MCPError(-32602, f"File not found: {path}")
        with open(safe_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    def write_file(self, path: str, content: str) -> str:
        safe_path = self._get_safe_path(path)
        os.makedirs(os.path.dirname(safe_path), exist_ok=True)
        with open(safe_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote to {path}"

    def list_directory(self, path: str = ".") -> List[str]:
        safe_path = self._get_safe_path(path)
        if not os.path.isdir(safe_path):
            raise MCPError(-32602, f"Directory not found: {path}")
        return os.listdir(safe_path)


class MCPServer:
    """JSON-RPC 2.0 Server for MCP over stdio."""

    def __init__(self, workspace_fs: WorkspaceFS):
        self.fs = workspace_fs
        self.tools = {
            "read_file": self._tool_read_file,
            "write_file": self._tool_write_file,
            "list_directory": self._tool_list_directory,
        }

    def _tool_read_file(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        path = arguments.get("path")
        if not path:
            raise MCPError(-32602, "Missing 'path' argument.")
        content = self.fs.read_file(path)
        return {"content": [{"type": "text", "text": content}]}

    def _tool_write_file(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        path = arguments.get("path")
        content = arguments.get("content")
        if not path or content is None:
            raise MCPError(-32602, "Missing 'path' or 'content' argument.")
        result = self.fs.write_file(path, content)
        return {"content": [{"type": "text", "text": result}]}

    def _tool_list_directory(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        path = arguments.get("path", ".")
        items = self.fs.list_directory(path)
        return {"content": [{"type": "text", "text": "\n".join(items)}]}

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
                    "serverInfo": {"name": "sprawl-workspace-fs", "version": "1.0.0"}
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
                            "name": "read_file",
                            "description": "Read the content of a file within the workspace.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {"path": {"type": "string"}},
                                "required": ["path"]
                            }
                        },
                        {
                            "name": "write_file",
                            "description": "Write content to a file within the workspace.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
                                "required": ["path", "content"]
                            }
                        },
                        {
                            "name": "list_directory",
                            "description": "List contents of a directory within the workspace.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {"path": {"type": "string"}},
                                "required": []
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
        print("Usage: python workspace_fs.py <root_path>", file=sys.stderr)
        sys.exit(1)
    
    root = sys.argv[1]
    try:
        fs = WorkspaceFS(root)
        server = MCPServer(fs)
        server.run()
    except Exception as e:
        print(f"Failed to start server: {e}", file=sys.stderr)
        sys.exit(1)
