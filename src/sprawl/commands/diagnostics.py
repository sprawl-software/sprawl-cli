"""Diagnostics commands — update, cleanup, manual, and demo engine."""

import os
import shutil
import subprocess
import sys

from ..config import config
from ..exceptions import SprawlError
from ..output import print_error, print_status, print_warning
from ..utils import get_git_env
from ._helpers import cmd_clean_test, resolve_repo_root


def _update_global_dna() -> None:
    """Pulls the latest commits for the Global DNA repository if initialized."""
    if not (
        os.path.exists(config.agents_dir_global)
        and os.path.exists(os.path.join(config.agents_dir_global, ".git"))
    ):
        print_warning(
            f"Global DNA not found or not a git repository at {config.agents_dir_global}. Run 'sprawl init' first."
        )
        return

    print_status(f"Updating Global DNA at {config.agents_dir_global}...")
    if config.dry_run:
        return

    try:
        git_env = get_git_env()
        current_branch = subprocess.check_output(
            ["git", "-C", config.agents_dir_global, "rev-parse", "--abbrev-ref", "HEAD"],
            text=True,
            env=git_env,
            timeout=30,
        ).strip()
        subprocess.run(
            ["git", "-C", config.agents_dir_global, "pull", "origin", current_branch],
            check=True,
            env=git_env,
            timeout=60,
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


def _reinstall_local_repo_via_pipx(repo_root: str, git_env: dict[str, str]) -> None:
    """Re-installs the local source repository into pipx."""
    if sys.platform == "win32":
        runpip_res = subprocess.run(
            [
                "pipx",
                "runpip",
                "sprawl-cli",
                "install",
                "--upgrade",
                "--no-cache-dir",
                ".",
            ],
            cwd=repo_root,
            env=git_env,
            timeout=120,
        )
        if runpip_res.returncode != 0:
            subprocess.run(
                ["pipx", "install", ".", "--force"],
                cwd=repo_root,
                check=True,
                env=git_env,
                timeout=120,
            )
    else:
        subprocess.run(
            ["pipx", "install", ".", "--force"],
            cwd=repo_root,
            check=True,
            env=git_env,
            timeout=120,
        )


def _update_from_source_repo(repo_root: str) -> None:
    """Pulls the local Sprawl CLI git repository and reinstalls via pipx."""
    print_status(f"Updating Sprawl Engine CLI from source at {repo_root}...")
    if config.dry_run:
        return

    try:
        git_env = get_git_env()
        current_branch = subprocess.check_output(
            ["git", "-C", repo_root, "rev-parse", "--abbrev-ref", "HEAD"],
            text=True,
            env=git_env,
            timeout=30,
        ).strip()
        try:
            subprocess.run(
                ["git", "-C", repo_root, "pull", "origin", current_branch],
                check=True,
                env=git_env,
                timeout=60,
            )
            print_status("Source updated from remote.")
        except subprocess.CalledProcessError as e:
            print_warning(f"Git pull failed (possibly a local branch or no network): {e}")
            print_status("Continuing with local source code...")

        print_status("Re-installing globally via pipx...")
        _reinstall_local_repo_via_pipx(repo_root, git_env)
        print_status("Sprawl Engine updated and installed globally successfully.")
    except subprocess.CalledProcessError as e:
        raise SprawlError(f"Failed to run pipx: {e}") from e


def _update_production_windows(git_env: dict[str, str]) -> None:
    """Upgrades sprawl-cli on Windows via pipx upgrade -> runpip -> install fallback."""
    print_status("Attempting upgrade via pipx...")
    result = subprocess.run(
        ["pipx", "upgrade", "sprawl-cli", "--pip-args=--no-cache-dir"],
        env=git_env,
        timeout=120,
    )
    if result.returncode == 0:
        print_status("Sprawl CLI updated successfully via pipx upgrade.")
        return

    print_status("Attempting in-place installation via pipx runpip...")
    runpip_result = subprocess.run(
        [
            "pipx",
            "runpip",
            "sprawl-cli",
            "install",
            "--upgrade",
            "--no-cache-dir",
            "git+https://github.com/sprawl-software/sprawl-cli.git",
        ],
        env=git_env,
        timeout=120,
    )
    if runpip_result.returncode == 0:
        print_status("Sprawl CLI updated successfully from GitHub via HTTPS.")
        return

    print_status("Attempting installation via pipx install --force...")
    subprocess.run(
        [
            "pipx",
            "install",
            "git+https://github.com/sprawl-software/sprawl-cli.git",
            "--force",
            "--pip-args=--no-cache-dir",
        ],
        check=True,
        env=git_env,
        timeout=120,
    )
    print_status("Sprawl CLI installed successfully from GitHub via HTTPS.")


def _update_production_posix(git_env: dict[str, str]) -> None:
    """Upgrades sprawl-cli on POSIX via GitHub HTTPS with SSH fallback."""
    print_status(
        "Attempting installation via HTTPS: git+https://github.com/sprawl-software/sprawl-cli.git..."
    )
    result = subprocess.run(
        [
            "pipx",
            "install",
            "git+https://github.com/sprawl-software/sprawl-cli.git",
            "--force",
            "--pip-args=--no-cache-dir",
        ],
        env=git_env,
        timeout=120,
    )
    if result.returncode == 0:
        print_status("Sprawl CLI updated successfully from GitHub via HTTPS.")
        return

    print_warning(
        "HTTPS installation failed.\n"
        "Attempting fallback to SSH: git+ssh://git@github.com/sprawl-software/sprawl-cli.git..."
    )
    subprocess.run(
        [
            "pipx",
            "install",
            "git+ssh://git@github.com/sprawl-software/sprawl-cli.git",
            "--force",
            "--pip-args=--no-cache-dir",
        ],
        check=True,
        env=git_env,
        timeout=120,
    )
    print_status("Sprawl CLI updated successfully from GitHub via SSH.")


def _update_production_release() -> None:
    """Upgrades a production installation of sprawl-cli from GitHub."""
    print_status("Production/release installation detected. Installing update from GitHub...")
    if config.dry_run:
        return

    try:
        git_env = get_git_env()
        if sys.platform == "win32":
            _update_production_windows(git_env)
        else:
            _update_production_posix(git_env)
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to update via pipx: {e}")
        print_warning("Ensure pipx is available and you have active network connectivity.")


def cmd_update() -> None:
    """Global Synchronization & Self-Updating Mechanism."""
    print_status("Initiating Sprawl Update Sequence...")
    _update_global_dna()

    repo_root = resolve_repo_root()
    if repo_root:
        _update_from_source_repo(repo_root)
    else:
        _update_production_release()

    print_status("Update Sequence complete.")


def cmd_demo(demo_name: str | None = None) -> None:
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
        if os.path.islink(demo_dir):
            raise SprawlError(
                f"Security Violation: '{demo_dir}' is a symbolic link. Refusing to delete to prevent path traversal."
            )

        real_demo = os.path.realpath(demo_dir)
        real_expected = os.path.realpath(os.path.join(os.getcwd(), "sprawl_demo"))
        if os.path.normcase(real_demo) != os.path.normcase(real_expected):
            raise SprawlError(
                f"Security Violation: '{demo_dir}' resolves to a different real path. Refusing to delete."
            )

        try:
            shutil.rmtree(real_demo)
            print_status(f"[-] Securely deleted demo workspace container: {real_demo}")
        except OSError as e:
            raise SprawlError(f"Failed to delete demo workspace container: {e}") from e
    else:
        print_warning(f"No sprawl_demo directory found at {demo_dir}.")

    print_status("Triggering testmode artifact cleanup...")
    os.environ["SPRAWL_TEST_MODE"] = "1"
    config.reinitialize()
    try:
        cmd_clean_test()
    except SprawlError as e:
        print_warning(f"Testmode cleanup skipped: {e}")
