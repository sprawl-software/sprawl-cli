import argparse
import sys
import json
import os
from typing import Any
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.align import Align
from . import __version__
from .config import config
from .exceptions import SprawlError
from .output import print_error, console
from .commands import (
    cmd_init, cmd_create, cmd_graft, cmd_sync, cmd_update,
    cmd_clean_test, cmd_man, cmd_fetch_dna, cmd_list, cmd_add,
    cmd_scaffold, cmd_remove, cmd_demo, cmd_clean_demo, cmd_bind, cmd_doctor,
    cmd_diff, cmd_shell, cmd_status,
)
from .commands.dna import cmd_dna_update, cmd_dna_inspect

def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Sprawl Orchestrator (Atomic Agentic Fabric)",
        add_help=False,  # We handle help manually to match old behavior
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    # Global options
    parser.add_argument("-v", "--version", action="store_true", help="Checks the active Sprawl engine version structure.")
    parser.add_argument("--verbose", action="store_true", help="Engages strict logging mode dumping tracking execution outputs.")
    parser.add_argument("--dry-run", action="store_true", help="Safety mode; simulates structural file logic without destroying paths.")
    parser.add_argument("--testmode", action="store_true", help="Spins up a parallel sandbox environment to isolate local DNA changes.")
    parser.add_argument("--json", action="store_true", help="Outputs structured JSON logs instead of terminal text.")
    parser.add_argument("-h", "--help", action="store_true", help="Display this interactive setup screen.")
    
    # Commands
    subparsers = parser.add_subparsers(dest="command", title="Commands")
    
    # init
    init_parser = subparsers.add_parser("init", help="Clones your Sovereign DNA globally (~/.sprawl/core) and links the CLI.")
    init_parser.add_argument("git_url", help="Target Git remote URL")
    init_parser.add_argument("target_dir", nargs="?", default=config.sprawl_dir, help="Target directory to initialize the Hub")

    # create
    create_parser = subparsers.add_parser("create", help="Scaffolds a new standard workspace.")
    create_parser.add_argument("workspace", help="Name of the workspace to create")
    create_parser.add_argument("--path", default=None, help="Path to create the workspace in")

    # fetch-dna
    fetch_parser = subparsers.add_parser("fetch-dna", help="Downloads a secondary DNA into the registry without modifying global context.")
    fetch_parser.add_argument("git_url", help="Target Git remote URL")
    fetch_parser.add_argument("alias", nargs="?", default=None, help="Optional alias for the DNA context")

    # dna
    dna_parser = subparsers.add_parser("dna", help="DNA Registry Management commands.")
    dna_subparsers = dna_parser.add_subparsers(dest="dna_command", title="DNA Commands", required=True)
    dna_subparsers.add_parser("update", help="Git-pulls the registered DNA source.")
    dna_subparsers.add_parser("inspect", help="Shows contents of the DNA as a tree.")
    dna_subparsers.add_parser("list", help="Lists all registered DNA sources.")

    # ls
    subparsers.add_parser("ls", help="Scans the active DNA registry and lists all available artifacts.")

    # ws
    ws_parser = subparsers.add_parser("ws", help="Workspace Lifecycle Operations.")
    ws_subparsers = ws_parser.add_subparsers(dest="ws_command", title="Workspace Commands", required=True)
    ws_subparsers.add_parser("list", help="Lists all tracked workspaces with status.")
    
    ws_remove_parser = ws_subparsers.add_parser("remove", help="Deregisters (and optionally deletes) a workspace.")
    ws_remove_parser.add_argument("name", help="Name of the workspace to remove.")
    ws_remove_parser.add_argument("--delete", action="store_true", help="Also delete the workspace directory from disk.")
    
    ws_push_parser = ws_subparsers.add_parser("push", help="Syncs DNA updates to all (or specific) tracked workspaces.")
    ws_push_parser.add_argument("name", nargs="?", default=None, help="Optional name of a specific workspace to push to.")

    # add
    add_parser = subparsers.add_parser("add", help="Smart Injection Engine: automatically infers and injects dependencies.")
    add_parser.add_argument("items", nargs="*", default=[], help="Names of the rules/skills/atoms/workflows to add.")

    # graft
    subparsers.add_parser("graft", help="Surgically stitch the Sprawl's DNA onto the skin of an existing project.")

    # sync
    sync_parser = subparsers.add_parser("sync", help="Injects DNA into local scope and orchestrates universal dependency sandboxing.")
    sync_parser.add_argument("target_dir", nargs="?", default=None, help="Target directory to sync")

    # bind
    bind_parser = subparsers.add_parser("bind", help="Generates universal IDE/Agent bindings (Antigravity, Cursor, RooCode, Windsurf, Copilot).")
    bind_parser.add_argument("target_dir", nargs="?", default=None, help="Target directory to bind")
    bind_parser.add_argument("--force", action="store_true", default=False, help="Overwrite existing bindings.")
    # diff
    diff_parser = subparsers.add_parser("diff", help="Visualizes DNA drift between local workspace and upstream registry.")
    diff_parser.add_argument("target_dir", nargs="?", default=None, help="Target workspace path to analyze.")

    # shell
    shell_parser = subparsers.add_parser("shell", help="Enters a workspace-isolated subshell with activated .venv.")
    shell_parser.add_argument("target_dir", nargs="?", default=None, help="Target workspace directory")

    # update
    subparsers.add_parser("update", help="Auto-updates both the Global DNA and the local Sprawl CLI engine.")

    # clean-test
    subparsers.add_parser("clean-test", help="Destroys all sandboxed artifacts generated by --testmode.")
    
    # clean-demo
    subparsers.add_parser("clean-demo", help="Destroys the local demo workspaces folder generated by sprawl demo.")

    # scaffold
    scaffold_parser = subparsers.add_parser("scaffold", help="Automated boilerplate scaffolding for personas, rules, and skills.")
    scaffold_parser.add_argument("type", choices=["persona", "rule", "skill", "atom", "workflow"], help="The type of artifact to scaffold (e.g., 'persona').")
    scaffold_parser.add_argument("name", help="The human-readable name of the artifact (e.g., 'GTM Specialist').")

    # rm
    rm_parser = subparsers.add_parser("rm", help="Symmetrical removal engine. Safely removes artifacts and triggers sync cleanup.")
    rm_parser.add_argument("items", nargs="+", help="Names of the rules/skills/atoms/workflows to remove.")

    # man
    subparsers.add_parser("man", help="Prints the comprehensive AAF manual and setup guide directly.")
    
    # doctor
    subparsers.add_parser("doctor", help="Runs system diagnostics to verify dependencies and health.")
    
    # demo
    demo_parser = subparsers.add_parser("demo", help="Interactive native demonstration engine.")
    demo_parser.add_argument("name", nargs="?", default=None, help="Name or ID of the demo to run.")
    # status
    status_parser = subparsers.add_parser("status", help="Displays workspace status: DNA binding, artifacts, venv health, and last sync.")
    status_parser.add_argument("target_dir", nargs="?", default=None, help="Target workspace path.")

    return parser


def print_help() -> None:
    """Outputs the stylish Sprawl ASCII logo and the terminal instructions manual."""
    if config.json_logging:
        print(json.dumps({"level": "info", "message": "Help requested."}))
        return

    # Gradient ASCII Logo
    raw_logo = [
        r"    _____                           __   ________    ____",
        r"   / ___/____  _________ __      __/ /  / ____/ /   /  _/",
        r"   \__ \/ __ \/ ___/ __ `/ | /| / / /  / /   / /    / /  ",
        r"  ___/ / /_/ / /  / /_/ /| |/ |/ / /  / /___/ /____/ /   ",
        r" /____/ .___/_/   \__,_/ |__/|__/_/   \____/_____/___/   ",
        r"     /_/                                                 ",
    ]
    
    gradient_colors = ["#5D5CFF", "#6A62FF", "#7868FF", "#856FFF", "#9375FF", "#A07BFF"]
    
    logo = Text()
    for i, line in enumerate(raw_logo):
        color = gradient_colors[i % len(gradient_colors)]
        logo.append(line + "\n", style=f"bold {color}")

    header = Text.assemble(
        (" [ OS: BRAINBLEND AI // FRAMEWORK: ATOMIC AGENTIC FABRIC ]\n", "info"),
        (f" [ ARCHITECT: Younes_Baghor // VERSION: {__version__} ]", "info")
    )

    console.print("\n")
    console.print(Align.center(logo))
    console.print(Align.center(header))
    console.print("\n[info]Usage:[/info] sprawl [accent]<command>[/accent] [args]\n")

    # Cognitive Journey Tables
    def create_category_table() -> None:
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Command", style="accent", width=22)
        table.add_column("Description", style="info")
        return table

    t_dna = create_category_table()
    t_dna.add_row("init <GIT_URL>", "Clones your Sovereign DNA globally (~/.sprawl/core).")
    t_dna.add_row("fetch-dna <URL>", "Installs an alternative DNA strictly into the registry.")
    t_dna.add_row("dna update", "Git-pulls the registered DNA source.")
    t_dna.add_row("dna inspect", "Shows contents of the DNA as a tree.")
    t_dna.add_row("update", "Auto-updates both the Global DNA and the CLI engine.")

    t_workspace = create_category_table()
    t_workspace.add_row("create <WORKSPACE>", "Scaffolds a new standard workspace.")
    t_workspace.add_row("ws list", "Lists all tracked workspaces.")
    t_workspace.add_row("ws remove <NAME>", "Deregisters a workspace from the tracking registry.")
    t_workspace.add_row("ws push [NAME]", "Syncs DNA updates to all or specific tracked workspaces.")
    t_workspace.add_row("graft", "Surgically stitch Sprawl DNA onto an existing legacy project.")
    t_workspace.add_row("sync", "Injects DNA locally and provisions sandboxes (.venv, npm, cargo).")
    t_workspace.add_row("bind", "Generates universal IDE/Agent bindings (Antigravity, Cursor, RooCode, Windsurf, Copilot).")

    t_artifact = create_category_table()
    t_artifact.add_row("ls", "Scans the active DNA registry and lists all available artifacts.")
    t_artifact.add_row("scaffold <TYPE> <N>", "Generates boilerplate for personas, rules, and skills.")
    t_artifact.add_row("add <ITEMS...>", "Smart Injection: automatically infers and injects dependencies.")
    t_artifact.add_row("rm <ITEMS...>", "Symmetrical Removal: safely removes artifacts and triggers prune.")

    t_diag = create_category_table()
    t_diag.add_row("status", "Displays workspace status: DNA, artifacts, venv health.")
    t_diag.add_row("demo [ID]", "Interactive native demonstration engine.")
    t_diag.add_row("clean-demo", "Destroys the local demo workspaces folder generated by sprawl demo.")
    t_diag.add_row("clean-test", "Destroys all sandboxed artifacts generated by --testmode.")
    t_diag.add_row("doctor", "Runs full system diagnostics.")
    t_diag.add_row("man", "Prints the comprehensive AAF manual and setup guide directly.")
    
    t_options = create_category_table()
    t_options.add_row("-v, --version", "Checks the active Sprawl engine version structure.")
    t_options.add_row("--verbose", "Engages strict logging mode dumping tracking execution outputs.")
    t_options.add_row("--dry-run", "Safety mode; simulates structural file logic without destroying paths.")
    t_options.add_row("--testmode", "Spins up a parallel sandbox environment to isolate local DNA changes.")
    t_options.add_row("--json", "Outputs structured JSON logs instead of terminal text.")
    t_options.add_row("-h, --help", "Display this interactive setup screen.")

    # Render Panels
    console.print(Panel(t_dna, title="[info]DNA Management[/info]", border_style="#5D5CFF", title_align="left"))
    console.print(Panel(t_workspace, title="[info]Workspace Operations[/info]", border_style="#5D5CFF", title_align="left"))
    console.print(Panel(t_artifact, title="[info]Artifact & Persona Engine[/info]", border_style="#5D5CFF", title_align="left"))
    console.print(Panel(t_diag, title="[info]Diagnostics[/info]", border_style="#5D5CFF", title_align="left"))
    console.print(Panel(t_options, title="[info]Options[/info]", border_style="#5D5CFF", title_align="left"))

    # Footer
    footer = Text.assemble(
        ("\n[?] NEW TO THE SPRAWL?\n", "bold #10B981"),
        ("Concepts like 'Sovereign DNA' and 'Personas' require context.\n", "info"),
        ("Read the full documentation native to your terminal:\n", "info"),
        ("  > sprawl man", "accent")
    )
    console.print(Panel(Align.center(footer), border_style="accent", padding=(0, 2)))

def main() -> None:
    parser = get_parser()
    
    # We parse known args first to extract global flags before routing to commands
    args, unknown = parser.parse_known_args()

    # Set configuration state globally across the package
    if args.verbose or "--verbose" in sys.argv:
        config.verbose = True
        from rich.traceback import install as install_traceback
        install_traceback(show_locals=True, theme="monokai")
    if args.dry_run or "--dry-run" in sys.argv:
        config.dry_run = True
    if args.json or "--json" in sys.argv:
        config.json_logging = True
    
    # We must explicitly check for testmode here to initialize the paths if running without wrapper
    if args.testmode or "--testmode" in sys.argv:
        os.environ["SPRAWL_TEST_MODE"] = "1"
        config.reinitialize()

    if args.help or (len(sys.argv) < 2):
        print_help()
        sys.exit(0)

    if args.version:
        if config.json_logging:
            print(json.dumps({"level": "info", "message": f"Sprawl Orchestrator {__version__} (Atomic Agentic Fabric)"}))
        else:
            console.print(f"[accent]\\[*][/accent] [info]Sprawl Orchestrator {__version__} (Atomic Agentic Fabric)[/info]")
        sys.exit(0)

    # -----------------------------------------------------------------------
    # Command Registry — single-point registration, dict-based dispatch
    # -----------------------------------------------------------------------
    def handle_dna_command(a: Any) -> None:
        from .commands.dna import cmd_dna_list
        if a.dna_command == "update":
            cmd_dna_update()
        elif a.dna_command == "inspect":
            cmd_dna_inspect()
        elif a.dna_command == "list":
            cmd_dna_list()
        else:
            print_error(f"Unknown DNA command: {a.dna_command}")
            sys.exit(1)

    def handle_ws_command(a: Any) -> None:
        from .commands.workspace import cmd_ws_list, cmd_ws_remove, cmd_ws_push
        if a.ws_command == "list":
            cmd_ws_list()
        elif a.ws_command == "remove":
            cmd_ws_remove(a.name, a.delete)
        elif a.ws_command == "push":
            cmd_ws_push(a.name)
        else:
            print_error(f"Unknown Workspace command: {a.ws_command}")
            sys.exit(1)

    COMMAND_REGISTRY = {
        "init":       lambda a: cmd_init(a.git_url, a.target_dir),
        "fetch-dna":  lambda a: cmd_fetch_dna(a.git_url, a.alias),
        "dna":        handle_dna_command,
        "ws":         handle_ws_command,
        "ls":         lambda a: cmd_list(),
        "add":        lambda a: cmd_add(a.items),
        "create":     lambda a: cmd_create(a.workspace, getattr(a, 'path', None)),
        "graft":      lambda a: cmd_graft(),
        "sync":       lambda a: cmd_sync(a.target_dir),
        "bind":       lambda a: cmd_bind(a.target_dir, force=getattr(a, 'force', False)),
        "diff":       lambda a: cmd_diff(a.target_dir),
        "shell":      lambda a: cmd_shell(a.target_dir),
        "update":     lambda a: cmd_update(),
        "clean-test": lambda a: cmd_clean_test(),
        "clean-demo": lambda a: cmd_clean_demo(),
        "scaffold":   lambda a: cmd_scaffold(a.type, a.name),
        "rm":         lambda a: cmd_remove(a.items),
        "man":        lambda a: cmd_man(),
        "doctor":     lambda a: cmd_doctor(),
        "status":     lambda a: cmd_status(getattr(a, 'target_dir', None)),
        "demo":       lambda a: cmd_demo(a.name),
    }

    try:
        if args.command not in ("init", "dna", "ws"):
            from .registry import check_dna_staleness
            check_dna_staleness()
            
        handler = COMMAND_REGISTRY.get(args.command)
        if handler:
            handler(args)
        else:
            print_error(f"Unknown command: {args.command}")
            print_help()
            sys.exit(1)
            
    except SprawlError as e:
        print_error(str(e))
        sys.exit(1)
    except KeyboardInterrupt:
        console.print("\n[warning]Execution aborted by user.[/warning]")
        sys.exit(130)
    except Exception as e:
        if config.verbose:
            raise
        else:
            print_error(f"An unexpected system fault occurred: {str(e)}")
            console.print("[info]Tip: Re-run this command with the [accent]--verbose[/accent] flag to view the full diagnostic stack trace.[/info]")
            sys.exit(1)

if __name__ == "__main__":
    main()

