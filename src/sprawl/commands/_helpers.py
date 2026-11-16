"""Shared helpers used across command modules."""

import os

from ..config import config
from ..exceptions import SprawlError
from ..output import print_status
from ..utils import CATEGORIES, rmtree_safe


def _delete_test_path(path: str, is_dir: bool) -> None:
    """Deletes a single testmode directory or file if it exists."""
    if not os.path.exists(path):
        return
    if is_dir:
        rmtree_safe(path)
    else:
        os.remove(path)
    print_status(f"[-] Deleted {path}")


def cmd_clean_test() -> None:
    """Removes all testmode isolated artifacts."""
    if not config.test_mode:
        raise SprawlError("Safety trigger: This command can only be run with --testmode.")

    print_status("Nuking all testmode artifacts...")
    try:
        _delete_test_path(config.agents_dir_global, is_dir=True)
        _delete_test_path(config.sprawl_dir, is_dir=True)
        _delete_test_path(config.config_path, is_dir=False)
        print_status("Testmode environment cleanly destroyed.")
    except OSError as e:
        raise SprawlError(f"Failed to clean testmode paths: {e}") from e


def resolve_item_in_dna(item: str, source_dna_dir: str) -> tuple[str | None, str | None]:
    """Resolves a named item to its exact filename within the active DNA context."""
    for category in CATEGORIES:
        cat_dir = os.path.join(source_dna_dir, category)
        if not os.path.exists(cat_dir):
            continue
        dir_contents = os.listdir(cat_dir)
        for candidate in (item, f"{item}.md", f"{item}.yml", f"{item}.yaml", f"{item}.json"):
            if candidate in dir_contents:
                return category, candidate
    return None, None


def _is_git_repo_root(path: str | None) -> bool:
    """Returns True if path is a non-empty directory containing a .git folder."""
    return bool(path and os.path.exists(os.path.join(path, ".git")))


def resolve_repo_root() -> str | None:
    """Deterministically resolves the Sprawl CLI source repository root."""
    script_path = os.path.realpath(__file__)
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(script_path))))
    if _is_git_repo_root(repo_root):
        return repo_root

    cwd = os.getcwd()
    if _is_git_repo_root(cwd) and os.path.exists(os.path.join(cwd, "src", "sprawl", "core.py")):
        return cwd

    env_path = os.environ.get("SPRAWL_DEV_MODE_PATH")
    return env_path if _is_git_repo_root(env_path) else None
