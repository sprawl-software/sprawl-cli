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

import json
import os
from .output import print_status, print_error, console

_RULES_CONTENT = """\
# Agentic Workspace Directives

Your behavior and knowledge base for this workspace are defined in the `agent.md` file and the `.agents/` directory.

**MANDATORY INSTRUCTIONS:**
1. Before taking any action, you MUST read `agent.md` at the workspace root.
2. If a persona is defined in `agent.md`, you must adopt its tone, expertise, and behavioral protocols absolutely.
3. When asked to execute a workflow, check `.agents/workflows/` for the exact step-by-step procedure.
4. If a specific skill or capability is mentioned, check `.agents/skills/` for the relevant documentation.

Follow the conventions and protocols defined in `agent.md` and `.agents/` without deviation.
"""


def _write_binding(
    label: str,
    target_path: str,
    content: str,
    force: bool,
) -> bool:
    """Writes a text binding file.

    Args:
        label: Human-readable name for the adapter (e.g. 'Cursor').
        target_path: Absolute path to write.
        content: Content to write.
        force: Whether to overwrite if exists.

    Returns:
        bool: True if written, False if skipped.
    """
    if os.path.exists(target_path) and not force:
        console.print(f"  [dim]○ {label} Binding:[/dim] already exists (use --force to overwrite)")
        return False
    try:
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        with open(target_path, "w") as f:
            f.write(content)
        action = "Overwritten" if os.path.exists(target_path) and force else "Created"
        console.print(f"  [success]✔ {label} Binding:[/success] {action} → {os.path.basename(target_path)}")
        return True
    except Exception as e:
        console.print(f"  [error]✗ {label} Binding:[/error] Failed: {e}")
        return False


def _write_symlink(label: str, link_path: str, target: str, force: bool) -> bool:
    """Creates a symlink binding.

    Args:
        label: Human-readable name.
        link_path: Path where symlink should live.
        target: Symlink target (relative).
        force: Whether to overwrite if exists.

    Returns:
        bool: True if created, False if skipped.
    """
    if os.path.exists(link_path) or os.path.islink(link_path):
        if not force:
            console.print(f"  [dim]○ {label} Binding:[/dim] already exists (use --force to overwrite)")
            return False
        os.remove(link_path)

    try:
        os.symlink(target, link_path)
        console.print(f"  [success]✔ {label} Binding:[/success] Created symlink → {target}")
        return True
    except Exception as e:
        console.print(f"  [error]✗ {label} Binding:[/error] Failed: {e}")
        return False


def _write_antigravity_gemini_json(target_dir: str, force: bool) -> bool:
    """Generates .gemini/antigravity/gemini.json for Antigravity workspace detection.

    This file signals to the Antigravity IDE extension that this workspace
    uses Sprawl-managed agents from `.agents/`.

    Args:
        target_dir: Workspace root directory.
        force: Whether to overwrite if exists.

    Returns:
        bool: True if written.
    """
    gemini_dir = os.path.join(target_dir, ".gemini", "antigravity")
    gemini_json_path = os.path.join(gemini_dir, "gemini.json")

    agents_abs = os.path.abspath(os.path.join(target_dir, ".agents"))

    manifest = {
        "sprawl": {
            "version": "2.0",
            "agents_dir": agents_abs,
            "managed": True,
        }
    }

    content = json.dumps(manifest, indent=2)
    return _write_binding("Antigravity gemini.json", gemini_json_path, content, force)


def bind_adapters(target_dir: str = ".", force: bool = False) -> bool:
    """Generates IDE/Agent bindings to the Sprawl .agents/ directory.

    Args:
        target_dir: Workspace root directory to bind.
        force: If True, overwrites existing bindings.

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

    mode_label = "[bold accent]FORCE[/bold accent]" if force else "standard"
    print_status(f"Generating IDE & Agent bindings ({mode_label} mode)...")

    results = []

    # 1. Antigravity .agent symlink
    ag_link = os.path.join(target_dir, ".agent")
    results.append(_write_symlink("Antigravity .agent", ag_link, ".agents", force))

    # 2. Antigravity gemini.json workspace manifest
    results.append(_write_antigravity_gemini_json(target_dir, force))

    # 3. Cursor
    results.append(_write_binding(
        "Cursor",
        os.path.join(target_dir, ".cursorrules"),
        _RULES_CONTENT,
        force,
    ))

    # 4. Cline / RooCode
    results.append(_write_binding(
        "RooCode/Cline",
        os.path.join(target_dir, ".clinerules"),
        _RULES_CONTENT,
        force,
    ))

    # 5. Windsurf
    results.append(_write_binding(
        "Windsurf",
        os.path.join(target_dir, ".windsurfrules"),
        _RULES_CONTENT,
        force,
    ))

    # 6. GitHub Copilot
    results.append(_write_binding(
        "GitHub Copilot",
        os.path.join(target_dir, ".github", "copilot-instructions.md"),
        _RULES_CONTENT,
        force,
    ))

    # Summary
    written = sum(1 for r in results if r)
    total = len(results)
    if written > 0 or force:
        console.print(f"\n[success]✔ Binding complete:[/success] {written}/{total} adapters registered.")
    else:
        console.print("\n[dim]All bindings already present. Use --force to refresh.[/dim]")

    return True
