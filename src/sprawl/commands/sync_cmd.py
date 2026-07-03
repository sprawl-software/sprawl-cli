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


def update_manifest_bindings(target_dir: str, targets: list[str]) -> None:
    manifest_path = os.path.join(target_dir, ".agents", "sprawl_manifest.yml")
    if not os.path.exists(manifest_path):
        return
        
    with open(manifest_path, "r") as f:
        content = f.read()
        
    from ..validation import parse_yaml_frontmatter
    manifest_data = parse_yaml_frontmatter(f"---\n{content}\n---")
    
    # Preserve the rest of the manifest and replace/add the `bindings` key
    dna_val = manifest_data.get("dna", "core")
    new_manifest = []
    new_manifest.append(f"dna: {dna_val}\n")
    
    from ..utils import CATEGORIES
    for category in CATEGORIES:
        items = manifest_data.get(category, [])
        new_manifest.append(f"{category}:")
        if items:
            for item in items:
                new_manifest.append(f"  - {item}")
        new_manifest.append("")
        
    local_rules = manifest_data.get("local_rules", [])
    if local_rules:
        new_manifest.append("local_rules:")
        for item in local_rules:
            new_manifest.append(f"  - {item}")
        new_manifest.append("")
        
    new_manifest.append("bindings:")
    for target in sorted(targets):
        new_manifest.append(f"  - {target}")
    new_manifest.append("")
    
    for k, v in manifest_data.items():
        if k not in CATEGORIES and k not in ("dna", "local_rules", "bindings"):
            if isinstance(v, list):
                new_manifest.append(f"{k}:")
                for item in v:
                    new_manifest.append(f"  - {item}")
            else:
                new_manifest.append(f"{k}: {v}")
            new_manifest.append("")
            
    manifest_text = "\n".join(new_manifest)
    with open(manifest_path, "w") as f:
        f.write(manifest_text)


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

    # Check if bindings are defined in the manifest
    manifest_bindings = None
    manifest_path = os.path.join(target_dir, ".agents", "sprawl_manifest.yml")
    if os.path.exists(manifest_path):
        try:
            from ..validation import parse_yaml_frontmatter
            with open(manifest_path, "r") as f:
                content = f.read()
            manifest_data = parse_yaml_frontmatter(f"---\n{content}\n---")
            if "bindings" in manifest_data:
                manifest_bindings = manifest_data["bindings"]
                if not isinstance(manifest_bindings, list):
                    manifest_bindings = [manifest_bindings] if manifest_bindings else []
                manifest_bindings = [str(b).strip().lower() for b in manifest_bindings]
        except Exception:
            pass

    targets = None

    if only:
        targets = [t.strip() for t in only.split(",")]
        update_manifest_bindings(target_dir, targets)
    elif all_adapters:
        targets = list(ADAPTER_MAP.keys())
        update_manifest_bindings(target_dir, targets)
    else:
        # If no flags are passed, check if we are in interactive TTY mode
        if sys.stdin.isatty() and sys.stdout.isatty():
            from ..utils.tui import show_checkbox_menu
            # Present interactive checkbox menu of the available integrations
            # Precheck based on manifest_bindings (if defined), otherwise default to all True
            categories = {
                "IDE / AI Agent Integrations": [
                    (key, manifest_bindings is None or key in manifest_bindings) for key in ADAPTER_MAP.keys()
                ]
            }
            selection = show_checkbox_menu("Select IDE & Agent Adapters", categories)
            if selection is None:
                print_status("Binding cancelled.")
                return False
            targets = selection.get("IDE / AI Agent Integrations", [])
            update_manifest_bindings(target_dir, targets)
        else:
            # Non-interactive / non-TTY (like sync or script running)
            # Use manifest_bindings if available, otherwise bind all
            if manifest_bindings is not None:
                targets = manifest_bindings
            else:
                targets = list(ADAPTER_MAP.keys())
                update_manifest_bindings(target_dir, targets)

    return bind_adapters(target_dir, force=force, targets=targets)
