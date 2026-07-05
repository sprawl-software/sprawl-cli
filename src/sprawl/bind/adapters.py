import os
from typing import Optional
from ..output import console

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
    """Writes a text binding file."""
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


def _find_workspace_root(path: str) -> Optional[str]:
    """Finds the workspace root by searching upwards for a .agents directory."""
    current = os.path.abspath(path)
    while True:
        if os.path.isdir(os.path.join(current, ".agents")):
            return os.path.realpath(current)
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    return None


def _is_safe_symlink_target(link_path: str, target: str) -> bool:
    """Verifies if the symlink target resolves strictly inside the workspace containing link_path."""
    workspace_root = _find_workspace_root(link_path)
    if not workspace_root:
        return True  # Allow outside-of-workspace symlinks if no .agents context exists (e.g. testing)

    abs_target = os.path.realpath(os.path.join(os.path.dirname(link_path), target))
    real_root = os.path.realpath(workspace_root)
    return abs_target == real_root or abs_target.startswith(real_root + os.sep)


def _write_symlink(label: str, link_path: str, target: str, force: bool) -> bool:
    """Creates a symlink binding."""
    if not _is_safe_symlink_target(link_path, target):
        console.print(f"  [error]✗ {label} Binding:[/error] Security Violation: Target '{target}' resolves outside workspace root.")
        return False

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


def _bind_rules_symlink(
    label: str,
    rules_path: str,
    agents_md_path: str,
    force: bool,
) -> bool:
    """Binds a rules path as a symlink to AGENTS.md, falling back to copy if needed."""
    if (os.path.exists(rules_path) or os.path.islink(rules_path)) and not force:
        console.print(f"  [dim]○ {label} Binding:[/dim] already exists (use --force to overwrite)")
        return False

    os.makedirs(os.path.dirname(rules_path), exist_ok=True)
    
    # Calculate target path of the symlink (relative to the directory of rules_path)
    rel_target = os.path.relpath(agents_md_path, os.path.dirname(rules_path))
    
    if not _is_safe_symlink_target(rules_path, rel_target):
        console.print(f"  [error]✗ {label} Binding:[/error] Security Violation: Target '{rel_target}' resolves outside workspace root.")
        return False

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
    except Exception as e:
        from ..config import config
        if config.verbose:
            console.print(f"  [dim]Debug: Failed to prune directory {dir_name}: {e}[/dim]")

