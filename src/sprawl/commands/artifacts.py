"""Artifact discovery, injection, scaffolding, and removal commands."""

import json
import os
import re
from typing import Any

from rich.panel import Panel
from rich.text import Text
from rich.tree import Tree

from ..config import config
from ..exceptions import SprawlError
from ..output import console, print_error, print_status, print_warning
from ..utils import CATEGORIES, get_active_dna_context
from ._helpers import resolve_item_in_dna
from .sync_cmd import cmd_sync


def _build_installed_contexts_text(source_dna_dir: str) -> Text:
    """Builds the Rich Text summary of installed DNA contexts and the active context."""
    contexts_text = Text("\nInstalled Contexts:\n", style="info")
    global_dna = config.agents_dir_global
    if os.path.exists(global_dna) and os.path.isdir(global_dna):
        contexts_text.append("  • @global (Default Sprawl Hub DNA)\n", style="accent")

    registry_dir = config.dna_registry_dir
    if os.path.exists(registry_dir) and os.path.isdir(registry_dir):
        for alias in sorted(os.listdir(registry_dir)):
            if os.path.isdir(os.path.join(registry_dir, alias)):
                contexts_text.append(f"  • @{alias}\n", style="accent")

    contexts_text.append("\nActive Context: ", style="info")
    contexts_text.append(f"{source_dna_dir}", style="accent")
    return contexts_text


def _collect_dna_artifact_groups(source_dna_dir: str) -> dict[str, list[str]]:
    """Groups active DNA artifacts into Personas, Rules, Skills, Atoms, and Workflows."""
    data: dict[str, list[str]] = {
        "Personas": [],
        "Rules": [],
        "Skills": [],
        "Atoms": [],
        "Workflows": [],
    }
    for category in CATEGORIES:
        category_dir = os.path.join(source_dna_dir, category)
        if not os.path.exists(category_dir):
            continue
        for item in sorted(os.listdir(category_dir)):
            if category == "skills" and item.startswith("persona-"):
                data["Personas"].append(item)
            else:
                data[category.capitalize()].append(item)
    return data


def cmd_list() -> None:
    """Discovery Engine: Scans the active DNA registry and lists all available artifacts."""
    source_dna_dir = get_active_dna_context()
    if not os.path.exists(source_dna_dir):
        print_error(f"DNA context not found at {source_dna_dir}. Have you run sprawl init?")
        return

    contexts_text = _build_installed_contexts_text(source_dna_dir)
    if config.json_logging:
        print(json.dumps({"level": "info", "message": contexts_text.plain}))
        return

    console.print()
    console.print(Panel(contexts_text, title="[info]DNA Registry[/info]", border_style="#222326"))
    console.print()

    data = _collect_dna_artifact_groups(source_dna_dir)
    tree = Tree(f"🧬 Active DNA Artifacts [dim]({source_dna_dir})[/dim]", guide_style="accent")
    for category, items in data.items():
        if items:
            branch = tree.add(f"[info]{category}[/info]")
            for item in items:
                branch.add(item)

    console.print(tree)
    console.print()


def _compile_manifest_from_selection(
    manifest_data: dict[str, Any],
    selection: dict[str, list[str]],
) -> str:
    """Serializes updated category selections and existing top-level keys into YAML."""
    dna_val = manifest_data.get("dna", "core")
    new_manifest: list[str] = [f"dna: {dna_val}\n"]

    for category in CATEGORIES:
        new_manifest.append(f"{category}:")
        for item in selection.get(category, []):
            new_manifest.append(f"  - {item}")
        new_manifest.append("")

    for key, val in manifest_data.items():
        if key in CATEGORIES or key == "dna":
            continue
        if isinstance(val, list):
            new_manifest.append(f"{key}:")
            for item in val:
                new_manifest.append(f"  - {item}")
        else:
            new_manifest.append(f"{key}: {val}")
        new_manifest.append("")

    return "\n".join(new_manifest)


def _run_interactive_add_tui(workspace_root: str, manifest_path: str) -> None:
    """Launches the interactive checkbox TUI to configure workspace DNA items."""
    from ..utils.registry_scanner import RegistryScanner
    from ..utils.tui import show_checkbox_menu
    from ..validation import parse_yaml_frontmatter

    scanner = RegistryScanner(workspace_root)
    selection = show_checkbox_menu("DNA Configuration", scanner.scan())
    if selection is None:
        print_status("Add command cancelled.")
        return

    with open(manifest_path, encoding="utf-8") as f:
        content = f.read()

    manifest_data = parse_yaml_frontmatter(f"---\n{content}\n---")
    manifest_text = _compile_manifest_from_selection(manifest_data, selection)

    print_status("Modifying sprawl_manifest.yml...")
    if not config.dry_run:
        with open(manifest_path, "w", encoding="utf-8") as f:
            f.write(manifest_text)

    print_status("Injecting DNA...")
    if not config.dry_run:
        cmd_sync(workspace_root)

    print_status("DNA successfully synchronized.")


def _resolve_requested_additions(
    items: list[str],
    source_dna_dir: str,
) -> dict[str, list[str]]:
    """Resolves wildcard '*' or named items against source_dna_dir categories."""
    additions: dict[str, list[str]] = {cat: [] for cat in CATEGORIES}
    if "*" in items:
        for category in CATEGORIES:
            category_dir = os.path.join(source_dna_dir, category)
            if os.path.exists(category_dir):
                additions[category].extend(
                    item for item in sorted(os.listdir(category_dir)) if not item.startswith(".")
                )
        return additions

    for item in items:
        category, resolved_name = resolve_item_in_dna(item, source_dna_dir)
        if category and resolved_name:
            additions[category].append(resolved_name)
        else:
            raise SprawlError(
                f"Item '{item}' not found in any category within the active DNA context."
            )
    return additions


def _inject_additions_into_manifest(
    content: str,
    additions: dict[str, list[str]],
) -> str:
    """Inserts resolved artifact names under their respective YAML category headers."""
    for category, new_items in additions.items():
        if not new_items:
            continue
        pattern = re.compile(rf"^({category}:.*)$", re.IGNORECASE | re.MULTILINE)
        match = pattern.search(content)
        if not match:
            continue
        insert_pos = match.end()
        insert_str = ""
        for item in new_items:
            if f"- {item}" not in content:
                insert_str += f"\n  - {item}"
                print_status(f"Resolving dependency: '{item}' into [{category}]")
        content = content[:insert_pos] + insert_str + content[insert_pos:]
    return content


def _print_sandboxed_receipts(additions: dict[str, list[str]]) -> None:
    """Prints completion receipts for each injected artifact."""
    for category, new_items in additions.items():
        cat_name = category[:-1].capitalize() if category.endswith("s") else category.capitalize()
        for item in new_items:
            print_status(f"[+] {cat_name} '{item}' successfully sandboxed.")


def cmd_add(items: list[str], target_dir: str | None = None) -> None:
    """Smart Injection Engine: Infers the category and injects items into the workspace."""
    workspace_root = os.path.abspath(target_dir) if target_dir else os.getcwd()
    source_dna_dir = get_active_dna_context()

    if not os.path.exists(source_dna_dir):
        raise SprawlError(f"DNA context not found at {source_dna_dir}. Have you run sprawl init?")

    manifest_path = os.path.join(workspace_root, ".agents", "sprawl_manifest.yml")
    if not os.path.exists(manifest_path):
        raise SprawlError(f"No sprawl_manifest.yml found at {manifest_path}.")

    if not items:
        _run_interactive_add_tui(workspace_root, manifest_path)
        return

    additions = _resolve_requested_additions(items, source_dna_dir)
    with open(manifest_path, encoding="utf-8") as f:
        content = f.read()

    updated_content = _inject_additions_into_manifest(content, additions)
    if not config.dry_run:
        with open(manifest_path, "w", encoding="utf-8") as f:
            f.write(updated_content)

    print_status("Modifying sprawl_manifest.yml...")
    print_status("Injecting DNA...")
    if not config.dry_run:
        cmd_sync(workspace_root)

    _print_sandboxed_receipts(additions)


def cmd_scaffold(type_str: str, name: str) -> None:
    """Automated Boilerplate Scaffolding Engine."""
    source_dna_dir = get_active_dna_context()

    if not os.path.exists(source_dna_dir):
        raise SprawlError(f"DNA context not found at {source_dna_dir}. Have you run sprawl init?")

    if ".." in name or "/" in name or "\\" in name:
        raise SprawlError(
            "Security Violation: Artifact name cannot contain path traversal characters."
        )
    if not re.match(r"^[a-zA-Z0-9_\- ]+$", name):
        raise SprawlError(
            "Security Violation: Artifact name must be alphanumeric, spaces, underscores, or hyphens only."
        )

    if type_str != "persona":
        print_warning(f"Scaffolding for type '{type_str}' is not yet implemented.")
        return

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
    with open(skill_file, "w", encoding="utf-8") as f:
        f.write(template)

    print_status(f"Persona Scaffolded successfully: '{folder_name}'")
    print_status(f"Generated boilerplate at {skill_file}")


def cmd_remove(items: list[str]) -> None:
    """Symmetrical Removal Engine: Removes dependencies from the workspace manifest."""
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
            print_warning(
                f"Item '{item}' not found in active DNA context. Proceeding to blindly attempt removal from manifest."
            )
            removals.append(item)

    with open(manifest_path, encoding="utf-8") as f:
        lines = f.read().splitlines()

    removal_set = {f"- {target}": target for target in removals}
    new_lines: list[str] = []
    removed_count = 0

    for line in lines:
        matched_target = removal_set.get(line.strip())
        if matched_target is not None:
            print_status(f"Removing dependency: '{matched_target}'")
            removed_count += 1
        else:
            new_lines.append(line)

    if removed_count == 0:
        print_warning("No matching items found in sprawl_manifest.yml to remove.")
        return

    with open(manifest_path, "w", encoding="utf-8") as f:
        f.write("\n".join(new_lines) + "\n")

    print_status("Manifest updated. Triggering synchronization cleanup...")
    cmd_sync(os.getcwd())
