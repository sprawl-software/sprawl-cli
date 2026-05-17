"""Workspace status command — rich dashboard view of workspace state."""

import os
from datetime import datetime, timezone
from typing import Optional

from rich.panel import Panel
from rich.table import Table

from ..config import config
from ..output import console, print_warning
from ..exceptions import SprawlError
from ..utils import CATEGORIES
from ..sync import parse_sprawl_manifest
from ..workspace import Workspace


def cmd_status(target_dir: Optional[str] = None) -> None:
    """Displays a Rich Panel with workspace name, DNA binding, loaded artifacts, venv health.

    Reads from ~/.sprawl/workspaces/<hash>/ + scans local .agents/ for actual state.

    Args:
        target_dir: Optional workspace path. Defaults to current working directory.
    """
    cwd = os.path.abspath(target_dir or os.getcwd())

    local_agents_dir = os.path.join(cwd, ".agents")
    manifest_path = os.path.join(local_agents_dir, "sprawl_manifest.yml")

    if not os.path.exists(manifest_path):
        raise SprawlError(
            f"Not in a Sprawl workspace (no .agents/sprawl_manifest.yml found in {cwd}).\n"
            "Run 'sprawl init <URL>' or 'sprawl graft' to set up."
        )

    workspace_name = os.path.basename(cwd)

    # --- Resolve DNA Binding ---
    ws = Workspace(cwd)
    dna_alias = ws.get_dna_alias() or "global/core (default)"

    # --- Read manifest ---
    try:
        reqs = parse_sprawl_manifest(manifest_path)
    except Exception:
        reqs = {cat: [] for cat in CATEGORIES}

    # --- Scan local .agents/ for real file state ---
    local_artifacts: dict[str, list[str]] = {cat: [] for cat in CATEGORIES}
    for cat in CATEGORIES:
        cat_dir = os.path.join(local_agents_dir, cat)
        if os.path.exists(cat_dir):
            local_artifacts[cat] = sorted(
                [f for f in os.listdir(cat_dir) if not f.startswith(".")]
            )

    # --- Venv health ---
    venv_dir = os.path.join(local_agents_dir, ".venv")
    venv_python = os.path.join(venv_dir, "bin", "python3")
    if os.path.exists(venv_python):
        try:
            import subprocess
            result = subprocess.check_output(
                [venv_python, "--version"], text=True, stderr=subprocess.STDOUT
            ).strip()
            venv_status = f"[success]● Healthy[/success] ({result})"
        except Exception:
            venv_status = "[warning]⚠ Python not executable[/warning]"
    elif os.path.exists(venv_dir):
        venv_status = "[warning]⚠ Exists but incomplete[/warning]"
    else:
        venv_status = "[error]○ Not provisioned[/error]"

    # --- Last sync timestamp ---
    sync_state = ws.get_sync_state()
    last_sync = sync_state.get("last_sync_timestamp", "Never")
    if last_sync and last_sync != "Never":
        try:
            dt = datetime.fromisoformat(last_sync)
            delta = datetime.now(timezone.utc) - dt
            if delta.days > 7:
                sync_display = f"[error]{last_sync} ({delta.days}d ago — STALE)[/error]"
            elif delta.days > 3:
                sync_display = f"[warning]{last_sync} ({delta.days}d ago)[/warning]"
            else:
                sync_display = f"[success]{last_sync}[/success]"
        except ValueError:
            sync_display = last_sync
    else:
        sync_display = "[error]Never[/error]"

    # --- Active model from config ---
    cfg_data = config.load()
    active_model = cfg_data.get("active_model", "[dim]Not set[/dim]")

    if config.json_logging:
        import json
        
        # Strip rich tags for clean JSON output
        import re
        def strip_tags(text: str) -> str:
            return re.sub(r'\[.*?\]', '', text)
            
        payload = {
            "workspace": workspace_name,
            "path": cwd,
            "dna_binding": dna_alias,
            "active_model": strip_tags(active_model),
            "venv_status": strip_tags(venv_status),
            "last_sync": last_sync,
            "artifacts_requested": reqs,
            "artifacts_installed": local_artifacts
        }
        print(json.dumps(payload))
        return

    # --- Build status panel ---
    console.print()

    # Header info table
    info_table = Table(show_header=False, box=None, padding=(0, 1))
    info_table.add_column("Key", style="accent", no_wrap=True, width=20)
    info_table.add_column("Value", style="info")

    info_table.add_row("Workspace", workspace_name)
    info_table.add_row("Path", cwd)
    info_table.add_row("DNA Binding", f"@{dna_alias}")
    info_table.add_row("Active Model", active_model)
    info_table.add_row("Venv", venv_status)
    info_table.add_row("Last Sync", sync_display)

    console.print(Panel(info_table, title="[bold accent]Workspace Identity[/bold accent]", border_style="#5D5CFF"))

    # Artifacts table
    artifact_table = Table(show_header=True, border_style="#5D5CFF")
    artifact_table.add_column("Category", style="accent", width=14)
    artifact_table.add_column("Manifest (Requested)", style="info")
    artifact_table.add_column("Local .agents/ (Installed)", style="success")

    for cat in CATEGORIES:
        requested = ", ".join(reqs.get(cat, [])) or "[dim]—[/dim]"
        installed = ", ".join(local_artifacts.get(cat, [])) or "[dim]—[/dim]"
        artifact_table.add_row(cat.capitalize(), requested, installed)

    console.print(Panel(artifact_table, title="[bold accent]DNA Artifacts[/bold accent]", border_style="#5D5CFF"))
    console.print()
