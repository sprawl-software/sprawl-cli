"""Canonical multi-IDE ignore shield compiler and non-destructive merger."""

from dataclasses import dataclass
from pathlib import Path
import time

from ..analyzers.stack import STACK_PROFILE_MAP, detect_workspace_stacks
from ..exceptions import SprawlError
from ..validation import parse_yaml_frontmatter

BASE_IGNORE_TARGETS: tuple[str, ...] = (
    ".agentignore",
    ".ignore",
)
ADAPTER_IGNORE_MAP: dict[str, str] = {
    "cursor": ".cursorignore",
    "claude-code": ".claudeignore",
    "windsurf": ".codeiumignore",
    "cline-roo": ".rooignore",
    "gemini-cli": ".geminiignore",
    "aider": ".aiderignore",
}
ALL_IGNORE_TARGETS: tuple[str, ...] = (
    ".agentignore",
    ".ignore",
    ".cursorignore",
    ".claudeignore",
    ".codeiumignore",
    ".rooignore",
    ".geminiignore",
    ".aiderignore",
)
IGNORE_TARGETS: tuple[str, ...] = ALL_IGNORE_TARGETS
MANAGED_HEADER = "# === SPRAWL GOVERNED IGNORE SHIELD (DO NOT EDIT ABOVE CUSTOM SEPARATOR) ==="
CUSTOM_SEPARATOR = "# === CUSTOM WORKSPACE IGNORES ==="


@dataclass(frozen=True)
class TargetIgnoreStatus:
    """Per-file synchronization status for an IDE ignore target."""

    target_file: str
    status: str  # "created" | "updated" | "unchanged" | "drifted"
    preserved_custom_lines: int


@dataclass(frozen=True)
class IgnoreSyncReport:
    """Aggregate report for a workspace ignore shield synchronization."""

    workspace_dir: str
    detected_stacks: tuple[str, ...]
    targets: tuple[TargetIgnoreStatus, ...]
    elapsed_ms: float

    @property
    def has_drift(self) -> bool:
        """Return True if any ignore target is out of sync with the canonical shield."""
        return any(target.status == "drifted" for target in self.targets)


def _count_active_rules(lines: list[str]) -> int:
    """Count non-empty, non-comment ignore pattern lines."""
    return sum(1 for line in lines if line.strip() and not line.strip().startswith("#"))


def _parse_bindings_value(raw_bindings: object) -> tuple[str, ...]:
    """Normalize parsed YAML bindings value (block list or flow list string)."""
    if isinstance(raw_bindings, list):
        return tuple(str(item).strip().strip("\"'") for item in raw_bindings if str(item).strip())
    if isinstance(raw_bindings, str) and raw_bindings.startswith("[") and raw_bindings.endswith("]"):
        inner = raw_bindings[1:-1].strip()
        if not inner:
            return ()
        return tuple(part.strip().strip("\"'") for part in inner.split(",") if part.strip())
    return ()


def _read_manifest_bindings(workspace_dir: Path) -> tuple[str, ...]:
    """Read active IDE adapter bindings from .agents/sprawl_manifest.yml if present."""
    manifest_path = workspace_dir / ".agents" / "sprawl_manifest.yml"
    if not manifest_path.is_file():
        return ()
    try:
        raw_text = manifest_path.read_text(encoding="utf-8")
    except OSError:
        return ()
    wrapped = raw_text if raw_text.startswith("---") else f"---\n{raw_text}\n---"
    parsed = parse_yaml_frontmatter(wrapped)
    return _parse_bindings_value(parsed.get("bindings"))


def resolve_ignore_targets(workspace_dir: Path, all_targets: bool = False) -> tuple[str, ...]:
    """Resolve active ignore targets from base tier, manifest bindings, and existing files."""
    if all_targets:
        return ALL_IGNORE_TARGETS

    bound_files = [
        ADAPTER_IGNORE_MAP[adapter]
        for adapter in _read_manifest_bindings(workspace_dir)
        if adapter in ADAPTER_IGNORE_MAP
    ]
    existing_files = [target for target in ALL_IGNORE_TARGETS if (workspace_dir / target).is_file()]
    combined = (*BASE_IGNORE_TARGETS, *bound_files, *existing_files)
    return tuple(dict.fromkeys(combined))


def _migrate_legacy_lines(
    normalized_text: str, managed_patterns: frozenset[str]
) -> tuple[str, int]:
    """Filter legacy unmanaged ignore content against managed patterns."""
    migrated = [
        line
        for line in normalized_text.splitlines()
        if line.strip() not in managed_patterns and line.strip() != MANAGED_HEADER
    ]
    cleaned = "\n".join(migrated).strip("\n")
    active_count = _count_active_rules(cleaned.splitlines())
    if not cleaned or active_count == 0:
        return "", 0
    return cleaned, active_count


def extract_custom_section(
    existing_content: str | None,
    managed_patterns: frozenset[str] = frozenset(),
) -> tuple[str, int]:
    """Extract custom rules below CUSTOM_SEPARATOR or migrate legacy unmanaged rules."""
    if not existing_content or not existing_content.strip():
        return "", 0

    normalized = existing_content.replace("\r\n", "\n")
    if CUSTOM_SEPARATOR in normalized:
        _, _, after = normalized.partition(CUSTOM_SEPARATOR)
        cleaned = after.strip("\n")
        if not cleaned:
            return "", 0
        return cleaned, _count_active_rules(cleaned.splitlines())

    return _migrate_legacy_lines(normalized, managed_patterns)


def _iter_section_lines(sections: list[str]) -> list[str]:
    """Flatten non-empty lines across all non-empty custom sections."""
    return [
        line
        for section in sections
        if section
        for line in section.replace("\r\n", "\n").splitlines()
        if line.strip()
    ]


def merge_custom_sections(sections: list[str]) -> tuple[str, int]:
    """Union and deduplicate custom ignore lines across multiple sections in order."""
    seen: set[str] = set()
    merged: list[str] = []
    for line in _iter_section_lines(sections):
        key = line.strip()
        if key not in seen:
            seen.add(key)
            merged.append(line)
    if not merged:
        return "", 0
    return "\n".join(merged), _count_active_rules(merged)


def _append_profile_patterns(
    stack_name: str, seen_patterns: set[str], output_lines: list[str]
) -> None:
    """Append deduplicated patterns for a single stack profile to output_lines."""
    profile = STACK_PROFILE_MAP.get(stack_name)
    if profile is None:
        return

    unique = [pat for pat in profile.ignore_patterns if pat not in seen_patterns]
    if not unique:
        return

    seen_patterns.update(unique)
    output_lines.append("")
    output_lines.append(f"# [sprawl:{profile.name}] {profile.description}")
    output_lines.extend(unique)


def compile_managed_block(stacks: tuple[str, ...]) -> str:
    """Compile the deterministic managed block grouped by detected stack profiles."""
    lines: list[str] = [
        MANAGED_HEADER,
        "# Generated by Sprawl CLI (sprawl ignore). Canonical SSoT: .agentignore",
    ]
    seen: set[str] = set()
    for stack_name in stacks:
        _append_profile_patterns(stack_name, seen, lines)
    return "\n".join(lines)


def _extract_patterns_from_block(managed_block: str) -> frozenset[str]:
    """Extract active pattern strings from a compiled managed block."""
    return frozenset(
        line.strip()
        for line in managed_block.splitlines()
        if line.strip() and not line.strip().startswith("#")
    )


def _format_merged_block(
    managed_block: str, custom_section: str, custom_count: int
) -> tuple[str, int]:
    """Combine managed_block, CUSTOM_SEPARATOR, and a custom section string."""
    base_merged = f"{managed_block.rstrip()}\n\n{CUSTOM_SEPARATOR}\n"
    if not custom_section:
        return base_merged, 0
    return f"{base_merged}{custom_section}\n", custom_count


def merge_ignore_content(managed_block: str, existing_content: str | None) -> tuple[str, int]:
    """Combine managed_block, CUSTOM_SEPARATOR, and preserved custom rules."""
    managed_patterns = _extract_patterns_from_block(managed_block)
    custom_section, custom_count = extract_custom_section(existing_content, managed_patterns)
    return _format_merged_block(managed_block, custom_section, custom_count)


def _read_existing_target(target_path: Path) -> str | None:
    """Read an existing ignore target file if present on disk."""
    if not target_path.is_file():
        return None
    try:
        return target_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SprawlError(f"Failed to read '{target_path}': {exc}") from exc


def _write_target_file(target_path: Path, content: str) -> None:
    """Write compiled ignore content to disk."""
    try:
        target_path.write_text(content, encoding="utf-8")
    except OSError as exc:
        raise SprawlError(f"Failed to write '{target_path}': {exc}") from exc


def _collect_workspace_custom_section(
    workspace_dir: Path,
    targets: tuple[str, ...],
    managed_patterns: frozenset[str],
) -> tuple[str, int]:
    """Harvest and union custom rules across all existing ignore files in workspace_dir."""
    candidates = tuple(dict.fromkeys((*targets, *ALL_IGNORE_TARGETS)))
    sections: list[str] = []
    for target_name in candidates:
        existing = _read_existing_target(workspace_dir / target_name)
        if existing is not None:
            section_text, _ = extract_custom_section(existing, managed_patterns)
            if section_text:
                sections.append(section_text)
    return merge_custom_sections(sections)


def _process_single_target(
    workspace_dir: Path,
    target_name: str,
    final_content: str,
    custom_count: int,
    check_only: bool,
    dry_run: bool,
) -> TargetIgnoreStatus:
    """Evaluate and optionally write a single ignore target file."""
    target_path = workspace_dir / target_name
    existing = _read_existing_target(target_path)

    if existing == final_content:
        return TargetIgnoreStatus(target_name, "unchanged", custom_count)

    if check_only:
        return TargetIgnoreStatus(target_name, "drifted", custom_count)

    status = "created" if existing is None else "updated"
    if not dry_run:
        _write_target_file(target_path, final_content)
    return TargetIgnoreStatus(target_name, status, custom_count)


def sync_workspace_ignores(
    workspace_dir: Path,
    check_only: bool = False,
    dry_run: bool = False,
    all_targets: bool = False,
) -> IgnoreSyncReport:
    """Detect workspace stacks, harvest custom rules, and sync active IDE ignore targets."""
    start_time = time.perf_counter()
    detection = detect_workspace_stacks(workspace_dir)
    managed_block = compile_managed_block(detection.detected_stacks)
    managed_patterns = _extract_patterns_from_block(managed_block)
    targets = resolve_ignore_targets(workspace_dir, all_targets=all_targets)

    custom_section, custom_count = _collect_workspace_custom_section(
        workspace_dir, targets, managed_patterns
    )
    final_content, _ = _format_merged_block(managed_block, custom_section, custom_count)

    statuses = tuple(
        _process_single_target(
            workspace_dir, target, final_content, custom_count, check_only, dry_run
        )
        for target in targets
    )
    elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
    return IgnoreSyncReport(
        workspace_dir=str(workspace_dir),
        detected_stacks=detection.detected_stacks,
        targets=statuses,
        elapsed_ms=elapsed_ms,
    )
