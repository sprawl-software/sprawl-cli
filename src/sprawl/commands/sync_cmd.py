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


def cmd_bind(target_dir: Optional[str] = None, force: bool = False) -> bool:
    """Generates universal IDE/Agent bindings (Antigravity, Cursor, RooCode).

    Args:
        target_dir: Optional target directory. Defaults to cwd.
        force: If True, overwrites existing bindings.
    """
    if not target_dir:
        target_dir = os.getcwd()
    from ..bind import bind_adapters
    return bind_adapters(target_dir, force=force)
