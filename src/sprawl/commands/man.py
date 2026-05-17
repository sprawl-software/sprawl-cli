"""Man command."""
import os
import json
from ..config import config
from ..output import print_error, console
from ..exceptions import SprawlError
from ._helpers import resolve_repo_root

def cmd_man() -> None:
    """Reads and prints the global README.md acting as a native CLI man page."""
    repo_root = resolve_repo_root()
    readme_path = os.path.join(repo_root, "README.md") if repo_root else None

    if readme_path and os.path.exists(readme_path):
        with open(readme_path, "r") as f:
            content = f.read()
            if config.json_logging:
                print(json.dumps({"level": "info", "message": content}))
            else:
                from rich.syntax import Syntax
                syntax = Syntax(content, "markdown", theme="monokai", word_wrap=True)
                console.print(syntax)
    else:
        raise SprawlError(f"Manual not found! Expected at: {readme_path or 'unknown path — run from source checkout'}")
