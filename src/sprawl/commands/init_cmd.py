"""DNA initialization and fetching commands."""

import os
import re
import subprocess
from typing import Optional

from ..config import config
from ..output import print_status, print_warning, print_error
from ..utils import DNA_ALIASES, get_git_env
from ..exceptions import SprawlError
from ._helpers import resolve_item_in_dna


def cmd_init(git_url: str, target_dir: str) -> None:
    """Core Initialization Pipeline: Initializes the Sprawl network locally.

    Args:
        git_url: Git remote URL or @alias for the DNA source.
        target_dir: Target directory for the Sprawl Hub.
    """
    if git_url.startswith("-"):
        raise SprawlError("Security Violation: Git URL cannot start with a hyphen.")

    if git_url.startswith("@"):
        alias_name = git_url[1:]
        if git_url in DNA_ALIASES:
            resolved_url = DNA_ALIASES[git_url]
            if config.verbose:
                print_status(f"Resolved DNA alias '{git_url}' to {resolved_url}")
            cmd_fetch_dna(resolved_url, alias_name)
        else:
            aliases_list = ", ".join(DNA_ALIASES.keys())
            raise SprawlError(f"Unknown DNA alias: '{git_url}'. Available aliases: {aliases_list}")

        target_abs = os.path.abspath(target_dir)
        print_status(f"Creating Workspace Hub at {target_abs}...")
        if not config.dry_run:
            os.makedirs(target_abs, exist_ok=True)
            from ..workspace import Workspace
            workspace = Workspace(target_abs)
            workspace.bind_dna(alias_name)
        print_status(f"Bound workspace to DNA context: @{alias_name}")
        return

    # Global Company DNA Initialization
    valid_prefixes = ("http://", "https://", "git@", "ssh://", "file://")
    if not git_url.startswith(valid_prefixes):
        raise SprawlError(f"Security Violation: Invalid Git URL scheme. Must start with one of {valid_prefixes}")

    safe_print_url = re.sub(r"(https?://)[^:]+:[^@]+@", r"\g<1>***:***@", git_url)

    target_abs = os.path.abspath(target_dir)
    print_status(f"Initializing Sprawl Hub from {safe_print_url} into {target_abs}...")

    config.update({
        "remote_dna_url": safe_print_url,
        "global_hub": config.agents_dir_global,
        "target_hub_dir": target_abs,
    })
    
    from ..registry import update_dna_registry
    if config.verbose:
        print_status(f"Configuration written natively to {config.config_path}")

    if os.path.exists(config.agents_dir_global):
        print_warning(f"{config.agents_dir_global} already exists. Skipping clone or you can manually update.")
        if not config.dry_run:
            update_dna_registry(git_url)
    else:
        print_status(f"Cloning Global DNA to {config.agents_dir_global}...")
        if not config.dry_run:
            try:
                subprocess.run(["git", "clone", git_url, config.agents_dir_global], check=True, env=get_git_env())
                update_dna_registry(git_url)
            except subprocess.CalledProcessError as e:
                print_warning(f"Failed to clone repository: {e}")
                print_error(
                    "=== AUTHENTICATION FAILED ===\n\n"
                    "Failed to clone the Global DNA repository. If this is a private enterprise repository, ensure you have access.\n\n"
                    "Options for Native Git Authentication:\n"
                    "  1. SSH: Use an SSH URL (git@github.com:org/repo.git) and ensure your SSH keys are loaded.\n"
                    "  2. Credential Manager: Ensure you are logged into your Git provider (e.g., `gh auth login`).\n"
                    "  3. Token: Embed your PAT in the URL (https://<TOKEN>@github.com/org/repo.git)."
                )
                raise SprawlError("Authentication failed during git clone.")

    if not os.path.exists(target_abs):
        print_status(f"Creating Workspace Hub at {target_abs}...")
        if not config.dry_run:
            os.makedirs(target_abs)
    else:
        if config.verbose:
            print_status(f"Workspace Hub {target_abs} already exists.")

    if config.verbose:
        print_status("Global CLI symlinks are now managed securely by pipx.")

    print_status("Initialization complete. Ensure ~/.local/bin is in your PATH.")


def cmd_fetch_dna(git_url: str, alias_name: Optional[str] = None) -> None:
    """Downloads a secondary DNA directly into the registry without modifying global context.

    Args:
        git_url: Git remote URL for the DNA source.
        alias_name: Optional alias for the DNA context.
    """
    if git_url.startswith("-"):
        raise SprawlError("Security Violation: Git URL cannot start with a hyphen.")

    valid_prefixes = ("http://", "https://", "git@", "ssh://", "file://")
    if not git_url.startswith(valid_prefixes):
        raise SprawlError(f"Security Violation: Invalid Git URL scheme. Must start with one of {valid_prefixes}")

    if not alias_name:
        match = re.search(r"([^/]+?)(?:\.git)?/?$", git_url)
        alias_name = match.group(1) if match else "default"

    if ".." in alias_name or "/" in alias_name or "\\" in alias_name:
        raise SprawlError("Security Violation: Alias name cannot contain path traversal characters.")
    if not re.match(r"^[a-zA-Z0-9_-]+$", alias_name):
        raise SprawlError("Security Violation: Alias name must be alphanumeric, underscores, or hyphens only.")

    dna_target_dir = os.path.join(config.dna_registry_dir, alias_name)

    if os.path.exists(dna_target_dir):
        print_status(f"DNA context '{alias_name}' already exists at {dna_target_dir}. Attempting to pull latest changes...")
        if not config.dry_run:
            try:
                subprocess.run(["git", "-C", dna_target_dir, "pull"], check=True, env=get_git_env())
            except subprocess.CalledProcessError as e:
                print_warning(f"Failed to pull latest DNA context: {e}")
    else:
        print_status(f"Fetching DNA context '{alias_name}' to {dna_target_dir}...")
        if not config.dry_run:
            os.makedirs(config.dna_registry_dir, exist_ok=True)
            try:
                subprocess.run(["git", "clone", git_url, dna_target_dir], check=True, env=get_git_env())
            except subprocess.CalledProcessError as e:
                print_warning(f"Failed to clone repository: {e}")
                raise SprawlError("Authentication failed during git clone.")

    if not config.dry_run:
        from ..validation import validate_dna_directory
        validate_dna_directory(dna_target_dir)
