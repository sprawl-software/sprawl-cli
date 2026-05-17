# ADR 002: Clean Room Architecture & Sandbox Isolation

**Status:** Accepted
**Date:** 2026-05-17

## Context
A major problem with early agentic orchestrators is "OS-level pollution" and sandbox leakage. If an agent operates within a workspace, it often encounters CLI branding, global manifests, or registry data that causes it to hallucinate or attempt actions outside its designated scope. The #1 constraint for Sprawl v2 is ensuring agents operate in a completely isolated context.

## Decision
We implement the "Clean Room" principle via a Two-Layer Stealth architecture:
1. **Stealth Injection (Workspace Layer):** The workspace contains only an `.agents/` folder. The `agents.md` file contains pure persona and rule context with ZERO Sprawl branding. The only Sprawl artifact visible is `.agents/sprawl_manifest.yml` (acting as the developer's shopping list). IDE rules (`.cursorrules`, etc.) simply point to `agents.md`.
2. **Management Plane (Invisible Layer):** All operational metadata, sync states, DNA bindings, and checksums are stored out-of-band in `~/.sprawl/workspaces/<hash>/`.

## Consequences
- **Positive:** Complete agent isolation. Agents remain unaware of the Sprawl engine, preventing them from trying to modify global DNA or breaking their sandbox constraints.
- **Negative:** Sync logic is more complex as state must be reconciled between the invisible management plane and the visible workspace `.agents/` folder.
