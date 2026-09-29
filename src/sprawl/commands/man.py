"""Man command."""

import contextlib
import importlib.resources as pkg_resources
import json
import os

import sprawl

from ..config import config
from ..exceptions import SprawlError
from ..output import console
from ._helpers import resolve_repo_root


def cmd_man() -> None:
    """Reads and prints the global README.md acting as a native CLI man page."""
    content = None

    # 1. Attempt loading packaged resource (Python 3.9+)
    with contextlib.suppress(Exception):
        content = pkg_resources.files(sprawl).joinpath("README.md").read_text(encoding="utf-8")

    # 2. Fallback to local dev repository path
    if content is None:
        repo_root = resolve_repo_root()
        readme_path = os.path.join(repo_root, "README.md") if repo_root else None
        if readme_path and os.path.exists(readme_path):
            try:
                with open(readme_path, encoding="utf-8") as f:
                    content = f.read()
            except OSError:
                pass

    if content is not None:
        if config.json_logging:
            print(json.dumps({"level": "info", "message": content}))
        else:
            from rich.syntax import Syntax

            syntax = Syntax(content, "markdown", theme="monokai", word_wrap=True)
            console.print(syntax)
    else:
        raise SprawlError(
            "Manual not found! Failed to read packaged README.md and local dev fallback."
        )
