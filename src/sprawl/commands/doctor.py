"""System diagnostics command."""

import os
import shutil
import sys

from rich.panel import Panel
from rich.table import Table

from ..config import config
from ..output import console

_STYLE_COLOR_MAP = {
    "success": "green",
    "error": "red",
    "warning": "yellow",
}

_STYLE_BADGE_MAP = {
    "success": "[green]✔ PASS[/green]",
    "error": "[bold red]✗ FAIL[/bold red]",
    "warning": "[yellow]⚠ WARN[/yellow]",
}


def _check_binary(
    label: str,
    binary: str,
    missing_icon: str,
    missing_style: str,
    missing_msg: str,
) -> tuple[str, str, str, str]:
    """Checks whether a CLI binary exists on PATH and returns a diagnostic tuple."""
    resolved = shutil.which(binary)
    if resolved:
        return (label, "✔", "success", f"Installed ({resolved})")
    return (label, missing_icon, missing_style, missing_msg)


def _collect_doctor_checks() -> list[tuple[str, str, str, str]]:
    """Evaluates Python, Git, Node, Rust, Global DNA, and Local Workspace health."""
    py = sys.version_info
    py_ver = f"{py.major}.{py.minor}.{py.micro}"
    py_check = (
        ("Python 3.10+", "✔", "success", py_ver)
        if py >= (3, 10)
        else ("Python 3.10+", "✗", "error", f"{py_ver} (Requires >= 3.10)")
    )

    dna_check = (
        ("Global DNA", "✔", "success", f"Initialized at {config.agents_dir_global}")
        if os.path.exists(config.agents_dir_global)
        else ("Global DNA", "✗", "error", "Not initialized (Run 'sprawl init')")
    )

    cwd = os.getcwd()
    manifest_path = os.path.join(cwd, ".agents", "sprawl_manifest.yml")
    ws_check = (
        ("Local Workspace", "✔", "success", f"Active at {cwd}")
        if os.path.exists(manifest_path)
        else (
            "Local Workspace",
            "⚠",
            "warning",
            "Not in a workspace (No sprawl_manifest.yml found)",
        )
    )

    return [
        py_check,
        _check_binary("Git", "git", "✗", "error", "Not Found (Required for DNA orchestration)"),
        _check_binary("Node/NPM", "npm", "⚠", "warning", "Not Found (Optional for TS/JS skills)"),
        _check_binary(
            "Rust/Cargo", "cargo", "⚠", "warning", "Not Found (Optional for Rust skills)"
        ),
        dna_check,
        ws_check,
    ]


def _render_final_verdict_panel(error_count: int, warning_count: int) -> None:
    """Prints the final red/yellow/green diagnostic verdict panel."""
    if error_count > 0:
        console.print(
            Panel(
                f"[red]Diagnostics failed with {error_count} error(s).[/red]\nPlease resolve the issues above before using Sprawl.",
                border_style="red",
            )
        )
    elif warning_count > 0:
        console.print(
            Panel(
                f"[yellow]Diagnostics passed with {warning_count} warning(s).[/yellow]\nSprawl will function, but some language-specific skills may fail to install.",
                border_style="yellow",
            )
        )
    else:
        console.print(
            Panel(
                "[green]All systems operational. Sprawl is ready for orchestration.[/green]",
                border_style="green",
            )
        )


def cmd_doctor() -> None:
    """Runs system diagnostics to verify dependencies and health."""
    console.print("\n[bold accent]Running Sprawl Diagnostics...[/bold accent]\n")
    checks = _collect_doctor_checks()

    for name, icon, style, _details in checks:
        color = _STYLE_COLOR_MAP.get(style, "yellow")
        console.print(f"[{color}]{icon}[/{color}] {name}")

    console.print()
    table = Table(
        title="[bold]Diagnostic Summary[/bold]", border_style="#5D5CFF", title_justify="left"
    )
    table.add_column("Component", style="cyan", no_wrap=True)
    table.add_column("Status", justify="center")
    table.add_column("Details", style="dim")

    error_count = sum(1 for _, _, style, _ in checks if style == "error")
    warning_count = sum(1 for _, _, style, _ in checks if style == "warning")

    for name, _icon, style, details in checks:
        table.add_row(name, _STYLE_BADGE_MAP.get(style, "[yellow]WARN[/yellow]"), details)

    console.print(table)
    console.print()
    _render_final_verdict_panel(error_count, warning_count)
