<div align="center">

<img src="https://sprawl.software/assets/sprawl-logo-emerald (3).svg" alt="Sprawl.software" width="480">

**Developer AI governance:<br>
GitOps rule management and multi-IDE consistency for AI coding agents.**<br>

# Sprawl CLI

One source of truth for the rules, skills, and boundaries your AI coding agents follow.

[![License: BSL-1.1](https://img.shields.io/badge/License-BSL--1.1-00FFCC.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-00FFCC.svg)](https://python.org)
[![Platform: Linux | macOS | Windows](https://img.shields.io/badge/Platform-Linux%20%7C%20macOS%20%7C%20Windows-00FFCC.svg)](#quickstart)
[![MCP Native](https://img.shields.io/badge/MCP-Native-D946EF.svg)](https://modelcontextprotocol.io)

[Website](https://sprawl.software) · [Docs](https://sprawl.software/docs/) · [Quickstart](#quickstart)

---

</div>

## The Problem

AI coding agents (Cursor, Claude Code, Copilot, RooCode, Antigravity) each read their own configuration files, and teams end up with:

- **Fragmented rules:** `.cursorrules`, `.windsurfrules`, `.clinerules`, and `CLAUDE.md` scattered across every repository, each slightly different.
- **Configuration drift:** a rule updated in one repo never reaches the other forty.
- **Wasted context:** agents load `node_modules`, build caches, and irrelevant files into their context window.
- **No audit trail:** security and platform teams cannot see which rules each team's agents actually run with.

## The Solution

Sprawl CLI keeps agent rules in Git and compiles them into every editor's native format, locally, with no cloud service.

| Capability | How |
| :--- | :--- |
| **GitOps Rule Sync** | Rules, skills, and personas live in a Git registry. `sprawl ws push` updates every tracked repository. |
| **Universal IDE Binding** | One manifest compiles to native settings for Cursor, VS Code, IntelliJ, Claude, Gemini, and Copilot. |
| **Drift Detection** | `sprawl diff` shows where a workspace has moved away from the central registry. |
| **Directory-Scoped MCP File Access** | The bundled MCP file server only serves the workspace and explicitly mounted directories. |
| **Local-Only** | No accounts, no telemetry, no network calls except the `git` operations you run. |

> Sprawl is a governance and configuration tool. It is not an operating system sandbox and does not replace OS-level isolation.

## Quickstart

### Install

**Linux & macOS:**
```bash
# Automated bootstrap with pipx isolation
curl -sL https://sprawl.software/install.sh | bash

# Fallback via GitHub raw:
curl -sL https://raw.githubusercontent.com/sprawl-software/sprawl-cli/main/install.sh | bash
```

**Windows (PowerShell 5.1+ / 7+):**
```powershell
# Native PowerShell bootstrap with pipx isolation
irm https://sprawl.software/install.ps1 | iex

# Fallback via GitHub raw:
irm https://raw.githubusercontent.com/sprawl-software/sprawl-cli/main/install.ps1 | iex
```

**Cross-Platform (direct pipx):**
```bash
pipx install git+https://github.com/sprawl-software/sprawl-cli.git
```

### Initialize & Govern

```bash
# Import your team's global DNA registry
sprawl init https://github.com/your-org/your-dna-repo.git

# Graft onto an existing project (harvests legacy editor rules automatically)
cd my-project/
sprawl graft

# Sync DNA, provision venv, compile IDE bindings
sprawl sync

# Connect to your active editors
sprawl bind
```

## Core Commands

| Command | Usage |
| :--- | :--- |
| `sprawl create` | Scaffold a new governance-compliant workspace |
| `sprawl graft` | Onboard an existing project without losing custom configs |
| `sprawl sync` | Pull DNA updates, provision venv, compile IDE bindings |
| `sprawl bind` | Generate native config files for all active editors |
| `sprawl add` | Inject rules, skills, or workflows from the registry |
| `sprawl mount` | Give agents scoped access to additional directories |
| `sprawl status` | Inspect workspace identity and DNA health |
| `sprawl diff` | Detect configuration drift against the central registry |
| `sprawl doctor` | Run system-wide diagnostics |
| `sprawl ws` | Manage all tracked workspaces from a single registry |
| `sprawl demo` | Interactive demonstration |
| `sprawl man` | Offline terminal documentation |
| `sprawl wipe` | Clean uninstall with no configuration left behind |

## Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│                     DEVELOPER WORKSTATION                       │
│                                                                 │
│   ┌──────────────┐                         ┌─────────────┐      │
│   │  IDE / Agent │───────── HTTPS ────────▶│  Cloud LLM  │      │
│   └──────────────┘                         └─────────────┘      │
│          │                                                      │
│   ┌──────┴───────────────────────────────────────────────────┐  │
│   │                    SPRAWL (LOCAL)                        │  │
│   │                                                          │  │
│   │  ┌───────────────────┐     ┌──────────────────────────┐  │  │
│   │  │  RULE REGISTRY    │     │  SCOPED MCP FILE SERVER  │  │  │
│   │  │  ~/.sprawl/ (Git) │     │  Path traversal guard    │  │  │
│   │  │  Compiled per IDE │     │  Workspace + mounts only │  │  │
│   │  └───────────────────┘     └──────────────────────────┘  │  │
│   │                                                          │  │
│   └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Supported Editors & Agents

- **Cursor** (`.cursorrules`)
- **VS Code / GitHub Copilot** (`.github/copilot-instructions.md`, `.vscode/settings.json`)
- **Visual Studio**
- **Claude Code** (`CLAUDE.md`, MCP config)
- **Gemini / Google Antigravity** (`gemini.json`, `.agent/`)
- **IntelliJ / JetBrains**
- **Windsurf** (`.windsurfrules`)
- **RooCode / Cline** (`.clinerules`)

## Design Principles

- **100% Local**: Runs entirely on your machine. No cloud, no accounts, zero telemetry.
- **Cross-Platform**: Linux, macOS, and Windows 10/11.
- **Agnostic Outputs**: One manifest compiles to all editors. Switch tools without reconfiguring.
- **Minimal Dependencies**: Python standard library plus Rich. Sub-100ms boot.
- **Auditable**: Small, readable codebase.

## Development & Testing

### 1. Setup Local Environment
Clone the repository and install Sprawl in editable mode with development dependencies:

```bash
git clone https://github.com/sprawl-software/sprawl-cli.git
cd sprawl-cli
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

### 2. Lint & Code Formatting (Ruff)

```bash
ruff check src/ tests/
ruff format --check src/ tests/
```

### 3. Run Unit & Integration Tests

```bash
pytest
```

### 4. Run E2E Integration Suite (Smoke Test)
Run the automated 26-scenario end-to-end verification:

```bash
python tests/qa_run_verifier.py --ci
```

## Contributing

Sprawl is in active private development. Contribution guidelines will be published at public launch. For early access or partnerships: hello@sprawl.software.

## License

Business Source License 1.1. See [LICENSE](LICENSE).

- Free for non-production use, and for production use by individuals and organisations with 5 people or fewer (see LICENSE for the exact thresholds).
- Other production use requires a commercial license.
- Agencies and consultants deploying Sprawl for clients require a Partner License.

Contact: hello@sprawl.software

Sprawl Software is a trading name of WebWizArt.be BV, Belgium.
