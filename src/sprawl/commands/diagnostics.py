"""Diagnostics commands — update, cleanup, manual, and demo engine."""

import os
import json
import shutil
import subprocess
from typing import Optional

from ..config import config
from ..output import print_status, print_warning, print_error, console
from ..exceptions import SprawlError
from ._helpers import resolve_repo_root
from ..utils import get_git_env


def cmd_update() -> None:
    """Global Synchronization & Self-Updating Mechanism."""
    print_status("Initiating Sprawl Update Sequence...")

    if os.path.exists(config.agents_dir_global) and os.path.exists(os.path.join(config.agents_dir_global, ".git")):
        print_status(f"Updating Global DNA at {config.agents_dir_global}...")
        if not config.dry_run:
            try:
                git_env = get_git_env()
                current_branch = subprocess.check_output(
                    ["git", "-C", config.agents_dir_global, "rev-parse", "--abbrev-ref", "HEAD"],
                    text=True,
                    env=git_env
                ).strip()
                subprocess.run(
                    ["git", "-C", config.agents_dir_global, "pull", "origin", current_branch],
                    check=True,
                    env=git_env
                )
                print_status("Global DNA updated successfully.")
            except subprocess.CalledProcessError as e:
                print_warning(f"Failed to pull Global DNA: {e}")
                print_error(
                    "=== AUTHENTICATION FAILED ===\n\n"
                    "Failed to pull the Global DNA repository. If this is a private enterprise repository, ensure you have access.\n\n"
                    "Options for Native Git Authentication:\n"
                    "  1. SSH: Ensure your SSH keys are loaded (if using an SSH URL).\n"
                    "  2. Credential Manager: Ensure you are logged into your Git provider (e.g., `gh auth login`)."
                )
    else:
        print_warning(f"Global DNA not found or not a git repository at {config.agents_dir_global}. Run 'sprawl init' first.")

    repo_root = resolve_repo_root()

    if repo_root:
        print_status(f"Updating Sprawl Engine CLI from source at {repo_root}...")
        if not config.dry_run:
            try:
                git_env = get_git_env()
                current_branch = subprocess.check_output(
                    ["git", "-C", repo_root, "rev-parse", "--abbrev-ref", "HEAD"],
                    text=True,
                    env=git_env
                ).strip()
                try:
                    subprocess.run(
                        ["git", "-C", repo_root, "pull", "origin", current_branch],
                        check=True,
                        env=git_env
                    )
                    print_status("Source updated from remote.")
                except subprocess.CalledProcessError as e:
                    print_warning(f"Git pull failed (possibly a local branch or no network): {e}")
                    print_status("Continuing with local source code...")

                print_status("Re-installing globally via pipx...")
                subprocess.run(["pipx", "install", ".", "--force"], cwd=repo_root, check=True)

                print_status("Sprawl Engine updated and installed globally successfully.")
            except subprocess.CalledProcessError as e:
                raise SprawlError(f"Failed to run pipx: {e}")
    else:
        print_status("Production/release installation detected. Installing update from GitHub...")
        if not config.dry_run:
            try:
                git_env = get_git_env()
                print_status("Attempting installation via HTTPS: git+https://github.com/sprawl-software/sprawl-cli.git...")
                result = subprocess.run(
                    ["pipx", "install", "git+https://github.com/sprawl-software/sprawl-cli.git", "--force", "--pip-args=--no-cache-dir"],
                    env=git_env
                )
                if result.returncode == 0:
                    print_status("Sprawl CLI updated successfully from GitHub via HTTPS.")
                else:
                    print_warning(
                        "HTTPS installation failed.\n"
                        "Attempting fallback to SSH: git+ssh://git@github.com/sprawl-software/sprawl-cli.git..."
                    )
                    subprocess.run(
                        ["pipx", "install", "git+ssh://git@github.com/sprawl-software/sprawl-cli.git", "--force", "--pip-args=--no-cache-dir"],
                        check=True, env=git_env
                    )
                    print_status("Sprawl CLI updated successfully from GitHub via SSH.")
            except subprocess.CalledProcessError as e:
                print_error(f"Failed to update via pipx: {e}")
                print_warning("Ensure pipx is available and you have active network connectivity.")

    print_status("Update Sequence complete.")


def cmd_clean_test() -> None:
    """Removes all testmode isolated artifacts."""
    if not config.test_mode:
        raise SprawlError("Safety trigger: This command can only be run with --testmode.")

    print_status("Nuking all testmode artifacts...")
    try:
        if os.path.exists(config.agents_dir_global):
            shutil.rmtree(config.agents_dir_global)
            print_status(f"[-] Deleted {config.agents_dir_global}")

        if os.path.exists(config.sprawl_dir):
            shutil.rmtree(config.sprawl_dir)
            print_status(f"[-] Deleted {config.sprawl_dir}")

        if os.path.exists(config.config_path):
            os.remove(config.config_path)
            print_status(f"[-] Deleted {config.config_path}")

        print_status("Testmode environment cleanly destroyed.")
    except Exception as e:
        raise SprawlError(f"Failed to clean testmode paths: {e}")




def cmd_demo(demo_name: Optional[str] = None) -> None:
    """Routes to the interactive native demonstration engine.

    Args:
        demo_name: Optional demo name or ID to run directly.
    """
    from ..demo_engine import run_interactive_demo
    run_interactive_demo(demo_name)


def cmd_clean_demo() -> None:
    """Destroys the local sprawl_demo directory and triggers cmd_clean_test."""
    demo_dir = os.path.abspath(os.path.join(os.getcwd(), "sprawl_demo"))

    if os.path.exists(demo_dir):
        # SECURITY HARDENING: Prevent Symlink Traversal Attacks
        if os.path.islink(demo_dir):
            raise SprawlError(f"Security Violation: '{demo_dir}' is a symbolic link. Refusing to delete to prevent path traversal.")

        # SECURITY HARDENING: Ensure exact path match
        if os.path.realpath(demo_dir) != demo_dir:
            raise SprawlError(f"Security Violation: '{demo_dir}' resolves to a different real path. Refusing to delete.")

        try:
            shutil.rmtree(demo_dir)
            print_status(f"[-] Securely deleted demo workspace container: {demo_dir}")
        except Exception as e:
            raise SprawlError(f"Failed to delete demo workspace container: {e}")
    else:
        print_warning(f"No sprawl_demo directory found at {demo_dir}.")

    # Call the cleanup function directly — no shell subprocess required
    print_status("Triggering testmode artifact cleanup...")
    os.environ["SPRAWL_TEST_MODE"] = "1"
    config.reinitialize()
    try:
        cmd_clean_test()
    except SprawlError as e:
        print_warning(f"Testmode cleanup skipped: {e}")
