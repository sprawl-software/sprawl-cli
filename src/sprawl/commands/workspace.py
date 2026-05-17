"""Workspace creation and grafting commands."""

import os
import re
import shutil

from ..config import config
from ..output import print_status, print_warning, console
from ..exceptions import SprawlError
from ..workspace import WorkspaceRegistry
from rich.table import Table


def cmd_create(workspace_name: str, path: str = None) -> None:
    """Instantiates a brand new Agentic Sandbox Workspace.

    Args:
        workspace_name: Name of the workspace to create.
    """
    if ".." in workspace_name or "/" in workspace_name or "\\" in workspace_name:
        raise SprawlError("Invalid workspace name. No path traversal allowed.")
    if not re.match(r"^[a-zA-Z0-9_-]+$", workspace_name):
        raise SprawlError("Workspace name must be alphanumeric, underscores, or hyphens only.")

    if path:
        workspace_dir = os.path.abspath(os.path.join(path, workspace_name))
    else:
        workspace_dir = os.path.abspath(workspace_name)

    if os.path.exists(workspace_dir):
        raise SprawlError(f"Workspace directory {workspace_dir} already exists.")

    from ..output import operation_spinner
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
  - engineering.md

skills:
  - web_artifacts_builder

atoms:

workflows:
"""
        with open(manifest_path, "w") as f:
            f.write(default_content)
        WorkspaceRegistry.register(workspace_name, workspace_dir)
        
    from rich.panel import Panel
    from ..output import console
    text = f"[success]✔ Workspace Created[/success]\n"
    text += f"• Name: {workspace_name}\n"
    text += f"• Path: {workspace_dir}\n"
    text += f"• DNA Binding: @core\n"
    text += f"\nRun [accent]sprawl sync[/accent] inside to orchestrate."
    console.print()
    console.print(Panel(text, title="[accent]Workspace Initialization[/accent]", border_style="#5D5CFF"))


def cmd_graft() -> None:
    """Surgical Injection Protocol: Stitches Sprawl DNA onto an existing project."""
    cwd = os.getcwd()
    app_name = os.path.basename(cwd)
    local_agents_dir = os.path.join(cwd, ".agents")
    if not config.dry_run:
        os.makedirs(local_agents_dir, exist_ok=True)
        
    manifest_path = os.path.join(local_agents_dir, "sprawl_manifest.yml")

    if os.path.exists(manifest_path):
        raise SprawlError(f"A sprawl_manifest.yml already exists in {local_agents_dir}. Grafting aborted.")

    print_status(f"Grafting Sprawl DNA onto '{app_name}' at {cwd}...")

    from ..utils import CATEGORIES
    discovered_artifacts = {cat: [] for cat in CATEGORIES}

    # 1. Scan existing .agents/
    for category in CATEGORIES:
        cat_dir = os.path.join(local_agents_dir, category)
        if os.path.exists(cat_dir):
            for item in os.listdir(cat_dir):
                if not item.startswith("."):
                    discovered_artifacts[category].append(item)

    # 2. Heuristic discovery based on workspace root files
    if not discovered_artifacts["rules"]:
        if os.path.exists(os.path.join(cwd, "requirements.txt")) or os.path.exists(os.path.join(cwd, "pyproject.toml")):
            discovered_artifacts["rules"].append("python.md")
        if os.path.exists(os.path.join(cwd, "package.json")):
            discovered_artifacts["rules"].append("web-dev.md")
        if os.path.exists(os.path.join(cwd, "Cargo.toml")):
            discovered_artifacts["rules"].append("wasm.md")
            
        if not discovered_artifacts["rules"]:
            discovered_artifacts["rules"].append("engineering.md") # absolute fallback

    if not discovered_artifacts["skills"]:
        discovered_artifacts["skills"].append("web_artifacts_builder") # absolute fallback

    # 3. Detect MCP configuration
    if os.path.exists(os.path.join(cwd, "mcp_config.json")) or os.path.exists(os.path.join(local_agents_dir, "mcp_config.json")):
        if "sprawl-workspace-fs" not in discovered_artifacts["atoms"]:
            discovered_artifacts["atoms"].append("sprawl-workspace-fs")

    # Build the YAML manifest string
    content_lines = [f"# {app_name}", "dna: core", ""]
    for category in CATEGORIES:
        content_lines.append(f"{category}:")
        if discovered_artifacts[category]:
            for item in sorted(discovered_artifacts[category]):
                content_lines.append(f"  - {item}")
        content_lines.append("")

    manifest_content = "\n".join(content_lines)

    if config.verbose and config.dry_run:
        print_status(f"DRY RUN: Would surgically graft sprawl_manifest.yml into {local_agents_dir}")
        print_status("Generated manifest:\n" + manifest_content)
    elif not config.dry_run:
        with open(manifest_path, "w") as f:
            f.write(manifest_content)
        WorkspaceRegistry.register(app_name, cwd)
        print_status(f"Successfully grafted sprawl_manifest.yml into {local_agents_dir}. You can now update the manifest and run 'sprawl sync'.")

def cmd_ws_list() -> None:
    """Lists all tracked workspaces with their details."""
    workspaces = WorkspaceRegistry.get_all()
    if not workspaces:
        if config.json_logging:
            import json
            print(json.dumps([]))
            return
        print_status("No workspaces currently tracked in the registry.")
        return

    if config.json_logging:
        import json
        print(json.dumps([{"name": k, **v} for k, v in workspaces.items()]))
        return

    table = Table(title="[info]Tracked Workspaces[/info]", border_style="#5D5CFF")
    table.add_column("Status", justify="center")
    table.add_column("Name", style="accent", no_wrap=True)
    table.add_column("Path", style="info")
    table.add_column("DNA Binding", style="info")
    table.add_column("Last Sync", style="info")

    from datetime import datetime, timezone

    for name, data in workspaces.items():
        path = data.get("path", "Unknown")
        dna = data.get("dna_source") or "Global/Default"
        last_sync = data.get("last_sync_timestamp") or "Never"
        
        status = "[success]●[/success]" if os.path.exists(path) else "[error]○[/error]"
        
        sync_colored = last_sync
        if last_sync != "Never":
            try:
                dt = datetime.fromisoformat(last_sync)
                delta = datetime.now(timezone.utc) - dt
                if delta.days > 7:
                    sync_colored = f"[error]{last_sync}[/error]"
                elif delta.days > 3:
                    sync_colored = f"[warning]{last_sync}[/warning]"
                else:
                    sync_colored = f"[success]{last_sync}[/success]"
            except Exception:
                pass
        else:
            sync_colored = "[error]Never[/error]"
            
        table.add_row(status, name, path, dna, sync_colored)

    console.print(table)

def cmd_ws_remove(name: str, delete: bool = False) -> None:
    """Removes a workspace from the registry and optionally from disk.
    
    Args:
        name: Name of the workspace to remove.
        delete: Whether to also delete the directory.
    """
    try:
        ws_info = WorkspaceRegistry.get(name)
        if not ws_info:
            print_warning(f"Workspace '{name}' is not currently tracked.")
            return

        path = ws_info.get("path")
        WorkspaceRegistry.deregister(name)
        print_status(f"Workspace '{name}' has been deregistered.")
        
        if delete and path and os.path.exists(path):
            if not config.dry_run:
                shutil.rmtree(path)
            print_status(f"Workspace directory {path} has been deleted.")
            
    except SprawlError as e:
        raise e
    except Exception as e:
        raise SprawlError(f"Failed to remove workspace '{name}': {e}")

def cmd_ws_push(name: str = None) -> None:
    """Syncs DNA updates to all tracked workspaces or a specific one.
    
    Args:
        name: Optional name of a specific workspace to sync.
    """
    from .sync_cmd import cmd_sync
    workspaces = WorkspaceRegistry.get_all()
    
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
        except Exception as e:
            print_warning(f"Failed to sync workspace '{ws_name}': {e}")


