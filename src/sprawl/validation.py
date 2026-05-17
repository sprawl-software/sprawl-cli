"""Sprawl CLI Validation — Zero-Trust DNA validation with stdlib-only schemas.

Replaces pydantic BaseModel schemas with dataclasses + manual validation.
Replaces pyyaml with a regex-based YAML frontmatter parser.
External dependencies: NONE (pure stdlib).
"""

import os
import json
import re
from dataclasses import dataclass
from typing import Any

from .output import print_warning, print_error, print_status
from .exceptions import SprawlError


# ---------------------------------------------------------------------------
# Stdlib YAML Frontmatter Parser (replaces pyyaml)
# ---------------------------------------------------------------------------

def parse_yaml_frontmatter(content: str) -> dict[str, Any]:
    """Parses YAML frontmatter from a markdown file using pure stdlib.

    Handles simple key: value pairs and list values (- item).
    Does NOT support nested YAML structures — intentionally minimal.

    Args:
        content: Raw file content string.

    Returns:
        Dictionary of parsed frontmatter key-value pairs.
    """
    if not content.startswith("---"):
        return {}

    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}

    frontmatter_raw = parts[1].strip()
    if not frontmatter_raw:
        return {}

    result: dict[str, Any] = {}
    current_key: str | None = None

    for line in frontmatter_raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        # List item under current key
        list_match = re.match(r"^-\s+(.+)$", stripped)
        if list_match and current_key is not None:
            if not isinstance(result.get(current_key), list):
                result[current_key] = []
            result[current_key].append(list_match.group(1).strip())
            continue

        # Key: value pair
        kv_match = re.match(r"^([a-zA-Z_][\w-]*)\s*:\s*(.*)$", stripped)
        if kv_match:
            key = kv_match.group(1)
            value = kv_match.group(2).strip()
            current_key = key

            if not value:
                # Could be a list header or empty value
                result[key] = ""
            elif value.lower() in ("true", "yes"):
                result[key] = True
            elif value.lower() in ("false", "no"):
                result[key] = False
            elif value.lower() in ("null", "none", "~"):
                result[key] = None
            else:
                # Try numeric conversion
                try:
                    result[key] = int(value)
                except ValueError:
                    try:
                        result[key] = float(value)
                    except ValueError:
                        # Strip optional quotes
                        if (value.startswith('"') and value.endswith('"')) or \
                           (value.startswith("'") and value.endswith("'")):
                            value = value[1:-1]
                        result[key] = value
            continue

    return result


# ---------------------------------------------------------------------------
# Dataclass Schemas (replaces pydantic BaseModel)
# ---------------------------------------------------------------------------

@dataclass
class AtomSchema:
    """Schema for validating Atom artifacts in the DNA registry."""
    name: str
    description: str
    type: str

    def validate(self) -> None:
        """Manual validation — raises ValueError on invalid state."""
        for field_name in ("name", "description", "type"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"AtomSchema: '{field_name}' must be a non-empty string, got: {value!r}")


@dataclass
class SkillSchema:
    """Schema for validating Skill artifacts in the DNA registry."""
    name: str
    description: str

    def validate(self) -> None:
        """Manual validation — raises ValueError on invalid state."""
        for field_name in ("name", "description"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"SkillSchema: '{field_name}' must be a non-empty string, got: {value!r}")


@dataclass
class MoleculeSchema:
    """Schema for validating Molecule artifacts in the DNA registry."""
    name: str
    version: str
    atoms: list[str]

    def validate(self) -> None:
        """Manual validation — raises ValueError on invalid state."""
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError(f"MoleculeSchema: 'name' must be a non-empty string, got: {self.name!r}")
        if not isinstance(self.version, str) or not self.version.strip():
            raise ValueError(f"MoleculeSchema: 'version' must be a non-empty string, got: {self.version!r}")
        if not isinstance(self.atoms, list):
            raise ValueError(f"MoleculeSchema: 'atoms' must be a list, got: {type(self.atoms).__name__}")


# ---------------------------------------------------------------------------
# DNA Directory Validation Engine
# ---------------------------------------------------------------------------

def validate_dna_directory(dna_dir: str) -> None:
    """Validates all incoming .md, .yml, .yaml, and .json files in a DNA directory.

    Uses dataclass schemas with manual validation (stdlib-only, no pydantic).

    Args:
        dna_dir: Path to the DNA directory to validate.

    Raises:
        SprawlError: If any validation errors are found.
    """
    print_status("Running Zero-Trust validation on DNA...")
    errors: list[str] = []

    for root, _, files in os.walk(dna_dir):
        if ".git" in root:
            continue
        for file in files:
            filepath = os.path.join(root, file)
            try:
                if file.endswith(".json"):
                    with open(filepath, "r") as f:
                        data = json.load(f)
                    if "atoms" in root:
                        schema = AtomSchema(**data)
                        schema.validate()
                    elif "molecules" in root:
                        schema = MoleculeSchema(**data)
                        schema.validate()
                elif file.endswith((".yaml", ".yml")):
                    # Generic structure check — just verify it's parseable
                    with open(filepath, "r") as f:
                        content = f.read()
                    parse_yaml_frontmatter(f"---\n{content}\n---")
                elif file.endswith(".md"):
                    with open(filepath, "r") as f:
                        content = f.read()
                    frontmatter = parse_yaml_frontmatter(content)
                    if "skills" in root and file == "SKILL.md":
                        schema = SkillSchema(
                            name=frontmatter.get("name", ""),
                            description=frontmatter.get("description", "")
                        )
                        schema.validate()
            except ValueError as e:
                errors.append(f"Validation failed for {filepath}: {e}")
            except Exception as e:
                errors.append(f"Could not parse {filepath}: {e}")

    if errors:
        for err in errors:
            print_error(err)
        raise SprawlError("Zero-Trust DNA Validation failed. The fetched DNA is corrupted or malicious.")
    print_status("DNA Validation passed.")
