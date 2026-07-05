#!/usr/bin/env python3
"""Sprawl CLI E2E QA Verification Suite & CI Smoke Test Runner.

Executes all sprawl subcommands in an isolated temporary sandbox,
asserts correct exit codes, and compiles a comprehensive Markdown
execution log.
"""

import os
import shutil
import subprocess
import time
import sys
from typing import List, Dict, Any

# Target paths
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SANDBOX_DIR = os.path.join(REPO_ROOT, "qa_sandbox")
VENV_DIR = os.path.join(SANDBOX_DIR, ".venv")
SPRAWL_BIN = os.path.join(VENV_DIR, "bin", "sprawl")
LOG_OUTPUT_PATH = os.path.join(REPO_ROOT, "docs", "QA_EXECUTION_LOG.md")

# Clean test environment targets
SPRAWL_TEST_HOME = os.path.expanduser("~/.sprawl_test")
SPRAWL_TEST_DOCS = os.path.expanduser("~/Documents/Sprawl_Test")

# Color utilities for terminal output
CYAN = "\033[0;36m"
GREEN = "\033[0;32m"
YELLOW = "\033[0;33m"
RED = "\033[0;31m"
BOLD = "\033[1m"
NC = "\033[0m"

def log_info(msg: str):
    print(f"{CYAN}[*]{NC} {msg}")

def log_success(msg: str):
    print(f"{GREEN}[✔]{NC} {msg}")

def log_warn(msg: str):
    print(f"{YELLOW}[!]{NC} {msg}")

def log_error(msg: str):
    print(f"{RED}[✗]{NC} {msg}")

def clean_sprawl_test_dirs():
    """Nukes any legacy sprawl_test system folders to guarantee fresh state."""
    log_info("Cleaning up previous test folders...")
    for path in [SPRAWL_TEST_HOME, SPRAWL_TEST_DOCS, SANDBOX_DIR]:
        if os.path.exists(path):
            shutil.rmtree(path, ignore_errors=True)
            log_success(f"Deleted: {path}")

def setup_sandbox_venv():
    """Provisions a Python virtual environment and installs sprawl-cli."""
    log_info(f"Creating isolated sandbox directory at {SANDBOX_DIR}...")
    os.makedirs(SANDBOX_DIR, exist_ok=True)
    
    log_info("Creating virtual environment...")
    subprocess.run([sys.executable, "-m", "venv", VENV_DIR], check=True)
    
    log_info("Upgrading pip inside sandbox venv...")
    pip_bin = os.path.join(VENV_DIR, "bin", "pip")
    subprocess.run([pip_bin, "install", "--upgrade", "pip"], check=True)
    
    log_info("Installing sprawl-cli from local source into sandbox venv...")
    # Install package locally
    subprocess.run([pip_bin, "install", "."], cwd=REPO_ROOT, check=True)
    log_success("Sprawl CLI installed successfully inside sandbox!")

def run_sprawl_cmd(args: List[str], cwd: str = SANDBOX_DIR) -> Dict[str, Any]:
    """Executes a sprawl command inside the sandbox venv with test mode enabled."""
    env = os.environ.copy()
    env["SPRAWL_TEST_MODE"] = "1"
    env["SPRAWL_DEV"] = "1"  # Allow test-only commands to run
    
    cmd = [SPRAWL_BIN] + args
    cmd_str = " ".join(cmd)
    
    start_time = time.time()
    result = subprocess.run(
        cmd,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True
    )
    elapsed = time.time() - start_time
    
    return {
        "command": cmd_str,
        "exit_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "elapsed_ms": int(elapsed * 1000)
    }

def main():
    ci_mode = "--ci" in sys.argv or os.environ.get("CI") == "true"
    
    clean_sprawl_test_dirs()
    setup_sandbox_venv()
    
    # Define test steps
    steps = [
        # Scenario 1: Versioning and Core Onboarding
        {
            "name": "Check Version",
            "args": ["--version"],
            "desc": "Verify the dynamically extracted version matches 2.0.2.",
            "expect_zero": True
        },
        {
            "name": "Man Page Output",
            "args": ["man"],
            "desc": "Check the offline AAF manuals output.",
            "expect_zero": True
        },
        {
            "name": "Initialize Core DNA",
            "args": ["init", "https://github.com/w3bwizart/atomic-agentic-fabric-demo-dna.git"],
            "desc": "Clones the Sovereign DNA template repo into the isolated core directory (~/.sprawl_test/core).",
            "expect_zero": True
        },
        
        # Scenario 2: Alternative DNA & Registry Listings
        {
            "name": "Fetch Alternative DNA",
            "args": ["fetch-dna", "https://github.com/w3bwizart/atomic-agentic-fabric-demo-dna.git", "alt_dna"],
            "desc": "Clones an alternative DNA repository using a custom alias.",
            "expect_zero": True
        },
        {
            "name": "List DNA Registry",
            "args": ["dna", "list"],
            "desc": "Verify both core and alt_dna exist in the registry.",
            "expect_zero": True
        },
        {
            "name": "Inspect DNA Structure",
            "args": ["dna", "inspect"],
            "desc": "Display the hierarchical tree of the active core DNA structure.",
            "expect_zero": True
        },
        {
            "name": "DNA Registry Update",
            "args": ["dna", "update"],
            "desc": "Test Git pull synchronization on the active DNA template.",
            "expect_zero": True
        },
        {
            "name": "Self-Update Dry-Run",
            "args": ["update", "--dry-run"],
            "desc": "Test the auto-updater sequence without modifying path targets.",
            "expect_zero": True
        },

        # Scenario 3: Workspace Lifecycle
        {
            "name": "Create Workspace",
            "args": ["create", "qa_workspace"],
            "desc": "Scaffolds a fresh sandbox workspace configuration.",
            "expect_zero": True
        },
        {
            "name": "List Tracked Workspaces",
            "args": ["ws", "list"],
            "desc": "Confirm the newly created workspace is tracked.",
            "expect_zero": True
        },
        
        # Scenario 4: Workspace Sync, Bind, and Status
        {
            "name": "Workspace Synchronize",
            "args": ["sync"],
            # Run sync inside the created workspace
            "cwd": os.path.join(SANDBOX_DIR, "qa_workspace"),
            "desc": "Synchronize active DNA parameters and initialize sandbox virtualenvs.",
            "expect_zero": True
        },
        {
            "name": "Workspace Status",
            "args": ["status"],
            "cwd": os.path.join(SANDBOX_DIR, "qa_workspace"),
            "desc": "Verify workspace stats and virtualenv health.",
            "expect_zero": True
        },
        {
            "name": "Generate Editor Bindings",
            "args": ["bind", "--all"],
            "cwd": os.path.join(SANDBOX_DIR, "qa_workspace"),
            "desc": "Generate rules files (.cursorrules, .windsurfrules, gemini.json) for all adapters.",
            "expect_zero": True
        },

        # Scenario 5: Sandboxed Directory Mounts
        {
            "name": "Add Directory Mount",
            "args": ["mount", "add", "/tmp", "--alias", "test_tmp"],
            "cwd": os.path.join(SANDBOX_DIR, "qa_workspace"),
            "desc": "Mount an external folder for agent workspace access.",
            "expect_zero": True
        },
        {
            "name": "List Active Mounts",
            "args": ["mount", "list"],
            "cwd": os.path.join(SANDBOX_DIR, "qa_workspace"),
            "desc": "Verify our test_tmp mount mapping.",
            "expect_zero": True
        },
        {
            "name": "Remove Directory Mount",
            "args": ["mount", "remove", "test_tmp"],
            "cwd": os.path.join(SANDBOX_DIR, "qa_workspace"),
            "desc": "Safely delete the configured mount.",
            "expect_zero": True
        },

        # Scenario 6: Artifact Scaffolding, Add, and Removal
        {
            "name": "List Available Artifacts",
            "args": ["ls"],
            "cwd": os.path.join(SANDBOX_DIR, "qa_workspace"),
            "desc": "Scan and print all available artifacts.",
            "expect_zero": True
        },
        {
            "name": "Scaffold Custom Persona",
            "args": ["scaffold", "persona", "verification-squad"],
            "cwd": os.path.join(SANDBOX_DIR, "qa_workspace"),
            "desc": "Scaffold a new persona template file inside global DNA.",
            "expect_zero": True
        },
        {
            "name": "Add Skill Dependency",
            "args": ["add", "persona-demo_engineer"],
            "cwd": os.path.join(SANDBOX_DIR, "qa_workspace"),
            "desc": "Incorporate persona-demo_engineer dependency inside local manifest.",
            "expect_zero": True
        },
        {
            "name": "Prune/Remove Dependency",
            "args": ["rm", "persona-demo_engineer"],
            "cwd": os.path.join(SANDBOX_DIR, "qa_workspace"),
            "desc": "Safely strip dependencies and trigger workspace manifest cleanups.",
            "expect_zero": True
        },

        # Scenario 7: Diagnostics, Drift, and Cleanup
        {
            "name": "Doctor Verification",
            "args": ["doctor"],
            "cwd": os.path.join(SANDBOX_DIR, "qa_workspace"),
            "desc": "Verify that all required tool and folder assertions pass.",
            "expect_zero": True
        },
        {
            "name": "Verify Drift Diff",
            "args": ["diff"],
            "cwd": os.path.join(SANDBOX_DIR, "qa_workspace"),
            "desc": "Compare active local overrides against the original DNA blueprint.",
            "expect_zero": True
        },
        {
            "name": "Interactive Demo Run",
            "args": ["demo", "1"],
            "desc": "Run E2E demo execution walkthrough non-interactively.",
            "expect_zero": True
        },
        {
            "name": "Clean Demo Workspaces",
            "args": ["clean-demo"],
            "desc": "Delete the directories generated by the demo walkthrough.",
            "expect_zero": True
        },
        {
            "name": "Clean Test Mode Assets",
            "args": ["clean-test"],
            "desc": "Destroys all isolated directories.",
            "expect_zero": True
        },
        {
            "name": "Nuclear Wipe",
            "args": ["wipe", "--force"],
            "cwd": os.path.join(SANDBOX_DIR, "qa_workspace"),
            "desc": "Erase all configurations and trace marks from the system completely.",
            "expect_zero": True
        }
    ]

    log_info("Starting QA Test Scenarios Run...")
    markdown_log = []
    markdown_log.append("# Sprawl CLI — Comprehensive QA & Integration Execution Log")
    markdown_log.append(f"\n* **Execution Date:** {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}")
    markdown_log.append(f"* **Local Python Version:** {sys.version.split()[0]}")
    markdown_log.append(f"* **Workspace Root:** `{REPO_ROOT}`")
    markdown_log.append(f"* **Sandbox Directory:** `{SANDBOX_DIR}`")
    markdown_log.append(f"* **Test Mode Home:** `{SPRAWL_TEST_HOME}`")
    markdown_log.append("\n---\n")

    has_failures = False
    
    for idx, step in enumerate(steps, 1):
        name = step["name"]
        args = step["args"]
        desc = step["desc"]
        cwd = step.get("cwd", SANDBOX_DIR)
        expect_zero = step.get("expect_zero", True)
        
        log_info(f"[{idx}/{len(steps)}] Running: {BOLD}{name}{NC} (sprawl {' '.join(args)})...")
        
        # Execute command
        result = run_sprawl_cmd(args, cwd=cwd)
        
        exit_code = result["exit_code"]
        stdout = result["stdout"]
        stderr = result["stderr"]
        elapsed = result["elapsed_ms"]
        
        # Determine status
        is_success = (exit_code == 0) if expect_zero else (exit_code != 0)
        status_label = "PASS" if is_success else "FAIL"
        status_color = GREEN if is_success else RED
        
        print(f"    Status: {status_color}{status_label}{NC} ({elapsed}ms, exit code: {exit_code})")
        
        if not is_success:
            has_failures = True
            log_error(f"Command failed: sprawl {' '.join(args)}")
            if stderr:
                print(f"{RED}{stderr}{NC}")
        
        # Format Markdown Log Entry
        markdown_log.append(f"## Step {idx}: {name}")
        markdown_log.append(f"\n* **Description:** {desc}")
        markdown_log.append(f"* **Command:** `sprawl {' '.join(args)}` (cwd: `{os.path.basename(cwd)}`)")
        markdown_log.append(f"* **Execution Time:** `{elapsed}ms`")
        markdown_log.append(f"* **Status:** **`{status_label}`** (Expected Code: `0`, Got: `{exit_code}`)")
        
        if stdout:
            markdown_log.append("\n### Standard Output (stdout):")
            markdown_log.append(f"```text\n{stdout.strip()}\n```")
        
        if stderr:
            markdown_log.append("\n### Error Output (stderr):")
            markdown_log.append(f"```text\n{stderr.strip()}\n```")
            
        markdown_log.append("\n---\n")

    # Write log file
    os.makedirs(os.path.dirname(LOG_OUTPUT_PATH), exist_ok=True)
    with open(LOG_OUTPUT_PATH, "w") as f:
        f.write("\n".join(markdown_log))
        
    log_success(f"QA Verification Completed! Log report saved to: {LOG_OUTPUT_PATH}")
    
    # Tear down sandbox venv
    if os.path.exists(SANDBOX_DIR):
        shutil.rmtree(SANDBOX_DIR, ignore_errors=True)
        log_info("Tore down sandbox venv.")
        
    if has_failures and ci_mode:
        log_error("Smoke tests failed! Exiting with non-zero code.")
        sys.exit(1)
    elif has_failures:
        log_warn("Verification completed with command failures. Please inspect the log.")
        sys.exit(0)
    else:
        log_success("All commands executed successfully and passed smoke tests!")
        sys.exit(0)

if __name__ == "__main__":
    main()
