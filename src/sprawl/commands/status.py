"""Workspace status command — rich dashboard view of workspace state."""

import json
import os
import re
import subprocess
from datetime import datetime, timezone

from rich.panel import Panel
from rich.table import Table

from ..config import config
from ..exceptions import SprawlError
from ..output import console
from ..sync import parse_sprawl_manifest
from ..utils import CATEGORIES, get_venv_executable
from ..workspace import Workspace


def _scan_installed_artifacts(
    local_agents_dir: str,
) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    """Scans .agents/ categories into (standard_installed, local_installed) mappings."""
    standard_installed: dict[str, list[str]] = {cat: [] for cat in CATEGORIES}
    local_installed: dict[str, list[str]] = {cat: [] for cat in CATEGORIES}

    for cat in CATEGORIES:
        cat_dir = os.path.join(local_agents_dir, cat)
        if not os.path.exists(cat_dir):
            continue
        files = sorted(f for f in os.listdir(cat_dir) if not f.startswith("."))
        standard_installed[cat] = [f for f in files if not f.startswith("local_")]
        local_installed[cat] = [f for f in files if f.startswith("local_")]

    return standard_installed, local_installed


def _evaluate_venv_health(local_agents_dir: str) -> str:
    """Checks .agents/.venv Python binary availability and returns a Rich status string."""
    venv_dir = os.path.join(local_agents_dir, ".venv")
    venv_python = get_venv_executable(venv_dir, "python3")
    if not os.path.exists(venv_python):
        venv_python = get_venv_executable(venv_dir, "python")

    if os.path.exists(venv_python):
        try:
            result = subprocess.check_output(
                [venv_python, "--version"],
                text=True,
                stderr=subprocess.STDOUT,
                timeout=5,
            ).strip()
            return f"[success]● Healthy[/success] ({result})"
        except (OSError, subprocess.SubprocessError):
            return "[warning]⚠ Python not executable[/warning]"

    if os.path.exists(venv_dir):
        return "[warning]⚠ Exists but incomplete[/warning]"
    return "[error]○ Not provisioned[/error]"


def _format_sync_timestamp(last_sync: str | None) -> str:
    """Formats the ISO last_sync timestamp with staleness color indicators."""
    if not last_sync or last_sync == "Never":
        return "[error]Never[/error]"
    try:
        dt = datetime.fromisoformat(last_sync)
        delta = datetime.now(timezone.utc) - dt
        if delta.days > 7:
            return f"[error]{last_sync} ({delta.days}d ago — STALE)[/error]"
        if delta.days > 3:
            return f"[warning]{last_sync} ({delta.days}d ago)[/warning]"
        return f"[success]{last_sync}[/success]"
    except ValueError:
        return last_sync


def _strip_rich_tags(text: str) -> str:
    """Removes Rich bracket markup tags for clean JSON serialization."""
    return re.sub(r"\[.*?\]", "", text)


def _build_artifacts_table(
    reqs: dict[str, list[str]],
    local_artifacts: dict[str, list[str]],
    local_installed: dict[str, list[str]],
) -> Table:
    """Constructs the DNA Artifacts Rich table comparing manifest vs installed items."""
    artifact_table = Table(show_header=True, border_style="#5D5CFF")
    artifact_table.add_column("Category", style="accent", width=14)
    artifact_table.add_column("Manifest (Requested)", style="info")
    artifact_table.add_column("Local .agents/ (Installed)", style="success")

    for cat in CATEGORIES:
        requested = ", ".join(reqs.get(cat, [])) or "[dim]—[/dim]"
        installed = ", ".join(local_artifacts.get(cat, [])) or "[dim]—[/dim]"
        artifact_table.add_row(cat.capitalize(), requested, installed)

    for cat in CATEGORIES:
        req_local = reqs.get(f"local_{cat}", [])
        inst_local = local_installed.get(cat, [])
        if req_local or inst_local:
            requested_str = ", ".join(req_local) or "[dim]—[/dim]"
            installed_str = ", ".join(inst_local) or "[dim]—[/dim]"
            artifact_table.add_row(f"Local {cat.capitalize()}", requested_str, installed_str)

    return artifact_table


def cmd_status(target_dir: str | None = None) -> None:
    """Displays a Rich Panel with workspace name, DNA binding, loaded artifacts, venv health."""
    cwd = os.path.abspath(target_dir or os.getcwd())
    local_agents_dir = os.path.join(cwd, ".agents")
    manifest_path = os.path.join(local_agents_dir, "sprawl_manifest.yml")

    if not os.path.exists(manifest_path):
        raise SprawlError(
            f"Not in a Sprawl workspace (no .agents/sprawl_manifest.yml found in {cwd}).\n"
            "Run 'sprawl init <URL>' or 'sprawl graft' to set up."
        )

    workspace_name = os.path.basename(cwd)
    ws = Workspace(cwd)
    dna_alias = ws.get_dna_alias() or "global/core (default)"

    try:
        reqs = parse_sprawl_manifest(manifest_path)
    except (OSError, SprawlError, ValueError):
        reqs = {cat: [] for cat in CATEGORIES}

    local_artifacts, local_installed = _scan_installed_artifacts(local_agents_dir)
    venv_status = _evaluate_venv_health(local_agents_dir)
    last_sync = ws.get_sync_state().get("last_sync_timestamp", "Never")
    sync_display = _format_sync_timestamp(last_sync)
    active_model = config.load().get("active_model", "[dim]Not set[/dim]")

    if config.json_logging:
        payload = {
            "workspace": workspace_name,
            "path": cwd,
            "dna_binding": dna_alias,
            "active_model": _strip_rich_tags(active_model),
            "venv_status": _strip_rich_tags(venv_status),
            "last_sync": last_sync,
            "artifacts_requested": reqs,
            "artifacts_installed": local_artifacts,
        }
        print(json.dumps(payload))
        return

    console.print()
    info_table = Table(show_header=False, box=None, padding=(0, 1))
    info_table.add_column("Key", style="accent", no_wrap=True, width=20)
    info_table.add_column("Value", style="info")
    info_table.add_row("Workspace", workspace_name)
    info_table.add_row("Path", cwd)
    info_table.add_row("DNA Binding", f"@{dna_alias}")
    info_table.add_row("Active Model", active_model)
    info_table.add_row("Venv", venv_status)
    info_table.add_row("Last Sync", sync_display)

    console.print(
        Panel(
            info_table,
            title="[bold accent]Workspace Identity[/bold accent]",
            border_style="#5D5CFF",
        )
    )
    artifact_table = _build_artifacts_table(reqs, local_artifacts, local_installed)
    console.print(
        Panel(
            artifact_table,
            title="[bold accent]DNA Artifacts[/bold accent]",
            border_style="#5D5CFF",
        )
    )
    console.print()
