"""Interactive workspace shell command."""

import os
import subprocess

from ..exceptions import SprawlError
from ..output import print_status


def cmd_shell(target_dir: str | None = None) -> None:
    """Activates the workspace virtual environment in a subshell.

    Args:
        target_dir: Optional target directory. Defaults to cwd.
    """
    cwd = target_dir or os.getcwd()
    local_agents_dir = os.path.join(cwd, ".agents")
    venv_dir = os.path.join(local_agents_dir, ".venv")

    if not os.path.exists(venv_dir):
        raise SprawlError(
            f"No virtual environment found at {venv_dir}. "
            "Run 'sprawl sync' first to provision the workspace."
        )

    print_status(f"Entering workspace shell at {cwd}...")
    print_status("Type 'exit' or press Ctrl+D to return to the host shell.")

    # Prepare environment
    env = os.environ.copy()

    # Prepend venv bin to PATH
    if os.name == "nt":
        venv_bin = os.path.join(venv_dir, "Scripts")
    else:
        venv_bin = os.path.join(venv_dir, "bin")
    env["PATH"] = f"{venv_bin}{os.pathsep}{env.get('PATH', '')}"

    # Set VIRTUAL_ENV (standard for venv activation)
    env["VIRTUAL_ENV"] = venv_dir

    # Set workspace context
    env["SPRAWL_WORKSPACE"] = os.path.abspath(cwd)

    # Remove any parent VIRTUAL_ENV if it exists to avoid confusion
    env.pop("PYTHONHOME", None)

    # Determine shell
    shell = env.get("SHELL")
    if not shell:
        shell = env.get("COMSPEC", "cmd.exe") if os.name == "nt" else "/bin/bash"

    # Launch subshell
    try:
        subprocess.run([shell], env=env, check=False)
    except Exception as e:
        raise SprawlError(f"Failed to launch shell: {e}")

    print_status("Exited workspace shell.")
