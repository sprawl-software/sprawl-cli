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
from ..output import print_status, print_error, console
from .adapters import ADAPTER_MAP, _bind_rules_symlink, _write_symlink, _prune_empty_dirs
from .antigravity import _write_antigravity_gemini_json, _provision_antigravity_schemas, _remove_antigravity_schemas
from .copilot import _export_copilot_prompts, _export_category_to_prompts



def bind_adapters(target_dir: str = ".", force: bool = False, targets: list[str] = None) -> bool:
    """Generates selective or universal IDE/Agent bindings to the Sprawl .agents/ directory.

    Args:
        target_dir: Workspace root directory to bind.
        force: If True, overwrites existing bindings.
        targets: Optional list of target adapter keys to bind.

    Returns:
        bool: True if all critical bindings succeeded.
    """
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
        # Normalize and validate target keys
        targets = [t.strip().lower() for t in targets]
        invalid_targets = [t for t in targets if t not in ADAPTER_MAP]
        if invalid_targets:
            raise SprawlError(f"Unsupported bind target(s): {', '.join(invalid_targets)}")

    mode_label = "[bold accent]FORCE[/bold accent]" if force else "standard"
    print_status(f"Generating IDE & Agent bindings ({mode_label} mode)...")

    results = []

    for tkey in targets:
        adapter = ADAPTER_MAP[tkey]
        if adapter["type"] == "antigravity":
            # 1. Antigravity .agent symlink
            ag_link = os.path.join(target_dir, ".agent")
            results.append(_write_symlink("Antigravity .agent", ag_link, ".agents", force))

            # 2. Antigravity gemini.json workspace manifest
            results.append(_write_antigravity_gemini_json(target_dir, force))

            # 3. Antigravity MCP tool schemas
            results.append(_provision_antigravity_schemas())
        elif adapter["type"] == "symlink":
            rules_path = os.path.join(target_dir, adapter["path"])
            results.append(_bind_rules_symlink(
                adapter["label"],
                rules_path,
                os.path.join(target_dir, "AGENTS.md"),
                force
            ))
            if tkey == "copilot":
                _export_copilot_prompts(target_dir)

    # Deletion of excluded bindings
    excluded_targets = [k for k in ADAPTER_MAP.keys() if k not in targets]
    from ..config import config
    for tkey in excluded_targets:
        adapter = ADAPTER_MAP[tkey]
        if adapter["type"] == "antigravity":
            # 1. Antigravity .agent symlink removal
            ag_link = os.path.join(target_dir, ".agent")
            if os.path.exists(ag_link) or os.path.islink(ag_link):
                try:
                    os.remove(ag_link)
                    console.print(f"  [info][-] Antigravity .agent Binding:[/info] Removed → .agent")
                except Exception as e:
                    if config.verbose:
                        console.print(f"  [dim]Debug: Failed to remove {ag_link}: {e}[/dim]")
            # 2. Antigravity gemini.json manifest removal
            gemini_json_path = os.path.join(target_dir, ".gemini", "antigravity", "gemini.json")
            if os.path.exists(gemini_json_path):
                try:
                    os.remove(gemini_json_path)
                    console.print(f"  [info][-] Antigravity gemini.json Binding:[/info] Removed → gemini.json")
                    _prune_empty_dirs(gemini_json_path)
                except Exception as e:
                    if config.verbose:
                        console.print(f"  [dim]Debug: Failed to remove {gemini_json_path}: {e}[/dim]")
            # 3. Antigravity MCP tool schemas removal
            _remove_antigravity_schemas()
        elif adapter["type"] == "symlink":
            rules_path = os.path.join(target_dir, adapter["path"])
            if os.path.exists(rules_path) or os.path.islink(rules_path):
                try:
                    os.remove(rules_path)
                    console.print(f"  [info][-] {adapter['label']} Binding:[/info] Removed → {adapter['path']}")
                    _prune_empty_dirs(rules_path)
                except Exception as e:
                    if config.verbose:
                        console.print(f"  [dim]Debug: Failed to remove {rules_path}: {e}[/dim]")
            if tkey == "copilot":
                # Clean up prompts folder
                prompts_dir = os.path.join(target_dir, ".github", "prompts")
                if os.path.exists(prompts_dir):
                    try:
                        shutil.rmtree(prompts_dir)
                        console.print("  [info][-] GitHub Copilot Prompts:[/info] Removed prompts directory")
                        _prune_empty_dirs(os.path.join(prompts_dir, "dummy.txt"))
                    except Exception as e:
                        if config.verbose:
                            console.print(f"  [dim]Debug: Failed to remove prompts directory {prompts_dir}: {e}[/dim]")

    # Summary
    written = sum(1 for r in results if r)
    total = len(results)
    if written > 0 or force:
        console.print(f"\n[success]✔ Binding complete:[/success] {written}/{total} adapters registered.")
    else:
        console.print("\n[dim]Bindings are present, to configure you bindings run sprawl bind.[/dim]")

    return True
