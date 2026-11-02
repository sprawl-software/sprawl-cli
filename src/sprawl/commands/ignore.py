"""CLI command handler and Rich/JSON presenter for `sprawl ignore`."""

import json
import os
from pathlib import Path

from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ..analyzers.stack import (
    STACK_PROFILE_MAP,
    STACK_PROFILES,
    StackDetectionResult,
    detect_workspace_stacks,
)
from ..config import config
from ..exceptions import SprawlError
from ..generators.ignore import IgnoreSyncReport, sync_workspace_ignores
from ..output import console, print_status, print_success, print_warning

_STATUS_BADGES: dict[str, str] = {
    "created": "[bold #10B981]created[/bold #10B981]",
    "updated": "[bold #5D5CFF]updated[/bold #5D5CFF]",
    "unchanged": "[dim]unchanged[/dim]",
    "drifted": "[bold #EF4444]drifted[/bold #EF4444]",
}


def _resolve_workspace_path(target_dir: str | None) -> Path:
    """Resolve and validate the target workspace directory path."""
    raw_path = Path(target_dir) if target_dir else Path(os.getcwd())
    workspace_path = raw_path.resolve()
    if not workspace_path.is_dir():
        raise SprawlError(f"Target workspace directory does not exist: '{workspace_path}'")
    return workspace_path


def _format_markers(markers: tuple[str, ...]) -> str:
    """Format matched marker tuple for Rich table display."""
    if not markers:
        return "Always active (Git & Secrets)"
    return f"Found: {', '.join(markers)}"


def _format_exposed_paths(exposed: tuple[str, ...]) -> str:
    """Format detected bloat or sensitive paths present on disk."""
    if not exposed:
        return "[dim]none currently on disk[/dim]"
    return f"[bold #F59E0B]{', '.join(exposed)}[/bold #F59E0B]"


def _build_detection_table(result: StackDetectionResult) -> Table:
    """Build the 4-column Rich table for stack detection."""
    table = Table(border_style="#5D5CFF", expand=True)
    table.add_column("Stack Profile", style="accent")
    table.add_column("Why Detected (Markers Found)", style="info")
    table.add_column("Matching Paths in Repo")
    table.add_column("Shield Rules", justify="right", style="info")

    for stack_name in result.detected_stacks:
        profile = STACK_PROFILE_MAP[stack_name]
        markers = result.matched_markers.get(stack_name, ())
        exposed = result.exposed_paths.get(stack_name, ())
        table.add_row(
            stack_name,
            _format_markers(markers),
            _format_exposed_paths(exposed),
            f"{len(profile.ignore_patterns)} patterns",
        )
    return table


def _format_unchecked_stacks(detected_stacks: tuple[str, ...]) -> str:
    """Return a summary line of stack profiles not detected in the workspace."""
    missing = [p.name for p in STACK_PROFILES if p.name not in detected_stacks]
    if not missing:
        return "All supported stack profiles detected in workspace."
    return f"Not detected: {', '.join(missing)}"


def _render_detection(result: StackDetectionResult, workspace_path: Path) -> None:
    """Render stack detection output as JSON or a Rich terminal diagnostic panel."""
    if config.json_logging:
        payload = {
            "action": "detect",
            "workspace_dir": str(workspace_path),
            "detected_stacks": list(result.detected_stacks),
            "matched_markers": {k: list(v) for k, v in result.matched_markers.items()},
            "exposed_paths": {k: list(v) for k, v in result.exposed_paths.items()},
        }
        print(json.dumps(payload))
        return

    intro = Text(
        "Scanned workspace root for technology markers (pyproject.toml, package.json, "
        "Cargo.toml, go.mod, .obsidian, Dockerfile) to determine which build caches, "
        "secrets, and archives must be hidden from AI agents.\n",
        style="info",
    )
    table = _build_detection_table(result)
    footer = Text.assemble(
        ("\n" + _format_unchecked_stacks(result.detected_stacks) + "\n", "dim"),
        ("Next Step: Run ", "info"),
        ("'sprawl ignore'", "bold accent"),
        (" to compile these rules into your workspace ignore files.", "info"),
    )
    panel = Panel(
        Group(intro, table, footer),
        title=f"[bold accent]Workspace Ignore Diagnostic ({workspace_path.name})[/bold accent]",
        border_style="#5D5CFF",
    )
    console.print(panel)


def _build_sync_json(report: IgnoreSyncReport, check_only: bool) -> dict[str, object]:
    """Build structured JSON dictionary for sync or check operations."""
    return {
        "action": "check" if check_only else "sync",
        "workspace_dir": report.workspace_dir,
        "dry_run": config.dry_run,
        "detected_stacks": list(report.detected_stacks),
        "has_drift": report.has_drift,
        "elapsed_ms": report.elapsed_ms,
        "targets": [
            {
                "target_file": target.target_file,
                "status": target.status,
                "preserved_custom_lines": target.preserved_custom_lines,
                "reason": target.reason,
            }
            for target in report.targets
        ],
    }


def _render_sync_table(report: IgnoreSyncReport) -> None:
    """Render the Rich table summarizing all active IDE ignore target files."""
    stacks_label = ", ".join(report.detected_stacks)
    table = Table(
        title=f"Sprawl Multi-IDE Ignore Shield ({stacks_label})",
        border_style="#5D5CFF",
    )
    table.add_column("Target File", style="accent")
    table.add_column("Status")
    table.add_column("Custom Rules Preserved", justify="right", style="info")
    table.add_column("Details / What Changed", style="info")

    for target in report.targets:
        badge = _STATUS_BADGES.get(target.status, target.status)
        table.add_row(
            target.target_file,
            badge,
            str(target.preserved_custom_lines),
            target.reason,
        )

    console.print(table)


def _render_sync_report(report: IgnoreSyncReport, check_only: bool) -> None:
    """Render sync or check report in JSON or Rich terminal format."""
    if config.json_logging:
        print(json.dumps(_build_sync_json(report, check_only)))
        return

    _render_sync_table(report)
    if report.has_drift:
        print_warning(
            f"Ignore shield drift detected across workspace ({report.elapsed_ms:.2f}ms)."
        )
        return

    mode_prefix = "\\[DRY-RUN] " if config.dry_run and not check_only else ""
    stacks_str = ", ".join(report.detected_stacks)
    target_count = len(report.targets)
    print_success(
        f"{mode_prefix}Synchronized {target_count} IDE ignore targets for stacks "
        f"({stacks_str}) in {report.elapsed_ms:.2f}ms."
    )


def _run_detect_action(workspace_path: Path, _all_targets: bool) -> None:
    """Execute the 'detect' subcommand."""
    result = detect_workspace_stacks(workspace_path)
    _render_detection(result, workspace_path)


def _run_sync_action(workspace_path: Path, all_targets: bool) -> None:
    """Execute the 'sync' subcommand."""
    if config.dry_run and not config.json_logging:
        print_status(f"\\[DRY-RUN] Simulating ignore shield sync in '{workspace_path}'...")
    report = sync_workspace_ignores(
        workspace_path,
        check_only=False,
        dry_run=config.dry_run,
        all_targets=all_targets,
    )
    _render_sync_report(report, check_only=False)


def _run_check_action(workspace_path: Path, all_targets: bool) -> None:
    """Execute the 'check' subcommand and fail on drift."""
    report = sync_workspace_ignores(
        workspace_path,
        check_only=True,
        dry_run=True,
        all_targets=all_targets,
    )
    _render_sync_report(report, check_only=True)
    if report.has_drift:
        raise SprawlError(
            "Ignore shield drift detected: one or more ignore files are missing or out of "
            "sync with the workspace stack. Run 'sprawl ignore' to update them non-destructively."
        )


_ACTION_DISPATCH = {
    "detect": _run_detect_action,
    "sync": _run_sync_action,
    "check": _run_check_action,
}


def _resolve_ignore_args(
    action: str,
    target_dir: str | None,
    positional_dir: str | None = None,
) -> tuple[str, Path]:
    """Resolve action name and workspace path from positional or flag arguments."""
    if action in _ACTION_DISPATCH:
        return action, _resolve_workspace_path(target_dir or positional_dir)

    candidate_path = Path(action)
    if candidate_path.is_dir():
        return "sync", candidate_path.resolve()

    raise SprawlError(
        f"Unknown ignore action or missing directory: '{action}'. "
        "Expected 'detect', 'sync', or 'check'."
    )


def cmd_ignore(
    action: str = "sync",
    target_dir: str | None = None,
    all_targets: bool = False,
    positional_dir: str | None = None,
) -> None:
    """Entrypoint for `sprawl ignore [detect|sync|check] [DIR] [--path DIR] [--all]`."""
    resolved_action, workspace_path = _resolve_ignore_args(action, target_dir, positional_dir)
    handler = _ACTION_DISPATCH[resolved_action]
    handler(workspace_path, all_targets)
