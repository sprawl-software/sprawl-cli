"""Diff visualization command."""

import os
import difflib
from typing import Optional

from ..output import console, print_status, print_warning
from ..exceptions import SprawlError
from ..utils import get_active_dna_context, CATEGORIES
from ..sync import parse_sprawl_manifest

def diff_files(src_path: str, dest_path: str, rel_path: str) -> bool:
    """Computes unified diff between two files and prints it if drift exists.
    
    Returns:
        bool: True if differences were found, False otherwise.
    """
    from rich.syntax import Syntax

    src_content = []
    dest_content = []
    
    if os.path.exists(src_path):
        with open(src_path, "r", encoding="utf-8", errors="ignore") as f:
            src_content = f.readlines()
            
    if os.path.exists(dest_path):
        with open(dest_path, "r", encoding="utf-8", errors="ignore") as f:
            dest_content = f.readlines()
            
    if src_content == dest_content:
        return False
        
    diff = list(difflib.unified_diff(
        src_content, dest_content,
        fromfile=f"DNA: {rel_path}",
        tofile=f"Local: {rel_path}",
        lineterm=""
    ))
    
    if diff:
        diff_text = "".join(diff)
        syntax = Syntax(diff_text, "diff", theme="monokai", background_color="default")
        console.print(syntax)
        console.print()
        return True
        
    return False

def diff_recursive(src_base: str, dest_base: str, rel_base: str) -> bool:
    """Recursively diffs two directories.
    
    Returns:
        bool: True if differences were found.
    """
    drift_found = False
    
    src_exists = os.path.exists(src_base)
    dest_exists = os.path.exists(dest_base)
    
    if not src_exists and not dest_exists:
        return False
        
    if src_exists and not os.path.isdir(src_base):
        return diff_files(src_base, dest_base, rel_base)
        
    if dest_exists and not os.path.isdir(dest_base):
        return diff_files(src_base, dest_base, rel_base)
        
    all_files = set()
    if src_exists:
        all_files.update(os.listdir(src_base))
    if dest_exists:
        all_files.update(os.listdir(dest_base))
        
    for item in sorted(all_files):
        # Ignore virtual environments, git, etc.
        if item in (".venv", "__pycache__", ".git", "node_modules"):
            continue
            
        src_item = os.path.join(src_base, item)
        dest_item = os.path.join(dest_base, item)
        rel_item = os.path.join(rel_base, item)
        
        is_dir = False
        if os.path.exists(src_item) and os.path.isdir(src_item):
            is_dir = True
        elif os.path.exists(dest_item) and os.path.isdir(dest_item):
            is_dir = True
            
        if is_dir:
            if diff_recursive(src_item, dest_item, rel_item):
                drift_found = True
        else:
            if diff_files(src_item, dest_item, rel_item):
                drift_found = True
                
    return drift_found

def cmd_diff(target_dir: Optional[str] = None) -> None:
    """Shows local vs source DNA drift.

    Args:
        target_dir: Optional target directory. Defaults to current working directory.
    """
    cwd = target_dir or os.getcwd()
    
    local_agents_dir = os.path.join(cwd, ".agents")
    manifest_path = os.path.join(local_agents_dir, "sprawl_manifest.yml")
    if not os.path.exists(manifest_path):
        raise SprawlError(f"No sprawl_manifest.yml found in {local_agents_dir}.")

    source_dna_dir = get_active_dna_context(cwd)
    reqs = parse_sprawl_manifest(manifest_path)
    
    from rich.panel import Panel
    
    console.print(f"\n[bold accent]Comparing local DNA drift against @{os.path.basename(source_dna_dir)}...[/bold accent]\n")
    
    drift_found = False

    # Check DESIGN.md override
    src_design = os.path.join(source_dna_dir, "DESIGN.md")
    dest_design = os.path.join(local_agents_dir, "DESIGN.md")
    if diff_files(src_design, dest_design, "DESIGN.md"):
        drift_found = True

    for category, files in reqs.items():
        if category == "local_rules":
            continue
        if not files:
            continue
            
        category_dir = os.path.join(local_agents_dir, category)
        
        for file_name in files:
            src_path = os.path.join(source_dna_dir, category, file_name)
            dest_path = os.path.join(category_dir, file_name)
            rel_path = f"{category}/{file_name}"
            
            if diff_recursive(src_path, dest_path, rel_path):
                drift_found = True

    if not drift_found:
        console.print(Panel(
            "[green]✔ No DNA drift detected.[/green] Your local workspace perfectly matches the upstream registry.",
            title="[bold green]Sync Status[/bold green]",
            border_style="green"
        ))
    else:
        console.print(Panel(
            "[yellow]⚠ DNA drift detected.[/yellow] Run [accent]sprawl sync[/accent] to overwrite local changes, or update your Global DNA.",
            title="[bold yellow]Sync Status[/bold yellow]",
            border_style="yellow"
        ))
