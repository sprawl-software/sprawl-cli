"""Workspace creation and grafting commands."""

import json
import os
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

from rich.panel import Panel
from rich.table import Table

from ..config import config
from ..exceptions import SprawlError
from ..output import console, operation_spinner, print_status, print_warning
from ..utils import CATEGORIES
from ..workspace import (
    deregister_workspace,
    get_all_workspaces,
    get_workspace_info,
    register_workspace,
)


def _resolve_dna_rule(candidates: list[str]) -> str:
    """Returns the first candidate rule that exists in the active DNA rules folder."""
    from ..utils import get_active_dna_context

    rules_dir = os.path.join(get_active_dna_context(), "rules")
    for name in candidates:
        if os.path.exists(os.path.join(rules_dir, name)):
            return name
    return candidates[0]


def _resolve_dna_skill(candidates: list[str]) -> str | None:
    """Returns the first candidate skill that exists in the active DNA skills folder, or None."""
    from ..utils import get_active_dna_context

    skills_dir = os.path.join(get_active_dna_context(), "skills")
    for name in candidates:
        if os.path.exists(os.path.join(skills_dir, name)):
            return name
    return None


_HARVEST_BINDING_MAP: dict[str, str] = {
    "local_cursor.md": "cursor",
    "local_cline.md": "cline-roo",
    "local_windsurf.md": "windsurf",
    "local_copilot.md": "copilot",
    "local_claude.md": "claude-code",
    "local_agent.md": "google-antigravity",
}


def cmd_create(workspace_name: str, path: str | None = None) -> None:
    """Instantiates a brand new Agentic Sandbox Workspace."""
    if ".." in workspace_name or "/" in workspace_name or "\\" in workspace_name:
        raise SprawlError("Invalid workspace name. No path traversal allowed.")
    if not re.match(r"^[a-zA-Z0-9_-]+$", workspace_name):
        raise SprawlError("Workspace name must be alphanumeric, underscores, or hyphens only.")

    workspace_dir = (
        os.path.abspath(os.path.join(path, workspace_name))
        if path
        else os.path.abspath(workspace_name)
    )
    if os.path.exists(workspace_dir):
        raise SprawlError(f"Workspace directory {workspace_dir} already exists.")

    if config.dry_run:
        print_status(f"Creating new workspace '{workspace_name}' at {workspace_dir}...")
        if config.verbose:
            print_status(f"DRY RUN: Would create default sprawl_manifest.yml in {workspace_dir}")
        return

    with operation_spinner(f"Creating new workspace '{workspace_name}' at {workspace_dir}..."):
        os.makedirs(workspace_dir)
        local_agents_dir = os.path.join(workspace_dir, ".agents")
        os.makedirs(local_agents_dir, exist_ok=True)
        manifest_path = os.path.join(local_agents_dir, "sprawl_manifest.yml")
        default_content = f"""# {workspace_name}
dna: core

rules:

skills:

workflows:

bindings: []
"""
        with open(manifest_path, "w", encoding="utf-8") as f:
            f.write(default_content)

        config_path = os.path.join(local_agents_dir, "sprawl-config.json")
        with open(config_path, "w", encoding="utf-8") as f:
            f.write('{\n  "allowed_mounts": {}\n}\n')

        register_workspace(workspace_name, workspace_dir)

    text = (
        "[success]✔ Workspace Created[/success]\n"
        f"• Name: {workspace_name}\n"
        f"• Path: {workspace_dir}\n"
        "• DNA Binding: @core\n"
        "\n• Run [accent]sprawl bind[/accent] inside to select rules bindings for your IDEs/agents."
        "\n• Run [accent]sprawl sync[/accent] inside to orchestrate."
    )
    console.print()
    console.print(
        Panel(text, title="[accent]Workspace Initialization[/accent]", border_style="#5D5CFF")
    )


def _infer_heuristic_rules(cwd: str) -> list[str]:
    """Infers default DNA rule files from workspace root manifest markers."""
    inferred: list[str] = []
    if os.path.exists(os.path.join(cwd, "requirements.txt")) or os.path.exists(
        os.path.join(cwd, "pyproject.toml")
    ):
        inferred.append(_resolve_dna_rule(["python.md"]))
    if os.path.exists(os.path.join(cwd, "package.json")):
        inferred.append(
            _resolve_dna_rule(["web_development.md", "web-dev.md", "react_best_practices.md"])
        )
    if os.path.exists(os.path.join(cwd, "Cargo.toml")):
        inferred.append(_resolve_dna_rule(["wasm.md"]))
    if not inferred:
        inferred.append("engineering.md")
    return inferred


def _discover_graft_artifacts(cwd: str, local_agents_dir: str) -> dict[str, list[str]]:
    """Scans existing .agents/ categories and applies stack heuristic defaults."""
    discovered: dict[str, list[str]] = {cat: [] for cat in CATEGORIES}
    for category in CATEGORIES:
        cat_dir = os.path.join(local_agents_dir, category)
        if os.path.exists(cat_dir):
            discovered[category].extend(
                item
                for item in os.listdir(cat_dir)
                if not item.startswith(".") and not item.startswith("local_")
            )

    if not discovered["rules"]:
        discovered["rules"].extend(_infer_heuristic_rules(cwd))

    if not discovered["skills"]:
        fallback_skill = _resolve_dna_skill(["web_artifacts_builder"])
        if fallback_skill:
            discovered["skills"].append(fallback_skill)

    return discovered


def _classify_harvested_paths(
    harvested: list[str],
) -> tuple[dict[str, list[str]], list[str]]:
    """Groups harvested relative paths into local_<cat> lists and inferred IDE bindings."""
    active_bindings: list[str] = []
    local_groups: dict[str, list[str]] = {f"local_{cat}": [] for cat in CATEGORIES}

    for path in harvested:
        parts = path.split("/", 1)
        if len(parts) != 2:
            continue
        cat, fname = parts
        grp_key = f"local_{cat}"
        if grp_key in local_groups:
            local_groups[grp_key].append(fname)
        if fname in _HARVEST_BINDING_MAP:
            active_bindings.append(_HARVEST_BINDING_MAP[fname])

    return local_groups, active_bindings


def _render_graft_manifest_yaml(
    app_name: str,
    discovered_artifacts: dict[str, list[str]],
    local_groups: dict[str, list[str]],
    active_bindings: list[str],
) -> str:
    """Renders the initial sprawl_manifest.yml content string."""
    content_lines: list[str] = [f"# {app_name}", "dna: core", ""]
    for category in CATEGORIES:
        content_lines.append(f"{category}:")
        for item in sorted(discovered_artifacts[category]):
            content_lines.append(f"  - {item}")
        content_lines.append("")

    for cat in CATEGORIES:
        grp_key = f"local_{cat}"
        items = local_groups.get(grp_key, [])
        if items:
            content_lines.append(f"{grp_key}:")
            for item in sorted(items):
                content_lines.append(f"  - {item}")
            content_lines.append("")

    if active_bindings:
        content_lines.append("bindings:")
        for binding in sorted(active_bindings):
            content_lines.append(f"  - {binding}")
        content_lines.append("")
    else:
        content_lines.append("bindings: []")
        content_lines.append("")

    return "\n".join(content_lines)


def cmd_graft() -> None:
    """Surgical Injection Protocol: Stitches Sprawl DNA onto an existing project."""
    cwd = os.getcwd()
    app_name = os.path.basename(cwd)
    local_agents_dir = os.path.join(cwd, ".agents")
    if not config.dry_run:
        os.makedirs(local_agents_dir, exist_ok=True)

    manifest_path = os.path.join(local_agents_dir, "sprawl_manifest.yml")
    if os.path.exists(manifest_path):
        raise SprawlError(
            f"A sprawl_manifest.yml already exists in {local_agents_dir}. Grafting aborted."
        )

    print_status(f"Grafting Sprawl DNA onto '{app_name}' at {cwd}...")

    from ..generators.ignore import sync_workspace_ignores
    from ..graft import harvest_legacy_rules

    harvested = harvest_legacy_rules(cwd, local_agents_dir) if not config.dry_run else []
    discovered_artifacts = _discover_graft_artifacts(cwd, local_agents_dir)
    local_groups, active_bindings = _classify_harvested_paths(harvested)
    manifest_content = _render_graft_manifest_yaml(
        app_name, discovered_artifacts, local_groups, active_bindings
    )

    if config.verbose and config.dry_run:
        print_status(f"DRY RUN: Would surgically graft sprawl_manifest.yml into {local_agents_dir}")
        print_status("Generated manifest:\n" + manifest_content)
        sync_workspace_ignores(Path(cwd), dry_run=True)
    elif not config.dry_run:
        with open(manifest_path, "w", encoding="utf-8") as f:
            f.write(manifest_content)
        sync_workspace_ignores(Path(cwd), dry_run=False)
        register_workspace(app_name, cwd)
        print_status(
            f"Successfully grafted sprawl_manifest.yml into {local_agents_dir}.\n"
            "• You can now run [accent]sprawl bind[/accent] to select rules bindings for your active IDEs/agents.\n"
            "• Run [accent]sprawl sync[/accent] to orchestrate the workspace."
        )


def _format_ws_sync_badge(last_sync: str) -> str:
    """Formats a workspace last_sync timestamp with Rich color tags."""
    if last_sync == "Never":
        return "[error]Never[/error]"
    try:
        dt = datetime.fromisoformat(last_sync)
        delta = datetime.now(timezone.utc) - dt
        if delta.days > 7:
            return f"[error]{last_sync}[/error]"
        if delta.days > 3:
            return f"[warning]{last_sync}[/warning]"
        return f"[success]{last_sync}[/success]"
    except ValueError:
        return last_sync


def cmd_ws_list() -> None:
    """Lists all tracked workspaces with their details."""
    workspaces = get_all_workspaces()
    if not workspaces:
        if config.json_logging:
            print(json.dumps([]))
            return
        print_status("No workspaces currently tracked in the registry.")
        return

    if config.json_logging:
        print(json.dumps([{"name": k, **v} for k, v in workspaces.items()]))
        return

    table = Table(title="[info]Tracked Workspaces[/info]", border_style="#5D5CFF")
    table.add_column("Status", justify="center")
    table.add_column("Name", style="accent", no_wrap=True)
    table.add_column("Path", style="info")
    table.add_column("DNA Binding", style="info")
    table.add_column("Last Sync", style="info")

    for name, data in workspaces.items():
        path = data.get("path", "Unknown")
        dna = data.get("dna_source") or "Global/Default"
        last_sync = data.get("last_sync_timestamp") or "Never"
        status = "[success]●[/success]" if os.path.exists(path) else "[error]○[/error]"
        table.add_row(status, name, path, dna, _format_ws_sync_badge(last_sync))

    console.print(table)


def cmd_ws_remove(name: str, delete: bool = False) -> None:
    """Removes a workspace from the registry and optionally from disk."""
    try:
        ws_info = get_workspace_info(name)
        if not ws_info:
            print_warning(f"Workspace '{name}' is not currently tracked.")
            return

        path = ws_info.get("path")
        deregister_workspace(name)
        print_status(f"Workspace '{name}' has been deregistered.")

        if delete and path and os.path.exists(path):
            if not config.dry_run:
                shutil.rmtree(path)
            print_status(f"Workspace directory {path} has been deleted.")
    except SprawlError:
        raise
    except OSError as e:
        raise SprawlError(f"Failed to remove workspace '{name}': {e}") from e


def cmd_ws_push(name: str | None = None) -> None:
    """Syncs DNA updates to all tracked workspaces or a specific one."""
    from .sync_cmd import cmd_sync

    workspaces = get_all_workspaces()
    if name:
        if name not in workspaces:
            raise SprawlError(f"Workspace '{name}' is not currently tracked.")
        targets = {name: workspaces[name]}
    else:
        targets = workspaces

    if not targets:
        print_status("No workspaces currently tracked in the registry.")
        return

    for ws_name, data in targets.items():
        path = data.get("path")
        if not path or not os.path.exists(path):
            print_warning(f"Workspace '{ws_name}' path '{path}' not found. Skipping.")
            continue

        print_status(f"Pushing updates to workspace '{ws_name}' at {path}...")
        try:
            cmd_sync(target_dir=path)
        except (SprawlError, OSError) as e:
            print_warning(f"Failed to sync workspace '{ws_name}': {e}")
