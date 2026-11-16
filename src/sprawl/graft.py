"""Universal workspace harvesting adapter framework.

Scans the root project directory for existing AI agent rules configuration files
and copies them as local-only rules inside the workspace registry.
"""

import abc
import os

from .output import print_status
from .validation import parse_yaml_frontmatter


class HarvestAdapter(abc.ABC):
    """Abstract base class for all harvest adapters."""

    @abc.abstractmethod
    def matches(self, root_dir: str) -> bool:
        """Return True if this adapter detects harvestable content in root_dir."""

    @abc.abstractmethod
    def harvest(self, root_dir: str, dest_dir: str) -> list[str]:
        """Harvest content from root_dir into dest_dir/rules/."""


_SPRAWL_DIRECTIVES = (
    "Agentic Workspace Directives",
    "Your behavior and knowledge base for this workspace",
)

_PROMPT_TYPE_TO_CATEGORY = {
    "skill": "skills",
    "workflow": "workflows",
}


class FileHarvestAdapter(HarvestAdapter):
    """Adapter for harvesting a single file-based legacy rules config."""

    def __init__(self, filename: str, target_key: str) -> None:
        self.filename = filename
        self.target_key = target_key

    def matches(self, root_dir: str) -> bool:
        path = os.path.join(root_dir, self.filename)
        return os.path.exists(path) and os.path.isfile(path)

    def harvest(self, root_dir: str, dest_dir: str) -> list[str]:
        src_path = os.path.join(root_dir, self.filename)
        if not os.path.exists(src_path):
            return []

        with open(src_path, encoding="utf-8", errors="ignore") as f:
            content = f.read()

        if any(sentinel in content for sentinel in _SPRAWL_DIRECTIVES) or not content.strip():
            return []

        local_name = f"local_{self.target_key}.md"
        dest_path = os.path.join(dest_dir, "rules", local_name)
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        with open(dest_path, "w", encoding="utf-8") as f:
            f.write(content)

        return [f"rules/{local_name}"]


def _strip_prompt_extension(filename: str) -> str:
    """Strips .prompt.md or .md suffix from a prompt filename."""
    if filename.endswith(".prompt.md"):
        return filename[:-10]
    if filename.endswith(".md"):
        return filename[:-3]
    return filename


def _harvest_prompt_file(file_path: str, filename: str, dest_dir: str) -> str | None:
    """Harvests a single .github/prompts/*.md file into dest_dir/<category>/."""
    if not (filename.endswith(".prompt.md") or filename.endswith(".md")):
        return None
    if not os.path.isfile(file_path):
        return None

    with open(file_path, encoding="utf-8", errors="ignore") as f:
        content = f.read()
    if not content.strip():
        return None

    base_name = _strip_prompt_extension(filename)
    frontmatter = parse_yaml_frontmatter(content)
    ft_type = str(frontmatter.get("type", "rule")).strip().lower()
    category = _PROMPT_TYPE_TO_CATEGORY.get(ft_type, "rules")

    local_name = f"local_{base_name}.md"
    dest_path = os.path.join(dest_dir, category, local_name)
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    with open(dest_path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"{category}/{local_name}"


class PromptsFolderAdapter(HarvestAdapter):
    """Adapter for harvesting .github/prompts/ folder contents."""

    def matches(self, root_dir: str) -> bool:
        prompts_dir = os.path.join(root_dir, ".github", "prompts")
        return os.path.exists(prompts_dir) and os.path.isdir(prompts_dir)

    def harvest(self, root_dir: str, dest_dir: str) -> list[str]:
        prompts_dir = os.path.join(root_dir, ".github", "prompts")
        if not os.path.exists(prompts_dir) or not os.path.isdir(prompts_dir):
            return []

        harvested_files: list[str] = []
        for file in os.listdir(prompts_dir):
            harvested = _harvest_prompt_file(os.path.join(prompts_dir, file), file, dest_dir)
            if harvested:
                harvested_files.append(harvested)
        return harvested_files


def harvest_legacy_rules(root_dir: str, dest_dir: str) -> list[str]:
    """Harvests existing rules/prompts configuration files from root_dir to dest_dir."""
    adapters: list[HarvestAdapter] = [
        FileHarvestAdapter(".cursorrules", "cursor"),
        FileHarvestAdapter(".clinerules", "cline"),
        FileHarvestAdapter(".windsurfrules", "windsurf"),
        FileHarvestAdapter(".github/copilot-instructions.md", "copilot"),
        FileHarvestAdapter("CLAUDE.md", "claude"),
        FileHarvestAdapter("AGENTS.md", "agent"),
        FileHarvestAdapter("DESIGN.md", "design"),
        PromptsFolderAdapter(),
    ]

    harvested_rules: list[str] = []
    for adapter in adapters:
        if adapter.matches(root_dir):
            harvested_rules.extend(adapter.harvest(root_dir, dest_dir))

    if harvested_rules:
        print_status(f"Harvested {len(harvested_rules)} legacy rules/prompts files into .agents/")

    return harvested_rules


BaseHarvestAdapter = FileHarvestAdapter
