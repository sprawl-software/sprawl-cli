"""Nuclear wipe command to remove Sprawl traces."""

import contextlib
import os

from rich.prompt import Confirm

from ..config import config
from ..exceptions import SprawlError
from ..output import console, print_status, print_warning
from ..utils import rmtree_safe
from ..workspace import WorkspaceError, deregister_workspace, get_all_workspaces


def _confirm_wipe_plan(
    local_agents_dir: str,
    has_local: bool,
    has_global: bool,
    local_only: bool,
    force: bool,
) -> bool:
    """Renders the nuclear wipe warning summary and prompts for user confirmation."""
    console.print("\n[bold red]!!! NUCLEAR WIPE INITIATED !!![/bold red]")

    if has_local:
        console.print(f"[warning]Will destroy local workspace: {local_agents_dir}[/warning]")

    if not local_only and has_global:
        global_dir = os.path.dirname(config.config_path)
        console.print(
            f"[warning]Will destroy global DNA registry & configuration: {global_dir}[/warning]"
        )
        console.print(
            "[dim]Note: To completely uninstall the CLI tool itself, run: pipx uninstall sprawl-cli[/dim]"
        )

    if force:
        return True

    console.print()
    if not Confirm.ask(
        "[bold red]Are you absolutely sure you want to destroy these Sprawl traces?[/bold red]"
    ):
        print_status("Wipe aborted.")
        return False
    return True


def _wipe_local_workspace(
    cwd: str,
    local_agents_dir: str,
    deregister_global: bool,
) -> None:
    """Deregisters and deletes the local .agents workspace directory."""
    if deregister_global:
        workspace_name = os.path.basename(cwd)
        with contextlib.suppress(WorkspaceError, OSError):
            deregister_workspace(workspace_name)
            print_status(f"Deregistered workspace '{workspace_name}' from global tracking.")

    try:
        rmtree_safe(local_agents_dir)
        print_status(f"Destroyed local workspace: {local_agents_dir}")
    except OSError as e:
        raise SprawlError(f"Failed to wipe local workspace: {e}") from e


def _cleanup_workspace_editor_bindings(ws_path: str) -> None:
    """Removes .agent symlink and IDE rule files inside a tracked workspace."""
    from ..bind import ADAPTER_MAP

    ag_symlink = os.path.join(ws_path, ".agent")
    if os.path.islink(ag_symlink) or os.path.exists(ag_symlink):
        with contextlib.suppress(OSError):
            os.remove(ag_symlink)

    for adapter in ADAPTER_MAP.values():
        rel_rule = adapter.get("path")
        if not rel_rule:
            continue
        rule_path = os.path.join(ws_path, rel_rule)
        if os.path.exists(rule_path):
            with contextlib.suppress(OSError):
                os.remove(rule_path)
    print_status(f"Cleaned up editor bindings in workspace: {ws_path}")


def _cleanup_registered_workspaces() -> None:
    """Iterates known workspaces in the registry and cleans up their editor bindings."""
    with contextlib.suppress(WorkspaceError, OSError):
        workspaces = get_all_workspaces()
        for ws_info in workspaces.values():
            ws_path = ws_info.get("path")
            if ws_path and os.path.exists(ws_path):
                _cleanup_workspace_editor_bindings(ws_path)


def _remove_sprawl_rc_override() -> None:
    """Removes ~/.sprawl_rc or ~/.sprawl_rc_test if present."""
    sprawl_rc = os.path.expanduser("~/.sprawl_rc_test" if config.test_mode else "~/.sprawl_rc")
    if not os.path.exists(sprawl_rc):
        return
    try:
        os.remove(sprawl_rc)
        print_status(f"Destroyed global configuration override: {sprawl_rc}")
    except OSError as e:
        raise SprawlError(f"Failed to delete {sprawl_rc}: {e}") from e


def _wipe_global_registry_directory() -> None:
    """Removes Antigravity MCP schemas and deletes the global ~/.sprawl directory."""
    from ..bind import _remove_antigravity_schemas

    with contextlib.suppress(OSError):
        _remove_antigravity_schemas()

    global_dir = os.path.dirname(config.config_path)
    try:
        rmtree_safe(global_dir)
        print_status(f"Destroyed global DNA registry and configuration: {global_dir}")
    except OSError as e:
        raise SprawlError(f"Failed to wipe global registry: {e}") from e


def cmd_wipe(target_dir: str | None = None, force: bool = False, local_only: bool = False) -> None:
    """Deletes Sprawl artifacts."""
    cwd = target_dir or os.getcwd()
    local_agents_dir = os.path.join(cwd, ".agents")

    has_local = os.path.exists(local_agents_dir)
    has_global = os.path.exists(os.path.dirname(config.config_path))

    if not has_local and (not has_global or local_only):
        print_warning("No Sprawl traces found to wipe.")
        return

    if not _confirm_wipe_plan(local_agents_dir, has_local, has_global, local_only, force):
        return

    if has_local:
        _wipe_local_workspace(
            cwd, local_agents_dir, deregister_global=has_global and not local_only
        )

    if not local_only and has_global:
        _cleanup_registered_workspaces()

    if not local_only:
        _remove_sprawl_rc_override()

    if not local_only and has_global:
        _wipe_global_registry_directory()

    console.print("\n[bold green]✔ Sprawl traces have been wiped.[/bold green]")
