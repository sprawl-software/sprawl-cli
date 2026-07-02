"""Sync orchestration and IDE binding commands."""

import os
from typing import Optional

from ..config import config
from ..output import print_status
from ..exceptions import SprawlError
from ..sync import sync_app_directory


def cmd_sync(target_dir: Optional[str] = None) -> None:
    """File Orchestration Protocol: Syncs DNA into local workspace scope.

    Args:
        target_dir: Optional target directory. Auto-detects if not provided.
    """
    if target_dir:
        cwd = os.path.abspath(target_dir)
    elif os.path.exists(os.path.join(os.getcwd(), ".agents", "sprawl_manifest.yml")):
        cwd = os.getcwd()
    else:
        cwd = None

    from ..output import operation_spinner
    if cwd:
        if config.verbose:
            print_status(f"Running sync in TARGETED MODE at {cwd}.")
        with operation_spinner(f"Syncing workspace at {cwd}"):
            stats = sync_app_directory(cwd)
            bindings = cmd_bind(cwd)
            
        if stats:
            from rich.panel import Panel
            from ..output import console
            text = f"[success]✔ Sync Complete[/success]\n"
            text += f"• Files Synced: {stats['copied']}\n"
            text += f"• Files Pruned: {stats['pruned']}\n"
            text += f"• Venv Provisioned: {'Yes' if stats['venv_provisioned'] else 'Existing'}\n"
            text += f"• Bindings Created: {'Yes' if bindings else 'No'}"
            console.print()
            console.print(Panel(text, title="[accent]Workspace Orchestration[/accent]", border_style="#5D5CFF"))
    else:
        if config.verbose:
            print_status(f"Running sync in RECURSIVE MODE inside {config.sprawl_dir}...")

        if not os.path.isdir(config.sprawl_dir):
            raise SprawlError(
                f"Sprawl Hub directory not found at {config.sprawl_dir}. "
                "Run from inside a workspace containing '.agents/sprawl_manifest.yml' to use targeted mode."
            )

        for item in os.listdir(config.sprawl_dir):
            item_path = os.path.join(config.sprawl_dir, item)
            if os.path.isdir(item_path):
                with operation_spinner(f"Syncing workspace at {item_path}"):
                    stats = sync_app_directory(item_path)
                    bindings = cmd_bind(item_path)
                    
                if stats:
                    from rich.panel import Panel
                    from ..output import console
                    text = f"[success]✔ Sync Complete[/success]\n"
                    text += f"• Files Synced: {stats['copied']}\n"
                    text += f"• Files Pruned: {stats['pruned']}\n"
                    text += f"• Venv Provisioned: {'Yes' if stats['venv_provisioned'] else 'Existing'}\n"
                    text += f"• Bindings Created: {'Yes' if bindings else 'No'}"
                    console.print()
                    console.print(Panel(text, title="[accent]Workspace Orchestration[/accent]", border_style="#5D5CFF"))


def cmd_bind(
    target_dir: Optional[str] = None, 
    force: bool = False, 
    all_adapters: bool = False, 
    only: Optional[str] = None
) -> bool:
    """Generates selective or universal IDE/Agent bindings.

    Args:
        target_dir: Optional target directory. Defaults to cwd.
        force: If True, overwrites existing bindings.
        all_adapters: If True, bypasses TUI prompt and binds all adapters.
        only: Comma-separated list of adapters to bind.
    """
    import sys
    if not target_dir:
        target_dir = os.getcwd()

    from ..bind import bind_adapters, ADAPTER_MAP

    targets = None

    if only:
        targets = [t.strip() for t in only.split(",")]
    elif not all_adapters:
        # Check if stdin/stdout are TTYs for interactive checkboxes TUI
        if sys.stdin.isatty() and sys.stdout.isatty():
            from ..utils.tui import show_checkbox_menu
            # Present interactive checkbox menu of the 14 available integrations
            categories = {
                "IDE / AI Agent Integrations": [
                    (key, True) for key in ADAPTER_MAP.keys()
                ]
            }
            selection = show_checkbox_menu("Select IDE & Agent Adapters", categories)
            if selection is None:
                print_status("Binding cancelled.")
                return False
            targets = selection.get("IDE / AI Agent Integrations", [])
        else:
            # Non-interactive or non-TTY mode defaults to binding all (backward compatibility)
            targets = list(ADAPTER_MAP.keys())
    else:
        # --all flag passed explicitly
        targets = list(ADAPTER_MAP.keys())

    return bind_adapters(target_dir, force=force, targets=targets)
