"""CLI command handler and Rich/JSON presenter for `sprawl ignore`."""

import json
import os
from pathlib import Path

from rich.table import Table

from ..analyzers.stack import (
    STACK_PROFILE_MAP,
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
        return "[dim](always active)[/dim]"
    return ", ".join(markers)


def _render_detection(result: StackDetectionResult, workspace_path: Path) -> None:
    """Render stack detection output as JSON or a Rich terminal table."""
    if config.json_logging:
        payload = {
            "action": "detect",
            "workspace_dir": str(workspace_path),
            "detected_stacks": list(result.detected_stacks),
            "matched_markers": {k: list(v) for k, v in result.matched_markers.items()},
        }
        print(json.dumps(payload))
        return

    table = Table(
        title=f"Detected Workspace Stacks ({workspace_path.name})",
        border_style="#5D5CFF",
    )
    table.add_column("Stack", style="accent")
    table.add_column("Matched Root Markers", style="info")
    table.add_column("Patterns", justify="right")

    for stack_name in result.detected_stacks:
        profile = STACK_PROFILE_MAP[stack_name]
        markers = result.matched_markers.get(stack_name, ())
        table.add_row(
            stack_name,
            _format_markers(markers),
            str(len(profile.ignore_patterns)),
        )

    console.print(table)


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

    for target in report.targets:
        badge = _STATUS_BADGES.get(target.status, target.status)
        table.add_row(target.target_file, badge, str(target.preserved_custom_lines))

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
        raise SprawlError("Ignore shield drift detected. Run 'sprawl ignore sync' to remediate.")


_ACTION_DISPATCH = {
    "detect": _run_detect_action,
    "sync": _run_sync_action,
    "check": _run_check_action,
}


def cmd_ignore(
    action: str = "sync",
    target_dir: str | None = None,
    all_targets: bool = False,
) -> None:
    """Entrypoint for `sprawl ignore [detect|sync|check] [--path DIR] [--all]`."""
    workspace_path = _resolve_workspace_path(target_dir)
    handler = _ACTION_DISPATCH.get(action)
    if handler is None:
        raise SprawlError(
            f"Unknown ignore action: '{action}'. Expected 'detect', 'sync', or 'check'."
        )
    handler(workspace_path, all_targets)
