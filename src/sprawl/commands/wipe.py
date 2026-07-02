"""Nuclear wipe command to remove Sprawl traces."""

import os
import shutil
from typing import Optional

from rich.prompt import Confirm

from ..config import config
from ..output import console, print_status, print_warning
from ..exceptions import SprawlError


def cmd_wipe(target_dir: Optional[str] = None, force: bool = False, local_only: bool = False) -> None:
    """Deletes Sprawl artifacts.
    
    If local_only is True, only wipes the local workspace (.agents/).
    Otherwise, wipes both the local workspace (if active) and the entire global Sprawl registry (~/.sprawl).
    
    Args:
        target_dir: The directory to check for a local workspace. Defaults to cwd.
        force: Skip confirmation prompts.
        local_only: Only wipe the local workspace, leave global DNA intact.
    """
    cwd = target_dir or os.getcwd()
    local_agents_dir = os.path.join(cwd, ".agents")
    
    has_local = os.path.exists(local_agents_dir)
    has_global = os.path.exists(os.path.dirname(config.config_path))
    
    if not has_local and (not has_global or local_only):
        print_warning("No Sprawl traces found to wipe.")
        return

    # Warning UI
    console.print("\n[bold red]!!! NUCLEAR WIPE INITIATED !!![/bold red]")
    
    if has_local:
        console.print(f"[warning]Will destroy local workspace: {local_agents_dir}[/warning]")
    
    if not local_only and has_global:
        global_dir = os.path.dirname(config.config_path)
        console.print(f"[warning]Will destroy global DNA registry & configuration: {global_dir}[/warning]")
        console.print("[dim]Note: To completely uninstall the CLI tool itself, run: pipx uninstall sprawl-cli[/dim]")

    if not force:
        console.print()
        if not Confirm.ask("[bold red]Are you absolutely sure you want to destroy these Sprawl traces?[/bold red]"):
            print_status("Wipe aborted.")
            return

    # Wiping local
    if has_local:
        # First, try to deregister it from the workspace registry if the global registry exists
        if has_global and not local_only:
            try:
                from ..workspace import WorkspaceRegistry, WorkspaceError
                workspace_name = os.path.basename(cwd)
                try:
                    WorkspaceRegistry.deregister(workspace_name)
                    print_status(f"Deregistered workspace '{workspace_name}' from global tracking.")
                except WorkspaceError:
                    pass # Was not registered, ignore
            except Exception:
                pass # Ignore registry errors during a nuclear wipe
                
        try:
            shutil.rmtree(local_agents_dir)
            print_status(f"Destroyed local workspace: {local_agents_dir}")
        except Exception as e:
            raise SprawlError(f"Failed to wipe local workspace: {e}")

    # Scan known workspaces in the registry and clean up editor rules files/symlinks
    if not local_only and has_global:
        try:
            from ..workspace import WorkspaceRegistry
            from ..bind import ADAPTER_MAP
            workspaces = WorkspaceRegistry.get_all()
            for ws_name, ws_info in workspaces.items():
                ws_path = ws_info.get("path")
                if ws_path and os.path.exists(ws_path):
                    # Remove .agent symlink/file
                    ag_symlink = os.path.join(ws_path, ".agent")
                    if os.path.islink(ag_symlink) or os.path.exists(ag_symlink):
                        try:
                            os.remove(ag_symlink)
                        except Exception:
                            pass
                    
                    # Remove all standard rules files
                    for adapter in ADAPTER_MAP.values():
                        if "path" in adapter:
                            rule_path = os.path.join(ws_path, adapter["path"])
                            if os.path.exists(rule_path):
                                try:
                                    os.remove(rule_path)
                                except Exception:
                                    pass
                    print_status(f"Cleaned up editor bindings in workspace: {ws_path}")
        except Exception:
            pass

    # Delete global configuration overrides (~/.sprawl_rc) if present
    if not local_only:
        sprawl_rc = os.path.expanduser("~/.sprawl_rc")
        if os.path.exists(sprawl_rc):
            try:
                os.remove(sprawl_rc)
                print_status(f"Destroyed global configuration override: {sprawl_rc}")
            except Exception as e:
                raise SprawlError(f"Failed to delete {sprawl_rc}: {e}")

    # Wiping global
    if not local_only and has_global:
        global_dir = os.path.dirname(config.config_path)
        try:
            shutil.rmtree(global_dir)
            print_status(f"Destroyed global DNA registry and configuration: {global_dir}")
        except Exception as e:
            raise SprawlError(f"Failed to wipe global registry: {e}")
            
    console.print("\n[bold green]✔ Sprawl traces have been wiped.[/bold green]")
