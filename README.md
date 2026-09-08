<div align="center">

<img src="https://sprawl.software/assets/sprawl-logo-emerald (3).svg" alt="Sprawl.software" width="480"> 

**Developer infrastructure for <>/br
AI agent containment, telemetry, and workspace governance.**</br>

# Sprawl CLI

The workspace sandbox and context governance engine.

[![License: BSL-1.1](https://img.shields.io/badge/License-BSL--1.1-00FFCC.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-00FFCC.svg)](https://python.org)
[![Platform: Linux | macOS | Windows](https://img.shields.io/badge/Platform-Linux%20%7C%20macOS%20%7C%20Windows-00FFCC.svg)](#quickstart)
[![MCP Native](https://img.shields.io/badge/MCP-Native-D946EF.svg)](https://modelcontextprotocol.io)

[Website](https://sprawl.software) · [Docs](https://sprawl.software/docs/) · [Quickstart](#quickstart)

---

</div>

## The Problem

AI coding agents (Cursor, Claude Code, Copilot, RooCode, Antigravity) operate unconstrained on developer workstations:

- **They read everything** — parent directories, `~/.ssh`, `.env` files, corporate credentials
- **They burn tokens** — stuffing context windows with `node_modules`, build caches, and irrelevant fixtures
- **They fragment rules** — scattering `.cursorrules`, `.windsurfrules`, `.clinerules` across every repo
- **They block enterprise adoption** — CISOs restrict AI tools because they lack containment and audit trails

## The Solution

Sprawl CLI is the local-first, zero-dependency engine that locks this down at the workstation boundary.


| Capability                | How                                                                                                |
| ------------------------- | -------------------------------------------------------------------------------------------------- |
| **Filesystem Sandboxing** | Directory-locked MCP servers block path traversal in <2ms                                          |
| **Universal IDE Binding** | Single manifest compiles to native settings for Cursor, VS Code, IntelliJ, Claude, Gemini, Copilot |
| **GitOps Rule Sync**      | Rules, skills, personas version-controlled in Git. Drift detection built in.                       |
| **Stealth Isolation**     | Agents operate under constraints they cannot see or modify                                         |
| **Zero Cloud Dependency** | 100% local. Zero telemetry. Zero network calls.                                                    |

## Quickstart

### Install

**Linux & macOS:**
```bash
# Automated bootstrap with pipx isolation
curl -sL https://raw.githubusercontent.com/sprawl-software/sprawl-cli/main/install.sh | bash
```

**Windows (PowerShell 5.1+ / 7+):**
```powershell
# Native PowerShell bootstrap with pipx isolation
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
| `sprawl mount` | Grant agents secure access to external directories |
| `sprawl status` | Inspect workspace identity, DNA health, and telemetry |
| `sprawl diff` | Detect configuration drift against the central registry |
| `sprawl doctor` | Run system-wide diagnostics |
| `sprawl ws` | Manage all tracked workspaces from a single registry |
| `sprawl demo` | Interactive sandbox demonstration |
| `sprawl man` | Offline terminal documentation |
| `sprawl wipe` | Clean uninstall — zero configuration trail |

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
│   │              SPRAWL SYSTEM BOUNDARY                      │  │
│   │                                                          │  │
│   │  ┌───────────────────┐     ┌──────────────────────────┐  │  │
│   │  │  STEALTH SANDBOX  │     │  SCOPED MCP SERVER       │  │  │
│   │  │  ~/.sprawl/       │     │  Path traversal guard    │  │  │
│   │  │  Hidden state     │     │  Directory-locked I/O    │  │  │
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
- **Cross-Platform**: First-class support across Linux, macOS, and Windows 10/11.
- **Stealth Injection**: Agents operate under containment constraints they cannot see or modify.
- **Agnostic Outputs**: One manifest compiles to all editors. Switch tools without reconfiguring.
- **Zero Heavy Dependencies**: Pure Python standard library + Rich. Sub-100ms boot.
- **Standard Library Only**: No dependency bloat. Auditable in 48 hours.

### Contributing

Sprawl is in active private development. Contribution guidelines will be published at public launch. For early access or partnerships: hello@sprawl.software.

## License

Business Source License 1.1
— Free for non-production use.

Built with zero dependencies in Antwerp 🇧🇪 by Younes Baghor
