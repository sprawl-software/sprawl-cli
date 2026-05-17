"""System diagnostics command."""

import os
import sys
import shutil
from typing import List, Tuple

from ..config import config
from ..output import console, print_status

def cmd_doctor() -> None:
    """Runs system diagnostics to verify dependencies and health."""
    from rich.table import Table
    from rich.panel import Panel
    
    console.print("\n[bold accent]Running Sprawl Diagnostics...[/bold accent]\n")
    
    checks: List[Tuple[str, str, str, str]] = []
    
    # 1. Python version
    py_version = sys.version_info
    if py_version >= (3, 10):
        checks.append(("Python 3.10+", "✔", "success", f"{py_version.major}.{py_version.minor}.{py_version.micro}"))
    else:
        checks.append(("Python 3.10+", "✗", "error", f"{py_version.major}.{py_version.minor}.{py_version.micro} (Requires >= 3.10)"))
        
    # 2. Git
    git_path = shutil.which("git")
    if git_path:
        checks.append(("Git", "✔", "success", f"Installed ({git_path})"))
    else:
        checks.append(("Git", "✗", "error", "Not Found (Required for DNA orchestration)"))
        
    # 3. Node/NPM
    npm_path = shutil.which("npm")
    if npm_path:
        checks.append(("Node/NPM", "✔", "success", f"Installed ({npm_path})"))
    else:
        checks.append(("Node/NPM", "⚠", "warning", "Not Found (Optional for TS/JS skills)"))
        
    # 4. Cargo/Rust
    cargo_path = shutil.which("cargo")
    if cargo_path:
        checks.append(("Rust/Cargo", "✔", "success", f"Installed ({cargo_path})"))
    else:
        checks.append(("Rust/Cargo", "⚠", "warning", "Not Found (Optional for Rust skills)"))
        
    # 5. Global DNA Setup
    if os.path.exists(config.agents_dir_global):
        checks.append(("Global DNA", "✔", "success", f"Initialized at {config.agents_dir_global}"))
    else:
        checks.append(("Global DNA", "✗", "error", "Not initialized (Run 'sprawl init')"))
        
    # 6. Current Workspace State
    cwd = os.getcwd()
    manifest_path = os.path.join(cwd, ".agents", "sprawl_manifest.yml")
    if os.path.exists(manifest_path):
        checks.append(("Local Workspace", "✔", "success", f"Active at {cwd}"))
    else:
        checks.append(("Local Workspace", "⚠", "warning", f"Not in a workspace (No sprawl_manifest.yml found)"))

    # Print checklist interactively
    for name, icon, style, details in checks:
        if style == "success":
            color = "green"
        elif style == "error":
            color = "red"
        else:
            color = "yellow"
            
        console.print(f"[{color}]{icon}[/{color}] {name}")

    console.print()

    # Render Output Table
    table = Table(title="[bold]Diagnostic Summary[/bold]", border_style="#5D5CFF", title_justify="left")
    table.add_column("Component", style="cyan", no_wrap=True)
    table.add_column("Status", justify="center")
    table.add_column("Details", style="dim")
    
    error_count = 0
    warning_count = 0
    
    for name, icon, style, details in checks:
        if style == "success":
            status_text = f"[green]{icon} PASS[/green]"
        elif style == "error":
            status_text = f"[bold red]{icon} FAIL[/bold red]"
            error_count += 1
        else:
            status_text = f"[yellow]{icon} WARN[/yellow]"
            warning_count += 1
            
        table.add_row(name, status_text, details)
        
    console.print(table)
    
    console.print()
    if error_count > 0:
        console.print(Panel(
            f"[red]Diagnostics failed with {error_count} error(s).[/red]\nPlease resolve the issues above before using Sprawl.",
            border_style="red"
        ))
    elif warning_count > 0:
        console.print(Panel(
            f"[yellow]Diagnostics passed with {warning_count} warning(s).[/yellow]\nSprawl will function, but some language-specific skills may fail to install.",
            border_style="yellow"
        ))
    else:
        console.print(Panel(
            "[green]All systems operational. Sprawl is ready for orchestration.[/green]",
            border_style="green"
        ))
