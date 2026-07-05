"""Man command."""
import os
import json
import importlib.resources as pkg_resources
import sprawl
from ..config import config
from ..output import print_error, console
from ..exceptions import SprawlError
from ._helpers import resolve_repo_root

def cmd_man() -> None:
    """Reads and prints the global README.md acting as a native CLI man page."""
    content = None
    
    # 1. Attempt loading packaged resource (Python 3.9+)
    try:
        content = pkg_resources.files(sprawl).joinpath("README.md").read_text(encoding="utf-8")
    except Exception:
        pass

    # 2. Fallback to local dev repository path
    if content is None:
        repo_root = resolve_repo_root()
        readme_path = os.path.join(repo_root, "README.md") if repo_root else None
        if readme_path and os.path.exists(readme_path):
            try:
                with open(readme_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception:
                pass

    if content is not None:
        if config.json_logging:
            print(json.dumps({"level": "info", "message": content}))
        else:
            from rich.syntax import Syntax
            syntax = Syntax(content, "markdown", theme="monokai", word_wrap=True)
            console.print(syntax)
    else:
        raise SprawlError("Manual not found! Failed to read packaged README.md and local dev fallback.")
