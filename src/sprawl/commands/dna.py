"""DNA registry specific commands."""

import os
import subprocess

from rich.tree import Tree

from ..config import config
from ..output import print_status, print_warning, print_error, console
from ..exceptions import SprawlError
from ..registry import get_dna_registry, update_dna_registry
from ..utils import CATEGORIES

def cmd_dna_update() -> None:
    """Updates the globally registered DNA source."""
    registry = get_dna_registry()
    if not registry:
        raise SprawlError("No Global DNA is registered. Run 'sprawl init <URL>' first.")

    dna_path = config.agents_dir_global
    if not os.path.exists(dna_path) or not os.path.exists(os.path.join(dna_path, ".git")):
        raise SprawlError(f"Global DNA not found or not a git repository at {dna_path}. Run 'sprawl init' first.")

    from ..output import operation_spinner
    if not config.dry_run:
        with operation_spinner(f"Updating Global DNA at {dna_path}..."):
            try:
                current_branch = subprocess.check_output(
                    ["git", "-C", dna_path, "rev-parse", "--abbrev-ref", "HEAD"], text=True
                ).strip()
                subprocess.run(["git", "-C", dna_path, "pull", "origin", current_branch], check=True)
                print_status("Global DNA updated successfully.")
                # Update registry to bump the last_pulled timestamp
                update_dna_registry(registry.get("url", ""))
            except subprocess.CalledProcessError as e:
                print_warning(f"Failed to pull Global DNA: {e}")
                print_error("=== AUTHENTICATION FAILED ===")
                raise SprawlError("Failed to pull the Global DNA repository.")
    else:
        print_status(f"Updating Global DNA at {dna_path}...")

def cmd_dna_inspect() -> None:
    """Shows contents of the DNA (rules, skills, atoms, molecules, workflows) as a Rich Tree."""
    registry = get_dna_registry()
    if not registry:
        raise SprawlError("No Global DNA is registered. Run 'sprawl init <URL>' first.")

    dna_path = config.agents_dir_global
    if not os.path.exists(dna_path):
        raise SprawlError(f"Global DNA not found at {dna_path}.")

    tree = Tree(f"🧬 Global DNA Registry [dim]({dna_path})[/dim]", guide_style="accent")
    
    for category in CATEGORIES:
        cat_dir = os.path.join(dna_path, category)
        if os.path.exists(cat_dir):
            items = sorted(os.listdir(cat_dir))
            # Filter out hidden files
            items = [item for item in items if not item.startswith(".")]
            if items:
                branch = tree.add(f"[info]{category.capitalize()}[/info]")
                for item in items:
                    branch.add(item)
                    
    console.print(tree)

def cmd_dna_list() -> None:
    """Lists all registered DNA sources."""
    if config.json_logging:
        import json
        out = []
        global_dna = config.agents_dir_global
        if os.path.exists(global_dna):
            out.append({"alias": "@global", "type": "Primary", "path": global_dna, "status": "installed"})
        else:
            out.append({"alias": "@global", "type": "Primary", "path": "Not Installed", "status": "missing"})
            
        registry_dir = config.dna_registry_dir
        if os.path.exists(registry_dir):
            for alias in sorted(os.listdir(registry_dir)):
                path = os.path.join(registry_dir, alias)
                if os.path.isdir(path):
                    out.append({"alias": f"@{alias}", "type": "Secondary", "path": path, "status": "installed"})
        print(json.dumps(out))
        return

    from rich.table import Table
    table = Table(title="[info]Registered DNA Sources[/info]", border_style="#5D5CFF")
    table.add_column("Status", justify="center")
    table.add_column("Alias", style="accent")
    table.add_column("Type", style="info")
    table.add_column("Path", style="info")
    
    global_dna = config.agents_dir_global
    if os.path.exists(global_dna):
        table.add_row("[success]●[/success]", "@global", "Primary", global_dna)
    else:
        table.add_row("[error]○[/error]", "@global", "Primary", "Not Installed")
        
    registry_dir = config.dna_registry_dir
    if os.path.exists(registry_dir):
        for alias in sorted(os.listdir(registry_dir)):
            path = os.path.join(registry_dir, alias)
            if os.path.isdir(path):
                table.add_row("[success]●[/success]", f"@{alias}", "Secondary", path)
                
    console.print(table)
