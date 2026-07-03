"""Universal workspace harvesting adapter framework.

Scans the root project directory for existing AI agent rules configuration files
and copies them as local-only rules inside the workspace registry.
"""

import abc
import os
from typing import List
from .output import print_status


class HarvestAdapter(abc.ABC):
    """Abstract base class for all harvest adapters.

    All adapters must implement matches() and harvest() with a consistent
    interface returning a list of harvested filenames.
    """

    @abc.abstractmethod
    def matches(self, root_dir: str) -> bool:
        """Return True if this adapter detects harvestable content in root_dir."""

    @abc.abstractmethod
    def harvest(self, root_dir: str, dest_dir: str) -> List[str]:
        """Harvest content from root_dir into dest_dir/rules/.

        Returns:
            List of harvested local rule filenames (e.g. ['local_cursor.md']).
        """


# Sentinel strings used to detect Sprawl's own generated workspace directives.
_SPRAWL_DIRECTIVES = (
    "Agentic Workspace Directives",
    "Your behavior and knowledge base for this workspace",
)


class FileHarvestAdapter(HarvestAdapter):
    """Adapter for harvesting a single file-based legacy rules config."""

    def __init__(self, filename: str, target_key: str):
        self.filename = filename
        self.target_key = target_key

    def matches(self, root_dir: str) -> bool:
        path = os.path.join(root_dir, self.filename)
        return os.path.exists(path) and os.path.isfile(path)

    def harvest(self, root_dir: str, dest_dir: str) -> List[str]:
        src_path = os.path.join(root_dir, self.filename)
        if not os.path.exists(src_path):
            return []

        with open(src_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        # Ignore our own generated workspace directives
        if any(sentinel in content for sentinel in _SPRAWL_DIRECTIVES):
            return []

        if not content.strip():
            return []

        local_name = f"local_{self.target_key}.md"
        dest_path = os.path.join(dest_dir, "rules", local_name)
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        with open(dest_path, "w", encoding="utf-8") as f:
            f.write(content)

        return [f"rules/{local_name}"]


class PromptsFolderAdapter(HarvestAdapter):
    """Adapter for harvesting .github/prompts/ folder contents."""

    def matches(self, root_dir: str) -> bool:
        prompts_dir = os.path.join(root_dir, ".github", "prompts")
        return os.path.exists(prompts_dir) and os.path.isdir(prompts_dir)

    def harvest(self, root_dir: str, dest_dir: str) -> List[str]:
        prompts_dir = os.path.join(root_dir, ".github", "prompts")
        harvested_files = []
        if not os.path.exists(prompts_dir) or not os.path.isdir(prompts_dir):
            return harvested_files

        from .validation import parse_yaml_frontmatter

        for file in os.listdir(prompts_dir):
            if file.endswith(".prompt.md") or file.endswith(".md"):
                file_path = os.path.join(prompts_dir, file)
                if os.path.isfile(file_path):
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()

                    if not content.strip():
                        continue

                    base_name = file
                    if base_name.endswith(".prompt.md"):
                        base_name = base_name[:-10]
                    elif base_name.endswith(".md"):
                        base_name = base_name[:-3]

                    frontmatter = parse_yaml_frontmatter(content)
                    ft_type = str(frontmatter.get("type", "rule")).strip().lower()
                    
                    if ft_type == "skill":
                        category = "skills"
                    elif ft_type == "workflow":
                        category = "workflows"
                    else:
                        category = "rules"

                    local_name = f"local_{base_name}.md"
                    dest_path = os.path.join(dest_dir, category, local_name)
                    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                    with open(dest_path, "w", encoding="utf-8") as f:
                        f.write(content)
                    harvested_files.append(f"{category}/{local_name}")

        return harvested_files


def harvest_legacy_rules(root_dir: str, dest_dir: str) -> List[str]:
    """Harvests existing rules/prompts configuration files from root_dir to dest_dir."""
    adapters: List[HarvestAdapter] = [
        FileHarvestAdapter(".cursorrules", "cursor"),
        FileHarvestAdapter(".clinerules", "cline"),
        FileHarvestAdapter(".windsurfrules", "windsurf"),
        FileHarvestAdapter(".github/copilot-instructions.md", "copilot"),
        FileHarvestAdapter("CLAUDE.md", "claude"),
        FileHarvestAdapter("AGENTS.md", "agent"),
        FileHarvestAdapter("DESIGN.md", "design"),
        PromptsFolderAdapter(),
    ]

    harvested_rules = []

    for adapter in adapters:
        if adapter.matches(root_dir):
            harvested_rules.extend(adapter.harvest(root_dir, dest_dir))

    if harvested_rules:
        print_status(f"Harvested {len(harvested_rules)} legacy rules/prompts files into .agents/")

    return harvested_rules


# Backward compatibility aliases
BaseHarvestAdapter = FileHarvestAdapter
