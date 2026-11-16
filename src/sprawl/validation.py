"""Sprawl CLI Validation — Zero-Trust DNA validation with stdlib-only schemas.

Replaces pydantic BaseModel schemas with dataclasses + manual validation.
Replaces pyyaml with a regex-based YAML frontmatter parser.
External dependencies: NONE (pure stdlib).
"""

import json
import os
import re
from dataclasses import dataclass, fields
from typing import Any

from .exceptions import SprawlError
from .output import print_error, print_status

_LIST_ITEM_RE = re.compile(r"^-\s+(.+)$")
_KEY_VALUE_RE = re.compile(r"^([a-zA-Z_][\w-]*)\s*:\s*(.*)$")


def _strip_matching_quotes(value: str) -> str:
    """Strips surrounding single or double quotes when present."""
    if len(value) >= 2 and (
        (value.startswith('"') and value.endswith('"'))
        or (value.startswith("'") and value.endswith("'"))
    ):
        return value[1:-1]
    return value


def _parse_yaml_scalar(value: str) -> Any:
    """Coerces a raw YAML scalar token into bool, None, int, float, or str."""
    if not value:
        return ""
    lowered = value.lower()
    if lowered in ("true", "yes"):
        return True
    if lowered in ("false", "no"):
        return False
    if lowered in ("null", "none", "~"):
        return None
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return _strip_matching_quotes(value)


def parse_yaml_frontmatter(content: str) -> dict[str, Any]:
    """Parses YAML frontmatter from a markdown file using pure stdlib."""
    if not content.startswith("---"):
        return {}

    parts = content.split("---", 2)
    if len(parts) < 3 or not parts[1].strip():
        return {}

    result: dict[str, Any] = {}
    current_key: str | None = None

    for line in parts[1].strip().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        list_match = _LIST_ITEM_RE.match(stripped)
        if list_match and current_key is not None:
            if not isinstance(result.get(current_key), list):
                result[current_key] = []
            result[current_key].append(list_match.group(1).strip())
            continue

        kv_match = _KEY_VALUE_RE.match(stripped)
        if kv_match:
            current_key = kv_match.group(1)
            result[current_key] = _parse_yaml_scalar(kv_match.group(2).strip())

    return result


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
                raise ValueError(
                    f"AtomSchema: '{field_name}' must be a non-empty string, got: {value!r}"
                )


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
                raise ValueError(
                    f"SkillSchema: '{field_name}' must be a non-empty string, got: {value!r}"
                )


@dataclass
class MoleculeSchema:
    """Schema for validating Molecule artifacts in the DNA registry."""

    name: str
    version: str
    atoms: list[str]

    def validate(self) -> None:
        """Manual validation — raises ValueError on invalid state."""
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError(
                f"MoleculeSchema: 'name' must be a non-empty string, got: {self.name!r}"
            )
        if not isinstance(self.version, str) or not self.version.strip():
            raise ValueError(
                f"MoleculeSchema: 'version' must be a non-empty string, got: {self.version!r}"
            )
        if not isinstance(self.atoms, list):
            raise ValueError(
                f"MoleculeSchema: 'atoms' must be a list, got: {type(self.atoms).__name__}"
            )


def _validate_atom_json(data: dict[str, Any], filename: str) -> None:
    """Validates an Atom JSON payload against AtomSchema."""
    allowed_fields = {f.name for f in fields(AtomSchema)}
    filtered = {k: v for k, v in data.items() if k in allowed_fields}
    name = (
        filtered["name"]
        if filtered.get("name") is not None
        else (data.get("title") or os.path.splitext(filename)[0])
    )
    desc = filtered["description"] if filtered.get("description") is not None else ""
    atype = filtered["type"] if filtered.get("type") is not None else "object"
    AtomSchema(name=name, description=desc, type=atype).validate()


def _validate_molecule_json(data: dict[str, Any], filename: str) -> None:
    """Validates a Molecule JSON payload against MoleculeSchema (skipping raw MCP configs)."""
    if "mcpServers" in data and "atoms" not in data:
        return
    allowed_fields = {f.name for f in fields(MoleculeSchema)}
    filtered = {k: v for k, v in data.items() if k in allowed_fields}
    name = filtered["name"] if filtered.get("name") is not None else os.path.splitext(filename)[0]
    version = filtered["version"] if filtered.get("version") is not None else "1.0.0"
    atoms = filtered["atoms"] if filtered.get("atoms") is not None else []
    MoleculeSchema(name=name, version=version, atoms=atoms).validate()


def _validate_json_file(filepath: str, root: str, file: str) -> None:
    """Parses and validates a JSON DNA file."""
    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)
    if "atoms" in root:
        _validate_atom_json(data, file)
    elif "molecules" in root:
        _validate_molecule_json(data, file)


def _validate_markdown_file(filepath: str, root: str, file: str) -> None:
    """Parses markdown frontmatter and validates SKILL.md schemas."""
    with open(filepath, encoding="utf-8") as f:
        content = f.read()
    frontmatter = parse_yaml_frontmatter(content)
    if "skills" in root and file == "SKILL.md":
        SkillSchema(
            name=frontmatter.get("name", ""),
            description=frontmatter.get("description", ""),
        ).validate()


def _validate_single_dna_file(filepath: str, root: str, file: str) -> str | None:
    """Validates a single DNA file and returns an error string if invalid."""
    try:
        if file.endswith(".json"):
            _validate_json_file(filepath, root, file)
        elif file.endswith((".yaml", ".yml")):
            with open(filepath, encoding="utf-8") as f:
                parse_yaml_frontmatter(f"---\n{f.read()}\n---")
        elif file.endswith(".md"):
            _validate_markdown_file(filepath, root, file)
        return None
    except json.JSONDecodeError as e:
        return f"Could not parse {filepath}: {e}"
    except ValueError as e:
        return f"Validation failed for {filepath}: {e}"
    except OSError as e:
        return f"Could not parse {filepath}: {e}"


def validate_dna_directory(dna_dir: str) -> None:
    """Validates all incoming .md, .yml, .yaml, and .json files in a DNA directory."""
    print_status("Running Zero-Trust validation on DNA...")
    errors: list[str] = []

    for root, _, files in os.walk(dna_dir):
        if ".git" in root:
            continue
        for file in files:
            err = _validate_single_dna_file(os.path.join(root, file), root, file)
            if err:
                errors.append(err)

    if errors:
        for err in errors:
            print_error(err)
        raise SprawlError(
            "Zero-Trust DNA Validation failed. The fetched DNA is corrupted or malicious."
        )
    print_status("DNA Validation passed.")
