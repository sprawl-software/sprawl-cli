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
    fd = sys.stdin.fileno()
    # Check if stdin is a TTY (running in terminal vs piped tests)
    if not sys.stdin.isatty():
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
    except Exception:
        return ""

    if char == "\x1b":
        # Check if more characters are waiting in the escape buffer
        rlist, _, _ = select.select([fd], [], [], 0.05)
        if rlist:
            try:
                next_chars = os.read(fd, 2).decode("utf-8", errors="ignore")
                return char + next_chars
            except Exception:
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

    active_idx = 0
    last_printed_lines = 0

    with raw_terminal():
        while True:
            cfg = _load_config(config_path)
            mounts = cfg.get("allowed_mounts", {})
            if not isinstance(mounts, dict):
                mounts = {}

            # Construct dashboard rows
            rows = []
            for alias, path in sorted(mounts.items()):
                rows.append({
                    "alias": alias,
                    "path": path,
                    "checked": True,
                    "is_add_btn": False
                })
            rows.append({
                "alias": "[Add new directory mount...]",
                "path": "",
                "checked": False,
                "is_add_btn": True
            })

            # Erase previous print
            if last_printed_lines > 0:
                sys.stdout.write(f"\r\033[{last_printed_lines}A")
                sys.stdout.write("\033[J")
                sys.stdout.flush()

            # Render dashboard
            output_lines = []
            output_lines.append("\033[1m━━━ Manage Allowed Workspace Mounts ━━━\033[0m")
            output_lines.append("Press Space to toggle mounts. Unchecking will remove them.\n")

            for i, r in enumerate(rows):
                pointer = "→" if i == active_idx else " "
                if r["is_add_btn"]:
                    btn_text = f"\033[38;2;16;185;129m{r['alias']}\033[0m"
                    output_lines.append(f" {pointer}   {btn_text}")
                else:
                    status_icon = "✔" if r["checked"] else "☐"
                    status_color = "\033[38;2;16;185;129m" if r["checked"] else "\033[38;2;239;68;68m"
                    reset = "\033[0m"
                    line = f" {pointer} [{status_color}{status_icon}{reset}] \033[38;2;93;92;255m@{r['alias']}\033[0m → {r['path']}"
                    output_lines.append(line)

            output_lines.append("\n\033[2m[Enter] Save & Sync | [Esc/q] Cancel\033[0m")
            
            # Print dashboard
            for line in output_lines:
                sys.stdout.write(line + "\n")
            sys.stdout.flush()
            last_printed_lines = len(output_lines)

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
                    # Open Directory Picker
                    if last_printed_lines > 0:
                        sys.stdout.write(f"\r\033[{last_printed_lines}A")
                        sys.stdout.write("\033[J")
                        sys.stdout.flush()
                        last_printed_lines = 0
                    
                    new_path = show_directory_picker(workspace_root)
                    if new_path:
                        default_alias = slugify(os.path.basename(new_path))
                        sys.stdout.write(f"\rEnter mount alias (default: {default_alias}): ")
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
                            sys.stdout.write("\033[?25l")
                            sys.stdout.flush()

                        alias = slugify(alias_input) if alias_input else default_alias
                        if not alias:
                            alias = "mount"

                        cfg["allowed_mounts"][alias] = new_path
                        _write_config(config_path, cfg)
                else:
                    alias = r["alias"]
                    if alias in cfg.get("allowed_mounts", {}):
                        cfg["allowed_mounts"].pop(alias)
                    else:
                        cfg["allowed_mounts"][alias] = r["path"]
                    _write_config(config_path, cfg)

            elif key in ("\r", "\n"):  # Enter to confirm or add
                r = rows[active_idx]
                if r["is_add_btn"]:
                    if last_printed_lines > 0:
                        sys.stdout.write(f"\r\033[{last_printed_lines}A")
                        sys.stdout.write("\033[J")
                        sys.stdout.flush()
                        last_printed_lines = 0
                    new_path = show_directory_picker(workspace_root)
                    if new_path:
                        default_alias = slugify(os.path.basename(new_path))
                        sys.stdout.write(f"\rEnter mount alias (default: {default_alias}): ")
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
                            sys.stdout.write("\033[?25l")
                            sys.stdout.flush()
                        alias = slugify(alias_input) if alias_input else default_alias
                        if not alias:
                            alias = "mount"
                        cfg["allowed_mounts"][alias] = new_path
                        _write_config(config_path, cfg)
                else:
                    if last_printed_lines > 0:
                        sys.stdout.write(f"\r\033[{last_printed_lines}A")
                        sys.stdout.write("\033[J")
                        sys.stdout.flush()
                    print_status("Synchronizing workspace configurations...")
                    cmd_sync(workspace_root)
                    return


def show_directory_picker(start_dir: str) -> Optional[str]:
    """Renders a keyboard-interactive directory selection browser TUI."""
    current_dir = os.path.abspath(start_dir)
    active_idx = 0
    last_printed_lines = 0
    
    while True:
        rows = []
        rows.append({
            "label": f"[Select this directory: {current_dir}]",
            "path": current_dir,
            "is_dir": True,
            "is_select_btn": True,
            "is_parent": False
        })
        
        parent = os.path.dirname(current_dir)
        if parent != current_dir:
            rows.append({
                "label": ".. (Up one level)",
                "path": parent,
                "is_dir": True,
                "is_select_btn": False,
                "is_parent": True
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
                        "is_dir": True,
                        "is_select_btn": False,
                        "is_parent": False
                    })
        except Exception:
            pass

        if active_idx >= len(rows):
            active_idx = len(rows) - 1
        if active_idx < 0:
            active_idx = 0

        if last_printed_lines > 0:
            sys.stdout.write(f"\r\033[{last_printed_lines}A")
            sys.stdout.write("\033[J")
            sys.stdout.flush()

        output_lines = []
        output_lines.append("\033[1m━━━ Select Directory to Mount ━━━\033[0m")
        output_lines.append(f"Current Path: \033[38;2;93;92;255m{current_dir}\033[0m\n")

        for i, r in enumerate(rows):
            pointer = "→" if i == active_idx else " "
            if r["is_select_btn"]:
                output_lines.append(f" {pointer}   \033[38;2;16;185;129m{r['label']}\033[0m")
            elif r["is_parent"]:
                output_lines.append(f" {pointer}   \033[2m{r['label']}\033[0m")
            else:
                output_lines.append(f" {pointer}   {r['label']}")

        output_lines.append("\n\033[2m[Enter] Navigate/Select | [Left] Go Up | [q/Esc] Back\033[0m")

        for line in output_lines:
            sys.stdout.write(line + "\n")
        sys.stdout.flush()
        last_printed_lines = len(output_lines)

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

        elif key in ("\r", "\n", "\x1b[C"):
            r = rows[active_idx]
            if r["is_select_btn"]:
                if last_printed_lines > 0:
                    sys.stdout.write(f"\r\033[{last_printed_lines}A")
                    sys.stdout.write("\033[J")
                    sys.stdout.flush()
                return r["path"]
            elif r["is_parent"] or r["is_dir"]:
                current_dir = r["path"]
                active_idx = 0

