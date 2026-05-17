# ADR 001: Strict Stdlib-Only Architecture

**Status:** Accepted
**Date:** 2026-05-17

## Context
The Sprawl CLI is designed to be an enterprise-grade execution engine for the Atomic Agentic Fabric (AAF). Initially, the project relied on third-party dependencies such as Pydantic for validation and PyYAML for parsing manifest frontmatter. This increased the distribution footprint, created a brittle supply chain, and introduced potential friction for deployment across heterogeneous environments.

## Decision
We have decided to adopt a strict single-dependency architecture for Sprawl v2. The only permitted external dependency is `rich` (for rendering terminal UIs).
All other functionality must be implemented using Python's standard library:
- **Validation:** Dropped Pydantic. Use `dataclasses` with manual validation.
- **YAML Parsing:** Dropped PyYAML. Use a custom stdlib-based regex/split parser for basic frontmatter extraction.
- **CLI Framework:** Did not adopt Typer. Refactored `argparse` with a clean command registry pattern.
- **Logging:** Did not adopt `structlog`. Enhanced `rich` print helpers to handle JSON and leveled logging.

## Consequences
- **Positive:** Frictionless `pipx` installation, auditable supply chain, reduced security risk surface, and deterministic behavior across Python environments.
- **Negative:** Increased boilerplate for data validation and schema handling; loss of advanced YAML features (which we don't need for the manifest subset).
