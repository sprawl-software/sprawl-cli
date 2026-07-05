# ADR 004: Non-Destructive Workspace Isolation & Local Rules Drift Exclusion

## Status
Accepted

## Context
Sprawl integrates globally managed DNA (e.g. general engineering guidelines, corporate skills, and shared workflows) into local workspaces. During `sprawl graft`, existing rules (e.g. `.cursorrules`, `.clinerules`) inside a project are harvested and converted into local-only files inside `.agents/rules/` prefixed with `local_` to preserve them.

Previously, the graft command scanned these `local_` files and registered them under both `rules:` (denoting global DNA template requirements) and `local_rules:` (denoting workspace overrides). Consequently, when running `sprawl diff` or checking `sprawl status`, the system compared the `local_` rules against the upstream DNA registry. Since no corresponding templates exist globally, this triggered false-positive "DNA drift detected" diffs containing full file contents, creating confusion and giving the false impression that `sprawl sync` might destroy local custom rules.

## Decision
1. **Workspace Boundary**: Reaffirm that Sprawl CLI operations must be strictly non-destructive. It must only overwrite/manage its own `.agents/` tracking data and the relative symlink files pointing to `AGENTS.md`. No user source code outside of these specific registry files may be altered.
2. **Double-Categorization Elimination**: Exclude any `local_` prefixed rules when the `graft` scanner scans existing categories inside `.agents/rules/`. They must only be declared under `local_rules:` in `sprawl_manifest.yml`.
3. **Drift Exclusion for Local Rules**: Modify the diff and status comparison engine to explicitly skip files starting with `local_`. They represent workspace-specific, custom extensions and are exempted from upstream DNA core validation.
4. **Auditable Visual Segregation**:
    *   **Status Dashboard**: The `sprawl status` artifacts table must filter `local_` files out of the core DNA `Rules` category and list them separately in a dedicated **Local Rules** row.
    *   **Diff Dashboard**: The `sprawl diff` command must show an informational **Workspace Extensions** panel detailing all local-only rules present in the repository, making them transparently auditable without triggering false drift alerts.

## Consequences
- **Zero-Drift Local Environments**: Workspace-specific, custom rules can exist alongside global templates without triggering false-positive drift warnings.
- **Auditable & Compliant Workspaces**: Enterprise security auditors can easily identify custom workspace extensions via both status and diff dashboards, satisfying compliance requirements while retaining developer flexibility.
- **Improved UX and Safety**: `sprawl status` accurately reports `✔ No DNA drift detected.` for fully aligned repositories, removing anxiety over potential code loss.
