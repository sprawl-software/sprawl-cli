<div align="center">

<img src="https://sprawl.software/assets/sprawl-logo-emerald (3).svg" alt="Sprawl.software" width="480"> 

**Developer infrastructure for <>/br
AI agent containment, telemetry, and workspace governance.**</br>

# Sprawl CLI

The workspace sandbox and context governance engine.

[![License: BSL-1.1](https://img.shields.io/badge/License-BSL--1.1-00FFCC.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-00FFCC.svg)](https://python.org)
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

```bash
# Recommended: automated bootstrap with pipx isolation
curl -sL https://raw.githubusercontent.com/sprawl-software/sprawl-cli/main/install.sh | bash

# Or: direct pipx install
pipx install git+https://github.com/sprawl-software/sprawl-cli.git
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

| Command         | Usage                                         
| --------------- | ---------------------------------------------
| sprawl create   | Scaffold a new governance-compliant workspace      
|                 |                                                     
| sprawl create	|   Scaffold a new governance-compliant workspace
| sprawl graft	   |   Onboard an existing project without losing custom configs
| sprawl sync	   |   Pull DNA updates, provision venv, compile IDE bindings
| sprawl bind	   |   Generate native config files for all active editors
| sprawl add	   |   Inject rules, skills, or workflows from the registry
| sprawl mount	   |   Grant agents secure access to external directories
| sprawl status	|   Inspect workspace identity, DNA health, and telemetry
| sprawl diff	   |   Detect configuration drift against the central registry
| sprawl doctor	|   Run system-wide diagnostics
| sprawl ws	      |   Manage all tracked workspaces from a single registry
| sprawl demo	   |   Interactive sandbox demonstration
| sprawl man	   |   Offline terminal documentation
| sprawl wipe	   |   Clean uninstall — zero configuration trail| 

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

- Cursor	.cursorrules
- VS Code / Copilot
- Visual Studio
- Claude Code
- Gemini / Antigravity
- IntelliJ / JetBrains
- Windsurfu
- RooCode / Cline

## Design Principles

- 100% Local, Runs on your machine. No cloud. No accounts. No telemetry.
- Stealth Injection, Agents operate under constraints they cannot see or modify
- Agnostic Outputs, One manifest → all editors. Switch tools without reconfiguring.
- Zero Heavy Dependencies, Pure Python standard library. Sub-100ms boot.
- Standard Library,  Only	No supply chain risk. Auditable in 48 hours.

### Contributing

Sprawl is in active private development. Contribution guidelines will be published at public launch. For early access or partnerships: hello@sprawl.software.

## License

Business Source License 1.1
— Free for non-production use.

Built with zero dependencies in Antwerp 🇧🇪 by Younes Baghor
