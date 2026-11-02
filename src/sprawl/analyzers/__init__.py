"""Sprawl CLI Analyzers Package - Stack fingerprinting and static context token auditing."""

from .context import (
    ContextArtifactMetric,
    ContextAuditReport,
    LayerSummary,
    analyze_mcp_json,
    analyze_rule_text,
    analyze_skill_text,
    build_context_report,
    build_optimization_hints,
    estimate_tokens,
    scan_workspace_context,
)
from .stack import (
    STACK_PROFILE_MAP,
    STACK_PROFILES,
    StackDetectionResult,
    StackIgnoreProfile,
    StackProfile,
    detect_stacks_from_entries,
    detect_workspace_stacks,
    find_matching_workspace_bloat,
)

__all__ = [
    "ContextArtifactMetric",
    "ContextAuditReport",
    "LayerSummary",
    "STACK_PROFILE_MAP",
    "STACK_PROFILES",
    "StackDetectionResult",
    "StackIgnoreProfile",
    "StackProfile",
    "analyze_mcp_json",
    "analyze_rule_text",
    "analyze_skill_text",
    "build_context_report",
    "build_optimization_hints",
    "detect_stacks_from_entries",
    "detect_workspace_stacks",
    "estimate_tokens",
    "find_matching_workspace_bloat",
    "scan_workspace_context",
]
