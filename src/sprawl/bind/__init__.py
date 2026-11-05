"""IDE adapter binding engine — zero-trust multi-IDE integration layer.

Generates universal IDE bindings in the target workspace, routing all agents
to the .agents/ directory as the sovereign source of truth.

Supports:
  - Antigravity (.agent symlink + gemini.json workspace manifest)
  - Cursor (.cursorrules)
  - Cline / RooCode (.clinerules)
  - Windsurf (.windsurfrules)
  - GitHub Copilot (.github/copilot-instructions.md)

Use --force to overwrite any existing bindings.
"""

import os
import shutil

from ..output import console, print_error, print_status
from .adapters import ADAPTER_MAP, _bind_rules_symlink, _prune_empty_dirs, _write_symlink
from .antigravity import (
    _provision_antigravity_schemas,
    _remove_antigravity_schemas,
    _write_antigravity_gemini_json,
)
from .copilot import _export_category_to_prompts, _export_copilot_prompts

__all__ = ["bind_adapters", "_export_copilot_prompts", "_export_category_to_prompts"]


def _bind_active_targets(target_dir: str, targets: list[str], force: bool) -> list[bool]:
    """Provisions bindings for all selected adapter targets."""
    results: list[bool] = []
    for tkey in targets:
        adapter = ADAPTER_MAP[tkey]
        if adapter["type"] == "antigravity":
            ag_link = os.path.join(target_dir, ".agent")
            results.append(_write_symlink("Antigravity .agent", ag_link, ".agents", force))
            results.append(_write_antigravity_gemini_json(target_dir, force))
            results.append(_provision_antigravity_schemas())
        elif adapter["type"] == "symlink":
            rules_path = os.path.join(target_dir, adapter["path"])
            results.append(
                _bind_rules_symlink(
                    adapter["label"], rules_path, os.path.join(target_dir, "AGENTS.md"), force
                )
            )
            if tkey == "copilot":
                _export_copilot_prompts(target_dir)
    return results


def _remove_antigravity_bindings(target_dir: str, targets: list[str], verbose: bool) -> None:
    """Removes legacy .agent symlink and gemini.json when google-antigravity is excluded."""
    ag_link = os.path.join(target_dir, ".agent")
    if os.path.exists(ag_link) or os.path.islink(ag_link):
        try:
            os.remove(ag_link)
            console.print("  [info][-] Antigravity .agent Binding:[/info] Removed → .agent")
        except OSError as e:
            if verbose:
                console.print(f"  [dim]Debug: Failed to remove {ag_link}: {e}[/dim]")

    gemini_json_path = os.path.join(target_dir, ".gemini", "antigravity", "gemini.json")
    if os.path.exists(gemini_json_path):
        try:
            os.remove(gemini_json_path)
            console.print(
                "  [info][-] Antigravity gemini.json Binding:[/info] Removed → gemini.json"
            )
            _prune_empty_dirs(gemini_json_path)
        except OSError as e:
            if verbose:
                console.print(f"  [dim]Debug: Failed to remove {gemini_json_path}: {e}[/dim]")

    if targets and "antigravity" not in targets and "google-antigravity" not in targets:
        _remove_antigravity_schemas()


def _remove_symlink_binding(
    target_dir: str, tkey: str, adapter: dict[str, str], verbose: bool
) -> None:
    """Removes an excluded symlink adapter binding and any associated prompt directories."""
    rules_path = os.path.join(target_dir, adapter["path"])
    if os.path.exists(rules_path) or os.path.islink(rules_path):
        try:
            os.remove(rules_path)
            console.print(
                f"  [info][-] {adapter['label']} Binding:[/info] Removed → {adapter['path']}"
            )
            _prune_empty_dirs(rules_path)
        except OSError as e:
            if verbose:
                console.print(f"  [dim]Debug: Failed to remove {rules_path}: {e}[/dim]")
    if tkey == "copilot":
        prompts_dir = os.path.join(target_dir, ".github", "prompts")
        if os.path.exists(prompts_dir):
            try:
                shutil.rmtree(prompts_dir)
                console.print(
                    "  [info][-] GitHub Copilot Prompts:[/info] Removed prompts directory"
                )
                _prune_empty_dirs(os.path.join(prompts_dir, "dummy.txt"))
            except OSError as e:
                if verbose:
                    console.print(
                        f"  [dim]Debug: Failed to remove prompts directory {prompts_dir}: {e}[/dim]"
                    )


def _cleanup_excluded_targets(
    target_dir: str, targets: list[str], excluded_targets: list[str]
) -> None:
    """Removes bindings for adapters excluded from the target list."""
    from ..config import config

    for tkey in excluded_targets:
        adapter = ADAPTER_MAP[tkey]
        if adapter["type"] == "antigravity":
            _remove_antigravity_bindings(target_dir, targets, config.verbose)
        elif adapter["type"] == "symlink":
            _remove_symlink_binding(target_dir, tkey, adapter, config.verbose)


def bind_adapters(
    target_dir: str = ".", force: bool = False, targets: list[str] | None = None
) -> bool:
    """Generates selective or universal IDE/Agent bindings to the Sprawl .agents/ directory."""
    agents_dir = os.path.join(target_dir, ".agents")
    if not os.path.exists(agents_dir):
        print_error(
            f"Cannot bind: {agents_dir} not found. Is this an agentic workspace?\n"
            "Run 'sprawl init <URL>' or 'sprawl graft' first."
        )
        return False

    if targets is None:
        targets = list(ADAPTER_MAP.keys())
    else:
        from ..exceptions import SprawlError

        targets = [t.strip().lower() for t in targets]
        invalid_targets = [t for t in targets if t not in ADAPTER_MAP]
        if invalid_targets:
            raise SprawlError(f"Unsupported bind target(s): {', '.join(invalid_targets)}")

    mode_label = "[bold accent]FORCE[/bold accent]" if force else "standard"
    print_status(f"Generating IDE & Agent bindings ({mode_label} mode)...")

    results = _bind_active_targets(target_dir, targets, force)
    excluded_targets = [k for k in ADAPTER_MAP if k not in targets]
    _cleanup_excluded_targets(target_dir, targets, excluded_targets)

    written = sum(1 for r in results if r)
    total = len(results)
    if written > 0 or force:
        console.print(
            f"\n[success]✔ Binding complete:[/success] {written}/{total} adapters registered."
        )
    else:
        console.print(
            "\n[dim]Bindings are present, to configure you bindings run sprawl bind.[/dim]"
        )

    return True
