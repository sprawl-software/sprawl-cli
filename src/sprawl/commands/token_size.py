"""CLI handler and SDS Rich visualization for sprawl token-size (alias: sprawl context)."""

from __future__ import annotations

import dataclasses
import json
import os
from pathlib import Path

from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

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


def _build_summary_banner(report: ContextAuditReport, max_tokens: int | None = None) -> Text:
    """Builds the plain-English 3-bullet context budget summary below the layer table."""
    banner = Text()
    banner.append("\n• Unoptimized Peak Context: ", style="info")
    banner.append(f"{report.peak_tokens:,} tokens", style="bold")
    banner.append("  (if all rules & skills were loaded upfront)\n", style="dim")

    banner.append("• Actual Turn-1 Prompt:     ", style="info")
    banner.append(f"{report.zero_hop_tokens:,} tokens", style="bold warning")
    banner.append("  (Always-On baseline injected on first message)\n", style="dim")

    banner.append("• Context Saved (Lazy):     ", style="info")
    banner.append(f"{report.progressive_tokens:,} tokens", style="bold success")
    banner.append(
        f"  ({report.pruned_ratio_pct}% reduction via On-Demand loading)",
        style="success",
    )
    if max_tokens is not None:
        banner.append(f"  [Budget Ceiling: {max_tokens:,} tokens]", style="accent")
    return banner


def _render_summary_table(report: ContextAuditReport, max_tokens: int | None = None) -> None:
    """Renders the 4-layer Always-On (Turn 1) vs. Lazy-Loaded (On-Demand) summary table."""
    console.print()
    table = Table(show_header=True, border_style="#5D5CFF")
    table.add_column("Context Layer", style="accent")
    table.add_column("Files", justify="right", style="info", no_wrap=True)
    table.add_column("Bytes", justify="right", style="info", no_wrap=True)
    table.add_column("Always-On Tokens (Turn 1)", justify="right", style="warning")
    table.add_column("Lazy-Loaded Tokens (On-Demand)", justify="right", style="success")

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

    banner = _build_summary_banner(report, max_tokens=max_tokens)
    console.print(
        Panel(
            Group(table, banner),
            title=f"[bold accent]Context Pollution Audit ({os.path.basename(report.workspace_dir)})[/bold accent]",
            subtitle=f"[info]Scanned in {report.elapsed_ms:.1f}ms[/info]",
            border_style="#5D5CFF",
        )
    )


def _render_detailed_table(report: ContextAuditReport) -> None:
    """Renders per-artifact token breakdown sorted by total token weight without path truncation."""
    detail = Table(show_header=True, border_style="#5D5CFF", expand=True)
    detail.add_column("Layer", style="accent", no_wrap=True)
    detail.add_column("Artifact Path", style="accent", ratio=3, min_width=24, overflow="fold")
    detail.add_column("Bytes", justify="right", style="info", no_wrap=True)
    detail.add_column("Always-On\nTokens", justify="right", style="warning")
    detail.add_column("Lazy-Loaded\nTokens", justify="right", style="success")
    detail.add_column("Loading Behavior", style="info", ratio=2, min_width=16)

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
