"""Man command."""

import contextlib
import importlib.resources as pkg_resources
import json
import os

from rich.syntax import Syntax

import sprawl

from ..config import config
from ..exceptions import SprawlError
from ..output import console
from ._helpers import resolve_repo_root


def _load_packaged_readme() -> str | None:
    """Attempts to read packaged README.md from importlib.resources."""
    with contextlib.suppress(OSError, TypeError, ValueError):
        return pkg_resources.files(sprawl).joinpath("README.md").read_text(encoding="utf-8")
    return None


def _load_repo_readme() -> str | None:
    """Fallback loader for README.md inside the local developer source repository."""
    repo_root = resolve_repo_root()
    if not repo_root:
        return None
    readme_path = os.path.join(repo_root, "README.md")
    if not os.path.exists(readme_path):
        return None
    with contextlib.suppress(OSError), open(readme_path, encoding="utf-8") as f:
        return f.read()
    return None


def cmd_man() -> None:
    """Reads and prints the global README.md acting as a native CLI man page."""
    content = _load_packaged_readme() or _load_repo_readme()
    if content is None:
        raise SprawlError(
            "Manual not found! Failed to read packaged README.md and local dev fallback."
        )

    if config.json_logging:
        print(json.dumps({"level": "info", "message": content}))
    else:
        console.print(Syntax(content, "markdown", theme="monokai", word_wrap=True))
