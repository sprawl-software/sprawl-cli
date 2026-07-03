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

Your behavior and knowledge base for this workspace are defined in the `AGENTS.md` file and the `.agents/` directory.

**MANDATORY INSTRUCTIONS:**
1. Before taking any action, you MUST read `AGENTS.md` at the workspace root.
2. If a persona is defined in `AGENTS.md`, you must adopt its tone, expertise, and behavioral protocols absolutely.
3. When asked to execute a workflow, check `.agents/workflows/` for the exact step-by-step procedure.
4. If a specific skill or capability is mentioned, check `.agents/skills/` for the relevant documentation.

Follow the conventions and protocols defined in `AGENTS.md` and `.agents/` without deviation.
"""


ADAPTER_MAP = {
    "claude-code": {
        "label": "Claude Code",
        "path": "CLAUDE.md",
        "type": "symlink"
    },
    "gemini-cli": {
        "label": "Gemini CLI",
        "path": "GEMINI.md",
        "type": "symlink"
    },
    "google-antigravity": {
        "label": "Google Antigravity",
        "type": "antigravity"
    },
    "copilot": {
        "label": "GitHub Copilot",
        "path": os.path.join(".github", "copilot-instructions.md"),
        "type": "symlink"
    },
    "cursor": {
        "label": "Cursor",
        "path": ".cursorrules",
        "type": "symlink"
    },
    "windsurf": {
        "label": "Windsurf",
        "path": ".windsurfrules",
        "type": "symlink"
    },
    "codex": {
        "label": "Codex",
        "path": os.path.join("rules", ".rules"),
        "type": "symlink"
    },
    "intellij": {
        "label": "IntelliJ",
        "path": os.path.join(".aiassistant", "rules", "agents.md"),
        "type": "symlink"
    },
    "jupyter": {
        "label": "Jupyter Notebooks",
        "path": ".jupyterrules",
        "type": "symlink"
    },
    "vscode": {
        "label": "VS Code",
        "path": ".vscoderules",
        "type": "symlink"
    },
    "vscodium": {
        "label": "VS Codium",
        "path": ".vscodiumrules",
        "type": "symlink"
    },
    "cline-roo": {
        "label": "RooCode/Cline",
        "path": ".clinerules",
        "type": "symlink"
    },
    "zed": {
        "label": "Zed",
        "path": ".zedrules",
        "type": "symlink"
    },
    "opencode": {
        "label": "OpenCode",
        "path": os.path.join(".opencode", "rules", "agents.md"),
        "type": "symlink"
    }
}


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


def _bind_rules_symlink(
    label: str,
    rules_path: str,
    agents_md_path: str,
    force: bool,
) -> bool:
    """Binds a rules path as a symlink to AGENTS.md, falling back to copy if needed.

    Args:
        label: Human-readable name.
        rules_path: Absolute path to the rules file (e.g. CLAUDE.md).
        agents_md_path: Absolute path to the AGENTS.md file.
        force: Whether to overwrite existing rules.

    Returns:
        bool: True if created successfully, False otherwise.
    """
    if (os.path.exists(rules_path) or os.path.islink(rules_path)) and not force:
        console.print(f"  [dim]○ {label} Binding:[/dim] already exists (use --force to overwrite)")
        return False

    os.makedirs(os.path.dirname(rules_path), exist_ok=True)
    
    # Calculate target path of the symlink (relative to the directory of rules_path)
    rel_target = os.path.relpath(agents_md_path, os.path.dirname(rules_path))
    
    # Try to create symlink
    try:
        if os.path.exists(rules_path) or os.path.islink(rules_path):
            os.remove(rules_path)
        os.symlink(rel_target, rules_path)
        action = "Overwritten symlink" if force else "Created symlink"
        console.print(f"  [success]✔ {label} Binding:[/success] {action} → {rel_target}")
        return True
    except OSError:
        # Fallback to copy content of AGENTS.md
        try:
            content = _RULES_CONTENT
            if os.path.exists(agents_md_path):
                with open(agents_md_path, "r", encoding="utf-8") as f:
                    content = f.read()
            
            if os.path.exists(rules_path) or os.path.islink(rules_path):
                os.remove(rules_path)
                
            with open(rules_path, "w", encoding="utf-8") as f:
                f.write(content)
            action = "Overwritten copy (fallback)" if force else "Created copy (fallback)"
            console.print(f"  [success]✔ {label} Binding:[/success] {action} → {os.path.basename(rules_path)}")
            return True
        except Exception as e:
            console.print(f"  [error]✗ {label} Binding:[/error] Failed: {e}")
            return False


def _prune_empty_dirs(path: str) -> None:
    """Recursively prunes empty directories up to the workspace root."""
    try:
        dir_name = os.path.dirname(path)
        if os.path.isdir(dir_name) and not os.listdir(dir_name):
            os.rmdir(dir_name)
            _prune_empty_dirs(dir_name)
    except Exception:
        pass


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
        from .exceptions import SprawlError
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
    import shutil
    for tkey in excluded_targets:
        adapter = ADAPTER_MAP[tkey]
        if adapter["type"] == "antigravity":
            # 1. Antigravity .agent symlink removal
            ag_link = os.path.join(target_dir, ".agent")
            if os.path.exists(ag_link) or os.path.islink(ag_link):
                try:
                    os.remove(ag_link)
                    console.print(f"  [info][-] Antigravity .agent Binding:[/info] Removed → .agent")
                except Exception:
                    pass
            # 2. Antigravity gemini.json manifest removal
            gemini_json_path = os.path.join(target_dir, ".gemini", "antigravity", "gemini.json")
            if os.path.exists(gemini_json_path):
                try:
                    os.remove(gemini_json_path)
                    console.print(f"  [info][-] Antigravity gemini.json Binding:[/info] Removed → gemini.json")
                    _prune_empty_dirs(gemini_json_path)
                except Exception:
                    pass
        elif adapter["type"] == "symlink":
            rules_path = os.path.join(target_dir, adapter["path"])
            if os.path.exists(rules_path) or os.path.islink(rules_path):
                try:
                    os.remove(rules_path)
                    console.print(f"  [info][-] {adapter['label']} Binding:[/info] Removed → {adapter['path']}")
                    _prune_empty_dirs(rules_path)
                except Exception:
                    pass
            if tkey == "copilot":
                # Clean up prompts folder
                prompts_dir = os.path.join(target_dir, ".github", "prompts")
                if os.path.exists(prompts_dir):
                    try:
                        shutil.rmtree(prompts_dir)
                        console.print("  [info][-] GitHub Copilot Prompts:[/info] Removed prompts directory")
                        _prune_empty_dirs(os.path.join(prompts_dir, "dummy.txt"))
                    except Exception:
                        pass

    # Summary
    written = sum(1 for r in results if r)
    total = len(results)
    if written > 0 or force:
        console.print(f"\n[success]✔ Binding complete:[/success] {written}/{total} adapters registered.")
    else:
        console.print("\n[dim]Bindings are present, to configure you bindings run sprawl bind.[/dim]")

    return True


def _export_category_to_prompts(
    category_dir: str,
    prompts_dir: str,
    check_skill_subdirs: bool = False,
) -> None:
    """Exports .md files from a category directory into .github/prompts/*.prompt.md files.

    Args:
        category_dir: Absolute path to the category directory (skills/ or workflows/).
        prompts_dir: Absolute path to the .github/prompts/ output directory.
        check_skill_subdirs: If True, also checks subdirectories for SKILL.md entry points.
    """
    if not os.path.exists(category_dir):
        return

    for item in os.listdir(category_dir):
        if item.startswith("."):
            continue
        item_path = os.path.join(category_dir, item)

        content = None
        name = None

        if os.path.isfile(item_path) and item.endswith(".md"):
            with open(item_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            name = item[:-3]
        elif check_skill_subdirs and os.path.isdir(item_path):
            skill_md = os.path.join(item_path, "SKILL.md")
            if os.path.exists(skill_md):
                with open(skill_md, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
            name = item

        if content and name:
            os.makedirs(prompts_dir, exist_ok=True)
            prompt_file = os.path.join(prompts_dir, f"{name}.prompt.md")
            try:
                with open(prompt_file, "w", encoding="utf-8") as f:
                    f.write(content)
                print_status(f"Exported Copilot prompt: .github/prompts/{name}.prompt.md")
            except Exception as e:
                from .output import print_warning
                print_warning(f"Failed to export prompt {name}: {e}")


def _export_copilot_prompts(target_dir: str) -> None:
    """Compiles local skills and workflows into .github/prompts/*.prompt.md files."""
    agents_dir = os.path.join(target_dir, ".agents")
    prompts_dir = os.path.join(target_dir, ".github", "prompts")

    # Clean up stale prompt files before re-exporting
    if os.path.exists(prompts_dir):
        for f in os.listdir(prompts_dir):
            if f.endswith(".prompt.md"):
                try:
                    os.remove(os.path.join(prompts_dir, f))
                except Exception:
                    pass

    # Export skills (with SKILL.md subdir support) and workflows
    _export_category_to_prompts(
        os.path.join(agents_dir, "skills"), prompts_dir, check_skill_subdirs=True,
    )
    _export_category_to_prompts(
        os.path.join(agents_dir, "workflows"), prompts_dir, check_skill_subdirs=False,
    )

