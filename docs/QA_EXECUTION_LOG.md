# Sprawl CLI — Comprehensive QA & Integration Execution Log

* **Execution Date:** 2026-07-05 11:08:19 UTC
* **Local Python Version:** 3.12.3
* **Workspace Root:** `/home/developer/Development/sprawl-cli`
* **Sandbox Directory:** `/home/developer/Development/sprawl-cli/qa_sandbox`
* **Test Mode Home:** `/home/developer/.sprawl_test`

---

## Step 1: Check Version

* **Description:** Verify the dynamically extracted version matches 2.0.2.
* **Command:** `sprawl --version` (cwd: `qa_sandbox`)
* **Execution Time:** `52ms`
* **Status:** **`PASS`** (Expected Code: `0`, Got: `0`)

### Standard Output (stdout):
```text
[*] Sprawl Orchestrator 2.0.2 (Atomic Agentic Fabric)
```

---

## Step 2: Man Page Output

* **Description:** Check the offline AAF manuals output.
* **Command:** `sprawl man` (cwd: `qa_sandbox`)
* **Execution Time:** `94ms`
* **Status:** **`PASS`** (Expected Code: `0`, Got: `0`)

### Standard Output (stdout):
```text
# Sprawl CLI: The Atomic Agentic Fabric                                         
                                                                                
**Stop letting hallucinating agents trash your infrastructure. Orchestrate with 
Zero-Trust.**                                                                   
                                                                                
Welcome to the Master Repository for the **Sprawl CLI**, the enterprise-grade   
execution engine for the **Atomic Agentic Fabric (AAF)**.                       
                                                                                
Right now, the industry is obsessed with building faster AI "Brains." But an AI 
Brain without a secure, governable execution "Body" is a massive liability. The 
Sprawl CLI solves the **Portability Crisis** by decoupling intent from          
execution. It acts as a mandatory governance layer, ensuring your system        
architecture remains deterministic, sandboxed, and immune to OS-level pollution.
                                                                                
We shift software engineering from "Construction" (writing code) to             
"Orchestration" (orchestrating intent) using Universal Dependency Sandboxing and
Sovereign DNA Cloning.                                                          
                                                                                
> For the comprehensive master architecture blueprint, please refer to the      
[Atomic Agentic Fabric Architecture](./architecture/atomic-agentic-fabric.md)   
document.                                                                       
                                                                                
## 🏗️ Clean Room Architecture (v2)                                              
                                                                                
Sprawl v2 is built on the **Clean Room** principle: an AI agent operating inside
a workspace must never know that Sprawl exists, that other projects exist, or   
that a global DNA registry manages the machine. This eliminates OS-level        
pollution and sandbox leakage.                                                  
                                                                                
We achieve this via a **Two-Layer Stealth** architecture:                       
                                                                                
1. **Layer 1: Stealth Injection (Workspace)**                                   
   - The workspace contains an `.agents/` folder.                               
   - The `agents.md` file contains pure persona and rule context, with zero     
Sprawl branding.                                                                
   - The developer defines dependencies in `.agents/sprawl_manifest.yml`. This  
is the ONLY Sprawl-specific file the agent can see.                             
   - IDE rules (`.cursorrules`, `.clinerules`) simply point the agent to        
`agents.md`.                                                                    
                                                                                
2. **Layer 2: Management Plane (Invisible)**                                    
   - All operational metadata (sync state, DNA bindings, last sync timestamps)  
lives outside the workspace in `~/.sprawl/workspaces/`.                         
   - The Sprawl engine strictly manages this separation, pulling from the global
DNA core and silently updating the local workspace.                             
                                                                                
## 🚀 The Fresh Start Workflow (Installation & Setup)                           
                                                                                
If you are deploying to a fresh machine or starting completely from scratch,    
follow this zero-friction pipeline:                                             
                                                                                
### 1. Install Globally (Zero-Friction Bootstrap)                               
                                                                                
Run the automated installation script. It handles dependency checks, sets up the
Python environment, and dynamically links the executable:                       
                                                                                
```bash                                                                         
curl -sL https://raw.githubusercontent.com/developer/sprawl-cli/main/install.sh 
| bash                                                                          
```                                                                             
                                                                                
*Note: This script automatically leverages `pipx` to securely sandbox the engine
without breaking system Python packages. If `pipx` isn't found, the installer   
automatically provisions it.*                                                   
                                                                                
### 2. Verify Installation                                                      
                                                                                
Ensure the engine is correctly wired into your `$PATH`:                         
                                                                                
```bash                                                                         
sprawl --help                                                                   
```                                                                             
                                                                                
### 3. Initialize the Core Fabric                                               
                                                                                
Initialize your environment by cloning your **Primary Company DNA** (rules,     
skills) from GitHub. This creates your untouchable global `~/.sprawl/core/`     
folder and `~/.sprawl_rc` config.                                               
                                                                                
```bash                                                                         
# To test the system immediately, use the official Demo DNA:                    
sprawl init https://github.com/developer/atomic-agentic-fabric-demo-dna.git     
                                                                                
# Or initialize with your own private DNA:                                      
# sprawl init <YOUR_GIT_URL> [TARGET_DIR]                                       
```                                                                             
                                                                                
<!-- ![Sprawl Init Execution](marketing/assets/sprawl_init.webp) -->            
                                                                                
### 4. Fetch Secondary DNA Contexts (Optional)                                  
                                                                                
If you work on multiple isolated domains (e.g. Marketing vs. Engineering), you  
can download secondary DNAs into a local registry (`~/.sprawl/dna/`) without    
overwriting your Core Fabric:                                                   
                                                                                
```bash                                                                         
sprawl fetch-dna https://github.com/org/marketing-dna.git marketing             
```                                                                             
                                                                                
You can also hardcode aliases like `@marketing` directly into                   
`src/sprawl/utils.py`. Once a context is registered, you can instantly bind any 
local workspace to it by running `sprawl init @marketing`.                      
                                                                                
That's it. You're fully operational.                                            
                                                                                
---                                                                             
                                                                                
## 🛠️ Sprawl CLI Workspace Guide                                                
                                                                                
Once you are initialized, you can use the Sprawl CLI to effortlessly manage your
environments.                                                                   
                                                                                
> [!NOTE]                                                                       
> **DNA Context Binding:** The `init` command securely locks your workspace to a
specific DNA alias. This binding is stored in Sprawl's hidden management plane  
(`~/.sprawl/workspaces/`), ensuring no `.sprawl_dna` file leaks into your       
workspace. `sprawl sync` reads this binding to ensure it only pulls logic from  
the correct `~/.sprawl/dna/<alias>/` registry.                                  
                                                                                
### Step 1: Create a New Workspace Scaffold                                     
                                                                                
Start a new workspace project within your Sprawl Hub (or your chosen            
`TARGET_DIR`).                                                                  
                                                                                
```bash                                                                         
sprawl create <WORKSPACE_NAME>                                                  
```                                                                             
                                                                                
*Creates the workspace directory `~/Documents/Sprawl/<WORKSPACE_NAME>/` and     
automatically drops a blank `.agents/sprawl_manifest.yml` inside.*              
                                                                                
### Step 2: Discover & Inject Dependencies                                      
                                                                                
Navigate into your newly created workspace directory.                           
                                                                                
```bash                                                                         
cd ~/Documents/Sprawl/<WORKSPACE_NAME>/                                         
```                                                                             
                                                                                
You no longer need to manually edit configuration files. Use the **Discovery    
Engine** to scan your DNA registry for available rules, skills, personas, atoms,
and workflows:                                                                  
                                                                                
```bash                                                                         
sprawl ls                                                                       
```                                                                             
                                                                                
Once you know what you need, use the **Smart Injection Engine** to automatically
inject the dependencies. It intelligently infers the correct categories,        
rewrites your `.agents/sprawl_manifest.yml` manifest, and triggers an instant   
synchronization:                                                                
                                                                                
```bash                                                                         
sprawl add engineering.md web_artifacts_builder                                 
```                                                                             
                                                                                
### Step 3: Removing Dependencies (Undo)                                        
                                                                                
If you need to change context or permanently remove a dependency, use the       
**Symmetrical Removal Engine**:                                                 
                                                                                
```bash                                                                         
sprawl rm persona-sec_agent                                                     
```                                                                             
                                                                                
This will strip the dependency from your `.agents/sprawl_manifest.yml` manifest 
and dynamically trigger a **Strict Pruning Sync** to securely erase the ghost   
artifact from your local workspace.                                             
                                                                                
### Step 4: Manual Sync (Optional)                                              
                                                                                
If you decide to manually edit the `.agents/sprawl_manifest.yml` or if you need 
to manually force a sync, simply run:                                           
                                                                                
```bash                                                                         
sprawl sync                                                                     
```                                                                             
                                                                                
*This operation securely locks the current workspace and safely links           
dependencies via the Clean Room execution sandbox.*                             
                                                                                
Once synced, `sprawl` automatically performs the following:                     
                                                                                
1. **Workspace Sandboxing**: Automatically ensures isolated boundaries by       
linking directly to the isolated Python sandbox interpreter.                    
2. Mirrors your Sovereign `DESIGN.md`.                                          
3. Scaffolds the structural mapping folders locally.                            
4. **Universal Dependency Sandboxing**: Unconditionally provisions a `.venv`    
Virtual Environment, and dynamically orchestrates local package managers (`pip`,
`npm`, `cargo`) depending on the skills cloned, ensuring AI agents NEVER pollute
your global OS.                                                                 
5. Builds a local `mcp_config.json` that correctly maps to the `.venv` python   
executable.                                                                     
6. Compiles your `AGENTS.md` active registry persona, complete with strict      
isolation instructions.                                                         
7. **Universal IDE/Agent Binding**: Automatically generates Zero-Trust bindings 
(Antigravity `.agent` symlinks, `.cursorrules`, `.clinerules`, `.windsurfrules`,
`.github/copilot-instructions.md`) to seamlessly connect your Sprawl DNA        
directly to your preferred AI editors.                                          
                                                                                
### Step 5: Universal IDE & Agent Binding (Manual)                              
                                                                                
If you are setting up a workspace without running a full sync, or need to       
forcefully bridge your `.agents/` source of truth to a new IDE, use the `bind`  
command:                                                                        
                                                                                
```bash                                                                         
sprawl bind [--force]                                                           
```                                                                             
                                                                                
This acts as a **Universal Adapter**, automatically generating:                 
1. **Antigravity:** Creates a `.agent` symlink and a                            
`.gemini/antigravity/gemini.json` manifest.                                     
2. **Cursor:** Generates a `.cursorrules` file.                                 
3. **RooCode/Cline:** Generates a `.clinerules` file.                           
4. **Windsurf:** Generates a `.windsurfrules` file.                             
5. **GitHub Copilot (VS Code / IntelliJ):** Generates a                         
`.github/copilot-instructions.md` file.                                         
                                                                                
These bindings mandate that your AI agents strictly follow the deterministic    
workflows and personas defined in your Sovereign DNA, preventing them from      
hallucinating outside of your established protocols.                            
                                                                                
### Step 6: Keep the Engine Updated                                             
                                                                                
To keep your entire system up-to-date effortlessly, run:                        
                                                                                
```bash                                                                         
sprawl update                                                                   
```                                                                             
                                                                                
*This powerful dual-target command will securely navigate into your Global DNA  
(`~/.sprawl/core/`) and run a `git pull` to fetch your latest rules and skills. 
Simultaneously, it will intelligently self-update the local Sprawl CLI Engine   
itself if running from a cloned repository, automatically running `pipx install 
. --force` to push the latest source code to your global system path.*          
### Step 7: Nuclear Wipe & Uninstall (`wipe`)                                   
                                                                                
If you want to cleanly remove all Sprawl footprints, databases, directories, and
configurations from your local workspace or your entire system, use the `wipe`  
command:                                                                        
                                                                                
```bash                                                                         
# Nuclear wipe: purges local workspace (.agents/) and global registry           
(~/.sprawl/)                                                                    
sprawl wipe                                                                     
                                                                                
# Wipe local workspace only, leaving the global registry intact                 
sprawl wipe --local-only                                                        
                                                                                
# Force wipe without confirmation prompts                                       
sprawl wipe --force                                                             
```                                                                             
                                                                                
---                                                                             
                                                                                
## 🎬 Native Interactive Demos                                                  
                                                                                
To see the Atomic Agentic Fabric in action without touching your real           
configurations, the Sprawl engine ships with a built-in interactive demo suite. 
                                                                                
Run the following command from anywhere on your machine:                        
                                                                                
```bash                                                                         
sprawl demo                                                                     
```                                                                             
                                                                                
<!-- ![Sprawl Interactive Demo](marketing/assets/sprawl_demo.webp) -->          
                                                                                
You will be presented with an interactive menu of industry-specific scenarios   
(e.g., E-commerce, Fintech, Healthcare). The engine will automatically:         
                                                                                
1. Lock itself into an isolated `--testmode` sandbox.                           
2. Generate a transient Dummy DNA registry.                                     
3. Scaffold multiple cross-functional workspaces (e.g., a React squad and a .NET
squad).                                                                         
4. Auto-inject the correct security rules, APIs, and workflows into their       
respective sandboxes.                                                           
                                                                                
You can safely destroy the entire demo environment (both local workspaces and   
global sandboxes) anytime by running:                                           
                                                                                
```bash                                                                         
sprawl clean-demo                                                               
```                                                                             
                                                                                
---                                                                             
                                                                                
## ⚙️ Enterprise Capabilities                                                   
                                                                                
The newly updated Sprawl Engine possesses the following state-of-the-art native 
runtime modifiers and architectural features:                                   
                                                                                
- **Universal Dependency Sandboxing**: Automatically safeguards client machines 
by resolving `requirements.txt` into highly-contained `.venv` endpoints,        
preventing global OS pollution.                                                 
- **MCP Protocol Binding**: Automatically generates context-rich                
`mcp_config.json` definitions mapping directly to local sandbox paths for       
seamless IDE integration.                                                       
- **Sovereign DNA Cloning**: Mirrors structural rules, tools (molecules), and   
data schemas (atoms) into `AGENTS.md` and isolates the workspace.               
                                                                                
- **Test Mode Sandbox**: A dedicated `--testmode` flag that securely duplicates 
and isolates all system paths (`~/.sprawl/core`, databases, configs) to an      
ephemeral `_test` suffix, allowing for robust local testing without corrupting  
production DNA.                                                                 
- **Sandbox Eradication**: A dedicated `sprawl clean-test` command that         
surgically destroys the parallel test universe without risking active           
development paths.                                                              
- **Diagnostics & Telemetry**:                                                  
  - `sprawl doctor`: Validates global Sprawl Hub integrity, CLI configuration,  
and dependency health.                                                          
  - `sprawl status`: Displays real-time Rich panel telemetry of the active      
workspace, indicating drift, bindings, and manifest state.                      
  - `sprawl diff`: Visually contrasts the local workspace `.agents/` directory  
against the upstream DNA source to detect drift or uncommitted mutations.       
### 🛡️ Sprawl Shell (The Agent Simulator)                                       
                                                                                
`sprawl shell` is your **human bridge** into the AI's isolated execution        
environment.                                                                    
                                                                                
Because Sprawl enforces a strict "Clean Room" architecture, the dependencies,   
libraries, and binaries installed by your AI agents are heavily sandboxed. They 
aren't installed on your global OS.                                             
                                                                                
- **Zero-Friction Debugging:** If your AI agent fails to run a script, type     
`sprawl shell`. You are instantly dropped into the **exact same Python          
environment** the agent uses to debug it manually.                              
- **Manual Package Management:** Need a specific dependency? Run `sprawl shell` 
and type `pip install <package>`. Sprawl guarantees it goes into the workspace  
sandbox, protecting your system Python.                                         
- **Native Binaries:** If the DNA injected `pytest` or an MCP server, they      
aren't in your normal terminal. `sprawl shell` prepends the sandbox to your     
`$PATH` so you can run them natively.                                           
                                                                                
*Think of it as `poetry shell` or `pipenv shell`, but seamlessly tied to your   
Atomic Agentic Fabric.*                                                         
- `sprawl bind [--force]`: Manually generates Universal IDE/Agent Adapters      
(Antigravity, Cursor, RooCode, Windsurf) to bridge the `.agents/` Source of     
Truth to the editor's expected configuration paths.                             
- `sprawl man`: Serves exactly this `README.md` block directly into your        
terminal.                                                                       
- `sprawl sync --dry-run`: Safety net parser. Identifies path structures and    
resolves arrays, but guarantees 0 files will be overwritten or cloned by        
operating purely in standard-out mode.                                          
- `sprawl sync --verbose`: Replaces silent executions with strict native        
logging, outputting exactly which rules, files, and symlink layers are actively 
shifting via Cyber-Brutalist color formatting.                                  
                                                                                
<!-- ![Sprawl Sync Verbose Output](marketing/assets/sprawl_sync_verbose.webp)   
-->                                                                             
                                                                                
- `sprawl --version`: Tracks your deterministic engine architecture dynamic     
builds.                                                                         
- `sprawl --json`: Enables structured JSON logging for programmatic telemetry   
and SIEM integration.                                                           
                                                                                
---                                                                             
                                                                                
## 🎭 Agentic Personas (DNA vs. Lenses)                                         
                                                                                
In the Sprawl ecosystem, it is critical to distinguish between **DNA** and      
**Personas**:                                                                   
                                                                                
- **DNA (The Architecture):** Defines *how* the system operates (e.g.,          
`rules/engineering.md`, `protocols/WASM.md`). It is the sum of the atoms,       
molecules, and organisms that govern the overarching Prime Architect.           
- **Personas (The Lens):** A temporary behavioral override or specific expert   
"hat" an agent can put on. It does not change the underlying architecture; it   
just changes the analytical perspective.                                        
                                                                                
To maintain atomic composability, **Personas are structurally treated as        
Skills**. They reside in the global `~/.sprawl/core/skills/` registry and are   
strictly identified by a `persona-` prefix (e.g., `persona-gtm_specialist`,     
`persona-white_hacker`).                                                        
*Note: Always use role-based naming, not specific character names, for directory
structures.*                                                                    
                                                                                
### 🛠️ Automated Persona Scaffolding                                            
                                                                                
You do not need to manually format boilerplate directories. The CLI natively    
generates this for you:                                                         
                                                                                
```bash                                                                         
sprawl scaffold persona "White Hacker"                                          
```                                                                             
                                                                                
The engine automatically applies the `persona-` prefix, converts the string to  
standard `snake_case`, and scaffolds your structured `SKILL.md` directly into   
your global DNA context.                                                        
                                                                                
---                                                                             
                                                                                
## ⚖️ License & Open Core Model                                                 
                                                                                
The Atomic Agentic Fabric operates on an **Open Core** business model:          
                                                                                
- **Sprawl CLI (Source-Available):** The core orchestration engine and CLI      
tooling are licensed under the **Business Source License 1.1 (BSL)**. It is free
for individuals and small teams, but requires an Enterprise/Partner license for 
large-scale commercial deployments or agency reselling.                         
- **Sprawl Enterprise SaaS (Proprietary):** Advanced capabilities—such as       
role-based access control (RBAC), multi-tenant DNA registries, fleet management,
SOC2/GDPR compliance telemetry, and cloud-hosted dashboards—are proprietary and 
require an Enterprise commercial license.                                       
                                                                                
---                                                                             
                                                                                
## 🏢 Enterprise & Consulting                                                   
                                                                                
The Atomic Agentic Fabric and Sprawl CLI are built on an Open Core model, but   
implementing an enterprise-grade agentic architecture requires precision,       
security, and strategic DNA mapping.                                            
                                                                                
If you are a CTO, Engineering Leader, or SOC Analyst looking to productionize AI
agents without incurring massive semantic debt, we offer premium consulting and 
custom integration pipelines.                                                   
                                                                                
**[Book a Consulting Call ->](https://brainblendai.com)**                       
                                                                                
---                                                                             
                                                                                
## 🧪 Testing Suite                                                             
                                                                                
To ensure the CLI's string-parsing handlers and path configurations are         
executing correctly, this codebase uses Python's native `unittest` suite.       
                                                                                
To execute all tests locally, run from the root directory:                      
                                                                                
```bash                                                                         
python3 -m unittest discover -s tests                                           
```
```

---

## Step 3: Initialize Core DNA

* **Description:** Clones the Sovereign DNA template repo into the isolated core directory (~/.sprawl_test/core).
* **Command:** `sprawl init https://github.com/developer/atomic-agentic-fabric-demo-dna.git` (cwd: `qa_sandbox`)
* **Execution Time:** `822ms`
* **Status:** **`PASS`** (Expected Code: `0`, Got: `0`)

### Standard Output (stdout):
```text
[*] Initializing Sprawl Hub from 
https://github.com/developer/atomic-agentic-fabric-demo-dna.git into 
/home/developer/Documents/Sprawl_Test...
[*] Cloning Global DNA to /home/developer/.sprawl_test/core...
[*] Creating Workspace Hub at /home/developer/Documents/Sprawl_Test...
[*] Initialization complete. Ensure ~/.local/bin is in your PATH.
```

### Error Output (stderr):
```text
Cloning into '/home/developer/.sprawl_test/core'...
```

---

## Step 4: Fetch Alternative DNA

* **Description:** Clones an alternative DNA repository using a custom alias.
* **Command:** `sprawl fetch-dna https://github.com/developer/atomic-agentic-fabric-demo-dna.git alt_dna` (cwd: `qa_sandbox`)
* **Execution Time:** `797ms`
* **Status:** **`PASS`** (Expected Code: `0`, Got: `0`)

### Standard Output (stdout):
```text
[*] Fetching DNA context 'alt_dna' to 
/home/developer/.sprawl_test/dna/alt_dna...
[*] Running Zero-Trust validation on DNA...
[*] DNA Validation passed.
```

### Error Output (stderr):
```text
Cloning into '/home/developer/.sprawl_test/dna/alt_dna'...
```

---

## Step 5: List DNA Registry

* **Description:** Verify both core and alt_dna exist in the registry.
* **Command:** `sprawl dna list` (cwd: `qa_sandbox`)
* **Execution Time:** `49ms`
* **Status:** **`PASS`** (Expected Code: `0`, Got: `0`)

### Standard Output (stdout):
```text
Registered DNA Sources                           
┏━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Status ┃ Alias    ┃ Type      ┃ Path                                     ┃
┡━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│   ●    │ @global  │ Primary   │ /home/developer/.sprawl_test/core        │
│   ●    │ @alt_dna │ Secondary │ /home/developer/.sprawl_test/dna/alt_dna │
└────────┴──────────┴───────────┴──────────────────────────────────────────┘
```

---

## Step 6: Inspect DNA Structure

* **Description:** Display the hierarchical tree of the active core DNA structure.
* **Command:** `sprawl dna inspect` (cwd: `qa_sandbox`)
* **Execution Time:** `49ms`
* **Status:** **`PASS`** (Expected Code: `0`, Got: `0`)

### Standard Output (stdout):
```text
🧬 Global DNA Registry (/home/developer/.sprawl_test/core)
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
* **Execution Time:** `659ms`
* **Status:** **`PASS`** (Expected Code: `0`, Got: `0`)

### Standard Output (stdout):
```text
Already up-to-date.
[*] Global DNA updated successfully.
```

### Error Output (stderr):
```text
From https://github.com/developer/atomic-agentic-fabric-demo-dna
 * branch            main       -> FETCH_HEAD
```

---

## Step 8: Self-Update Dry-Run

* **Description:** Test the auto-updater sequence without modifying path targets.
* **Command:** `sprawl update --dry-run` (cwd: `qa_sandbox`)
* **Execution Time:** `414737ms`
* **Status:** **`PASS`** (Expected Code: `0`, Got: `0`)

### Standard Output (stdout):
```text
[*] Initiating Sprawl Update Sequence...
[*] Updating Global DNA at /home/developer/.sprawl_test/core...
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
From https://github.com/developer/atomic-agentic-fabric-demo-dna
 * branch            main       -> FETCH_HEAD
```

---

## Step 9: Create Workspace

* **Description:** Scaffolds a fresh sandbox workspace configuration.
* **Command:** `sprawl create qa_workspace` (cwd: `qa_sandbox`)
* **Execution Time:** `51ms`
* **Status:** **`PASS`** (Expected Code: `0`, Got: `0`)

### Standard Output (stdout):
```text
╭────────────────────────── Workspace Initialization ──────────────────────────╮
│ ✔ Workspace Created                                                          │
│ • Name: qa_workspace                                                         │
│ • Path: /home/developer/Development/sprawl-cli/qa_sandbox/qa_workspace       │
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
* **Execution Time:** `49ms`
* **Status:** **`PASS`** (Expected Code: `0`, Got: `0`)

### Standard Output (stdout):
```text
Tracked Workspaces                               
┏━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┓
┃ Status ┃ Name         ┃ Path                    ┃ DNA Binding    ┃ Last Sync ┃
┡━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━┩
│   ●    │ qa_workspace │ /home/developer/Develo… │ Global/Default │ Never     │
└────────┴──────────────┴─────────────────────────┴────────────────┴───────────┘
```

---

## Step 11: Workspace Synchronize

* **Description:** Synchronize active DNA parameters and initialize sandbox virtualenvs.
* **Command:** `sprawl sync` (cwd: `qa_workspace`)
* **Execution Time:** `1306ms`
* **Status:** **`PASS`** (Expected Code: `0`, Got: `0`)

### Standard Output (stdout):
```text
[*] Syncing /home/developer/Development/sprawl-cli/qa_sandbox/qa_workspace...
[*] Provisioning sandboxed virtual environment at 
/home/developer/Development/sprawl-cli/qa_sandbox/qa_workspace/.agents/.venv...
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
* **Execution Time:** `54ms`
* **Status:** **`PASS`** (Expected Code: `0`, Got: `0`)

### Standard Output (stdout):
```text
╭───────────────────────────── Workspace Identity ─────────────────────────────╮
│  Workspace             qa_workspace                                          │
│  Path                  /home/developer/Development/sprawl-cli/qa_sandbox/q…  │
│  DNA Binding           @global/core (default)                                │
│  Active Model          Not set                                               │
│  Venv                  ● Healthy (Python 3.12.3)                             │
│  Last Sync             2026-07-05T11:15:18.602313+00:00                      │
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
* **Execution Time:** `55ms`
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
[*] Syncing /home/developer/Development/sprawl-cli/qa_sandbox/qa_workspace...
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
* **Execution Time:** `50ms`
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
* **Execution Time:** `86ms`
* **Status:** **`PASS`** (Expected Code: `0`, Got: `0`)

### Standard Output (stdout):
```text
[*] Removed workspace mount: test_tmp (was mapping to /tmp)
[*] Synchronizing workspace configurations...
[*] Syncing /home/developer/Development/sprawl-cli/qa_sandbox/qa_workspace...
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
* **Execution Time:** `51ms`
* **Status:** **`PASS`** (Expected Code: `0`, Got: `0`)

### Standard Output (stdout):
```text
╭──────────────────────────────── DNA Registry ────────────────────────────────╮
│                                                                              │
│ Installed Contexts:                                                          │
│   • @global (Default Sprawl Hub DNA)                                         │
│   • @alt_dna                                                                 │
│                                                                              │
│ Active Context: /home/developer/.sprawl_test/core                            │
╰──────────────────────────────────────────────────────────────────────────────╯

🧬 Active DNA Artifacts (/home/developer/.sprawl_test/core)
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
* **Execution Time:** `53ms`
* **Status:** **`PASS`** (Expected Code: `0`, Got: `0`)

### Standard Output (stdout):
```text
[*] Persona Scaffolded successfully: 'persona-verification-squad'
[*] Generated boilerplate at 
/home/developer/.sprawl_test/core/skills/persona-verification-squad/SKILL.md
```

---

## Step 19: Add Skill Dependency

* **Description:** Incorporate persona-demo_engineer dependency inside local manifest.
* **Command:** `sprawl add persona-demo_engineer` (cwd: `qa_workspace`)
* **Execution Time:** `85ms`
* **Status:** **`PASS`** (Expected Code: `0`, Got: `0`)

### Standard Output (stdout):
```text
[*] Resolving dependency: 'persona-demo_engineer' into 
[*] Modifying sprawl_manifest.yml...
[*] Injecting DNA...
[*] Syncing /home/developer/Development/sprawl-cli/qa_sandbox/qa_workspace...
[*] Generating IDE & Agent bindings (standard mode)...
  ○ Claude Code Binding: already exists (use --force to overwrite)
  ○ RooCode/Cline Binding: already exists (use --force to overwrite)
  ✔ Codex Binding: Created symlink → ../AGENTS.md
  ○ GitHub Copilot Binding: already exists (use --force to overwrite)
[*] Exported Copilot prompt: .github/prompts/persona-demo_engineer.prompt.md
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
│ • Files Synced: 1                                                            │
│ • Files Pruned: 0                                                            │
│ • Venv Provisioned: Existing                                                 │
│ • Bindings Created: Yes                                                      │
╰──────────────────────────────────────────────────────────────────────────────╯
[*] [+] Skill 'persona-demo_engineer' successfully sandboxed.
```

---

## Step 20: Prune/Remove Dependency

* **Description:** Safely strip dependencies and trigger workspace manifest cleanups.
* **Command:** `sprawl rm persona-demo_engineer` (cwd: `qa_workspace`)
* **Execution Time:** `84ms`
* **Status:** **`PASS`** (Expected Code: `0`, Got: `0`)

### Standard Output (stdout):
```text
[*] Removing dependency: 'persona-demo_engineer'
[*] Manifest updated. Triggering synchronization cleanup...
[*] Syncing /home/developer/Development/sprawl-cli/qa_sandbox/qa_workspace...
[*] [Pruned] persona-demo_engineer removed from local skills/
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
│ • Files Pruned: 1                                                            │
│ • Venv Provisioned: Existing                                                 │
│ • Bindings Created: Yes                                                      │
╰──────────────────────────────────────────────────────────────────────────────╯
```

---

## Step 21: Doctor Verification

* **Description:** Verify that all required tool and folder assertions pass.
* **Command:** `sprawl doctor` (cwd: `qa_workspace`)
* **Execution Time:** `54ms`
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
│ Global DNA      │ ✔ PASS │ Initialized at /home/developer/.sprawl_test/core  │
│ Local Workspace │ ✔ PASS │ Active at                                         │
│                 │        │ /home/developer/Development/sprawl-cli/qa_sandbo… │
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
* **Execution Time:** `54ms`
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
* **Execution Time:** `5082ms`
* **Status:** **`PASS`** (Expected Code: `0`, Got: `0`)

### Standard Output (stdout):
```text
[*] Starting Demo: Cross-Team Scaffolding
[*] Ensuring clean test environment...
[*] Nuking all testmode artifacts...
[*] [-] Deleted /home/developer/.sprawl_test/core
[*] [-] Deleted /home/developer/Documents/Sprawl_Test
[*] [-] Deleted /home/developer/.sprawl_test/config.json
[*] Testmode environment cleanly destroyed.
[*] Generating Transient Dummy DNA...
[*] Initializing Central Hub...
[*] Initializing Sprawl Hub from file:///tmp/sprawl_dummy_dna_sgxt_t8g into 
/home/developer/Documents/Sprawl_Test...
[*] Cloning Global DNA to /home/developer/.sprawl_test/core...
[*] Creating Workspace Hub at /home/developer/Documents/Sprawl_Test...
[*] Initialization complete. Ensure ~/.local/bin is in your PATH.
[*] Isolating demo workspaces in /tmp/sprawl_demo_osil2rsx...

=========================================
   TEAM 1: DOTNET-SQUAD
=========================================

╭────────────────────────── Workspace Initialization ──────────────────────────╮
│ ✔ Workspace Created                                                          │
│ • Name: dotnet-squad                                                         │
│ • Path: /tmp/sprawl_demo_osil2rsx/dotnet-squad                               │
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
[*] Syncing /tmp/sprawl_demo_osil2rsx/dotnet-squad...
[*] Provisioning sandboxed virtual environment at 
/tmp/sprawl_demo_osil2rsx/dotnet-squad/.agents/.venv...
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
│ • Path: /tmp/sprawl_demo_osil2rsx/web-squad                                  │
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
[*] Syncing /tmp/sprawl_demo_osil2rsx/web-squad...
[*] Provisioning sandboxed virtual environment at 
/tmp/sprawl_demo_osil2rsx/web-squad/.agents/.venv...
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
│ • Path: /tmp/sprawl_demo_osil2rsx/sales-squad                                │
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
[*] Syncing /tmp/sprawl_demo_osil2rsx/sales-squad...
[*] Provisioning sandboxed virtual environment at 
/tmp/sprawl_demo_osil2rsx/sales-squad/.agents/.venv...
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
│ • Path: /tmp/sprawl_demo_osil2rsx/legacy-squad                               │
│ • DNA Binding: @core                                                         │
│                                                                              │
│ • Run sprawl bind inside to select rules bindings for your IDEs/agents.      │
│ • Run sprawl sync inside to orchestrate.                                     │
╰──────────────────────────────────────────────────────────────────────────────╯
[*] Syncing /tmp/sprawl_demo_osil2rsx/legacy-squad...
[*] Provisioning sandboxed virtual environment at 
/tmp/sprawl_demo_osil2rsx/legacy-squad/.agents/.venv...
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
Cloning into '/home/developer/.sprawl_test/core'...
```

---

## Step 24: Clean Demo Workspaces

* **Description:** Delete the directories generated by the demo walkthrough.
* **Command:** `sprawl clean-demo` (cwd: `qa_sandbox`)
* **Execution Time:** `52ms`
* **Status:** **`PASS`** (Expected Code: `0`, Got: `0`)

### Standard Output (stdout):
```text
[!] WARNING: No sprawl_demo directory found at 
/home/developer/Development/sprawl-cli/qa_sandbox/sprawl_demo.
[*] Triggering testmode artifact cleanup...
[*] Nuking all testmode artifacts...
[*] [-] Deleted /home/developer/.sprawl_test/core
[*] [-] Deleted /home/developer/Documents/Sprawl_Test
[*] [-] Deleted /home/developer/.sprawl_test/config.json
[*] Testmode environment cleanly destroyed.
```

---

## Step 25: Clean Test Mode Assets

* **Description:** Destroys all isolated directories.
* **Command:** `sprawl clean-test` (cwd: `qa_sandbox`)
* **Execution Time:** `52ms`
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
* **Execution Time:** `63ms`
* **Status:** **`PASS`** (Expected Code: `0`, Got: `0`)

### Standard Output (stdout):
```text
!!! NUCLEAR WIPE INITIATED !!!
Will destroy local workspace: 
/home/developer/Development/sprawl-cli/qa_sandbox/qa_workspace/.agents
Will destroy global DNA registry & configuration: /home/developer/.sprawl_test
Note: To completely uninstall the CLI tool itself, run: pipx uninstall 
sprawl-cli
[*] Deregistered workspace 'qa_workspace' from global tracking.
[*] Destroyed local workspace: 
/home/developer/Development/sprawl-cli/qa_sandbox/qa_workspace/.agents
[*] Destroyed global DNA registry and configuration: 
/home/developer/.sprawl_test

✔ Sprawl traces have been wiped.
```

---