"""Sprawl Keyboard-Interactive Checkbox TUI Engine.

Pure standard library raw keypress reader and visual selection rendering using Rich.
Restores terminal cleanly on exit or abrupt failure.
"""

import os
import sys
import tty
import select
import termios
import contextlib
from typing import Any, Dict, List, Optional, Tuple

from rich.console import Console
from rich.panel import Panel
from ..theme import SDS_THEME

# Reuse the global console styled with Sprawl Design System theme
console = Console(theme=SDS_THEME)


@contextlib.contextmanager
def raw_terminal():
    """Context manager to enable raw terminal mode and safely restore settings on exit."""
    try:
        fd = sys.stdin.fileno()
    except Exception:
        fd = None

    # Check if stdin is a TTY (running in terminal vs piped tests)
    if fd is None or not sys.stdin.isatty():
        yield fd
        return

    old_settings = termios.tcgetattr(fd)
    try:
        # Hide cursor
        sys.stdout.write("\033[?25l")
        sys.stdout.flush()
        tty.setcbreak(fd)
        yield fd
    finally:
        # Restore cursor and settings
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def read_key() -> str:
    """Reads a single keypress or ANSI escape sequence from stdin in raw mode."""
    if not sys.stdin.isatty():
        # Fallback for non-interactive test environments
        return sys.stdin.read(1)

    fd = sys.stdin.fileno()
    try:
        char = os.read(fd, 1).decode("utf-8", errors="ignore")
    except OSError:
        return ""

    if char == "\x1b":
        # Check if more characters are waiting in the escape buffer
        rlist, _, _ = select.select([fd], [], [], 0.05)
        if rlist:
            try:
                next_chars = os.read(fd, 2).decode("utf-8", errors="ignore")
                return char + next_chars
            except OSError:
                pass
        return char
    return char


def show_checkbox_menu(
    title: str,
    categories: Dict[str, List[Tuple[str, bool]]],
    max_viewport: int = 12,
) -> Optional[Dict[str, List[str]]]:
    """Renders a keyboard-interactive TUI checkbox menu for categorized DNA items.

    Args:
        title: Title of the TUI menu panel.
        categories: Dict mapping category name to list of (item_name, is_checked).
        max_viewport: Maximum number of rows to display in the scrollable viewport.

    Returns:
        Dict mapping category name to list of checked item names, or None if cancelled.
    """
    # Flatten categories into flat list of rows for rendering and index mapping
    rows: List[Dict[str, Any]] = []
    for cat, items in categories.items():
        rows.append({
            "is_header": True,
            "label": cat.upper(),
            "category": cat,
        })
        for name, checked in items:
            rows.append({
                "is_header": False,
                "label": name,
                "category": cat,
                "checked": checked,
            })

    # List of all selectable file rows (non-headers)
    selectable_indices = [i for i, r in enumerate(rows) if not r["is_header"]]

    if not selectable_indices:
        console.print("[warning][!] No items found to configure.[/warning]")
        return None

    # TUI Interactive state
    active_selectable_idx = 0
    scroll_offset = 0
    last_printed_lines = 0

    with raw_terminal():
        while True:
            # 1. Update scroll viewport offset based on active row
            active_row_idx = selectable_indices[active_selectable_idx]
            if active_row_idx >= scroll_offset + max_viewport:
                scroll_offset = active_row_idx - max_viewport + 1
            elif active_row_idx < scroll_offset:
                scroll_offset = active_row_idx

            # 2. Render TUI Output using Rich Console Capture to measure lines
            with console.capture() as capture:
                # Menu Title / Instructions
                console.print(f"[accent]━━━ {title} ━━━[/accent]")
                console.print("[muted]Navigate: ↑/↓ | Toggle: Space | Confirm: Enter | Cancel: Esc/q[/muted]")
                console.print()

                # Viewport window of rows
                visible_rows = rows[scroll_offset : scroll_offset + max_viewport]
                
                # Indicator if scrolled off top
                if scroll_offset > 0:
                    console.print("   [accent]▲ (more items above)[/accent]")
                else:
                    console.print()

                for idx, row in enumerate(visible_rows):
                    absolute_idx = scroll_offset + idx
                    is_active = (absolute_idx == active_row_idx)

                    if row["is_header"]:
                        console.print(f" 📁 [accent]{row['label']}[/accent]")
                    else:
                        checkbox = "[success]✔[/success]" if row["checked"] else "[muted]☐[/muted]"
                        if is_active:
                            console.print(f"  [accent]→[/accent] {checkbox} [accent][bold]{row['label']}[/bold][/accent]")
                        else:
                            item_style = "info" if row["checked"] else "muted"
                            console.print(f"    {checkbox} [{item_style}]{row['label']}[/{item_style}]")

                # Indicator if scrolled off bottom
                if scroll_offset + max_viewport < len(rows):
                    console.print("   [accent]▼ (more items below)[/accent]")
                else:
                    console.print()

                # Bottom status/metrics
                num_checked = sum(1 for r in rows if not r["is_header"] and r.get("checked"))
                active_label = rows[active_row_idx]["label"]
                console.print(f" [muted]Selected: {active_label} | Checked: {num_checked}/{len(selectable_indices)}[/muted]")

            # Render output and clean up old lines
            output_text = capture.get()
            lines_to_print = output_text.splitlines()

            # If not first print, move cursor up to rewrite in place
            if last_printed_lines > 0:
                sys.stdout.write(f"\r\033[{last_printed_lines}A")
                sys.stdout.write("\033[J")  # Clear screen below cursor
                sys.stdout.flush()

            # Print current state
            sys.stdout.write(output_text)
            sys.stdout.flush()
            last_printed_lines = len(lines_to_print)

            # 3. Read raw keypress and handle actions
            key = read_key()

            if key in ("q", "Q", "\x1b"):  # Esc or 'q' to cancel
                # Clear printed lines and exit cleanly
                if last_printed_lines > 0:
                    sys.stdout.write(f"\r\033[{last_printed_lines}A")
                    sys.stdout.write("\033[J")
                    sys.stdout.flush()
                return None

            elif key == "\x1b[A":  # Arrow Up
                if active_selectable_idx > 0:
                    active_selectable_idx -= 1

            elif key == "\x1b[B":  # Arrow Down
                if active_selectable_idx < len(selectable_indices) - 1:
                    active_selectable_idx += 1

            elif key == " ":  # Space bar to toggle
                rows[active_row_idx]["checked"] = not rows[active_row_idx]["checked"]

            elif key in ("\r", "\n"):  # Enter to confirm
                # Clear printed lines
                if last_printed_lines > 0:
                    sys.stdout.write(f"\r\033[{last_printed_lines}A")
                    sys.stdout.write("\033[J")
                    sys.stdout.flush()

                # Compile and return checked items mapping
                result: Dict[str, List[str]] = {cat: [] for cat in categories}
                for r in rows:
                    if not r["is_header"] and r["checked"]:
                        result[r["category"]].append(r["label"])
                return result


def show_mount_dashboard(workspace_root: str) -> None:
    """Renders the workspace mount manager dashboard."""
    from ..commands.mount import _load_config, _write_config, _get_workspace_paths, slugify
    from ..commands.sync_cmd import cmd_sync

    _, _, config_path = _get_workspace_paths(workspace_root)

    cfg = _load_config(config_path)
    mounts = cfg.get("allowed_mounts", {})
    if not isinstance(mounts, dict):
        mounts = {}

    # Copy to mutable local state
    mounts = dict(mounts)
    checked_states = {alias: True for alias in mounts}

    active_idx = 0
    scroll_offset = 0
    max_viewport = 10
    last_printed_lines = 0

    with raw_terminal():
        while True:
            # Construct dashboard rows
            rows = []
            for alias, path in sorted(mounts.items()):
                rows.append({
                    "alias": alias,
                    "path": path,
                    "checked": checked_states.get(alias, False),
                    "is_add_btn": False
                })
            rows.append({
                "alias": "[Add new directory mount...]",
                "path": "",
                "checked": False,
                "is_add_btn": True
            })

            # Selectable index bounds
            if active_idx < 0:
                active_idx = 0
            if active_idx >= len(rows):
                active_idx = len(rows) - 1

            # Adjust scroll offset
            if active_idx < scroll_offset:
                scroll_offset = active_idx
            elif active_idx >= scroll_offset + max_viewport:
                scroll_offset = active_idx - max_viewport + 1

            visible_rows = rows[scroll_offset : scroll_offset + max_viewport]

            # Render dashboard with capture
            with console.capture() as capture:
                console.print("[bold]━━━ Manage Allowed Workspace Mounts ━━━[/bold]")
                console.print("Press Space to toggle mounts. Unchecking will remove them.\n")

                if scroll_offset > 0:
                    console.print("   [accent]▲ (more items above)[/accent]")
                else:
                    console.print()

                for idx, r in enumerate(visible_rows):
                    abs_idx = scroll_offset + idx
                    pointer = "→" if abs_idx == active_idx else " "
                    
                    if r["is_add_btn"]:
                        btn_text = f"[success]{r['alias']}[/success]"
                        if abs_idx == active_idx:
                            console.print(f"  [accent]→[/accent] [bold]{btn_text}[/bold]")
                        else:
                            console.print(f"     {btn_text}")
                    else:
                        checkbox = "[success]✔[/success]" if r["checked"] else "[muted]☐[/muted]"
                        if abs_idx == active_idx:
                            console.print(f"  [accent]→[/accent] {checkbox} [accent][bold]@{r['alias']}[/bold][/accent] → {r['path']}")
                        else:
                            item_style = "info" if r["checked"] else "muted"
                            console.print(f"     {checkbox} [{item_style}]@{r['alias']}[/{item_style}] → {r['path']}")

                if scroll_offset + max_viewport < len(rows):
                    console.print("   [accent]▼ (more items below)[/accent]")
                else:
                    console.print()

                console.print("\n[muted][Enter] Save & Sync | [Space] Toggle | [Esc/q] Cancel[/muted]")

            # Erase previous print
            output_text = capture.get()
            lines_to_print = output_text.splitlines()
            if last_printed_lines > 0:
                sys.stdout.write(f"\r\033[{last_printed_lines}A")
                sys.stdout.write("\033[J")
                sys.stdout.flush()

            # Print current state
            sys.stdout.write(output_text)
            sys.stdout.flush()
            last_printed_lines = len(lines_to_print)

            # Read keypress
            key = read_key()

            if key in ("q", "Q", "\x1b"):  # Esc or 'q' to cancel
                if last_printed_lines > 0:
                    sys.stdout.write(f"\r\033[{last_printed_lines}A")
                    sys.stdout.write("\033[J")
                    sys.stdout.flush()
                return

            elif key == "\x1b[A":  # Arrow Up
                if active_idx > 0:
                    active_idx -= 1

            elif key == "\x1b[B":  # Arrow Down
                if active_idx < len(rows) - 1:
                    active_idx += 1

            elif key == " ":  # Space to toggle or add
                r = rows[active_idx]
                if r["is_add_btn"]:
                    if last_printed_lines > 0:
                        sys.stdout.write(f"\r\033[{last_printed_lines}A")
                        sys.stdout.write("\033[J")
                        sys.stdout.flush()
                        last_printed_lines = 0
                    
                    if _add_new_mounts(workspace_root, mounts, checked_states):
                        cfg["allowed_mounts"] = {alias: path for alias, path in mounts.items() if checked_states.get(alias, False)}
                        _write_config(config_path, cfg)
                        from ..output import print_status
                        print_status("Synchronizing workspace configurations...")
                        cmd_sync(workspace_root)
                        return
                else:
                    alias = r["alias"]
                    checked_states[alias] = not checked_states[alias]

            elif key in ("\r", "\n"):  # Enter to confirm or add
                r = rows[active_idx]
                if r["is_add_btn"]:
                    if last_printed_lines > 0:
                        sys.stdout.write(f"\r\033[{last_printed_lines}A")
                        sys.stdout.write("\033[J")
                        sys.stdout.flush()
                        last_printed_lines = 0
                    if _add_new_mounts(workspace_root, mounts, checked_states):
                        cfg["allowed_mounts"] = {alias: path for alias, path in mounts.items() if checked_states.get(alias, False)}
                        _write_config(config_path, cfg)
                        from ..output import print_status
                        print_status("Synchronizing workspace configurations...")
                        cmd_sync(workspace_root)
                        return
                else:
                    # Save and exit!
                    if last_printed_lines > 0:
                        sys.stdout.write(f"\r\033[{last_printed_lines}A")
                        sys.stdout.write("\033[J")
                        sys.stdout.flush()
                    
                    cfg["allowed_mounts"] = {alias: path for alias, path in mounts.items() if checked_states.get(alias, False)}
                    _write_config(config_path, cfg)
 
                    from ..output import print_status
                    print_status("Synchronizing workspace configurations...")
                    cmd_sync(workspace_root)
                    return


def _add_new_mounts(workspace_root: str, mounts: dict, checked_states: dict) -> bool:
    """Helper to run the directory picker and prompt for aliases without key bleeding."""
    from ..commands.mount import slugify
    new_paths = show_directory_picker(workspace_root)
    if new_paths:
        for new_path in new_paths:
            default_alias = slugify(os.path.basename(new_path))
            sys.stdout.write(f"\rEnter mount alias for {os.path.basename(new_path)} (default: {default_alias}): ")
            sys.stdout.flush()
            sys.stdout.write("\033[?25h")
            sys.stdout.flush()
            
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                alias_input = sys.stdin.readline().strip()
            finally:
                tty.setcbreak(fd)
                termios.tcflush(fd, termios.TCIFLUSH)
                sys.stdout.write("\033[?25l")
                sys.stdout.flush()

            alias = slugify(alias_input) if alias_input else default_alias
            if not alias:
                alias = "mount"

            mounts[alias] = new_path
            checked_states[alias] = True
        return True
    return False



def show_directory_picker(start_dir: str) -> Optional[List[str]]:
    """Renders a keyboard-interactive directory selection browser TUI with checkboxes."""
    current_dir = os.path.abspath(start_dir)
    selected_paths = set()
    active_idx = 0
    scroll_offset = 0
    max_viewport = 10
    last_printed_lines = 0
    
    while True:
        rows = []
        rows.append({
            "label": f"[Confirm Selection ({len(selected_paths)} folders checked)]",
            "path": None,
            "is_confirm": True,
            "is_parent": False,
            "is_dir": False
        })
        
        parent = os.path.dirname(current_dir)
        if parent != current_dir:
            rows.append({
                "label": ".. (Up one level)",
                "path": parent,
                "is_confirm": False,
                "is_parent": True,
                "is_dir": False
            })
            
        try:
            for item in sorted(os.listdir(current_dir)):
                if item.startswith("."):
                    continue
                full_path = os.path.join(current_dir, item)
                if os.path.isdir(full_path):
                    rows.append({
                        "label": f"{item}/",
                        "path": full_path,
                        "is_confirm": False,
                        "is_parent": False,
                        "is_dir": True
                    })
        except OSError:
            pass

        if active_idx < 0:
            active_idx = 0
        if active_idx >= len(rows):
            active_idx = len(rows) - 1

        if active_idx < scroll_offset:
            scroll_offset = active_idx
        elif active_idx >= scroll_offset + max_viewport:
            scroll_offset = active_idx - max_viewport + 1

        visible_rows = rows[scroll_offset : scroll_offset + max_viewport]

        with console.capture() as capture:
            console.print("[bold]━━━ Select Directories to Mount ━━━[/bold]")
            console.print(f"Current Path: [accent]{current_dir}[/accent]\n")
            
            if scroll_offset > 0:
                console.print("   [accent]▲ (more items above)[/accent]")
            else:
                console.print()
                
            for idx, r in enumerate(visible_rows):
                abs_idx = scroll_offset + idx
                pointer = "→" if abs_idx == active_idx else " "
                
                if r["is_confirm"]:
                    if abs_idx == active_idx:
                        console.print(f"  [accent]→[/accent] [success][bold]{r['label']}[/bold][/success]")
                    else:
                        console.print(f"     [success]{r['label']}[/success]")
                elif r["is_parent"]:
                    if abs_idx == active_idx:
                        console.print(f"  [accent]→[/accent] [muted][bold]{r['label']}[/bold][/muted]")
                    else:
                        console.print(f"     [muted]{r['label']}[/muted]")
                else:
                    checked = r["path"] in selected_paths
                    checkbox = "[success]✔[/success]" if checked else "[muted]☐[/muted]"
                    if abs_idx == active_idx:
                        console.print(f"  [accent]→[/accent] {checkbox} [accent][bold]{r['label']}[/bold][/accent]")
                    else:
                        item_style = "info" if checked else "muted"
                        console.print(f"     {checkbox} [{item_style}]{r['label']}[/{item_style}]")
                        
            if scroll_offset + max_viewport < len(rows):
                console.print("   [accent]▼ (more items below)[/accent]")
            else:
                console.print()
                
            console.print("\n[muted][Space] Toggle Checkbox | [Enter] Navigate/Confirm | [Left] Go Up | [Esc/q] Cancel[/muted]")

        output_text = capture.get()
        lines_to_print = output_text.splitlines()
        if last_printed_lines > 0:
            sys.stdout.write(f"\r\033[{last_printed_lines}A")
            sys.stdout.write("\033[J")
            sys.stdout.flush()

        sys.stdout.write(output_text)
        sys.stdout.flush()
        last_printed_lines = len(lines_to_print)

        key = read_key()

        if key in ("q", "Q", "\x1b"):
            if last_printed_lines > 0:
                sys.stdout.write(f"\r\033[{last_printed_lines}A")
                sys.stdout.write("\033[J")
                sys.stdout.flush()
            return None

        elif key == "\x1b[A":
            if active_idx > 0:
                active_idx -= 1

        elif key == "\x1b[B":
            if active_idx < len(rows) - 1:
                active_idx += 1

        elif key == "\x1b[D":
            parent = os.path.dirname(current_dir)
            if parent != current_dir:
                current_dir = parent
                active_idx = 0
                scroll_offset = 0

        elif key == " ":
            r = rows[active_idx]
            if r["is_dir"]:
                path = r["path"]
                if path in selected_paths:
                    selected_paths.remove(path)
                else:
                    selected_paths.add(path)

        elif key in ("\r", "\n", "\x1b[C"):
            r = rows[active_idx]
            if r["is_confirm"]:
                if last_printed_lines > 0:
                    sys.stdout.write(f"\r\033[{last_printed_lines}A")
                    sys.stdout.write("\033[J")
                    sys.stdout.flush()
                return list(selected_paths)
            elif r["is_parent"] or r["is_dir"]:
                current_dir = r["path"]
                active_idx = 0
                scroll_offset = 0

