"""Sync orchestration and IDE binding commands."""

import os
import sys
from typing import Any

from rich.panel import Panel

from ..config import config
from ..exceptions import SprawlError
from ..output import console, operation_spinner, print_status
from ..sync import sync_app_directory
from ..utils import CATEGORIES
from ..validation import parse_yaml_frontmatter


def _render_sync_summary_panel(stats: dict[str, Any], bindings: bool) -> None:
    """Prints the Rich Workspace Orchestration completion panel."""
    text = (
        "[success]✔ Sync Complete[/success]\n"
        f"• Files Synced: {stats['copied']}\n"
        f"• Files Pruned: {stats['pruned']}\n"
        f"• Venv Provisioned: {'Yes' if stats['venv_provisioned'] else 'Existing'}\n"
        f"• Bindings Created: {'Yes' if bindings else 'No'}"
    )
    console.print()
    console.print(
        Panel(text, title="[accent]Workspace Orchestration[/accent]", border_style="#5D5CFF")
    )


def _sync_single_workspace(target_path: str) -> None:
    """Runs sync_app_directory and cmd_bind for a single workspace path."""
    with operation_spinner(f"Syncing workspace at {target_path}"):
        stats = sync_app_directory(target_path)
        bindings = cmd_bind(target_path, is_sync=True)
    if stats:
        _render_sync_summary_panel(stats, bindings)


def _resolve_targeted_sync_dir(target_dir: str | None) -> str | None:
    """Resolves explicit target_dir or current working directory if initialized."""
    if target_dir:
        return os.path.abspath(target_dir)
    if os.path.exists(os.path.join(os.getcwd(), ".agents", "sprawl_manifest.yml")):
        return os.getcwd()
    return None


def _sync_hub_recursively() -> None:
    """Syncs all workspace subdirectories inside config.sprawl_dir."""
    if config.verbose:
        print_status(f"Running sync in RECURSIVE MODE inside {config.sprawl_dir}...")

    if not os.path.isdir(config.sprawl_dir):
        raise SprawlError(
            f"Sprawl Hub directory not found at {config.sprawl_dir}. "
            "Run from inside a workspace containing '.agents/sprawl_manifest.yml' to use targeted mode."
        )

    for item in os.listdir(config.sprawl_dir):
        item_path = os.path.join(config.sprawl_dir, item)
        if os.path.isdir(item_path):
            _sync_single_workspace(item_path)


def cmd_sync(target_dir: str | None = None) -> None:
    """File Orchestration Protocol: Syncs DNA into local workspace scope."""
    cwd = _resolve_targeted_sync_dir(target_dir)
    if cwd:
        if config.verbose:
            print_status(f"Running sync in TARGETED MODE at {cwd}.")
        _sync_single_workspace(cwd)
        return

    _sync_hub_recursively()


def _append_yaml_list_block(lines: list[str], key: str, items: list[Any]) -> None:
    """Appends a YAML key and indented list items followed by a blank line."""
    lines.append(f"{key}:")
    for item in items:
        lines.append(f"  - {item}")
    lines.append("")


def _append_extra_manifest_keys(
    lines: list[str],
    manifest_data: dict[str, Any],
    reserved_keys: set[str],
) -> None:
    """Appends non-standard top-level YAML keys from manifest_data."""
    for key, val in manifest_data.items():
        if key in reserved_keys:
            continue
        if isinstance(val, list):
            _append_yaml_list_block(lines, key, val)
        else:
            lines.append(f"{key}: {val}")
            lines.append("")


def _as_list(value: Any) -> list[Any]:
    """Returns value if it is a list, otherwise an empty list."""
    return value if isinstance(value, list) else []


def _append_standard_categories(lines: list[str], manifest_data: dict[str, Any]) -> None:
    """Appends standard CATEGORIES and optional local_rules sections."""
    for category in CATEGORIES:
        _append_yaml_list_block(lines, category, _as_list(manifest_data.get(category)))

    local_rules = _as_list(manifest_data.get("local_rules"))
    if local_rules:
        _append_yaml_list_block(lines, "local_rules", local_rules)


def update_manifest_bindings(target_dir: str, targets: list[str]) -> None:
    """Updates the `bindings:` section inside .agents/sprawl_manifest.yml."""
    manifest_path = os.path.join(target_dir, ".agents", "sprawl_manifest.yml")
    if not os.path.exists(manifest_path):
        return

    with open(manifest_path, encoding="utf-8") as f:
        content = f.read()

    manifest_data = parse_yaml_frontmatter(f"---\n{content}\n---")
    dna_val = manifest_data.get("dna", "core")
    new_manifest: list[str] = [f"dna: {dna_val}\n"]

    _append_standard_categories(new_manifest, manifest_data)
    _append_yaml_list_block(new_manifest, "bindings", sorted(targets))
    reserved_keys = set(CATEGORIES) | {"dna", "local_rules", "bindings"}
    _append_extra_manifest_keys(new_manifest, manifest_data, reserved_keys)

    with open(manifest_path, "w", encoding="utf-8") as f:
        f.write("\n".join(new_manifest))


def _read_manifest_bindings(manifest_path: str) -> list[str] | None:
    """Reads and normalizes the `bindings` list from sprawl_manifest.yml if defined."""
    if not os.path.exists(manifest_path):
        return None
    try:
        with open(manifest_path, encoding="utf-8") as f:
            content = f.read()
        manifest_data = parse_yaml_frontmatter(f"---\n{content}\n---")
    except (OSError, ValueError, TypeError):
        return None

    if "bindings" not in manifest_data:
        return None
    val = manifest_data["bindings"]
    if val is None or str(val).strip() in ("[]", "", "none"):
        return []
    if isinstance(val, list):
        return [str(b).strip().lower() for b in val if str(b).strip() and str(b).strip() != "[]"]
    return [str(val).strip().lower()]


def _prompt_interactive_bindings(
    categories: dict[str, list[tuple[str, bool]]],
) -> dict[str, list[str]] | None:
    """Prompts the user via checkbox TUI or numbered fallback when stdin is a TTY."""
    from ..utils.tui import is_tui_supported, prompt_numbered_selection, show_checkbox_menu

    if sys.stdout.isatty() and is_tui_supported():
        try:
            return show_checkbox_menu("Select IDE & Agent Adapters", categories)
        except (OSError, ValueError, RuntimeError) as e:
            console.print(
                f"[warning]Interactive graphical menu unavailable ({e}). Falling back to numbered prompt...[/warning]"
            )
    return prompt_numbered_selection("Select IDE & Agent Adapters", categories)


def _resolve_bind_targets(
    target_dir: str,
    adapter_keys: list[str],
    manifest_bindings: list[str] | None,
    only: str | None,
    all_adapters: bool,
    is_sync: bool,
) -> list[str] | None:
    """Determines which IDE adapter keys to bind and persists updates to the manifest."""
    if only:
        targets = [t.strip() for t in only.split(",")]
        update_manifest_bindings(target_dir, targets)
        return targets

    if all_adapters:
        update_manifest_bindings(target_dir, adapter_keys)
        return adapter_keys

    if is_sync or not sys.stdin.isatty():
        if manifest_bindings is not None:
            return manifest_bindings
        update_manifest_bindings(target_dir, adapter_keys)
        return adapter_keys

    categories = {
        "IDE / AI Agent Integrations": [
            (key, manifest_bindings is None or key in manifest_bindings) for key in adapter_keys
        ]
    }
    selection = _prompt_interactive_bindings(categories)
    if selection is None:
        print_status("Binding cancelled.")
        return None

    targets = selection.get("IDE / AI Agent Integrations", [])
    update_manifest_bindings(target_dir, targets)
    return targets


def cmd_bind(
    target_dir: str | None = None,
    force: bool = False,
    all_adapters: bool = False,
    only: str | None = None,
    is_sync: bool = False,
) -> bool:
    """Generates selective or universal IDE/Agent bindings."""
    resolved_dir = target_dir or os.getcwd()
    from ..bind import ADAPTER_MAP, bind_adapters

    agents_dir = os.path.join(resolved_dir, ".agents")
    manifest_path = os.path.join(agents_dir, "sprawl_manifest.yml")
    if not os.path.exists(agents_dir) and not is_sync:
        from ..output import print_warning

        print_warning(f"No '.agents' governance directory found in {resolved_dir}.")
        console.print(
            "[muted]Tip: Run [accent]sprawl init <dna-repo>[/accent] (or [accent]sprawl init[/accent] with no URL for demo rules) to configure governance.[/muted]\n"
        )

    manifest_bindings = _read_manifest_bindings(manifest_path)
    targets = _resolve_bind_targets(
        resolved_dir,
        list(ADAPTER_MAP.keys()),
        manifest_bindings,
        only,
        all_adapters,
        is_sync,
    )
    if targets is None:
        return False

    return bind_adapters(resolved_dir, force=force, targets=targets)
