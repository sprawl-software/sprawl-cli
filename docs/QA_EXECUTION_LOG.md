# Sprawl CLI — Comprehensive QA & Integration Execution Log

* **Execution Date:** 2026-07-05 10:34:32 UTC
* **Local Python Version:** 3.12.3
* **Workspace Root:** `/home/w3bwizart/Development/sprawl-cli`
* **Sandbox Directory:** `/home/w3bwizart/Development/sprawl-cli/qa_sandbox`
* **Test Mode Home:** `/home/w3bwizart/.sprawl_test`

---

## Step 1: Check Version

* **Description:** Verify the dynamically extracted version matches 2.0.2.
* **Command:** `sprawl --version` (cwd: `qa_sandbox`)
* **Execution Time:** `53ms`
* **Status:** **`PASS`** (Expected Code: `0`, Got: `0`)

### Standard Output (stdout):
```text
[*] Sprawl Orchestrator 2.0.2 (Atomic Agentic Fabric)
```

---

## Step 2: Man Page Output

* **Description:** Check the offline AAF manuals output.
* **Command:** `sprawl man` (cwd: `qa_sandbox`)
* **Execution Time:** `54ms`
* **Status:** **`FAIL`** (Expected Code: `0`, Got: `1`)

### Standard Output (stdout):
```text
╭─────────────────────────── Sprawl Execution Error ───────────────────────────╮
│ Manual not found! Expected at: unknown path — run from source checkout       │
│                                                                              │
│ Tip: run sprawl doctor to diagnose environment issues.                       │
╰──────────────────────────────────────────────────────────────────────────────╯
```

---

## Step 3: Initialize Core DNA

* **Description:** Clones the Sovereign DNA template repo into the isolated core directory (~/.sprawl_test/core).
* **Command:** `sprawl init https://github.com/w3bwizart/atomic-agentic-fabric-demo-dna.git` (cwd: `qa_sandbox`)
* **Execution Time:** `805ms`
* **Status:** **`PASS`** (Expected Code: `0`, Got: `0`)

### Standard Output (stdout):
```text
[*] Initializing Sprawl Hub from 
https://github.com/w3bwizart/atomic-agentic-fabric-demo-dna.git into 
/home/w3bwizart/Documents/Sprawl_Test...
[*] Cloning Global DNA to /home/w3bwizart/.sprawl_test/core...
[*] Creating Workspace Hub at /home/w3bwizart/Documents/Sprawl_Test...
[*] Initialization complete. Ensure ~/.local/bin is in your PATH.
```

### Error Output (stderr):
```text
Cloning into '/home/w3bwizart/.sprawl_test/core'...
```

---

## Step 4: Fetch Alternative DNA

* **Description:** Clones an alternative DNA repository using a custom alias.
* **Command:** `sprawl fetch-dna https://github.com/w3bwizart/atomic-agentic-fabric-demo-dna.git alt_dna` (cwd: `qa_sandbox`)
* **Execution Time:** `799ms`
* **Status:** **`FAIL`** (Expected Code: `0`, Got: `1`)

### Standard Output (stdout):
```text
[*] Fetching DNA context 'alt_dna' to 
/home/w3bwizart/.sprawl_test/dna/alt_dna...
[*] Running Zero-Trust validation on DNA...

╭─────────────────────────── Sprawl Execution Error ───────────────────────────╮
│ Could not parse                                                              │
│ /home/w3bwizart/.sprawl_test/dna/alt_dna/molecules/local-filesystem-mcp.json │
│ : MoleculeSchema.__init__() got an unexpected keyword argument 'mcpServers'  │
│                                                                              │
│ Tip: run sprawl doctor to diagnose environment issues.                       │
╰──────────────────────────────────────────────────────────────────────────────╯


╭─────────────────────────── Sprawl Execution Error ───────────────────────────╮
│ Could not parse                                                              │
│ /home/w3bwizart/.sprawl_test/dna/alt_dna/atoms/user_profile.json:            │
│ AtomSchema.__init__() got an unexpected keyword argument 'title'             │
│                                                                              │
│ Tip: run sprawl doctor to diagnose environment issues.                       │
╰──────────────────────────────────────────────────────────────────────────────╯


╭─────────────────────────── Sprawl Execution Error ───────────────────────────╮
│ Zero-Trust DNA Validation failed. The fetched DNA is corrupted or malicious. │
│                                                                              │
│ Tip: run sprawl doctor to diagnose environment issues.                       │
╰──────────────────────────────────────────────────────────────────────────────╯
```

### Error Output (stderr):
```text
Cloning into '/home/w3bwizart/.sprawl_test/dna/alt_dna'...
```

---

## Step 5: List DNA Registry

* **Description:** Verify both core and alt_dna exist in the registry.
* **Command:** `sprawl dna list` (cwd: `qa_sandbox`)
* **Execution Time:** `61ms`
* **Status:** **`PASS`** (Expected Code: `0`, Got: `0`)

### Standard Output (stdout):
```text
Registered DNA Sources                           
┏━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Status ┃ Alias    ┃ Type      ┃ Path                                     ┃
┡━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│   ●    │ @global  │ Primary   │ /home/w3bwizart/.sprawl_test/core        │
│   ●    │ @alt_dna │ Secondary │ /home/w3bwizart/.sprawl_test/dna/alt_dna │
└────────┴──────────┴───────────┴──────────────────────────────────────────┘
```

---

## Step 6: Inspect DNA Structure

* **Description:** Display the hierarchical tree of the active core DNA structure.
* **Command:** `sprawl dna inspect` (cwd: `qa_sandbox`)
* **Execution Time:** `53ms`
* **Status:** **`PASS`** (Expected Code: `0`, Got: `0`)

### Standard Output (stdout):
```text
🧬 Global DNA Registry (/home/w3bwizart/.sprawl_test/core)
┣━━ Rules
┃   ┣━━ demo_security.md
┃   ┗━━ python_stdlib_only.md
┣━━ Skills
┃   ┣━━ persona-demo_engineer
┃   ┗━━ persona-senior_python_architect
┗━━ Workflows
    ┗━━ demo_build.md
```

---

## Step 7: DNA Registry Update

* **Description:** Test Git pull synchronization on the active DNA template.
* **Command:** `sprawl dna update` (cwd: `qa_sandbox`)
* **Execution Time:** `655ms`
* **Status:** **`PASS`** (Expected Code: `0`, Got: `0`)

### Standard Output (stdout):
```text
Already up-to-date.
[*] Global DNA updated successfully.
```

### Error Output (stderr):
```text
From https://github.com/w3bwizart/atomic-agentic-fabric-demo-dna
 * branch            main       -> FETCH_HEAD
```

---

## Step 8: Self-Update Dry-Run

* **Description:** Test the auto-updater sequence without modifying path targets.
* **Command:** `sprawl update --dry-run` (cwd: `qa_sandbox`)
* **Execution Time:** `521573ms`
* **Status:** **`PASS`** (Expected Code: `0`, Got: `0`)

### Standard Output (stdout):
```text
[*] Initiating Sprawl Update Sequence...
[*] Updating Global DNA at /home/w3bwizart/.sprawl_test/core...
Already up-to-date.
[*] Global DNA updated successfully.
[*] Production/release installation detected. Installing update from GitHub...
[*] Attempting installation via SSH: 
git+ssh://git@github.com/sprawl-software/sprawl-cli.git...
[*] Sprawl CLI updated successfully from GitHub via SSH.
[*] Update Sequence complete.
```

### Error Output (stderr):
```text
From https://github.com/w3bwizart/atomic-agentic-fabric-demo-dna
 * branch            main       -> FETCH_HEAD
```

---

## Step 9: Create Workspace

* **Description:** Scaffolds a fresh sandbox workspace configuration.
* **Command:** `sprawl create qa_workspace` (cwd: `qa_sandbox`)
* **Execution Time:** `53ms`
* **Status:** **`PASS`** (Expected Code: `0`, Got: `0`)

### Standard Output (stdout):
```text
╭────────────────────────── Workspace Initialization ──────────────────────────╮
│ ✔ Workspace Created                                                          │
│ • Name: qa_workspace                                                         │
│ • Path: /home/w3bwizart/Development/sprawl-cli/qa_sandbox/qa_workspace       │
│ • DNA Binding: @core                                                         │
│                                                                              │
│ • Run sprawl bind inside to select rules bindings for your IDEs/agents.      │
│ • Run sprawl sync inside to orchestrate.                                     │
╰──────────────────────────────────────────────────────────────────────────────╯
```

---

## Step 10: List Tracked Workspaces

* **Description:** Confirm the newly created workspace is tracked.
* **Command:** `sprawl ws list` (cwd: `qa_sandbox`)
* **Execution Time:** `53ms`
* **Status:** **`PASS`** (Expected Code: `0`, Got: `0`)

### Standard Output (stdout):
```text
Tracked Workspaces                               
┏━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┓
┃ Status ┃ Name         ┃ Path                    ┃ DNA Binding    ┃ Last Sync ┃
┡━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━┩
│   ●    │ qa_workspace │ /home/w3bwizart/Develo… │ Global/Default │ Never     │
└────────┴──────────────┴─────────────────────────┴────────────────┴───────────┘
```

---

## Step 11: Workspace Synchronize

* **Description:** Synchronize active DNA parameters and initialize sandbox virtualenvs.
* **Command:** `sprawl sync` (cwd: `qa_workspace`)
* **Execution Time:** `1348ms`
* **Status:** **`PASS`** (Expected Code: `0`, Got: `0`)

### Standard Output (stdout):
```text
[*] Syncing /home/w3bwizart/Development/sprawl-cli/qa_sandbox/qa_workspace...
[*] Provisioning sandboxed virtual environment at 
/home/w3bwizart/Development/sprawl-cli/qa_sandbox/qa_workspace/.agents/.venv...
[*] Generating IDE & Agent bindings (standard mode)...
  [-] Antigravity MCP Schemas: Removed → sprawl-workspace-fs
  [-] Antigravity MCP Schemas: Removed → sprawl-vault

Bindings are present, to configure you bindings run sprawl bind.

╭────────────────────────── Workspace Orchestration ───────────────────────────╮
│ ✔ Sync Complete                                                              │
│ • Files Synced: 0                                                            │
│ • Files Pruned: 0                                                            │
│ • Venv Provisioned: Yes                                                      │
│ • Bindings Created: Yes                                                      │
╰──────────────────────────────────────────────────────────────────────────────╯
```

---

## Step 12: Workspace Status

* **Description:** Verify workspace stats and virtualenv health.
* **Command:** `sprawl status` (cwd: `qa_workspace`)
* **Execution Time:** `60ms`
* **Status:** **`PASS`** (Expected Code: `0`, Got: `0`)

### Standard Output (stdout):
```text
╭───────────────────────────── Workspace Identity ─────────────────────────────╮
│  Workspace             qa_workspace                                          │
│  Path                  /home/w3bwizart/Development/sprawl-cli/qa_sandbox/q…  │
│  DNA Binding           @global/core (default)                                │
│  Active Model          Not set                                               │
│  Venv                  ● Healthy (Python 3.12.3)                             │
│  Last Sync             2026-07-05T10:43:18.359175+00:00                      │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─────────────────────────────── DNA Artifacts ────────────────────────────────╮
│ ┏━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓       │
│ ┃ Category       ┃ Manifest (Requested) ┃ Local .agents/ (Installed) ┃       │
│ ┡━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩       │
│ │ Rules          │ —                    │ —                          │       │
│ │ Skills         │ —                    │ —                          │       │
│ │ Workflows      │ —                    │ —                          │       │
│ └────────────────┴──────────────────────┴────────────────────────────┘       │
╰──────────────────────────────────────────────────────────────────────────────╯
```

---

## Step 13: Generate Editor Bindings

* **Description:** Generate rules files (.cursorrules, .windsurfrules, gemini.json) for all adapters.
* **Command:** `sprawl bind --all` (cwd: `qa_workspace`)
* **Execution Time:** `60ms`
* **Status:** **`PASS`** (Expected Code: `0`, Got: `0`)

### Standard Output (stdout):
```text
[*] Generating IDE & Agent bindings (standard mode)...
  ✔ Claude Code Binding: Created symlink → AGENTS.md
  ✔ Gemini CLI Binding: Created symlink → AGENTS.md
  ✔ Antigravity .agent Binding: Created symlink → .agents
  ✔ Antigravity gemini.json Binding: Created → gemini.json
  ✔ Antigravity MCP Schemas: Provisioned → ~/.gemini/antigravity/mcp/
  ✔ GitHub Copilot Binding: Created symlink → ../AGENTS.md
  ✔ Cursor Binding: Created symlink → AGENTS.md
  ✔ Windsurf Binding: Created symlink → AGENTS.md
  ✔ Codex Binding: Created symlink → ../AGENTS.md
  ✔ IntelliJ Binding: Created symlink → ../../AGENTS.md
  ✔ Jupyter Notebooks Binding: Created symlink → AGENTS.md
  ✔ VS Code Binding: Created symlink → AGENTS.md
  ✔ VS Codium Binding: Created symlink → AGENTS.md
  ✔ RooCode/Cline Binding: Created symlink → AGENTS.md
  ✔ Zed Binding: Created symlink → AGENTS.md
  ✔ OpenCode Binding: Created symlink → ../../AGENTS.md

✔ Binding complete: 16/16 adapters registered.
```

---

## Step 14: Add Directory Mount

* **Description:** Mount an external folder for agent workspace access.
* **Command:** `sprawl mount add /tmp --alias test_tmp` (cwd: `qa_workspace`)
* **Execution Time:** `89ms`
* **Status:** **`PASS`** (Expected Code: `0`, Got: `0`)

### Standard Output (stdout):
```text
[*] Added workspace mount: test_tmp → /tmp
[*] Synchronizing workspace configurations...
[*] Syncing /home/w3bwizart/Development/sprawl-cli/qa_sandbox/qa_workspace...
[*] Generating IDE & Agent bindings (standard mode)...
  ○ Claude Code Binding: already exists (use --force to overwrite)
  ○ RooCode/Cline Binding: already exists (use --force to overwrite)
  ✔ Codex Binding: Created symlink → ../AGENTS.md
  ○ GitHub Copilot Binding: already exists (use --force to overwrite)
  ○ Cursor Binding: already exists (use --force to overwrite)
  ○ Gemini CLI Binding: already exists (use --force to overwrite)
  ○ Antigravity .agent Binding: already exists (use --force to overwrite)
  ○ Antigravity gemini.json Binding: already exists (use --force to overwrite)
  ✔ Antigravity MCP Schemas: Provisioned → ~/.gemini/antigravity/mcp/
  ○ IntelliJ Binding: already exists (use --force to overwrite)
  ○ Jupyter Notebooks Binding: already exists (use --force to overwrite)
  ○ OpenCode Binding: already exists (use --force to overwrite)
  ○ VS Code Binding: already exists (use --force to overwrite)
  ○ VS Codium Binding: already exists (use --force to overwrite)
  ○ Windsurf Binding: already exists (use --force to overwrite)
  ○ Zed Binding: already exists (use --force to overwrite)

✔ Binding complete: 2/16 adapters registered.

╭────────────────────────── Workspace Orchestration ───────────────────────────╮
│ ✔ Sync Complete                                                              │
│ • Files Synced: 0                                                            │
│ • Files Pruned: 0                                                            │
│ • Venv Provisioned: Existing                                                 │
│ • Bindings Created: Yes                                                      │
╰──────────────────────────────────────────────────────────────────────────────╯
```

---

## Step 15: List Active Mounts

* **Description:** Verify our test_tmp mount mapping.
* **Command:** `sprawl mount list` (cwd: `qa_workspace`)
* **Execution Time:** `53ms`
* **Status:** **`PASS`** (Expected Code: `0`, Got: `0`)

### Standard Output (stdout):
```text
┏━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━┓
┃ Alias/Prefix ┃ Absolute Target Path ┃
┡━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━┩
│ @test_tmp    │ /tmp                 │
└──────────────┴──────────────────────┘
```

---

## Step 16: Remove Directory Mount

* **Description:** Safely delete the configured mount.
* **Command:** `sprawl mount remove test_tmp` (cwd: `qa_workspace`)
* **Execution Time:** `91ms`
* **Status:** **`PASS`** (Expected Code: `0`, Got: `0`)

### Standard Output (stdout):
```text
[*] Removed workspace mount: test_tmp (was mapping to /tmp)
[*] Synchronizing workspace configurations...
[*] Syncing /home/w3bwizart/Development/sprawl-cli/qa_sandbox/qa_workspace...
[*] Generating IDE & Agent bindings (standard mode)...
  ○ Claude Code Binding: already exists (use --force to overwrite)
  ○ RooCode/Cline Binding: already exists (use --force to overwrite)
  ✔ Codex Binding: Created symlink → ../AGENTS.md
  ○ GitHub Copilot Binding: already exists (use --force to overwrite)
  ○ Cursor Binding: already exists (use --force to overwrite)
  ○ Gemini CLI Binding: already exists (use --force to overwrite)
  ○ Antigravity .agent Binding: already exists (use --force to overwrite)
  ○ Antigravity gemini.json Binding: already exists (use --force to overwrite)
  ✔ Antigravity MCP Schemas: Provisioned → ~/.gemini/antigravity/mcp/
  ○ IntelliJ Binding: already exists (use --force to overwrite)
  ○ Jupyter Notebooks Binding: already exists (use --force to overwrite)
  ○ OpenCode Binding: already exists (use --force to overwrite)
  ○ VS Code Binding: already exists (use --force to overwrite)
  ○ VS Codium Binding: already exists (use --force to overwrite)
  ○ Windsurf Binding: already exists (use --force to overwrite)
  ○ Zed Binding: already exists (use --force to overwrite)

✔ Binding complete: 2/16 adapters registered.

╭────────────────────────── Workspace Orchestration ───────────────────────────╮
│ ✔ Sync Complete                                                              │
│ • Files Synced: 0                                                            │
│ • Files Pruned: 0                                                            │
│ • Venv Provisioned: Existing                                                 │
│ • Bindings Created: Yes                                                      │
╰──────────────────────────────────────────────────────────────────────────────╯
```

---

## Step 17: List Available Artifacts

* **Description:** Scan and print all available artifacts.
* **Command:** `sprawl ls` (cwd: `qa_workspace`)
* **Execution Time:** `54ms`
* **Status:** **`PASS`** (Expected Code: `0`, Got: `0`)

### Standard Output (stdout):
```text
╭──────────────────────────────── DNA Registry ────────────────────────────────╮
│                                                                              │
│ Installed Contexts:                                                          │
│   • @global (Default Sprawl Hub DNA)                                         │
│   • @alt_dna                                                                 │
│                                                                              │
│ Active Context: /home/w3bwizart/.sprawl_test/core                            │
╰──────────────────────────────────────────────────────────────────────────────╯

🧬 Active DNA Artifacts (/home/w3bwizart/.sprawl_test/core)
┣━━ Personas
┃   ┣━━ persona-demo_engineer
┃   ┗━━ persona-senior_python_architect
┣━━ Rules
┃   ┣━━ demo_security.md
┃   ┗━━ python_stdlib_only.md
┗━━ Workflows
    ┗━━ demo_build.md
```

---

## Step 18: Scaffold Custom Persona

* **Description:** Scaffold a new persona template file inside global DNA.
* **Command:** `sprawl scaffold persona verification-squad` (cwd: `qa_workspace`)
* **Execution Time:** `51ms`
* **Status:** **`PASS`** (Expected Code: `0`, Got: `0`)

### Standard Output (stdout):
```text
[*] Persona Scaffolded successfully: 'persona-verification-squad'
[*] Generated boilerplate at 
/home/w3bwizart/.sprawl_test/core/skills/persona-verification-squad/SKILL.md
```

---

## Step 19: Add Skill Dependency

* **Description:** Incorporate sprawl-design-system dependency inside local manifest.
* **Command:** `sprawl add sprawl-design-system` (cwd: `qa_workspace`)
* **Execution Time:** `49ms`
* **Status:** **`FAIL`** (Expected Code: `0`, Got: `1`)

### Standard Output (stdout):
```text
╭─────────────────────────── Sprawl Execution Error ───────────────────────────╮
│ Item 'sprawl-design-system' not found in any category within the active DNA  │
│ context.                                                                     │
│                                                                              │
│ Tip: run sprawl doctor to diagnose environment issues.                       │
╰──────────────────────────────────────────────────────────────────────────────╯
```

---

## Step 20: Prune/Remove Dependency

* **Description:** Safely strip dependencies and trigger workspace manifest cleanups.
* **Command:** `sprawl rm sprawl-design-system` (cwd: `qa_workspace`)
* **Execution Time:** `56ms`
* **Status:** **`PASS`** (Expected Code: `0`, Got: `0`)

### Standard Output (stdout):
```text
[!] WARNING: Item 'sprawl-design-system' not found in active DNA context. 
Proceeding to blindly attempt removal from manifest.
[!] WARNING: No matching items found in sprawl_manifest.yml to remove.
```

---

## Step 21: Doctor Verification

* **Description:** Verify that all required tool and folder assertions pass.
* **Command:** `sprawl doctor` (cwd: `qa_workspace`)
* **Execution Time:** `57ms`
* **Status:** **`PASS`** (Expected Code: `0`, Got: `0`)

### Standard Output (stdout):
```text
Running Sprawl Diagnostics...

✔ Python 3.10+
✔ Git
⚠ Node/NPM
⚠ Rust/Cargo
✔ Global DNA
✔ Local Workspace

Diagnostic Summary                                                              
┏━━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Component       ┃ Status ┃ Details                                           ┃
┡━━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Python 3.10+    │ ✔ PASS │ 3.12.3                                            │
│ Git             │ ✔ PASS │ Installed (/usr/bin/git)                          │
│ Node/NPM        │ ⚠ WARN │ Not Found (Optional for TS/JS skills)             │
│ Rust/Cargo      │ ⚠ WARN │ Not Found (Optional for Rust skills)              │
│ Global DNA      │ ✔ PASS │ Initialized at /home/w3bwizart/.sprawl_test/core  │
│ Local Workspace │ ✔ PASS │ Active at                                         │
│                 │        │ /home/w3bwizart/Development/sprawl-cli/qa_sandbo… │
└─────────────────┴────────┴───────────────────────────────────────────────────┘

╭──────────────────────────────────────────────────────────────────────────────╮
│ Diagnostics passed with 2 warning(s).                                        │
│ Sprawl will function, but some language-specific skills may fail to install. │
╰──────────────────────────────────────────────────────────────────────────────╯
```

---

## Step 22: Verify Drift Diff

* **Description:** Compare active local overrides against the original DNA blueprint.
* **Command:** `sprawl diff` (cwd: `qa_workspace`)
* **Execution Time:** `58ms`
* **Status:** **`PASS`** (Expected Code: `0`, Got: `0`)

### Standard Output (stdout):
```text
Comparing local DNA drift against @core...

╭──────────────────────────────── Sync Status ─────────────────────────────────╮
│ ✔ No DNA drift detected. Your local workspace perfectly matches the upstream │
│ registry.                                                                    │
╰──────────────────────────────────────────────────────────────────────────────╯
```

---

## Step 23: Interactive Demo Run

* **Description:** Run E2E demo execution walkthrough non-interactively.
* **Command:** `sprawl demo 1` (cwd: `qa_sandbox`)
* **Execution Time:** `5172ms`
* **Status:** **`PASS`** (Expected Code: `0`, Got: `0`)

### Standard Output (stdout):
```text
[*] Starting Demo: Cross-Team Scaffolding
[*] Ensuring clean test environment...
[*] Nuking all testmode artifacts...
[*] [-] Deleted /home/w3bwizart/.sprawl_test/core
[*] [-] Deleted /home/w3bwizart/Documents/Sprawl_Test
[*] [-] Deleted /home/w3bwizart/.sprawl_test/config.json
[*] Testmode environment cleanly destroyed.
[*] Generating Transient Dummy DNA...
[*] Initializing Central Hub...
[*] Initializing Sprawl Hub from file:///tmp/sprawl_dummy_dna_qmccbt71 into 
/home/w3bwizart/Documents/Sprawl_Test...
[*] Cloning Global DNA to /home/w3bwizart/.sprawl_test/core...
[*] Creating Workspace Hub at /home/w3bwizart/Documents/Sprawl_Test...
[*] Initialization complete. Ensure ~/.local/bin is in your PATH.
[*] Isolating demo workspaces in /tmp/sprawl_demo_74mhkmvo...

=========================================
   TEAM 1: DOTNET-SQUAD
=========================================

╭────────────────────────── Workspace Initialization ──────────────────────────╮
│ ✔ Workspace Created                                                          │
│ • Name: dotnet-squad                                                         │
│ • Path: /tmp/sprawl_demo_74mhkmvo/dotnet-squad                               │
│ • DNA Binding: @core                                                         │
│                                                                              │
│ • Run sprawl bind inside to select rules bindings for your IDEs/agents.      │
│ • Run sprawl sync inside to orchestrate.                                     │
╰──────────────────────────────────────────────────────────────────────────────╯
[*] Resolving dependency: 'csharp_standards.md' into 
[*] Resolving dependency: 'entity_framework_optimizer' into 
[*] Resolving dependency: 'ci_cd_azure.yml' into 
[*] Modifying sprawl_manifest.yml...
[*] Injecting DNA...
[*] Syncing /tmp/sprawl_demo_74mhkmvo/dotnet-squad...
[*] Provisioning sandboxed virtual environment at 
/tmp/sprawl_demo_74mhkmvo/dotnet-squad/.agents/.venv...
[*] Generating IDE & Agent bindings (standard mode)...
  [-] Antigravity MCP Schemas: Removed → sprawl-workspace-fs
  [-] Antigravity MCP Schemas: Removed → sprawl-vault

Bindings are present, to configure you bindings run sprawl bind.

╭────────────────────────── Workspace Orchestration ───────────────────────────╮
│ ✔ Sync Complete                                                              │
│ • Files Synced: 3                                                            │
│ • Files Pruned: 0                                                            │
│ • Venv Provisioned: Yes                                                      │
│ • Bindings Created: Yes                                                      │
╰──────────────────────────────────────────────────────────────────────────────╯
[*] [+] Rule 'csharp_standards.md' successfully sandboxed.
[*] [+] Skill 'entity_framework_optimizer' successfully sandboxed.
[*] [+] Workflow 'ci_cd_azure.yml' successfully sandboxed.

[Resulting DNA for dotnet-squad]:
  sprawl-config.json
  sprawl_manifest.yml
  rules/csharp_standards.md
  workflows/ci_cd_azure.yml
  skills/entity_framework_optimizer

=========================================
   TEAM 2: WEB-SQUAD
=========================================

╭────────────────────────── Workspace Initialization ──────────────────────────╮
│ ✔ Workspace Created                                                          │
│ • Name: web-squad                                                            │
│ • Path: /tmp/sprawl_demo_74mhkmvo/web-squad                                  │
│ • DNA Binding: @core                                                         │
│                                                                              │
│ • Run sprawl bind inside to select rules bindings for your IDEs/agents.      │
│ • Run sprawl sync inside to orchestrate.                                     │
╰──────────────────────────────────────────────────────────────────────────────╯
[*] Resolving dependency: 'react_best_practices.md' into 
[*] Resolving dependency: 'web_artifacts_builder' into 
[*] Resolving dependency: 'vercel_production_deployment.yml' into 
[*] Modifying sprawl_manifest.yml...
[*] Injecting DNA...
[*] Syncing /tmp/sprawl_demo_74mhkmvo/web-squad...
[*] Provisioning sandboxed virtual environment at 
/tmp/sprawl_demo_74mhkmvo/web-squad/.agents/.venv...
[*] Generating IDE & Agent bindings (standard mode)...
  [-] Antigravity MCP Schemas: Removed → sprawl-workspace-fs
  [-] Antigravity MCP Schemas: Removed → sprawl-vault

Bindings are present, to configure you bindings run sprawl bind.

╭────────────────────────── Workspace Orchestration ───────────────────────────╮
│ ✔ Sync Complete                                                              │
│ • Files Synced: 3                                                            │
│ • Files Pruned: 0                                                            │
│ • Venv Provisioned: Yes                                                      │
│ • Bindings Created: Yes                                                      │
╰──────────────────────────────────────────────────────────────────────────────╯
[*] [+] Rule 'react_best_practices.md' successfully sandboxed.
[*] [+] Skill 'web_artifacts_builder' successfully sandboxed.
[*] [+] Workflow 'vercel_production_deployment.yml' successfully sandboxed.

[Resulting DNA for web-squad]:
  sprawl-config.json
  sprawl_manifest.yml
  rules/react_best_practices.md
  workflows/vercel_production_deployment.yml
  skills/web_artifacts_builder

=========================================
   TEAM 3: SALES-SQUAD
=========================================

╭────────────────────────── Workspace Initialization ──────────────────────────╮
│ ✔ Workspace Created                                                          │
│ • Name: sales-squad                                                          │
│ • Path: /tmp/sprawl_demo_74mhkmvo/sales-squad                                │
│ • DNA Binding: @core                                                         │
│                                                                              │
│ • Run sprawl bind inside to select rules bindings for your IDEs/agents.      │
│ • Run sprawl sync inside to orchestrate.                                     │
╰──────────────────────────────────────────────────────────────────────────────╯
[*] Resolving dependency: 'sales_outreach_compliance.md' into 
[*] Resolving dependency: 'hubspot_api_connector' into 
[*] Resolving dependency: 'lead_generation.yml' into 
[*] Modifying sprawl_manifest.yml...
[*] Injecting DNA...
[*] Syncing /tmp/sprawl_demo_74mhkmvo/sales-squad...
[*] Provisioning sandboxed virtual environment at 
/tmp/sprawl_demo_74mhkmvo/sales-squad/.agents/.venv...
[*] Generating IDE & Agent bindings (standard mode)...
  [-] Antigravity MCP Schemas: Removed → sprawl-workspace-fs
  [-] Antigravity MCP Schemas: Removed → sprawl-vault

Bindings are present, to configure you bindings run sprawl bind.

╭────────────────────────── Workspace Orchestration ───────────────────────────╮
│ ✔ Sync Complete                                                              │
│ • Files Synced: 3                                                            │
│ • Files Pruned: 0                                                            │
│ • Venv Provisioned: Yes                                                      │
│ • Bindings Created: Yes                                                      │
╰──────────────────────────────────────────────────────────────────────────────╯
[*] [+] Rule 'sales_outreach_compliance.md' successfully sandboxed.
[*] [+] Skill 'hubspot_api_connector' successfully sandboxed.
[*] [+] Workflow 'lead_generation.yml' successfully sandboxed.

[Resulting DNA for sales-squad]:
  sprawl-config.json
  sprawl_manifest.yml
  rules/sales_outreach_compliance.md
  workflows/lead_generation.yml
  skills/hubspot_api_connector

=========================================
   TEAM 4: LEGACY-SQUAD
=========================================

╭────────────────────────── Workspace Initialization ──────────────────────────╮
│ ✔ Workspace Created                                                          │
│ • Name: legacy-squad                                                         │
│ • Path: /tmp/sprawl_demo_74mhkmvo/legacy-squad                               │
│ • DNA Binding: @core                                                         │
│                                                                              │
│ • Run sprawl bind inside to select rules bindings for your IDEs/agents.      │
│ • Run sprawl sync inside to orchestrate.                                     │
╰──────────────────────────────────────────────────────────────────────────────╯
[*] Syncing /tmp/sprawl_demo_74mhkmvo/legacy-squad...
[*] Provisioning sandboxed virtual environment at 
/tmp/sprawl_demo_74mhkmvo/legacy-squad/.agents/.venv...
[*] Generating IDE & Agent bindings (standard mode)...
  [-] Antigravity MCP Schemas: Removed → sprawl-workspace-fs
  [-] Antigravity MCP Schemas: Removed → sprawl-vault

Bindings are present, to configure you bindings run sprawl bind.

╭────────────────────────── Workspace Orchestration ───────────────────────────╮
│ ✔ Sync Complete                                                              │
│ • Files Synced: 0                                                            │
│ • Files Pruned: 0                                                            │
│ • Venv Provisioned: Yes                                                      │
│ • Bindings Created: Yes                                                      │
╰──────────────────────────────────────────────────────────────────────────────╯

[Resulting DNA for legacy-squad]:
  sprawl-config.json
  sprawl_manifest.yml

=========================================
   DEMO COMPLETE                        
=========================================
The isolated environments have been successfully scaffolded.
Demo artifacts are automatically cleaned up on exit.
```

### Error Output (stderr):
```text
Cloning into '/home/w3bwizart/.sprawl_test/core'...
```

---

## Step 24: Clean Demo Workspaces

* **Description:** Delete the directories generated by the demo walkthrough.
* **Command:** `sprawl clean-demo` (cwd: `qa_sandbox`)
* **Execution Time:** `55ms`
* **Status:** **`PASS`** (Expected Code: `0`, Got: `0`)

### Standard Output (stdout):
```text
[!] WARNING: No sprawl_demo directory found at 
/home/w3bwizart/Development/sprawl-cli/qa_sandbox/sprawl_demo.
[*] Triggering testmode artifact cleanup...
[*] Nuking all testmode artifacts...
[*] [-] Deleted /home/w3bwizart/.sprawl_test/core
[*] [-] Deleted /home/w3bwizart/Documents/Sprawl_Test
[*] [-] Deleted /home/w3bwizart/.sprawl_test/config.json
[*] Testmode environment cleanly destroyed.
```

---

## Step 25: Clean Test Mode Assets

* **Description:** Destroys all isolated directories.
* **Command:** `sprawl clean-test` (cwd: `qa_sandbox`)
* **Execution Time:** `50ms`
* **Status:** **`PASS`** (Expected Code: `0`, Got: `0`)

### Standard Output (stdout):
```text
[*] Nuking all testmode artifacts...
[*] Testmode environment cleanly destroyed.
```

---

## Step 26: Nuclear Wipe

* **Description:** Erase all configurations and trace marks from the system completely.
* **Command:** `sprawl wipe --force` (cwd: `qa_workspace`)
* **Execution Time:** `61ms`
* **Status:** **`PASS`** (Expected Code: `0`, Got: `0`)

### Standard Output (stdout):
```text
!!! NUCLEAR WIPE INITIATED !!!
Will destroy local workspace: 
/home/w3bwizart/Development/sprawl-cli/qa_sandbox/qa_workspace/.agents
Will destroy global DNA registry & configuration: /home/w3bwizart/.sprawl_test
Note: To completely uninstall the CLI tool itself, run: pipx uninstall 
sprawl-cli
[*] Deregistered workspace 'qa_workspace' from global tracking.
[*] Destroyed local workspace: 
/home/w3bwizart/Development/sprawl-cli/qa_sandbox/qa_workspace/.agents
[*] Destroyed global DNA registry and configuration: 
/home/w3bwizart/.sprawl_test

✔ Sprawl traces have been wiped.
```

---
