# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.0.4] - 2026-10-12

### Changed
- **License:** Licensor is now WebWizArt.be BV (trading as Sprawl Software). The Change Date is now rolling: each version converts to Apache 2.0 four years after its first public release. Versions before 2.0.4 keep the Change Date of May 7, 2030.
- **Positioning:** README and package metadata describe Sprawl as GitOps rule management and multi-IDE consistency for AI coding agents. Removed "sandbox" wording; Sprawl is not an OS-level sandbox. The MCP feature is documented as directory-scoped file access.
- **Package README:** Removed the Enterprise SaaS feature list (not shipped) and the third-party consulting link. The license section now matches the root README.
- **Metadata:** Author and contact updated to WebWizArt.be BV / younes@sprawl.software.

### Fixed
- **`sprawl graft` web heuristic:** Repos with `package.json` were assigned `web-dev.md`, which does not exist in the default DNA. Graft now selects the first existing rule from `web_development.md`, `web-dev.md`, `react_best_practices.md` in the active DNA, defaulting to `web_development.md`.

---

## [2.0.0-rc.1] - 2026-07-03

### Added
- **Universal Workspace Harvesting Adapter Framework (`TASK-012-01`)**: Scans root projects on `sprawl graft` for legacy configuration files (`.cursorrules`, `.clinerules`, `.windsurfrules`, `.github/copilot-instructions.md`, `CLAUDE.md`, `AGENT.md`, `DESIGN.md`) and `.github/prompts/` directories, harvesting them as local-only workspace rules without upstream DNA drift pollution.
- **GitHub Copilot prompts folder adapter (`TASK-012-02`)**: Added dynamic compiler support during `sprawl bind` to translate local skills and workflows into Copilot-native `.github/prompts/*.prompt.md` files.
- **Styled TUI Console Formatter (`TASK-012-03`)**: Created a zero-dependency Unicode panel printer with strict 100-character line-width wrapping, themed around Sovereign Violet borders and Emerald tick / Crimson cross status indicators.
- **Secure Dynamic MCP directory mounting (`TASK-012-05`)**: Integrated dynamic folder mounting in the `sprawl-workspace-fs` MCP server using the `@alias/` prefix namespace, loaded straight from `sprawl-config.json` with strict directory containment checks.
- **Selective IDE Checkbox TUI (`TASK-010-11`)**: Built a termios-driven cbreak checkbox list selection prompt inside `sprawl bind`, exposing all 14 major IDE/agent tools, supporting `--all` and `--only <list>` bypasses.
- **Nuclear Wipe Command (`TASK-010-15`)**: Added `sprawl wipe` to safely clean up all generated rules files in registered workspaces, delete local config directories, and purge system configuration databases.
- **Lead Generation Onboarding Flow (`TASK-010-17`)**: Implemented a first-run interactive questionnaire for onboarding and lead capture on `sprawl init` and `sprawl create`. Can be bypassed cleanly with `--non-interactive` or `--yes` flags.

### Security
- **Fix path containment prefix escape (P0)**: Patched a critical `startswith()` vulnerability in `workspace_fs.py` where sibling directories sharing a name prefix (e.g., `/mount` vs `/mount-secrets`) could bypass path containment checks. Both mount root and workspace root guards now enforce strict directory boundary using `os.sep`-appended comparison. Added 8 security-specific regression tests.

### Changed
- **Workspace Path Restructuring (`TASK-012-04`)**: Re-routed virtual files (`agent.md`, `design.md`, `mcp_config.json`) to keep the workspace root clean, containing all sprawl configuration databases (`sprawl_manifest.yml` and `sprawl-config.json`) within the `.agents/` folder.
- **CLI Self-Upgrade Pipeline (`TASK-010-16`)**: Shifted self-upgrade source in `sprawl update` from PyPI to target Git repository via SSH (cloning from repository URL with a graceful HTTPS fallback).
- **ASCII logo spelling (`TASK-010-14`)**: Corrected spelling of `SPRAWL` in ASCII header and updated command-line brand metadata details.
- **Unified adapter interface (P2)**: Refactored `graft.py` so both `FileHarvestAdapter` and `PromptsFolderAdapter` share a common `HarvestAdapter` ABC with a consistent `harvest() -> List[str]` return type.
- **DRY copilot export (P2)**: Extracted duplicated skills/workflows export logic in `bind.py` into a shared `_export_category_to_prompts()` helper, eliminating 30+ lines of duplication.

