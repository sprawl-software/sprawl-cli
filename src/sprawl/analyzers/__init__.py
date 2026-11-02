"""Sprawl CLI Analyzers Package - Stack fingerprinting and static context token auditing."""

from .context import (
    ContextArtifactMetric,
    ContextAuditReport,
    LayerSummary,
    analyze_mcp_json,
    analyze_rule_text,
    analyze_skill_text,
    build_context_report,
    estimate_tokens,
    scan_workspace_context,
)
from .stack import (
    STACK_PROFILE_MAP,
    STACK_PROFILES,
    StackDetectionResult,
    StackProfile,
    detect_stacks_from_entries,
    detect_workspace_stacks,
)

__all__ = [
    "ContextArtifactMetric",
    "ContextAuditReport",
    "LayerSummary",
    "STACK_PROFILE_MAP",
    "STACK_PROFILES",
    "StackDetectionResult",
    "StackProfile",
    "analyze_mcp_json",
    "analyze_rule_text",
    "analyze_skill_text",
    "build_context_report",
    "detect_stacks_from_entries",
    "detect_workspace_stacks",
    "estimate_tokens",
    "scan_workspace_context",
]
