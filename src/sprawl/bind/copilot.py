"""GitHub Copilot prompt export routines."""

import os
import shutil
from ..output import print_status, print_warning


def _export_category_to_prompts(
    category_dir: str,
    prompts_dir: str,
    check_skill_subdirs: bool = False,
) -> None:
    """Exports .md files from a category directory into .github/prompts/*.prompt.md files."""
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
