# Sprawl CLI: The Atomic Agentic Fabric

**Stop letting hallucinating agents trash your infrastructure. Orchestrate with Zero-Trust.**

Welcome to the Master Repository for the **Sprawl CLI**, the enterprise-grade execution engine for the **Atomic Agentic Fabric (AAF)**.

Right now, the industry is obsessed with building faster AI "Brains." But an AI Brain without a secure, governable execution "Body" is a massive liability. The Sprawl CLI solves the **Portability Crisis** by decoupling intent from execution. It acts as a mandatory governance layer, ensuring your system architecture remains deterministic, sandboxed, and immune to OS-level pollution.

We shift software engineering from "Construction" (writing code) to "Orchestration" (orchestrating intent) using Universal Dependency Sandboxing and Sovereign DNA Cloning.

> For the comprehensive master architecture blueprint, please refer to the [Atomic Agentic Fabric Architecture](./architecture/atomic-agentic-fabric.md) document.

## 🏗️ Clean Room Architecture (v2)

Sprawl v2 is built on the **Clean Room** principle: an AI agent operating inside a workspace must never know that Sprawl exists, that other projects exist, or that a global DNA registry manages the machine. This eliminates OS-level pollution and sandbox leakage.

We achieve this via a **Two-Layer Stealth** architecture:

1. **Layer 1: Stealth Injection (Workspace)**
   - The workspace contains an `.agents/` folder.
   - The `agents.md` file contains pure persona and rule context, with zero Sprawl branding.
   - The developer defines dependencies in `.agents/sprawl_manifest.yml`. This is the ONLY Sprawl-specific file the agent can see.
   - IDE rules (`.cursorrules`, `.clinerules`) simply point the agent to `agents.md`.

2. **Layer 2: Management Plane (Invisible)**
   - All operational metadata (sync state, DNA bindings, last sync timestamps) lives outside the workspace in `~/.sprawl/workspaces/`.
   - The Sprawl engine strictly manages this separation, pulling from the global DNA core and silently updating the local workspace.

## 🚀 The Fresh Start Workflow (Installation & Setup)

If you are deploying to a fresh machine or starting completely from scratch, follow this zero-friction pipeline:

### 1. Install Globally (Zero-Friction Bootstrap)

Run the automated installation script. It handles dependency checks, sets up the Python environment, and dynamically links the executable:

```bash
curl -sL https://raw.githubusercontent.com/sprawl-software/sprawl-cli/main/install.sh | bash
```

*Note: This script automatically leverages `pipx` to securely sandbox the engine without breaking system Python packages. If `pipx` isn't found, the installer automatically provisions it.*

### 2. Verify Installation

Ensure the engine is correctly wired into your `$PATH`:

```bash
sprawl --help
```

### 3. Initialize the Core Fabric

Initialize your environment by cloning your **Primary Company DNA** (rules, skills) from GitHub. This creates your untouchable global `~/.sprawl/core/` folder and `~/.sprawl_rc` config.

```bash
# To test the system immediately, use the official Demo DNA:
sprawl init https://github.com/sprawl-software/atomic-agentic-fabric-demo-dna.git

# Or initialize with your own private DNA:
# sprawl init <YOUR_GIT_URL> [TARGET_DIR]
```

<!-- ![Sprawl Init Execution](marketing/assets/sprawl_init.webp) -->

### 4. Fetch Secondary DNA Contexts (Optional)

If you work on multiple isolated domains (e.g. Marketing vs. Engineering), you can download secondary DNAs into a local registry (`~/.sprawl/dna/`) without overwriting your Core Fabric:

```bash
sprawl fetch-dna https://github.com/org/marketing-dna.git marketing
```

You can also hardcode aliases like `@marketing` directly into `src/sprawl/utils.py`. Once a context is registered, you can instantly bind any local workspace to it by running `sprawl init @marketing`.

That's it. You're fully operational.

---

## 🛠️ Sprawl CLI Workspace Guide

Once you are initialized, you can use the Sprawl CLI to effortlessly manage your environments.

> [!NOTE]
> **DNA Context Binding:** The `init` command securely locks your workspace to a specific DNA alias. This binding is stored in Sprawl's hidden management plane (`~/.sprawl/workspaces/`), ensuring no `.sprawl_dna` file leaks into your workspace. `sprawl sync` reads this binding to ensure it only pulls logic from the correct `~/.sprawl/dna/<alias>/` registry.

### Step 1: Create a New Workspace Scaffold

Start a new workspace project within your Sprawl Hub (or your chosen `TARGET_DIR`).

```bash
sprawl create <WORKSPACE_NAME>
```

*Creates the workspace directory `~/Documents/Sprawl/<WORKSPACE_NAME>/` and automatically drops a blank `.agents/sprawl_manifest.yml` inside.*

### Step 2: Discover & Inject Dependencies

Navigate into your newly created workspace directory.

```bash
cd ~/Documents/Sprawl/<WORKSPACE_NAME>/
```

You no longer need to manually edit configuration files. Use the **Discovery Engine** to scan your DNA registry for available rules, skills, personas, atoms, and workflows:

```bash
sprawl ls
```

Once you know what you need, use the **Smart Injection Engine** to automatically inject the dependencies. It intelligently infers the correct categories, rewrites your `.agents/sprawl_manifest.yml` manifest, and triggers an instant synchronization:

```bash
sprawl add engineering.md web_artifacts_builder
```

### Step 3: Removing Dependencies (Undo)

If you need to change context or permanently remove a dependency, use the **Symmetrical Removal Engine**:

```bash
sprawl rm persona-sec_agent
```

This will strip the dependency from your `.agents/sprawl_manifest.yml` manifest and dynamically trigger a **Strict Pruning Sync** to securely erase the ghost artifact from your local workspace.

### Step 4: Manual Sync (Optional)

If you decide to manually edit the `.agents/sprawl_manifest.yml` or if you need to manually force a sync, simply run:

```bash
sprawl sync
```

*This operation securely locks the current workspace and safely links dependencies via the Clean Room execution sandbox.*

Once synced, `sprawl` automatically performs the following:

1. **Workspace Sandboxing**: Automatically ensures isolated boundaries by linking directly to the isolated Python sandbox interpreter.
2. Mirrors your Sovereign `DESIGN.md`.
3. Scaffolds the structural mapping folders locally.
4. **Universal Dependency Sandboxing**: Unconditionally provisions a `.venv` Virtual Environment, and dynamically orchestrates local package managers (`pip`, `npm`, `cargo`) depending on the skills cloned, ensuring AI agents NEVER pollute your global OS.
5. Builds a local `mcp_config.json` that correctly maps to the `.venv` python executable.
6. Compiles your `AGENTS.md` active registry persona, complete with strict isolation instructions.
7. **Universal IDE/Agent Binding**: Automatically generates Zero-Trust bindings (Antigravity `.agent` symlinks, `.cursorrules`, `.clinerules`, `.windsurfrules`, `.github/copilot-instructions.md`) to seamlessly connect your Sprawl DNA directly to your preferred AI editors.

### Step 5: Universal IDE & Agent Binding (Manual)

If you are setting up a workspace without running a full sync, or need to forcefully bridge your `.agents/` source of truth to a new IDE, use the `bind` command:

```bash
sprawl bind [--force]
```

This acts as a **Universal Adapter**, automatically generating:
1. **Antigravity:** Creates a `.agent` symlink and a `.gemini/antigravity/gemini.json` manifest.
2. **Cursor:** Generates a `.cursorrules` file.
3. **RooCode/Cline:** Generates a `.clinerules` file.
4. **Windsurf:** Generates a `.windsurfrules` file.
5. **GitHub Copilot (VS Code / IntelliJ):** Generates a `.github/copilot-instructions.md` file.

These bindings mandate that your AI agents strictly follow the deterministic workflows and personas defined in your Sovereign DNA, preventing them from hallucinating outside of your established protocols.

### Step 6: Keep the Engine Updated

To keep your entire system up-to-date effortlessly, run:

```bash
sprawl update
```

*This powerful dual-target command will securely navigate into your Global DNA (`~/.sprawl/core/`) and run a `git pull` to fetch your latest rules and skills. Simultaneously, it will intelligently self-update the local Sprawl CLI Engine itself if running from a cloned repository, automatically running `pipx install . --force` to push the latest source code to your global system path.*
### Step 7: Nuclear Wipe & Uninstall (`wipe`)

If you want to cleanly remove all Sprawl footprints, databases, directories, and configurations from your local workspace or your entire system, use the `wipe` command:

```bash
# Nuclear wipe: purges local workspace (.agents/) and global registry (~/.sprawl/)
sprawl wipe

# Wipe local workspace only, leaving the global registry intact
sprawl wipe --local-only

# Force wipe without confirmation prompts
sprawl wipe --force
```

---

## 🎬 Native Interactive Demos

To see the Atomic Agentic Fabric in action without touching your real configurations, the Sprawl engine ships with a built-in interactive demo suite.

Run the following command from anywhere on your machine:

```bash
sprawl demo
```

<!-- ![Sprawl Interactive Demo](marketing/assets/sprawl_demo.webp) -->

You will be presented with an interactive menu of industry-specific scenarios (e.g., E-commerce, Fintech, Healthcare). The engine will automatically:

1. Lock itself into an isolated `--testmode` sandbox.
2. Generate a transient Dummy DNA registry.
3. Scaffold multiple cross-functional workspaces (e.g., a React squad and a .NET squad).
4. Auto-inject the correct security rules, APIs, and workflows into their respective sandboxes.

You can safely destroy the entire demo environment (both local workspaces and global sandboxes) anytime by running:

```bash
sprawl clean-demo
```

---

## ⚙️ Enterprise Capabilities

The newly updated Sprawl Engine possesses the following state-of-the-art native runtime modifiers and architectural features:

- **Universal Dependency Sandboxing**: Automatically safeguards client machines by resolving `requirements.txt` into highly-contained `.venv` endpoints, preventing global OS pollution.
- **MCP Protocol Binding**: Automatically generates context-rich `mcp_config.json` definitions mapping directly to local sandbox paths for seamless IDE integration.
- **Sovereign DNA Cloning**: Mirrors structural rules, tools (molecules), and data schemas (atoms) into `AGENTS.md` and isolates the workspace.

- **Test Mode Sandbox**: A dedicated `--testmode` flag that securely duplicates and isolates all system paths (`~/.sprawl/core`, databases, configs) to an ephemeral `_test` suffix, allowing for robust local testing without corrupting production DNA.
- **Sandbox Eradication**: A dedicated `sprawl clean-test` command that surgically destroys the parallel test universe without risking active development paths.
- **Diagnostics & Telemetry**:
  - `sprawl doctor`: Validates global Sprawl Hub integrity, CLI configuration, and dependency health.
  - `sprawl status`: Displays real-time Rich panel telemetry of the active workspace, indicating drift, bindings, and manifest state.
  - `sprawl diff`: Visually contrasts the local workspace `.agents/` directory against the upstream DNA source to detect drift or uncommitted mutations.
### 🛡️ Sprawl Shell (The Agent Simulator)

`sprawl shell` is your **human bridge** into the AI's isolated execution environment. 

Because Sprawl enforces a strict "Clean Room" architecture, the dependencies, libraries, and binaries installed by your AI agents are heavily sandboxed. They aren't installed on your global OS. 

- **Zero-Friction Debugging:** If your AI agent fails to run a script, type `sprawl shell`. You are instantly dropped into the **exact same Python environment** the agent uses to debug it manually.
- **Manual Package Management:** Need a specific dependency? Run `sprawl shell` and type `pip install <package>`. Sprawl guarantees it goes into the workspace sandbox, protecting your system Python.
- **Native Binaries:** If the DNA injected `pytest` or an MCP server, they aren't in your normal terminal. `sprawl shell` prepends the sandbox to your `$PATH` so you can run them natively.

*Think of it as `poetry shell` or `pipenv shell`, but seamlessly tied to your Atomic Agentic Fabric.*
- `sprawl bind [--force]`: Manually generates Universal IDE/Agent Adapters (Antigravity, Cursor, RooCode, Windsurf) to bridge the `.agents/` Source of Truth to the editor's expected configuration paths.
- `sprawl man`: Serves exactly this `README.md` block directly into your terminal.
- `sprawl sync --dry-run`: Safety net parser. Identifies path structures and resolves arrays, but guarantees 0 files will be overwritten or cloned by operating purely in standard-out mode.
- `sprawl sync --verbose`: Replaces silent executions with strict native logging, outputting exactly which rules, files, and symlink layers are actively shifting via Cyber-Brutalist color formatting.

<!-- ![Sprawl Sync Verbose Output](marketing/assets/sprawl_sync_verbose.webp) -->

- `sprawl --version`: Tracks your deterministic engine architecture dynamic builds.
- `sprawl --json`: Enables structured JSON logging for programmatic telemetry and SIEM integration.

---

## 🎭 Agentic Personas (DNA vs. Lenses)

In the Sprawl ecosystem, it is critical to distinguish between **DNA** and **Personas**:

- **DNA (The Architecture):** Defines *how* the system operates (e.g., `rules/engineering.md`, `protocols/WASM.md`). It is the sum of the atoms, molecules, and organisms that govern the overarching Prime Architect.
- **Personas (The Lens):** A temporary behavioral override or specific expert "hat" an agent can put on. It does not change the underlying architecture; it just changes the analytical perspective.

To maintain atomic composability, **Personas are structurally treated as Skills**. They reside in the global `~/.sprawl/core/skills/` registry and are strictly identified by a `persona-` prefix (e.g., `persona-gtm_specialist`, `persona-white_hacker`).
*Note: Always use role-based naming, not specific character names, for directory structures.*

### 🛠️ Automated Persona Scaffolding

You do not need to manually format boilerplate directories. The CLI natively generates this for you:

```bash
sprawl scaffold persona "White Hacker"
```

The engine automatically applies the `persona-` prefix, converts the string to standard `snake_case`, and scaffolds your structured `SKILL.md` directly into your global DNA context.

---

## ⚖️ License & Open Core Model

The Atomic Agentic Fabric operates on an **Open Core** business model:

- **Sprawl CLI (Source-Available):** The core orchestration engine and CLI tooling are licensed under the **Business Source License 1.1 (BSL)**. It is free for individuals and small teams, but requires an Enterprise/Partner license for large-scale commercial deployments or agency reselling.
- **Sprawl Enterprise SaaS (Proprietary):** Advanced capabilities—such as role-based access control (RBAC), multi-tenant DNA registries, fleet management, SOC2/GDPR compliance telemetry, and cloud-hosted dashboards—are proprietary and require an Enterprise commercial license.

---

## 🏢 Enterprise & Consulting

The Atomic Agentic Fabric and Sprawl CLI are built on an Open Core model, but implementing an enterprise-grade agentic architecture requires precision, security, and strategic DNA mapping.

If you are a CTO, Engineering Leader, or SOC Analyst looking to productionize AI agents without incurring massive semantic debt, we offer premium consulting and custom integration pipelines.

**[Book a Consulting Call ->](https://brainblendai.com)**

---

## 🧪 Testing Suite

To ensure the CLI's string-parsing handlers and path configurations are executing correctly, this codebase uses Python's native `unittest` suite.

To execute all tests locally, run from the root directory:

```bash
python3 -m unittest discover -s tests
```
