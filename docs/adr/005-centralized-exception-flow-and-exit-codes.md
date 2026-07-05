---
type: System/Resource
subtype: ADR
title: "ADR 005: Centralized Exception Flow and Exit Codes"
aliases:
  - "ADR 005"
  - "adr_005_centralized_exception_flow_and_exit_codes"
status: Accepted
priority: High
date_created: 2026-07-05
date_updated: 2026-07-05
category:
  - Software-development
  - Architecture-decision
organization: Sprawl.software
up_links:
  - "[[spec_technical_architecture]]"
related_links: []
ai_model: "Antigravity 2.0"
ai_context: "Architectural Decision Record establishing centralized exception bubbling and prohibiting direct sys.exit calls in Sprawl CLI command handlers."
---

# ADR 005: Centralized Exception Flow and Exit Codes

**Status:** Accepted
**Date:** 2026-07-05

## Context
In early iterations of the Sprawl CLI, core command handlers, helper utilities, and interactive onboarding wizards invoked `sys.exit(1)` or `sys.exit(130)` directly when encountering execution faults or user abort actions.

While this approach is common in basic script dispatchers, it introduced severe architectural issues:
1. **Broken Testability:** Unit tests executing these flows caught un-trapped `SystemExit` exceptions, requiring heavy test harnessing, mock isolation, and boilerplate assert catches.
2. **Poor Composability:** Programmatic invocation or chaining of commands (e.g., calling `cmd_sync` directly from a third-party script or inside a daemon loop) was unsafe, as any execution failure would abruptly terminate the parent process.
3. **Decentralized UI rendering:** Command handlers had to handle both error logic and visual printing of error structures, leading to inconsistent UI formatting.

## Decision
We have decided to completely prohibit direct `sys.exit` calls inside all inner command handlers, subcommands, wizards, and core utilities. 

1. **Bubble Exceptions:** All command handlers must bubble execution failures by raising structured exceptions (either subclassing `SprawlError` or standard runtime exceptions like `KeyboardInterrupt`).
2. **Centralized Exit Management:** The main CLI entrypoint (`src/sprawl/cli.py:main()`) is the sole orchestrator of process termination. It wraps execution in a top-level try/except block, governs visual Rich panel formatting of error details, and returns appropriate exit status codes (e.g., `1` for general failures, `130` for user aborts).

## Consequences
- **Positive:** 
  - Restored full programmatic API composability of command routines.
  - Greatly simplified unit testing by eliminating hard process termination paths.
  - Guaranteed a single, consistent visual style for CLI error outputs.
- **Negative:**
  - Slightly increases exception handling boilerplate at the outermost execution boundary.
