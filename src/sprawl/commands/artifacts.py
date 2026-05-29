"""Artifact discovery, injection, scaffolding, and removal commands."""

import os
import re
import json
from typing import Optional

from rich.panel import Panel
from rich.text import Text
from rich.tree import Tree

from ..config import config
from ..output import print_status, print_warning, print_error, console
from ..utils import CATEGORIES, get_active_dna_context
from ..exceptions import SprawlError
from ._helpers import resolve_item_in_dna
from .sync_cmd import cmd_sync


def cmd_list() -> None:
    """Discovery Engine: Scans the active DNA registry and lists all available artifacts."""
    source_dna_dir = get_active_dna_context()

    if not os.path.exists(source_dna_dir):
        print_error(f"DNA context not found at {source_dna_dir}. Have you run sprawl init?")
        return

    # List available DNA Contexts
    contexts_text = Text("\nInstalled Contexts:\n", style="info")
    global_dna = config.agents_dir_global
    if os.path.exists(global_dna) and os.path.isdir(global_dna):
        contexts_text.append("  • @global (Default Sprawl Hub DNA)\n", style="accent")

    registry_dir = config.dna_registry_dir
    if os.path.exists(registry_dir) and os.path.isdir(registry_dir):
        aliases = sorted(os.listdir(registry_dir))
        for alias in aliases:
            if os.path.isdir(os.path.join(registry_dir, alias)):
                contexts_text.append(f"  • @{alias}\n", style="accent")

    contexts_text.append("\nActive Context: ", style="info")
    contexts_text.append(f"{source_dna_dir}", style="accent")

    if config.json_logging:
        print(json.dumps({"level": "info", "message": contexts_text.plain}))
        return

    console.print()
    console.print(Panel(contexts_text, title="[info]DNA Registry[/info]", border_style="#222326"))
    console.print()

    # Gather Artifacts
    data: dict[str, list[str]] = {"Personas": [], "Rules": [], "Skills": [], "Atoms": [], "Workflows": []}
    for category in CATEGORIES:
        category_dir = os.path.join(source_dna_dir, category)
        if os.path.exists(category_dir):
            items = sorted(os.listdir(category_dir))
            for item in items:
                if category == "skills" and item.startswith("persona-"):
                    data["Personas"].append(item)
                else:
                    data[category.capitalize()].append(item)

    # Render Tree
    tree = Tree(f"🧬 Active DNA Artifacts [dim]({source_dna_dir})[/dim]", guide_style="accent")
    for category, items in data.items():
        if items:
            branch = tree.add(f"[info]{category}[/info]")
            for item in items:
                branch.add(item)

    console.print(tree)
    console.print()


def cmd_add(items: list[str], target_dir: Optional[str] = None) -> None:
    """Smart Injection Engine: Infers the category and injects items into the workspace.

    Args:
        items: List of artifact names to add.
        target_dir: Optional workspace root directory. Defaults to cwd.
    """
    workspace_root = os.path.abspath(target_dir) if target_dir else os.getcwd()
    source_dna_dir = get_active_dna_context()

    if not os.path.exists(source_dna_dir):
        raise SprawlError(f"DNA context not found at {source_dna_dir}. Have you run sprawl init?")

    manifest_path = os.path.join(workspace_root, ".agents", "sprawl_manifest.yml")
    if not os.path.exists(manifest_path):
        raise SprawlError(f"No sprawl_manifest.yml found at {manifest_path}.")

    if not items:
        # Keyboard-Interactive Checkbox TUI Selection Menu
        from ..utils.registry_scanner import RegistryScanner
        from ..utils.tui import show_checkbox_menu
        from ..validation import parse_yaml_frontmatter

        scanner = RegistryScanner(workspace_root)
        categories_data = scanner.scan()

        selection = show_checkbox_menu("DNA Configuration", categories_data)
        if selection is None:
            print_status("Add command cancelled.")
            return

        # Read existing manifest to preserve non-category values
        with open(manifest_path, "r") as f:
            content = f.read()

        manifest_data = parse_yaml_frontmatter(f"---\n{content}\n---")
        dna_val = manifest_data.get("dna", "core")

        # Compile new manifest content in YAML
        new_manifest = []
        new_manifest.append(f"dna: {dna_val}\n")

        for category in CATEGORIES:
            new_manifest.append(f"{category}:")
            selected_items = selection.get(category, [])
            if selected_items:
                for item in selected_items:
                    new_manifest.append(f"  - {item}")
            new_manifest.append("")

        # Append any other top-level keys not in CATEGORIES + ['dna']
        for k, v in manifest_data.items():
            if k not in CATEGORIES and k != "dna":
                if isinstance(v, list):
                    new_manifest.append(f"{k}:")
                    for item in v:
                        new_manifest.append(f"  - {item}")
                else:
                    new_manifest.append(f"{k}: {v}")
                new_manifest.append("")

        manifest_text = "\n".join(new_manifest)

        print_status("Modifying sprawl_manifest.yml...")
        if not config.dry_run:
            with open(manifest_path, "w") as f:
                f.write(manifest_text)

        print_status("Injecting DNA...")
        if not config.dry_run:
            cmd_sync(workspace_root)

        print_status("DNA successfully synchronized.")
        return

    additions: dict[str, list[str]] = {cat: [] for cat in CATEGORIES}

    if "*" in items:
        for category in CATEGORIES:
            category_dir = os.path.join(source_dna_dir, category)
            if os.path.exists(category_dir):
                for item in sorted(os.listdir(category_dir)):
                    if not item.startswith("."):
                        additions[category].append(item)
    else:
        for item in items:
            category, resolved_name = resolve_item_in_dna(item, source_dna_dir)
            if resolved_name:
                additions[category].append(resolved_name)
            else:
                raise SprawlError(f"Item '{item}' not found in any category within the active DNA context.")

    with open(manifest_path, "r") as f:
        content = f.read()

    for category, new_items in additions.items():
        if not new_items:
            continue

        pattern = re.compile(rf"^({category}:.*)$", re.IGNORECASE | re.MULTILINE)
        match = pattern.search(content)
        if match:
            insert_pos = match.end()
            insert_str = ""
            for item in new_items:
                if f"- {item}" not in content:
                    insert_str += f"\n  - {item}"
                    print_status(f"Resolving dependency: '{item}' into [{category}]")
            content = content[:insert_pos] + insert_str + content[insert_pos:]

    if not config.dry_run:
        with open(manifest_path, "w") as f:
            f.write(content)

    print_status("Modifying sprawl_manifest.yml...")
    print_status("Injecting DNA...")

    if not config.dry_run:
        cmd_sync(workspace_root)

    for category, new_items in additions.items():
        for item in new_items:
            cat_name = category[:-1].capitalize() if category.endswith("s") else category.capitalize()
            print_status(f"[+] {cat_name} '{item}' successfully sandboxed.")



def cmd_scaffold(type_str: str, name: str) -> None:
    """Automated Boilerplate Scaffolding Engine.

    Args:
        type_str: Type of artifact to scaffold (persona, rule, skill, etc.).
        name: Human-readable name of the artifact.
    """
    source_dna_dir = get_active_dna_context()

    if not os.path.exists(source_dna_dir):
        raise SprawlError(f"DNA context not found at {source_dna_dir}. Have you run sprawl init?")

    if ".." in name or "/" in name or "\\" in name:
        raise SprawlError("Security Violation: Artifact name cannot contain path traversal characters.")
    if not re.match(r"^[a-zA-Z0-9_\- ]+$", name):
        raise SprawlError("Security Violation: Artifact name must be alphanumeric, spaces, underscores, or hyphens only.")

    if type_str == "persona":
        name_snake = name.lower().replace(" ", "_")
        folder_name = f"persona-{name_snake}"
        target_dir = os.path.join(source_dna_dir, "skills", folder_name)

        if os.path.exists(target_dir):
            raise SprawlError(f"Persona '{folder_name}' already exists at {target_dir}")

        os.makedirs(target_dir)
        skill_file = os.path.join(target_dir, "SKILL.md")

        template = f"""---
name: {name}
description: Lens override for the {name} persona.
---

# System Prompt
[Insert persona definition here]

# Thesis
[Insert core thesis/worldview here]

# Evaluation Protocol
[Insert rules for evaluating outputs through this lens]
"""
        with open(skill_file, "w") as f:
            f.write(template)

        print_status(f"Persona Scaffolded successfully: '{folder_name}'")
        print_status(f"Generated boilerplate at {skill_file}")
    else:
        print_warning(f"Scaffolding for type '{type_str}' is not yet implemented.")


def cmd_remove(items: list[str]) -> None:
    """Symmetrical Removal Engine: Removes dependencies from the workspace manifest.

    Args:
        items: List of artifact names to remove.
    """
    source_dna_dir = get_active_dna_context()

    manifest_path = os.path.join(os.getcwd(), ".agents", "sprawl_manifest.yml")
    if not os.path.exists(manifest_path):
        raise SprawlError(f"No sprawl_manifest.yml found at {manifest_path}.")

    removals: list[str] = []

    for item in items:
        _, resolved_name = resolve_item_in_dna(item, source_dna_dir)
        if resolved_name:
            removals.append(resolved_name)
        else:
            print_warning(f"Item '{item}' not found in active DNA context. Proceeding to blindly attempt removal from manifest.")
            removals.append(item)

    with open(manifest_path, "r") as f:
        content = f.read()
    lines = content.splitlines()
    new_lines: list[str] = []
    removed_count = 0

    for line in lines:
        stripped = line.strip()
        should_remove = False
        for target in removals:
            if stripped == f"- {target}":
                should_remove = True
                print_status(f"Removing dependency: '{target}'")
                removed_count += 1
                break
        if not should_remove:
            new_lines.append(line)

    if removed_count == 0:
        print_warning("No matching items found in sprawl_manifest.yml to remove.")
        return

    with open(manifest_path, "w") as f:
        f.write("\n".join(new_lines) + "\n")

    print_status("Manifest updated. Triggering synchronization cleanup...")
    cmd_sync(os.getcwd())
