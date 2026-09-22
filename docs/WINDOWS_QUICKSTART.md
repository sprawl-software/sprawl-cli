# Sprawl CLI - Windows Quickstart Guide

This guide enables enterprise engineering teams running native Windows 10/11 (PowerShell / Windows Terminal) to set up and evaluate Sprawl CLI in under 5 minutes without WSL or external virtualization.

---

## 1. Prerequisites

Before installing, ensure the workstation has Python and Git installed:

* **Python 3.10+**: Run `python --version`. If not installed:
  ```powershell
  winget install Python.Python.3.12
  ```
  *(Ensure "Add Python to PATH" is checked during installation).*
* **Git for Windows**: Run `git --version`. If not installed:
  ```powershell
  winget install Git.Git
  ```

---

## 2. Install Sprawl CLI

Open PowerShell (Run as Administrator or regular user) and execute the automated installer:

```powershell
irm https://raw.githubusercontent.com/sprawl-software/sprawl-cli/main/install.ps1 | iex
```

*For local enterprise installations from source:*
```powershell
git clone https://github.com/sprawl-software/sprawl-cli.git
cd sprawl-cli
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

Verify the installation:
```powershell
sprawl --version
```

---

## 3. Initialize Global DNA Registry

Sprawl stores governance rules, schemas, and persona skills locally in `%USERPROFILE%\.sprawl\core\`.

To install the built-in demo DNA:
```powershell
sprawl init
```

To bind to your organization's centralized governance repository:
```powershell
sprawl init https://github.com/your-org/ai-governance-dna.git
```

---

## 4. Protect an Existing Project (Graft)

Navigate to an existing project repository:

```powershell
cd C:\Development\my-project
```

Inject the Sprawl governance harness:
```powershell
sprawl graft
```

This scaffolds the local `.agents/` containment directory and registers the workspace with Sprawl.

---

## 5. Select Governance Rules & Skills

Inspect available rules from your DNA registry:
```powershell
sprawl ls
```

Add your required tech stack rules and architectural personas:
```powershell
sprawl add python web-dev persona-master-engineer
```

---

## 6. Sync and Bind to IDEs

Lock the workspace and generate the active agent context:
```powershell
sprawl sync
```

Bind the governance context to your team's installed IDEs (Cursor, VS Code, Windsurf, Claude Code):
```powershell
sprawl bind
```

*Interactive selection:* Use arrow keys (or the numbered fallback prompt: `1, 2`) to select your active IDEs.

Sprawl automatically generates:
* `AGENTS.md` (canonical root instructions)
* `.cursorrules` (Cursor IDE)
* `.clinerules` (Cline / Roo-Code)
* `.windsurfrules` (Windsurf)
* `mcp_config.json` (directory-locked MCP file server boundary)

---

## 7. Audit & Verification

Run the diagnostics suite to verify runtime containment and confirm zero telemetry leaks:

```powershell
sprawl doctor
```

Check the active workspace configuration and token budget:
```powershell
sprawl status
```

---

## 8. Key Operational Notes for Windows

* **Directory Containment:** The Sprawl MCP filesystem server strictly locks coding assistants to your workspace directory. Any attempt by an AI agent to read outside paths (such as `C:\Users\...\.ssh\` or parent drives) is blocked deterministically.
* **Symlink vs. Copy Mode:** If Developer Mode is disabled on enterprise Windows machines, Sprawl automatically falls back from symlinks to verified file copies, ensuring zero setup friction.
* **Zero Cloud Dependencies:** Sprawl runs 100% on the local workstation using Python's standard library. No outbound credentials or project code ever leave the machine.
