"""Static Turn-1 context pollution auditor and zero-hop vs. progressive token analyzer."""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from pathlib import Path

from ..validation import parse_yaml_frontmatter

MAX_CONTEXT_FILE_BYTES = 10_485_760  # 10 MB safety ceiling

_TOKEN_RE = re.compile(r"\w+|[^\w\s]")
_LAYER_ORDER = ("manifest", "rule", "skill", "mcp")
_MANIFEST_CANDIDATES = (
    "AGENTS.md",
    ".agents/AGENTS.md",
    "GEMINI.md",
    "CLAUDE.md",
    ".cursorrules",
    ".windsurfrules",
    ".clinerules",
    ".github/copilot-instructions.md",
)
_MCP_CANDIDATES = (
    ".agents/mcp_config.json",
    "mcp_config.json",
    ".cursor/mcp.json",
    ".vscode/mcp.json",
)


@dataclass(frozen=True)
class ContextArtifactMetric:
    """Token weight and loading tier classification for a single workspace artifact."""

    layer: str  # "manifest" | "rule" | "skill" | "mcp"
    relative_path: str
    bytes_size: int
    zero_hop_tokens: int
    progressive_tokens: int
    is_symlink: bool = False
    note: str = ""


@dataclass(frozen=True)
class LayerSummary:
    """Aggregated token metrics for a context architecture layer."""

    layer: str
    artifact_count: int
    bytes_size: int
    zero_hop_tokens: int
    progressive_tokens: int


@dataclass(frozen=True)
class ContextAuditReport:
    """Complete Turn-1 context audit report for a workspace."""

    workspace_dir: str
    artifacts: tuple[ContextArtifactMetric, ...]
    layers: tuple[LayerSummary, ...]
    zero_hop_tokens: int
    progressive_tokens: int
    peak_tokens: int
    pruned_ratio_pct: float
    elapsed_ms: float


def estimate_tokens(text: str) -> int:
    """Estimates BPE token count using a deterministic stdlib lexical + byte hybrid heuristic."""
    if not text or not text.strip():
        return 0
    lexical_count = len(_TOKEN_RE.findall(text))
    byte_estimate = (len(text.encode("utf-8")) + 3) // 4
    return max(lexical_count, byte_estimate)


def analyze_rule_text(relative_path: str, content: str) -> ContextArtifactMetric:
    """Classifies a markdown rule into zero-hop (always-on) or progressive (scoped) tokens."""
    bytes_size = len(content.encode("utf-8"))
    tokens = estimate_tokens(content)
    frontmatter = parse_yaml_frontmatter(content)
    is_always = (
        frontmatter.get("alwaysApply") is True
        or str(frontmatter.get("activation", "")).lower() == "always"
    )
    if is_always:
        return ContextArtifactMetric(
            layer="rule",
            relative_path=relative_path,
            bytes_size=bytes_size,
            zero_hop_tokens=tokens,
            progressive_tokens=0,
            note="always-on (loaded every turn)",
        )
    return ContextArtifactMetric(
        layer="rule",
        relative_path=relative_path,
        bytes_size=bytes_size,
        zero_hop_tokens=0,
        progressive_tokens=tokens,
        note="on-demand (loaded when relevant)",
    )


def analyze_skill_text(relative_path: str, content: str) -> ContextArtifactMetric:
    """Splits a SKILL.md into Turn-1 catalog header tokens and on-demand body tokens."""
    bytes_size = len(content.encode("utf-8"))
    total_tokens = estimate_tokens(content)
    frontmatter = parse_yaml_frontmatter(content)
    catalog_header = f"{frontmatter.get('name', '')}: {frontmatter.get('description', '')}"
    zero_hop = min(total_tokens, estimate_tokens(catalog_header))
    progressive = max(0, total_tokens - zero_hop)
    return ContextArtifactMetric(
        layer="skill",
        relative_path=relative_path,
        bytes_size=bytes_size,
        zero_hop_tokens=zero_hop,
        progressive_tokens=progressive,
        note="index on Turn 1 + body on-demand",
    )


def analyze_mcp_json(relative_path: str, content: str) -> ContextArtifactMetric:
    """Analyzes an MCP configuration file for Turn-1 tool schema overhead."""
    bytes_size = len(content.encode("utf-8"))
    try:
        parsed = json.loads(content)
    except (ValueError, TypeError):
        return ContextArtifactMetric(
            layer="mcp",
            relative_path=relative_path,
            bytes_size=bytes_size,
            zero_hop_tokens=estimate_tokens(content),
            progressive_tokens=0,
            note="invalid JSON schema",
        )

    servers = parsed.get("mcpServers") if isinstance(parsed, dict) else None
    server_count = len(servers) if isinstance(servers, dict) else 0
    serialized = json.dumps(parsed, separators=(",", ":"))
    return ContextArtifactMetric(
        layer="mcp",
        relative_path=relative_path,
        bytes_size=bytes_size,
        zero_hop_tokens=estimate_tokens(serialized),
        progressive_tokens=0,
        note=f"{server_count} MCP server(s)",
    )


def build_context_report(
    workspace_dir: str,
    artifacts: tuple[ContextArtifactMetric, ...],
    elapsed_ms: float,
) -> ContextAuditReport:
    """Aggregates individual artifact metrics into layer summaries and workspace totals."""
    layers: list[LayerSummary] = []
    for layer_name in _LAYER_ORDER:
        items = [a for a in artifacts if a.layer == layer_name]
        layers.append(
            LayerSummary(
                layer=layer_name,
                artifact_count=len(items),
                bytes_size=sum(a.bytes_size for a in items),
                zero_hop_tokens=sum(a.zero_hop_tokens for a in items),
                progressive_tokens=sum(a.progressive_tokens for a in items),
            )
        )

    zero_hop_total = sum(row.zero_hop_tokens for row in layers)
    progressive_total = sum(row.progressive_tokens for row in layers)
    peak_total = zero_hop_total + progressive_total
    pruned_pct = round((progressive_total / peak_total) * 100.0, 1) if peak_total > 0 else 0.0

    return ContextAuditReport(
        workspace_dir=workspace_dir,
        artifacts=artifacts,
        layers=tuple(layers),
        zero_hop_tokens=zero_hop_total,
        progressive_tokens=progressive_total,
        peak_tokens=peak_total,
        pruned_ratio_pct=pruned_pct,
        elapsed_ms=round(elapsed_ms, 2),
    )


def _hint_for_artifact(item: ContextArtifactMetric) -> str | None:
    """Returns a concrete optimization hint for a single high-cost Turn-1 artifact."""
    if item.layer == "manifest" and "duplicate file" in item.note:
        return (
            f"Duplicate File: '{item.relative_path}' is a physical copy "
            f"(+{item.zero_hop_tokens:,} Always-On tokens). Replace with a symlink "
            f"or run 'sprawl bind --force' to save {item.zero_hop_tokens:,} tokens on every turn."
        )
    if item.layer == "rule" and item.zero_hop_tokens >= 500:
        return (
            f"Heavy Always-On Rule: '{item.relative_path}' injects "
            f"+{item.zero_hop_tokens:,} tokens on every turn ('alwaysApply: true'). "
            f"Set 'alwaysApply: false' in its frontmatter to load it On-Demand."
        )
    if item.layer == "manifest" and not item.is_symlink and item.zero_hop_tokens >= 3500:
        return (
            f"Large Root Manifest: '{item.relative_path}' consumes "
            f"{item.zero_hop_tokens:,} Turn-1 tokens. Move domain-specific sections "
            f"into '.agents/rules/' (with 'alwaysApply: false') or '.agents/skills/'."
        )
    return None


def build_optimization_hints(report: ContextAuditReport) -> tuple[str, ...]:
    """Generates actionable recommendations for reducing Turn-1 Always-On token bloat."""
    ranked = sorted(report.artifacts, key=lambda a: a.zero_hop_tokens, reverse=True)
    hints = [_hint_for_artifact(item) for item in ranked]
    return tuple(h for h in hints if h is not None)


def _resolve_within_allowed_bounds(path: Path, workspace_root: Path) -> Path | None:
    """Resolves path safely, rejecting circular symlinks and out-of-bounds targets."""
    try:
        resolved = path.resolve()
        if not resolved.is_file():
            return None
        ws_bound = workspace_root.resolve()
        core_bound = (Path.home() / ".sprawl" / "core").resolve()
    except (OSError, RuntimeError):
        return None

    if resolved.is_relative_to(ws_bound) or resolved.is_relative_to(core_bound):
        return resolved
    return None


def _read_bounded_text(
    path: Path, max_bytes: int = MAX_CONTEXT_FILE_BYTES
) -> tuple[str, int] | None:
    """Reads UTF-8 text only if the file size does not exceed max_bytes."""
    try:
        byte_size = path.stat().st_size
        if byte_size > max_bytes:
            return None
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    return text, len(text.encode("utf-8"))


def _evaluate_manifest(
    candidate: Path,
    rel_path: str,
    workspace_dir: Path,
    seen_realpaths: dict[Path, str],
) -> ContextArtifactMetric | None:
    """Evaluates a single root or IDE manifest, deduplicating symlinks to canonical files."""
    resolved = _resolve_within_allowed_bounds(candidate, workspace_dir)
    if resolved is None:
        return None
    read_result = _read_bounded_text(resolved)
    if read_result is None:
        return None

    content, bytes_size = read_result
    is_link = candidate.is_symlink()

    if is_link and resolved in seen_realpaths:
        target_name = seen_realpaths[resolved]
        return ContextArtifactMetric(
            layer="manifest",
            relative_path=rel_path,
            bytes_size=bytes_size,
            zero_hop_tokens=0,
            progressive_tokens=0,
            is_symlink=True,
            note=f"symlink -> {target_name} (0 dup tokens)",
        )

    is_first = len(seen_realpaths) == 0
    seen_realpaths.setdefault(resolved, rel_path)
    note = "canonical root manifest" if is_first else "duplicate file (use sprawl bind symlink)"
    return ContextArtifactMetric(
        layer="manifest",
        relative_path=rel_path,
        bytes_size=bytes_size,
        zero_hop_tokens=estimate_tokens(content),
        progressive_tokens=0,
        is_symlink=is_link,
        note=note,
    )


def _collect_manifests(workspace_dir: Path) -> list[ContextArtifactMetric]:
    """Scans root manifests and IDE bindings in deterministic order."""
    seen_realpaths: dict[Path, str] = {}
    metrics: list[ContextArtifactMetric] = []
    for rel_path in _MANIFEST_CANDIDATES:
        candidate = workspace_dir / rel_path
        metric = _evaluate_manifest(candidate, rel_path, workspace_dir, seen_realpaths)
        if metric is not None:
            metrics.append(metric)
    return metrics


def _resolve_agents_subdir(workspace_dir: Path, subdir: str) -> Path | None:
    """Locates the canonical .agents/<subdir> or fallback .agent/<subdir> directory."""
    primary = workspace_dir / ".agents" / subdir
    if primary.is_dir():
        return primary
    fallback = workspace_dir / ".agent" / subdir
    return fallback if fallback.is_dir() else None


def _collect_rules(workspace_dir: Path) -> list[ContextArtifactMetric]:
    """Scans markdown rule files inside the workspace rules directory."""
    rules_dir = _resolve_agents_subdir(workspace_dir, "rules")
    if rules_dir is None:
        return []
    metrics: list[ContextArtifactMetric] = []
    for rule_path in sorted(rules_dir.glob("*.md")):
        resolved = _resolve_within_allowed_bounds(rule_path, workspace_dir)
        read_result = _read_bounded_text(resolved) if resolved is not None else None
        if read_result is not None:
            rel = rule_path.relative_to(workspace_dir).as_posix()
            metrics.append(analyze_rule_text(rel, read_result[0]))
    return metrics


def _collect_skills(workspace_dir: Path) -> list[ContextArtifactMetric]:
    """Scans SKILL.md files inside the workspace skills directory."""
    skills_dir = _resolve_agents_subdir(workspace_dir, "skills")
    if skills_dir is None:
        return []
    metrics: list[ContextArtifactMetric] = []
    for skill_path in sorted(skills_dir.glob("*/SKILL.md")):
        resolved = _resolve_within_allowed_bounds(skill_path, workspace_dir)
        read_result = _read_bounded_text(resolved) if resolved is not None else None
        if read_result is not None:
            rel = skill_path.relative_to(workspace_dir).as_posix()
            metrics.append(analyze_skill_text(rel, read_result[0]))
    return metrics


def _collect_mcp_configs(workspace_dir: Path) -> list[ContextArtifactMetric]:
    """Scans MCP server configuration files in the workspace."""
    seen_realpaths: set[Path] = set()
    metrics: list[ContextArtifactMetric] = []
    for rel_path in _MCP_CANDIDATES:
        candidate = workspace_dir / rel_path
        resolved = _resolve_within_allowed_bounds(candidate, workspace_dir)
        if resolved is None or resolved in seen_realpaths:
            continue
        read_result = _read_bounded_text(resolved)
        if read_result is not None:
            seen_realpaths.add(resolved)
            metrics.append(analyze_mcp_json(rel_path, read_result[0]))
    return metrics


def scan_workspace_context(workspace_dir: Path) -> ContextAuditReport:
    """Executes a static 4-layer context pollution scan on the target workspace."""
    start = time.perf_counter()
    resolved_dir = workspace_dir.resolve()
    artifacts: list[ContextArtifactMetric] = []
    artifacts.extend(_collect_manifests(resolved_dir))
    artifacts.extend(_collect_rules(resolved_dir))
    artifacts.extend(_collect_skills(resolved_dir))
    artifacts.extend(_collect_mcp_configs(resolved_dir))
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    return build_context_report(str(resolved_dir), tuple(artifacts), elapsed_ms)
