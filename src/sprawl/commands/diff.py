"""Diff visualization command."""

import difflib
import os

from rich.panel import Panel
from rich.syntax import Syntax

from ..exceptions import SprawlError
from ..output import console
from ..sync import parse_sprawl_manifest
from ..utils import get_active_dna_context

_IGNORED_DIFF_ITEMS = frozenset({".venv", "__pycache__", ".git", "node_modules"})


def _read_lines_if_exists(path: str) -> list[str]:
    """Reads all lines of a UTF-8 file if it exists, or returns an empty list."""
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8", errors="ignore") as f:
        return f.readlines()


def diff_files(src_path: str, dest_path: str, rel_path: str) -> bool:
    """Computes unified diff between two files and prints it if drift exists."""
    src_content = _read_lines_if_exists(src_path)
    dest_content = _read_lines_if_exists(dest_path)
    if src_content == dest_content:
        return False

    diff = list(
        difflib.unified_diff(
            src_content,
            dest_content,
            fromfile=f"DNA: {rel_path}",
            tofile=f"Local: {rel_path}",
            lineterm="",
        )
    )
    if not diff:
        return False

    syntax = Syntax("".join(diff), "diff", theme="monokai", background_color="default")
    console.print(syntax)
    console.print()
    return True


def _collect_union_entries(src_base: str, dest_base: str) -> list[str]:
    """Returns sorted non-ignored entry names across src_base and dest_base."""
    entries: set[str] = set()
    if os.path.exists(src_base):
        entries.update(os.listdir(src_base))
    if os.path.exists(dest_base):
        entries.update(os.listdir(dest_base))
    return [item for item in sorted(entries) if item not in _IGNORED_DIFF_ITEMS]


def _diff_single_entry(src_item: str, dest_item: str, rel_item: str) -> bool:
    """Diffs a single directory or file entry pair."""
    if os.path.isdir(src_item) or os.path.isdir(dest_item):
        return diff_recursive(src_item, dest_item, rel_item)
    return diff_files(src_item, dest_item, rel_item)


def _is_non_directory_target(src_base: str, dest_base: str) -> bool:
    """Returns True if either existing endpoint is a regular file rather than a directory."""
    src_is_file = os.path.exists(src_base) and not os.path.isdir(src_base)
    dest_is_file = os.path.exists(dest_base) and not os.path.isdir(dest_base)
    return src_is_file or dest_is_file


def _any_entry_drifted(src_base: str, dest_base: str, rel_base: str) -> bool:
    """Checks all union entries inside src_base/dest_base and returns True if any drifted."""
    drifted = [
        _diff_single_entry(
            os.path.join(src_base, item),
            os.path.join(dest_base, item),
            os.path.join(rel_base, item),
        )
        for item in _collect_union_entries(src_base, dest_base)
    ]
    return any(drifted)


def diff_recursive(src_base: str, dest_base: str, rel_base: str) -> bool:
    """Recursively diffs two directories."""
    if not (os.path.exists(src_base) or os.path.exists(dest_base)):
        return False
    if _is_non_directory_target(src_base, dest_base):
        return diff_files(src_base, dest_base, rel_base)
    return _any_entry_drifted(src_base, dest_base, rel_base)


def _diff_category_files(
    category: str,
    files: list[str],
    source_dna_dir: str,
    local_agents_dir: str,
) -> bool:
    """Diffs all non-local files within a single category."""
    category_dir = os.path.join(local_agents_dir, category)
    drift = False
    for file_name in files:
        if file_name.startswith("local_"):
            continue
        if diff_recursive(
            os.path.join(source_dna_dir, category, file_name),
            os.path.join(category_dir, file_name),
            f"{category}/{file_name}",
        ):
            drift = True
    return drift


def _diff_manifest_categories(
    reqs: dict[str, list[str]],
    source_dna_dir: str,
    local_agents_dir: str,
) -> bool:
    """Diffs all standard manifest categories against source_dna_dir."""
    drift = False
    for category, files in reqs.items():
        if category.startswith("local_") or not files:
            continue
        if _diff_category_files(category, files, source_dna_dir, local_agents_dir):
            drift = True
    return drift


def _render_local_extensions_panel(reqs: dict[str, list[str]]) -> None:
    """Renders the Workspace Extensions panel when local_* items are present."""
    sections = [
        ("Rules", reqs.get("local_rules", [])),
        ("Skills", reqs.get("local_skills", [])),
        ("Workflows", reqs.get("local_workflows", [])),
    ]
    populated = [(label, items) for label, items in sections if items]
    if not populated:
        return

    console.print()
    lines = [
        "[info]ℹ Workspace Extensions Discovered:[/info]",
        "This workspace contains local-only custom artifacts not managed in the upstream DNA registry:",
    ]
    for label, items in populated:
        lines.append(f"  • {label}: " + ", ".join(items))
    lines.extend(
        [
            "",
            "[dim]Note: Local artifacts are exempted from DNA validation. In strict enterprise environments, ensure only approved DNA templates are committed.[/dim]",
        ]
    )
    console.print(
        Panel(
            "\n".join(lines),
            title="[bold info]Workspace Extensions[/bold info]",
            border_style="cyan",
        )
    )


def cmd_diff(target_dir: str | None = None) -> None:
    """Shows local vs source DNA drift."""
    cwd = target_dir or os.getcwd()
    local_agents_dir = os.path.join(cwd, ".agents")
    manifest_path = os.path.join(local_agents_dir, "sprawl_manifest.yml")
    if not os.path.exists(manifest_path):
        raise SprawlError(f"No sprawl_manifest.yml found in {local_agents_dir}.")

    source_dna_dir = get_active_dna_context(cwd)
    reqs = parse_sprawl_manifest(manifest_path)

    console.print(
        f"\n[bold accent]Comparing local DNA drift against @{os.path.basename(source_dna_dir)}...[/bold accent]\n"
    )

    design_drift = diff_files(
        os.path.join(source_dna_dir, "DESIGN.md"),
        os.path.join(cwd, "DESIGN.md"),
        "DESIGN.md",
    )
    cat_drift = _diff_manifest_categories(reqs, source_dna_dir, local_agents_dir)

    if not (design_drift or cat_drift):
        console.print(
            Panel(
                "[green]✔ No DNA drift detected.[/green] Your local workspace perfectly matches the upstream registry.",
                title="[bold green]Sync Status[/bold green]",
                border_style="green",
            )
        )
    else:
        console.print(
            Panel(
                "[yellow]⚠ DNA drift detected.[/yellow] Run [accent]sprawl sync[/accent] to overwrite local changes, or update your Global DNA.",
                title="[bold yellow]Sync Status[/bold yellow]",
                border_style="yellow",
            )
        )

    _render_local_extensions_panel(reqs)
