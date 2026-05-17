"""Generator for AGENTS.md — Clean Room architecture compliant."""

from typing import Dict, List, Optional


def generate_agents_md(
    output_path: str,
    reqs: Dict[str, List[str]],
    workspace_path: str,
    persona_content: Optional[str] = None
) -> None:
    """Generates a clean AGENTS.md file with persona and capability mapping.

    Args:
        output_path: Path where AGENTS.md will be written.
        reqs: Dictionary of required artifacts by category.
        workspace_path: Absolute path to the workspace root.
        persona_content: Optional raw content of a persona SKILL.md.
    """
    lines = []

    if persona_content:
        lines.append("# Persona Overrides")
        lines.append("")
        lines.append("Your identity for this workspace is defined by the following persona definition. Adopt its tone, expertise, and behavioral protocols absolutely.")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append(persona_content.strip())
        lines.append("")
        lines.append("---")
        lines.append("")
    else:
        lines.append("# Workspace Agent Context")
        lines.append("")
        lines.append("You are operating within a sandboxed environment. Your primary role is to assist the user by utilizing the tools and rules defined in this workspace.")
        lines.append("")

    lines.append("## Environment Boundaries")
    lines.append("")
    lines.append(f"**Workspace Root:** `{workspace_path}`")
    lines.append("")
    lines.append("1. **Strict Isolation:** You MUST NOT attempt to read or write files outside of the Workspace Root.")
    lines.append("2. **Path Resolution:** All relative paths mentioned in this workspace must be resolved relative to the Workspace Root.")
    lines.append("3. **Context Leakage:** Do not reference your internal training data for project-specific facts; rely entirely on the artifacts provided in this sandbox.")
    lines.append("")

    lines.append("## Workspace Capability Mapping")
    lines.append("")
    lines.append("The following capabilities have been explicitly loaded into your environment. Refer to the corresponding files in `.agents/` for detailed documentation and protocols.")
    lines.append("")

    for category, items in reqs.items():
        # Clean category name (e.g., "rules" -> "Rules")
        display_name = category.capitalize()
        lines.append(f"### {display_name}")
        
        if not items:
            lines.append("- *(None)*")
        else:
            for item in sorted(items):
                lines.append(f"- {item}")
        lines.append("")

    with open(output_path, "w") as f:
        f.write("\n".join(lines))
