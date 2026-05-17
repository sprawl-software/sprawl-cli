# Sprawl CLI - 5-Minute Quickstart

This guide will take you from zero to a fully sandboxed, deterministic AI workspace in 5 minutes.

## 1. Install Sprawl

Run the automated installation script. This provisions Sprawl via `pipx` to protect your system environment.

```bash
curl -sL https://raw.githubusercontent.com/w3bwizart/sprawl-cli/main/install.sh | bash
```

## 2. Initialize the Core DNA

Initialize your global environment by cloning your chosen rules and skills (the "DNA") from a Git repository.

```bash
sprawl init https://github.com/w3bwizart/atomic-agentic-fabric-demo-dna.git
```

*This creates your `~/.sprawl/core/` registry.*

## 3. Create a Workspace

Create a new project folder scaffolded by Sprawl.

```bash
sprawl create my-agent-project
cd my-agent-project
```

*Notice a `.agents/sprawl_manifest.yml` file is automatically created inside.*

## 4. Inject Dependencies

Search your available DNA registry and inject the rules and skills you need for this specific project.

```bash
sprawl ls
sprawl add python web-dev persona-master-engineer
```

*This automatically updates your `.agents/sprawl_manifest.yml`.*

## 5. Sync the Environment

Lock the workspace and execute the Clean Room injection.

```bash
sprawl sync
```

*This command creates an isolated .venv, enforces the Clean Room sandbox, and generates your strict AGENTS.md context file without polluting the workspace with Sprawl-specific artifacts.*

## 6. Configure Your IDE

Sprawl automatically generates Universal Agent Bindings for popular IDEs (`.cursorrules`, `.clinerules`, `.windsurfrules`).
If you are using a different environment or want to force a regeneration, run:

```bash
sprawl bind --force
```

Your AI agent is now strictly bound to the protocols defined in `AGENTS.md` and cannot operate outside of this sandboxed directory.

**Congratulations! Your deterministic workspace is ready.**
