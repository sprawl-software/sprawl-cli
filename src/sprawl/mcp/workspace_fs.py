"""sprawl-workspace-fs — Python-native MCP filesystem server.

Limited to the workspace root. Pure stdlib + rich.
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


def _assert_contained_within(real_path: str, real_root: str, error_message: str) -> None:
    """Enforces strict realpath + normcase containment to block sibling-prefix escapes."""
    norm_real_path = os.path.normcase(real_path)
    norm_real_root = os.path.normcase(real_root)
    if norm_real_path != norm_real_root and not norm_real_path.startswith(norm_real_root + os.sep):
        raise MCPError(-32602, error_message)


class WorkspaceFS:
    """Core logic for sandboxed filesystem operations."""

    def __init__(self, root_path: str, cli_mounts: dict[str, str] | None = None) -> None:
        self.root = os.path.abspath(os.path.expanduser(root_path))
        if not os.path.isdir(self.root):
            raise ValueError(f"Root path {self.root} is not a directory.")

        self._cli_mounts: dict[str, str] = dict(cli_mounts) if cli_mounts else {}
        self.allowed_mounts: dict[str, str] = {}
        self._refresh_mounts()

    @staticmethod
    def _load_workspace_mounts(workspace_dir: str) -> dict[str, str]:
        """Reads allowed_mounts from .agents/sprawl-config.json."""
        mounts: dict[str, str] = {}
        config_path = os.path.join(workspace_dir, ".agents", "sprawl-config.json")
        if not os.path.isfile(config_path):
            return mounts
        try:
            with open(config_path, encoding="utf-8") as f:
                cfg = json.load(f)
        except (json.JSONDecodeError, OSError):
            return mounts

        raw_mounts = cfg.get("allowed_mounts", {})
        if isinstance(raw_mounts, dict):
            for k, v in raw_mounts.items():
                if isinstance(v, str) and v.strip():
                    mounts[str(k)] = os.path.abspath(os.path.expanduser(v.strip()))
        return mounts

    def _refresh_mounts(self) -> None:
        """Reloads allowed_mounts from workspace config and overlays CLI mounts."""
        mounts = self._load_workspace_mounts(self.root)
        if self._cli_mounts:
            mounts.update(self._cli_mounts)
        self.allowed_mounts = mounts

    def _resolve_mounted_path(self, rel_path: str, normalized_rel: str) -> str:
        """Resolves an '@<alias>/<subpath>' mount reference against allowed_mounts."""
        parts = normalized_rel.split("/", 1)
        alias = parts[0][1:]
        if alias not in self.allowed_mounts:
            raise MCPError(
                -32602, f"Security Violation: Mount alias '{alias}' is not allowed/configured."
            )

        mount_root = os.path.abspath(os.path.expanduser(self.allowed_mounts[alias]))
        sub_path = parts[1] if len(parts) > 1 else ""
        if os.path.isabs(sub_path) or sub_path.startswith("~"):
            raise MCPError(
                -32602,
                "Security Violation: Absolute paths and home expansion are not allowed inside mounts.",
            )

        real_path = os.path.realpath(os.path.abspath(os.path.join(mount_root, sub_path)))
        real_mount_root = os.path.realpath(mount_root)
        _assert_contained_within(
            real_path,
            real_mount_root,
            f"Security Violation: Path '{rel_path}' resolves outside mount root '{alias}'.",
        )
        return real_path

    def _get_safe_path(self, rel_path: str) -> str:
        """Resolves relative path and ensures it stays within root or allowed mounts."""
        self._refresh_mounts()
        normalized_rel = rel_path.replace("\\", "/") if rel_path.startswith("@") else rel_path
        if normalized_rel.startswith("@"):
            return self._resolve_mounted_path(rel_path, normalized_rel)

        if os.path.isabs(rel_path) or rel_path.startswith("~"):
            raise MCPError(
                -32602, "Security Violation: Absolute paths and home expansion are not allowed."
            )

        real_path = os.path.realpath(os.path.abspath(os.path.join(self.root, rel_path)))
        real_root = os.path.realpath(self.root)
        _assert_contained_within(
            real_path,
            real_root,
            f"Security Violation: Path '{rel_path}' resolves outside workspace root.",
        )
        return real_path

    def read_file(self, path: str) -> str:
        return read_safe_utf8_file(self._get_safe_path(path), path, kind_label="File")

    def write_file(self, path: str, content: str) -> str:
        return write_safe_utf8_file(self._get_safe_path(path), path, content)

    def list_directory(self, path: str = ".") -> list[str]:
        safe_path = self._get_safe_path(path)
        if not os.path.isdir(safe_path):
            raise MCPError(-32602, f"Directory not found: {path}")
        return os.listdir(safe_path)


class MCPServer:
    """JSON-RPC 2.0 Server for MCP over stdio."""

    def __init__(self, workspace_fs: WorkspaceFS) -> None:
        self.fs = workspace_fs
        self.tools = {
            "read_file": self._tool_read_file,
            "write_file": self._tool_write_file,
            "list_directory": self._tool_list_directory,
        }

    def _tool_read_file(self, arguments: dict[str, Any]) -> dict[str, Any]:
        return format_mcp_text_result(self.fs.read_file(require_path_argument(arguments)))

    def _tool_write_file(self, arguments: dict[str, Any]) -> dict[str, Any]:
        path, content = require_path_and_content_arguments(arguments)
        return format_mcp_text_result(self.fs.write_file(path, content))

    def _tool_list_directory(self, arguments: dict[str, Any]) -> dict[str, Any]:
        path = arguments.get("path", ".")
        return format_mcp_text_result("\n".join(self.fs.list_directory(path)))

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
                    "serverInfo": {"name": "sprawl-workspace-fs", "version": "1.0.0"},
                    "instructions": (
                        "You have secure access to the local workspace and allowed mount points via this MCP server. "
                        "To list a mount root, call list_directory with path='@<alias>'. "
                        "To read, write, or list inside a mount, prefix path with '@<alias>/<subpath>'."
                    ),
                },
            }

        handled, common_resp = handle_common_mcp_method(msg_id, method)
        if handled:
            return common_resp

        if method == "tools/list":
            return {"jsonrpc": "2.0", "id": msg_id, "result": {"tools": self._build_tools_list()}}

        if method == "tools/call":
            return self._handle_tool_call(msg_id, params)

        if msg_id is not None:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"},
            }
        return None

    def _build_tools_list(self) -> list[dict[str, Any]]:
        """Builds the tools/list response dynamically incorporating active mount aliases."""
        self.fs._refresh_mounts()
        mounts_desc = ""
        if self.fs.allowed_mounts:
            aliases_str = ", ".join(f"@{a}" for a in sorted(self.fs.allowed_mounts.keys()))
            mounts_desc = (
                " You can also access allowed mount directories outside the workspace "
                f"using the '@<alias>/<subpath>' prefix. Configured mounts: {aliases_str}."
            )
        return [
            {
                "name": "read_file",
                "description": f"Read the content of a file within the workspace.{mounts_desc}",
                "inputSchema": {
                    "type": "object",
                    "properties": {"path": {"type": "string"}},
                    "required": ["path"],
                },
            },
            {
                "name": "write_file",
                "description": f"Write content to a file within the workspace.{mounts_desc}",
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
                "name": "list_directory",
                "description": f"List contents of a directory within the workspace.{mounts_desc}",
                "inputSchema": {
                    "type": "object",
                    "properties": {"path": {"type": "string"}},
                    "required": [],
                },
            },
        ]

    def _handle_tool_call(self, msg_id: Any, params: dict[str, Any]) -> dict[str, Any]:
        return dispatch_mcp_tool_call(msg_id, params, self.tools)

    def send_error(self, msg_id: Any, code: int, message: str) -> None:
        write_jsonrpc_error(msg_id, code, message)


def discover_cwd_workspace(start_dir: str | None = None) -> str | None:
    """Walks up from start_dir (or os.getcwd()) to find an active Sprawl workspace root."""
    try:
        curr = os.path.abspath(start_dir or os.getcwd())
    except OSError:
        return None

    while True:
        agents_dir = os.path.join(curr, ".agents")
        if os.path.isdir(agents_dir) and (
            os.path.isfile(os.path.join(agents_dir, "sprawl-config.json"))
            or os.path.isfile(os.path.join(agents_dir, "sprawl_manifest.yml"))
        ):
            return curr
        parent = os.path.dirname(curr)
        if parent == curr:
            break
        curr = parent
    return None


def _parse_cli_mounts(mount_args: list[str] | None) -> dict[str, str]:
    """Parses --mount ALIAS=PATH CLI arguments into an absolute path dictionary."""
    cli_mounts: dict[str, str] = {}
    if not mount_args:
        return cli_mounts
    for item in mount_args:
        if "=" in item:
            alias, path = item.split("=", 1)
            cli_mounts[alias.strip()] = os.path.abspath(os.path.expanduser(path.strip()))
    return cli_mounts


def run_workspace_fs_cli(argv: list[str] | None = None) -> None:
    """CLI entrypoint for launching the sprawl-workspace-fs MCP stdio server."""
    import argparse

    parser = argparse.ArgumentParser(description="sprawl-workspace-fs MCP Server")
    parser.add_argument("root", help="Path to workspace root directory")
    parser.add_argument(
        "--mount",
        action="append",
        dest="mounts",
        metavar="ALIAS=PATH",
        help="Allowed mount in format alias=path",
    )
    args = parser.parse_args(argv)
    cli_mounts = _parse_cli_mounts(args.mounts)

    configured_root = os.path.abspath(os.path.expanduser(args.root))
    cwd_workspace = discover_cwd_workspace()
    if cwd_workspace and os.path.normcase(cwd_workspace) != os.path.normcase(configured_root):
        active_root = cwd_workspace
        active_cli_mounts = None
    else:
        active_root = configured_root
        active_cli_mounts = cli_mounts

    try:
        fs = WorkspaceFS(active_root, cli_mounts=active_cli_mounts)
        server = MCPServer(fs)
        server.run()
    except (OSError, ValueError) as e:
        print(f"Failed to start server: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    run_workspace_fs_cli()
