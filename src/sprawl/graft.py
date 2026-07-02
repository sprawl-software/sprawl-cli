"""Universal workspace harvesting adapter framework.

Scans the root project directory for existing AI agent rules configuration files
and copies them as local-only rules inside the workspace registry.
"""

import os
from typing import List, Optional
from .output import print_status


class BaseHarvestAdapter:
    def __init__(self, filename: str, target_key: str):
        self.filename = filename
        self.target_key = target_key

    def matches(self, root_dir: str) -> bool:
        path = os.path.join(root_dir, self.filename)
        return os.path.exists(path) and os.path.isfile(path)

    def harvest(self, root_dir: str, dest_dir: str) -> Optional[str]:
        src_path = os.path.join(root_dir, self.filename)
        if not os.path.exists(src_path):
            return None

        with open(src_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        # Ignore our own generated workspace directives
        if "Agentic Workspace Directives" in content or "Your behavior and knowledge base for this workspace" in content:
            return None

        if not content.strip():
            return None

        local_name = f"local_{self.target_key}.md"
        dest_path = os.path.join(dest_dir, "rules", local_name)
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        with open(dest_path, "w", encoding="utf-8") as f:
            f.write(content)

        return local_name


class PromptsFolderAdapter:
    def matches(self, root_dir: str) -> bool:
        prompts_dir = os.path.join(root_dir, ".github", "prompts")
        return os.path.exists(prompts_dir) and os.path.isdir(prompts_dir)

    def harvest(self, root_dir: str, dest_dir: str) -> List[str]:
        prompts_dir = os.path.join(root_dir, ".github", "prompts")
        harvested_files = []
        if not os.path.exists(prompts_dir) or not os.path.isdir(prompts_dir):
            return harvested_files

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

                    local_name = f"local_{base_name}.md"
                    dest_path = os.path.join(dest_dir, "rules", local_name)
                    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                    with open(dest_path, "w", encoding="utf-8") as f:
                        f.write(content)
                    harvested_files.append(local_name)

        return harvested_files


def harvest_legacy_rules(root_dir: str, dest_dir: str) -> List[str]:
    """Harvests existing rules/prompts configuration files from root_dir to dest_dir."""
    adapters = [
        BaseHarvestAdapter(".cursorrules", "cursor"),
        BaseHarvestAdapter(".clinerules", "cline"),
        BaseHarvestAdapter(".windsurfrules", "windsurf"),
        BaseHarvestAdapter(".github/copilot-instructions.md", "copilot"),
        BaseHarvestAdapter("CLAUDE.md", "claude"),
        BaseHarvestAdapter("AGENT.md", "agent"),
        BaseHarvestAdapter("DESIGN.md", "design"),
    ]

    harvested_rules = []

    for adapter in adapters:
        if adapter.matches(root_dir):
            local_name = adapter.harvest(root_dir, dest_dir)
            if local_name:
                harvested_rules.append(local_name)

    folder_adapter = PromptsFolderAdapter()
    if folder_adapter.matches(root_dir):
        files = folder_adapter.harvest(root_dir, dest_dir)
        harvested_rules.extend(files)

    if harvested_rules:
        print_status(f"Harvested {len(harvested_rules)} legacy rules/prompts files into .agents/rules/")

    return harvested_rules
