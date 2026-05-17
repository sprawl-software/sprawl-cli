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

    # Wiping global
    if not local_only and has_global:
        global_dir = os.path.dirname(config.config_path)
        try:
            shutil.rmtree(global_dir)
            print_status(f"Destroyed global DNA registry and configuration: {global_dir}")
        except Exception as e:
            raise SprawlError(f"Failed to wipe global registry: {e}")
            
    console.print("\n[bold green]✔ Sprawl traces have been wiped.[/bold green]")
