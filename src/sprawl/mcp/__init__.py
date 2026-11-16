"""Shared JSON-RPC 2.0 and sandboxed file I/O primitives for Sprawl MCP servers."""

import json
import os
import sys
from collections.abc import Callable
from typing import Any


class MCPError(Exception):
    """Structured JSON-RPC 2.0 protocol or tool execution error."""

    def __init__(self, code: int, message: str, data: Any = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.data = data


def read_safe_utf8_file(
    safe_path: str,
    display_path: str,
    kind_label: str = "File",
) -> str:
    """Reads a validated UTF-8 file from disk or raises MCPError(-32602)."""
    if not os.path.isfile(safe_path):
        raise MCPError(-32602, f"{kind_label} not found: {display_path}")
    with open(safe_path, encoding="utf-8", errors="ignore") as f:
        return f.read()


def write_safe_utf8_file(
    safe_path: str,
    display_path: str,
    content: str,
) -> str:
    """Creates parent directories and writes UTF-8 content to safe_path."""
    os.makedirs(os.path.dirname(safe_path), exist_ok=True)
    with open(safe_path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"Successfully wrote to {display_path}"


def format_mcp_text_result(text: str) -> dict[str, Any]:
    """Formats a plain string response into the MCP text content envelope."""
    return {"content": [{"type": "text", "text": text}]}


def require_path_argument(arguments: dict[str, Any]) -> str:
    """Extracts and validates the required 'path' string argument."""
    path = arguments.get("path")
    if not path or not isinstance(path, str):
        raise MCPError(-32602, "Missing 'path' argument.")
    return path


def require_path_and_content_arguments(arguments: dict[str, Any]) -> tuple[str, str]:
    """Extracts and validates the required 'path' and 'content' arguments."""
    path = arguments.get("path")
    content = arguments.get("content")
    if not path or not isinstance(path, str) or content is None:
        raise MCPError(-32602, "Missing 'path' or 'content' argument.")
    return path, str(content)


_COMMON_METHOD_RESULTS: dict[str, dict[str, Any]] = {
    "ping": {},
    "resources/list": {"resources": []},
    "resources/templates/list": {"resourceTemplates": []},
    "prompts/list": {"prompts": []},
}


def dispatch_mcp_tool_call(
    msg_id: Any,
    params: dict[str, Any],
    tools: dict[str, Callable[[dict[str, Any]], dict[str, Any]]],
) -> dict[str, Any]:
    """Executes a registered MCP tool handler and wraps output or errors in JSON-RPC 2.0."""
    tool_name = params.get("name")
    handler = tools.get(str(tool_name))
    if handler is None:
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {"code": -32601, "message": f"Tool not found: {tool_name}"},
        }
    arguments = params.get("arguments")
    try:
        result = handler(arguments if isinstance(arguments, dict) else {})
        return {"jsonrpc": "2.0", "id": msg_id, "result": result}
    except MCPError as e:
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {"code": e.code, "message": e.message, "data": e.data},
        }
    except (OSError, ValueError, TypeError, KeyError) as e:
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {"code": -32603, "message": str(e)},
        }


def write_jsonrpc_error(msg_id: Any, code: int, message: str) -> None:
    """Writes a JSON-RPC 2.0 error frame to stdout and flushes."""
    response = {"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": message}}
    sys.stdout.write(json.dumps(response) + "\n")
    sys.stdout.flush()


def handle_common_mcp_method(
    msg_id: Any,
    method: str | None,
) -> tuple[bool, dict[str, Any] | None]:
    """Handles standard MCP discovery/no-op methods shared across all stdio servers."""
    if not method:
        return False, None
    if method.startswith("notifications/"):
        return True, None
    if method in _COMMON_METHOD_RESULTS:
        return True, {"jsonrpc": "2.0", "id": msg_id, "result": _COMMON_METHOD_RESULTS[method]}
    return False, None
