"""Pure stack fingerprinting engine for workspace ignore shield generation."""

from dataclasses import dataclass, field
from pathlib import Path

from ..exceptions import SprawlError


@dataclass(frozen=True)
class StackProfile:
    """Declarative stack profile definition with root markers and ignore patterns."""

    name: str
    description: str
    markers: tuple[str, ...]
    ignore_patterns: tuple[str, ...]


StackIgnoreProfile = StackProfile


@dataclass(frozen=True)
class StackDetectionResult:
    """Immutable result of workspace stack detection."""

    detected_stacks: tuple[str, ...]
    matched_markers: dict[str, tuple[str, ...]]
    exposed_paths: dict[str, tuple[str, ...]] = field(default_factory=dict)


STACK_PROFILES: tuple[StackProfile, ...] = (
    StackProfile(
        name="base",
        description="Universal baseline protection (VCS, archives, secrets, locks, minified assets)",
        markers=(),
        ignore_patterns=(
            ".git/",
            ".stfolder/",
            ".stversions/",
            ".trash/",
            ".DS_Store",
            "Thumbs.db",
            "**/4_ARCHIVE/**",
            "**/_ARCHIVE/**",
            "**/99_Archive/**",
            "**/archive/**",
            ".env",
            ".env.*",
            "!.env.example",
            "*.pem",
            "*.key",
            "*.min.js",
            "*.min.css",
            "*.map",
            "*.lock",
        ),
    ),
    StackProfile(
        name="python",
        description="Python virtual environments, bytecode caches, and build artifacts",
        markers=(
            "pyproject.toml",
            "requirements.txt",
            "setup.py",
            "Pipfile",
            "poetry.lock",
            "uv.lock",
        ),
        ignore_patterns=(
            ".venv/",
            "venv/",
            "Scripts/",
            "**/venv/**",
            "**/.venv/**",
            "**/__pycache__/**",
            "**/*.pyc",
            ".pytest_cache/",
            ".ruff_cache/",
            ".mypy_cache/",
            "build/",
            "dist/",
            "*.egg-info/",
        ),
    ),
    StackProfile(
        name="node",
        description="Node.js / TypeScript package directories and bundler caches",
        markers=(
            "package.json",
            "pnpm-lock.yaml",
            "yarn.lock",
            "package-lock.json",
            "tsconfig.json",
            "bun.lockb",
        ),
        ignore_patterns=(
            "node_modules/",
            "**/node_modules/**",
            ".next/",
            ".nuxt/",
            ".svelte-kit/",
            "dist/",
            "build/",
            "coverage/",
            ".turbo/",
        ),
    ),
    StackProfile(
        name="rust",
        description="Rust Cargo build target directories",
        markers=("Cargo.toml", "Cargo.lock"),
        ignore_patterns=(
            "target/",
            "**/target/**",
        ),
    ),
    StackProfile(
        name="go",
        description="Go vendor and compiled binary directories",
        markers=("go.mod", "go.sum"),
        ignore_patterns=(
            "vendor/",
            "bin/",
        ),
    ),
    StackProfile(
        name="vault",
        description="Obsidian / Markdown Knowledge Vault editor caches and decision logs",
        markers=("manifest.md", ".obsidian", "00_Atlas", "99_Archive"),
        ignore_patterns=(
            ".obsidian/",
            ".shards/*/DECISIONS.md",
        ),
    ),
    StackProfile(
        name="docker",
        description="Docker local build context caches",
        markers=("Dockerfile", "docker-compose.yml", "docker-compose.yaml", "compose.yml"),
        ignore_patterns=(".docker/",),
    ),
)

STACK_PROFILE_MAP: dict[str, StackProfile] = {p.name: p for p in STACK_PROFILES}


def _extract_root_candidate(pattern: str) -> str | None:
    """Extract a root entry name from an ignore pattern if unambiguous."""
    if pattern.startswith("!"):
        return None
    cleaned = pattern.removeprefix("**/").removesuffix("/**").rstrip("/")
    if not cleaned or "/" in cleaned or "*" in cleaned:
        return None
    return cleaned


def find_matching_workspace_bloat(
    entries: set[str] | frozenset[str], profile: StackProfile
) -> tuple[str, ...]:
    """Identify root-level bloat or sensitive paths from profile that exist in entries."""
    candidates = [
        cand
        for pat in profile.ignore_patterns
        if (cand := _extract_root_candidate(pat)) is not None and cand in entries
    ]
    if ".env.*" in profile.ignore_patterns:
        candidates.extend(
            sorted(e for e in entries if e.startswith(".env.") and e != ".env.example")
        )
    return tuple(dict.fromkeys(candidates))


def _match_profile_markers(profile: StackProfile, entry_names: frozenset[str]) -> tuple[str, ...]:
    """Return the ordered subset of profile markers present in entry_names."""
    return tuple(marker for marker in profile.markers if marker in entry_names)


def detect_stacks_from_entries(entry_names: frozenset[str]) -> StackDetectionResult:
    """Pure function matching directory entry names against STACK_PROFILES.

    Always includes 'base' first, followed by matched profiles in deterministic
    catalog order.
    """
    base_profile = STACK_PROFILE_MAP["base"]
    detected: list[str] = ["base"]
    matched_markers: dict[str, tuple[str, ...]] = {"base": ()}
    exposed_paths: dict[str, tuple[str, ...]] = {
        "base": find_matching_workspace_bloat(entry_names, base_profile)
    }

    for profile in STACK_PROFILES[1:]:
        hits = _match_profile_markers(profile, entry_names)
        if hits:
            detected.append(profile.name)
            matched_markers[profile.name] = hits
            exposed_paths[profile.name] = find_matching_workspace_bloat(entry_names, profile)

    return StackDetectionResult(
        detected_stacks=tuple(detected),
        matched_markers=matched_markers,
        exposed_paths=exposed_paths,
    )


def detect_workspace_stacks(workspace_dir: Path) -> StackDetectionResult:
    """Read root entry names from workspace_dir and detect active stacks."""
    try:
        entries = frozenset(p.name for p in workspace_dir.iterdir())
    except OSError as exc:
        raise SprawlError(f"Failed to scan workspace directory '{workspace_dir}': {exc}") from exc

    return detect_stacks_from_entries(entries)
