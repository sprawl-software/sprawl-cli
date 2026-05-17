# Architecture Decision Records (ADR)

An **Architecture Decision Record (ADR)** is a standard software engineering document that captures an important architectural decision made along with its context and consequences.

We use ADRs in Sprawl to formally document *why* the codebase is built the way it is. This prevents future developers (or AI agents) from accidentally reverting critical design choices (like re-introducing heavy third-party dependencies) because they didn't understand the original context.

### Current Records
- **ADR 001:** Enforces the "Stdlib-Only" dependency rule.
- **ADR 002:** Defines the "Clean Room" isolation architecture.
