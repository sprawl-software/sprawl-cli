"""CLI handler and SDS Rich visualization for sprawl token-size (alias: sprawl context)."""

from __future__ import annotations

import dataclasses
import json
import os
from pathlib import Path

from rich.panel import Panel
from rich.table import Table

from ..analyzers.context import ContextAuditReport, scan_workspace_context
from ..config import config
from ..exceptions import SprawlError
from ..output import console

_LAYER_LABELS = {
    "manifest": "Root Manifests & IDE Bindings",
    "rule": "Governance Rules (.agents/rules/)",
    "skill": "Agent Skills (.agents/skills/)",
    "mcp": "MCP Server Schemas (mcp_config.json)",
}


def _render_summary_table(report: ContextAuditReport, max_tokens: int | None = None) -> None:
    """Renders the 4-layer Turn-1 Zero-Hop vs. Progressive summary table."""
    console.print()
    table = Table(show_header=True, border_style="#5D5CFF")
    table.add_column("Context Layer", style="accent", width=34)
    table.add_column("Files", justify="right", style="info", width=7)
    table.add_column("Bytes", justify="right", style="info", width=10)
    table.add_column("Turn-1 (Zero-Hop)", justify="right", style="warning", width=18)
    table.add_column("On-Demand (Prog.)", justify="right", style="success", width=18)

    for row in report.layers:
        label = _LAYER_LABELS.get(row.layer, row.layer.capitalize())
        table.add_row(
            label,
            str(row.artifact_count),
            f"{row.bytes_size:,}",
            f"{row.zero_hop_tokens:,}",
            f"{row.progressive_tokens:,}",
        )

    total_files = sum(r.artifact_count for r in report.layers)
    total_bytes = sum(r.bytes_size for r in report.layers)
    table.add_section()
    table.add_row(
        "[bold]Workspace Total[/bold]",
        f"[bold]{total_files}[/bold]",
        f"[bold]{total_bytes:,}[/bold]",
        f"[bold]{report.zero_hop_tokens:,}[/bold]",
        f"[bold]{report.progressive_tokens:,}[/bold]",
    )

    budget_note = (
        f" | Budget Ceiling: {max_tokens:,} tokens" if max_tokens is not None else ""
    )
    subtitle = (
        f"[info]Turn-1 Baseline: [bold]{report.zero_hop_tokens:,}[/bold] tokens | "
        f"Pruned via Progressive Disclosure: [bold success]{report.pruned_ratio_pct}%[/bold success] "
        f"({report.progressive_tokens:,} / {report.peak_tokens:,} peak tokens) | "
        f"{report.elapsed_ms:.1f}ms{budget_note}[/info]"
    )
    console.print(
        Panel(
            table,
            title=f"[bold accent]Context Pollution Audit ({os.path.basename(report.workspace_dir)})[/bold accent]",
            subtitle=subtitle,
            border_style="#5D5CFF",
        )
    )


def _render_detailed_table(report: ContextAuditReport) -> None:
    """Renders per-artifact token breakdown sorted by total token weight."""
    detail = Table(show_header=True, border_style="#5D5CFF")
    detail.add_column("Layer", style="accent", width=10)
    detail.add_column("Artifact Path", style="info")
    detail.add_column("Bytes", justify="right", style="info", width=9)
    detail.add_column("Zero-Hop", justify="right", style="warning", width=10)
    detail.add_column("Progressive", justify="right", style="success", width=12)
    detail.add_column("Loading Tier / Diagnostic", style="info")

    sorted_items = sorted(
        report.artifacts,
        key=lambda a: (a.zero_hop_tokens + a.progressive_tokens, a.bytes_size),
        reverse=True,
    )
    for item in sorted_items:
        detail.add_row(
            item.layer,
            item.relative_path,
            f"{item.bytes_size:,}",
            f"{item.zero_hop_tokens:,}",
            f"{item.progressive_tokens:,}",
            item.note,
        )

    console.print(
        Panel(
            detail,
            title="[bold accent]Per-Artifact Token Breakdown (--detailed)[/bold accent]",
            border_style="#5D5CFF",
        )
    )
    console.print()


def cmd_token_size(
    target_dir: str | None = None,
    detailed: bool = False,
    max_tokens: int | None = None,
) -> None:
    """Audits workspace Turn-1 zero-hop vs. progressive context token weight."""
    workspace_path = Path(target_dir or os.getcwd()).resolve()
    if not workspace_path.is_dir():
        raise SprawlError(f"Target workspace directory does not exist: {workspace_path}")

    report = scan_workspace_context(workspace_path)

    if config.json_logging:
        print(json.dumps(dataclasses.asdict(report)))
    else:
        _render_summary_table(report, max_tokens=max_tokens)
        if detailed:
            _render_detailed_table(report)

    if max_tokens is not None and report.zero_hop_tokens > max_tokens:
        raise SprawlError(
            f"Context budget exceeded: Turn-1 zero-hop baseline is "
            f"{report.zero_hop_tokens} tokens (limit: {max_tokens})."
        )
