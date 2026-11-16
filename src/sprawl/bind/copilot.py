"""GitHub Copilot prompt export routines."""

import contextlib
import os

from ..output import print_status, print_warning


def _read_prompt_candidate(
    item_path: str,
    item: str,
    check_skill_subdirs: bool,
) -> tuple[str | None, str | None]:
    """Resolves (prompt_name, markdown_content) from a file or SKILL.md subdirectory."""
    if os.path.isfile(item_path) and item.endswith(".md"):
        with open(item_path, encoding="utf-8", errors="ignore") as f:
            return item[:-3], f.read()
    if check_skill_subdirs and os.path.isdir(item_path):
        skill_md = os.path.join(item_path, "SKILL.md")
        if os.path.exists(skill_md):
            with open(skill_md, encoding="utf-8", errors="ignore") as f:
                return item, f.read()
    return None, None


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
        name, content = _read_prompt_candidate(item_path, item, check_skill_subdirs)
        if not (content and name):
            continue

        os.makedirs(prompts_dir, exist_ok=True)
        prompt_file = os.path.join(prompts_dir, f"{name}.prompt.md")
        try:
            with open(prompt_file, "w", encoding="utf-8") as f:
                f.write(content)
            print_status(f"Exported Copilot prompt: .github/prompts/{name}.prompt.md")
        except OSError as e:
            print_warning(f"Failed to export prompt {name}: {e}")


def _export_copilot_prompts(target_dir: str) -> None:
    """Compiles local skills and workflows into .github/prompts/*.prompt.md files."""
    agents_dir = os.path.join(target_dir, ".agents")
    prompts_dir = os.path.join(target_dir, ".github", "prompts")

    if os.path.exists(prompts_dir):
        for f in os.listdir(prompts_dir):
            if f.endswith(".prompt.md"):
                with contextlib.suppress(OSError):
                    os.remove(os.path.join(prompts_dir, f))

    _export_category_to_prompts(
        os.path.join(agents_dir, "skills"),
        prompts_dir,
        check_skill_subdirs=True,
    )
    _export_category_to_prompts(
        os.path.join(agents_dir, "workflows"),
        prompts_dir,
        check_skill_subdirs=False,
    )
