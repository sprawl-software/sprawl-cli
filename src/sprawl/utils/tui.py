"""Sprawl Keyboard-Interactive Checkbox TUI Engine.

Pure standard library raw keypress reader and visual selection rendering using Rich.
Restores terminal cleanly on exit or abrupt failure.
"""

import contextlib
import json
import os
import re
import sys
from collections.abc import Callable, Iterator
from typing import Any

if sys.platform != "win32":
    try:
        import select
        import termios
        import tty
    except ImportError:
        tty = None  # type: ignore
        select = None  # type: ignore
        termios = None  # type: ignore
    msvcrt = None
else:
    try:
        import msvcrt
    except ImportError:
        msvcrt = None  # type: ignore
    tty = None  # type: ignore
    select = None  # type: ignore
    termios = None  # type: ignore

from rich.console import Console

from ..theme import SDS_THEME

# Reuse the global console styled with Sprawl Design System theme
console = Console(theme=SDS_THEME)

_WIN_ARROW_KEYS: dict[bytes, str] = {
    b"H": "\x1b[A",  # Arrow Up
    b"P": "\x1b[B",  # Arrow Down
    b"K": "\x1b[D",  # Arrow Left
    b"M": "\x1b[C",  # Arrow Right
}

_WIN_DIRECT_KEYS: dict[bytes, str] = {
    b"\r": "\r",
    b"\n": "\n",
    b"\x1b": "\x1b",
    b" ": " ",
}


def _slugify_alias(name: str) -> str:
    """Converts a folder name into a clean, safe alphanumeric mount alias."""
    normalized = re.sub(r"[^a-z0-9_-]", "_", name.lower())
    return re.sub(r"_+", "_", normalized).strip("_")


def _enable_windows_vt() -> None:
    """Enables Virtual Terminal Processing on Windows console for ANSI escape sequences."""
    if sys.platform != "win32":
        return
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE = -11
        mode = ctypes.c_ulong()
        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            kernel32.SetConsoleMode(handle, mode.value | 0x0004)
    except (AttributeError, OSError):  # nosec B110
        return


def is_tui_supported() -> bool:
    """Returns True if the current terminal environment supports raw interactive TUI mode."""
    try:
        if not (sys.stdin.isatty() and sys.stdout.isatty()):
            return False
    except (AttributeError, OSError, ValueError):
        return False

    if sys.platform == "win32":
        return msvcrt is not None
    return termios is not None and tty is not None and select is not None


@contextlib.contextmanager
def raw_terminal() -> Iterator[int | None]:
    """Context manager to enable raw terminal mode and safely restore settings on exit."""
    if sys.platform == "win32":
        _enable_windows_vt()
        try:
            sys.stdout.write("\033[?25l")
            sys.stdout.flush()
            yield None
        finally:
            sys.stdout.write("\033[?25h")
            sys.stdout.flush()
        return

    fd = _get_stdin_fd()
    if fd is None or not sys.stdin.isatty() or termios is None or tty is None:
        yield fd
        return

    old_settings = termios.tcgetattr(fd)
    try:
        sys.stdout.write("\033[?25l")
        sys.stdout.flush()
        tty.setcbreak(fd)
        yield fd
    finally:
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def _get_stdin_fd() -> int | None:
    """Safely resolves the file descriptor for standard input."""
    try:
        return sys.stdin.fileno()
    except (AttributeError, OSError, ValueError):
        return None


def _read_key_windows() -> str:
    """Reads a single keypress or arrow sequence on Windows consoles."""
    if not sys.stdin.isatty() or msvcrt is None:
        return sys.stdin.read(1)
    try:
        ch = msvcrt.getch()
    except OSError:
        return ""
    if ch in (b"\x00", b"\xe0"):
        try:
            ch2 = msvcrt.getch()
        except OSError:
            return ""
        return _WIN_ARROW_KEYS.get(ch2, "")
    if ch in _WIN_DIRECT_KEYS:
        return _WIN_DIRECT_KEYS[ch]
    return ch.decode("utf-8", errors="ignore")


def _read_key_posix() -> str:
    """Reads a single keypress or ANSI escape sequence on POSIX terminals."""
    if not sys.stdin.isatty() or termios is None or select is None:
        return sys.stdin.read(1)

    fd = sys.stdin.fileno()
    try:
        char = os.read(fd, 1).decode("utf-8", errors="ignore")
    except OSError:
        return ""

    if char == "\x1b":
        rlist, _, _ = select.select([fd], [], [], 0.05)
        if rlist:
            try:
                next_chars = os.read(fd, 2).decode("utf-8", errors="ignore")
                return char + next_chars
            except OSError:
                return char
    return char


def read_key() -> str:
    """Reads a single keypress or ANSI escape sequence from stdin in raw mode."""
    if sys.platform == "win32":
        return _read_key_windows()
    return _read_key_posix()


def _clear_rendered_lines(line_count: int) -> None:
    """Moves cursor up and clears previously rendered TUI frame lines."""
    if line_count > 0:
        sys.stdout.write(f"\r\033[{line_count}A")
        sys.stdout.write("\033[J")
        sys.stdout.flush()


def _present_captured_frame(output_text: str, last_printed_lines: int) -> int:
    """Replaces the previous terminal frame with newly captured text and returns line count."""
    _clear_rendered_lines(last_printed_lines)
    sys.stdout.write(output_text)
    sys.stdout.flush()
    return len(output_text.splitlines())


def _clamp_viewport_offset(active_idx: int, scroll_offset: int, max_viewport: int) -> int:
    """Computes the updated viewport scroll offset to keep active_idx visible."""
    if active_idx >= scroll_offset + max_viewport:
        return active_idx - max_viewport + 1
    if active_idx < scroll_offset:
        return active_idx
    return scroll_offset


def _flatten_category_rows(
    categories: dict[str, list[tuple[str, bool]]],
) -> list[dict[str, Any]]:
    """Flattens categorized (item, checked) tuples into renderable TUI row dicts."""
    rows: list[dict[str, Any]] = []
    for cat, items in categories.items():
        rows.append({"is_header": True, "label": cat.upper(), "category": cat})
        for name, checked in items:
            rows.append(
                {
                    "is_header": False,
                    "label": name,
                    "category": cat,
                    "checked": checked,
                }
            )
    return rows


def _render_checkbox_row(row: dict[str, Any], is_active: bool) -> None:
    """Renders a single header or selectable item row inside a checkbox menu."""
    if row["is_header"]:
        console.print(f" 📁 [accent]{row['label']}[/accent]")
        return

    checkbox = "[success]✔[/success]" if row["checked"] else "[muted]☐[/muted]"
    if is_active:
        console.print(
            f"  [accent]→[/accent] {checkbox} [accent][bold]{row['label']}[/bold][/accent]"
        )
    else:
        item_style = "info" if row["checked"] else "muted"
        console.print(f"    {checkbox} [{item_style}]{row['label']}[/{item_style}]")


def _render_checkbox_frame(
    title: str,
    rows: list[dict[str, Any]],
    active_row_idx: int,
    scroll_offset: int,
    max_viewport: int,
) -> str:
    """Captures a complete frame of the categorized checkbox menu."""
    selectable_total = sum(1 for r in rows if not r["is_header"])
    num_checked = sum(1 for r in rows if not r["is_header"] and r.get("checked"))
    visible_rows = rows[scroll_offset : scroll_offset + max_viewport]

    with console.capture() as capture:
        console.print(f"[accent]━━━ {title} ━━━[/accent]")
        console.print(
            "[muted]Navigate: ↑/↓ | Toggle: Space | Confirm: Enter | Cancel: Esc/q[/muted]\n"
        )
        console.print("   [accent]▲ (more items above)[/accent]" if scroll_offset > 0 else "")

        for idx, row in enumerate(visible_rows):
            _render_checkbox_row(row, (scroll_offset + idx) == active_row_idx)

        has_more_below = scroll_offset + max_viewport < len(rows)
        console.print("   [accent]▼ (more items below)[/accent]" if has_more_below else "")
        active_label = rows[active_row_idx]["label"]
        console.print(
            f" [muted]Selected: {active_label} | Checked: {num_checked}/{selectable_total}[/muted]"
        )

    return capture.get()


def _compile_checked_categories(
    categories: dict[str, list[tuple[str, bool]]],
    rows: list[dict[str, Any]],
) -> dict[str, list[str]]:
    """Extracts checked item labels grouped by category."""
    result: dict[str, list[str]] = {cat: [] for cat in categories}
    for row in rows:
        if not row["is_header"] and row["checked"]:
            result[row["category"]].append(row["label"])
    return result


def _step_selection_index(key: str, current_idx: int, total_items: int) -> int:
    """Updates the active index on Up/Down arrow keypresses within [0, total_items - 1]."""
    if key == "\x1b[A" and current_idx > 0:
        return current_idx - 1
    if key == "\x1b[B" and current_idx < total_items - 1:
        return current_idx + 1
    return current_idx


def show_checkbox_menu(
    title: str,
    categories: dict[str, list[tuple[str, bool]]],
    max_viewport: int = 12,
) -> dict[str, list[str]] | None:
    """Renders a keyboard-interactive TUI checkbox menu for categorized DNA items."""
    rows = _flatten_category_rows(categories)
    selectable_indices = [i for i, r in enumerate(rows) if not r["is_header"]]

    if not selectable_indices:
        console.print("[warning][!] No items found to configure.[/warning]")
        return None

    active_selectable_idx = 0
    scroll_offset = 0
    last_printed_lines = 0

    with raw_terminal():
        while True:
            active_row_idx = selectable_indices[active_selectable_idx]
            scroll_offset = _clamp_viewport_offset(active_row_idx, scroll_offset, max_viewport)
            frame = _render_checkbox_frame(title, rows, active_row_idx, scroll_offset, max_viewport)
            last_printed_lines = _present_captured_frame(frame, last_printed_lines)

            key = read_key()
            if key in ("q", "Q", "\x1b"):
                _clear_rendered_lines(last_printed_lines)
                return None
            if key in ("\r", "\n"):
                _clear_rendered_lines(last_printed_lines)
                return _compile_checked_categories(categories, rows)
            if key == " ":
                rows[active_row_idx]["checked"] = not rows[active_row_idx]["checked"]
            else:
                active_selectable_idx = _step_selection_index(
                    key, active_selectable_idx, len(selectable_indices)
                )


def _render_numbered_selection_prompt(
    title: str,
    flat_items: list[tuple[str, str, bool]],
) -> None:
    """Prints the numbered selection table and current default items."""
    console.print(f"\n[bold accent]━━━ {title} ━━━[/bold accent]")
    console.print(
        "[muted]Selective Configuration: Enter numbers (e.g. '1, 2'), names, 'all', 'none', or press Enter for defaults.[/muted]\n"
    )
    for idx, (cat, name, checked) in enumerate(flat_items, 1):
        status = "[success][selected][/success]" if checked else "[muted][unselected][/muted]"
        console.print(
            f"  [bold cyan][{idx:>2}][/bold cyan] {name:<16} {status} [muted]({cat})[/muted]"
        )
    defaults_summary = [name for _, name, checked in flat_items if checked]
    default_text = ", ".join(defaults_summary) if defaults_summary else "none"
    console.print(f"\n[muted]Current defaults: {default_text}[/muted]")


def _parse_numbered_user_input(
    user_input: str,
    categories: dict[str, list[tuple[str, bool]]],
    flat_items: list[tuple[str, str, bool]],
) -> dict[str, list[str]]:
    """Parses user selection tokens ('', 'none', 'all', indices, or item names)."""
    result: dict[str, list[str]] = {cat: [] for cat in categories}
    lowered = user_input.lower()

    if user_input == "":
        for cat, name, checked in flat_items:
            if checked:
                result[cat].append(name)
        return result

    if lowered in ("none", "0", "clear", "[]"):
        return result

    if lowered in ("all", "*"):
        for cat, name, _ in flat_items:
            result[cat].append(name)
        return result

    selected_indices = _resolve_token_indices(user_input, flat_items)
    for idx in sorted(selected_indices):
        cat, name, _ = flat_items[idx]
        result[cat].append(name)
    return result


def _resolve_token_indices(
    user_input: str,
    flat_items: list[tuple[str, str, bool]],
) -> set[int]:
    """Resolves comma/space-separated numeric indices or names into 0-based indices."""
    tokens = [t.strip() for t in user_input.replace(" ", ",").split(",") if t.strip()]
    selected_indices: set[int] = set()
    for token in tokens:
        if token.isdigit():
            idx = int(token)
            if 1 <= idx <= len(flat_items):
                selected_indices.add(idx - 1)
            continue
        token_lower = token.lower()
        for i, (_, name, _) in enumerate(flat_items):
            if name.lower() == token_lower:
                selected_indices.add(i)
    return selected_indices


def prompt_numbered_selection(
    title: str,
    categories: dict[str, list[tuple[str, bool]]],
) -> dict[str, list[str]] | None:
    """Renders a simple, zero-raw-mode numbered CLI prompt for selecting items."""
    flat_items = [
        (cat, name, checked) for cat, items in categories.items() for name, checked in items
    ]
    if not flat_items:
        console.print("[warning][!] No items found to configure.[/warning]")
        return None

    _render_numbered_selection_prompt(title, flat_items)

    try:
        sys.stdout.write("Selection (Enter for defaults, 'q' to cancel): ")
        sys.stdout.flush()
        raw_line = sys.stdin.readline()
        if not raw_line:
            return _parse_numbered_user_input("", categories, flat_items)
        user_input = raw_line.strip()
    except (KeyboardInterrupt, EOFError):
        console.print("\n[warning]Selection cancelled.[/warning]")
        return None

    if user_input.lower() in ("q", "quit", "exit", "cancel"):
        console.print("[warning]Operation cancelled.[/warning]")
        return None

    return _parse_numbered_user_input(user_input, categories, flat_items)


def _load_workspace_mounts_fallback(
    workspace_root: str,
) -> tuple[str, dict[str, Any], dict[str, str]]:
    """Loads .agents/sprawl-config.json directly without importing command modules."""
    config_path = os.path.join(os.path.abspath(workspace_root), ".agents", "sprawl-config.json")
    cfg: dict[str, Any] = {"allowed_mounts": {}}
    if os.path.exists(config_path):
        try:
            with open(config_path, encoding="utf-8") as f:
                loaded = json.load(f)
                if isinstance(loaded, dict):
                    cfg = loaded
        except (json.JSONDecodeError, OSError):
            pass
    raw_mounts = cfg.get("allowed_mounts", {})
    mounts = dict(raw_mounts) if isinstance(raw_mounts, dict) else {}
    return config_path, cfg, mounts


def _save_workspace_mounts_fallback(
    config_path: str,
    cfg: dict[str, Any],
    active_mounts: dict[str, str],
    on_save: Callable[[dict[str, str]], None] | None,
) -> None:
    """Persists updated mounts via callback or directly to sprawl-config.json."""
    if on_save is not None:
        on_save(active_mounts)
        return
    cfg["allowed_mounts"] = active_mounts
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)


def _build_mount_rows(
    mounts: dict[str, str],
    checked_states: dict[str, bool],
) -> list[dict[str, Any]]:
    """Builds row dictionaries for the interactive mount dashboard."""
    rows: list[dict[str, Any]] = [
        {
            "alias": alias,
            "path": path,
            "checked": checked_states.get(alias, False),
            "is_add_btn": False,
        }
        for alias, path in sorted(mounts.items())
    ]
    rows.append(
        {
            "alias": "[Add new directory mount...]",
            "path": "",
            "checked": False,
            "is_add_btn": True,
        }
    )
    return rows


def _render_mount_dashboard_row(row: dict[str, Any], is_active: bool) -> None:
    """Renders a single row of the workspace mount dashboard."""
    if row["is_add_btn"]:
        btn_text = f"[success]{row['alias']}[/success]"
        prefix = "  [accent]→[/accent] " if is_active else "     "
        label = f"[bold]{btn_text}[/bold]" if is_active else btn_text
        console.print(f"{prefix}{label}")
        return

    checkbox = "[success]✔[/success]" if row["checked"] else "[muted]☐[/muted]"
    if is_active:
        console.print(
            f"  [accent]→[/accent] {checkbox} [accent][bold]@{row['alias']}[/bold][/accent] → {row['path']}"
        )
    else:
        item_style = "info" if row["checked"] else "muted"
        console.print(
            f"     {checkbox} [{item_style}]@{row['alias']}[/{item_style}] → {row['path']}"
        )


def _render_mount_dashboard_frame(
    rows: list[dict[str, Any]],
    active_idx: int,
    scroll_offset: int,
    max_viewport: int,
) -> str:
    """Captures a complete frame of the mount dashboard."""
    visible_rows = rows[scroll_offset : scroll_offset + max_viewport]
    with console.capture() as capture:
        console.print("[bold]━━━ Manage Allowed Workspace Mounts ━━━[/bold]")
        console.print("Press Space to toggle mounts. Unchecking will remove them.\n")
        console.print("   [accent]▲ (more items above)[/accent]" if scroll_offset > 0 else "")

        for idx, row in enumerate(visible_rows):
            _render_mount_dashboard_row(row, (scroll_offset + idx) == active_idx)

        has_more_below = scroll_offset + max_viewport < len(rows)
        console.print("   [accent]▼ (more items below)[/accent]" if has_more_below else "")
        console.print("\n[muted][Enter] Save & Sync | [Space] Toggle | [Esc/q] Cancel[/muted]")
    return capture.get()


def _filter_checked_mounts(
    mounts: dict[str, str],
    checked_states: dict[str, bool],
) -> dict[str, str]:
    """Filters mounts dictionary to aliases currently marked as checked."""
    return {alias: path for alias, path in mounts.items() if checked_states.get(alias, False)}


def _handle_mount_dashboard_action(
    key: str,
    row: dict[str, Any],
    workspace_root: str,
    mounts: dict[str, str],
    checked_states: dict[str, bool],
) -> tuple[bool, bool]:
    """Processes Space/Enter on a mount dashboard row; returns (should_save, cleared_screen)."""
    if row["is_add_btn"]:
        added = _add_new_mounts(workspace_root, mounts, checked_states)
        return added, True
    if key == " ":
        alias = row["alias"]
        checked_states[alias] = not checked_states[alias]
        return False, False
    return True, False


def _process_mount_key(
    key: str,
    rows: list[dict[str, Any]],
    active_idx: int,
    workspace_root: str,
    mounts: dict[str, str],
    checked_states: dict[str, bool],
    last_printed_lines: int,
) -> tuple[bool, bool, int, int]:
    """Processes a single keypress in show_mount_dashboard; returns (cancelled, saved, active_idx, lines)."""
    if key in ("q", "Q", "\x1b"):
        _clear_rendered_lines(last_printed_lines)
        return True, False, active_idx, 0
    if key not in (" ", "\r", "\n"):
        return False, False, _step_selection_index(key, active_idx, len(rows)), last_printed_lines

    row = rows[active_idx]
    if row["is_add_btn"]:
        _clear_rendered_lines(last_printed_lines)
        last_printed_lines = 0
    should_save, _ = _handle_mount_dashboard_action(
        key, row, workspace_root, mounts, checked_states
    )
    return False, should_save, active_idx, last_printed_lines


def show_mount_dashboard(
    workspace_root: str,
    on_save: Callable[[dict[str, str]], None] | None = None,
) -> dict[str, str] | None:
    """Renders the workspace mount manager dashboard."""
    config_path, cfg, mounts = _load_workspace_mounts_fallback(workspace_root)
    checked_states = dict.fromkeys(mounts, True)

    active_idx = 0
    scroll_offset = 0
    max_viewport = 10
    last_printed_lines = 0

    with raw_terminal():
        while True:
            rows = _build_mount_rows(mounts, checked_states)
            active_idx = max(0, min(active_idx, len(rows) - 1))
            scroll_offset = _clamp_viewport_offset(active_idx, scroll_offset, max_viewport)
            frame = _render_mount_dashboard_frame(rows, active_idx, scroll_offset, max_viewport)
            last_printed_lines = _present_captured_frame(frame, last_printed_lines)

            cancelled, should_save, active_idx, last_printed_lines = _process_mount_key(
                read_key(),
                rows,
                active_idx,
                workspace_root,
                mounts,
                checked_states,
                last_printed_lines,
            )
            if cancelled:
                return None
            if should_save:
                _clear_rendered_lines(last_printed_lines)
                selected = _filter_checked_mounts(mounts, checked_states)
                _save_workspace_mounts_fallback(config_path, cfg, selected, on_save)
                return selected


def _read_cooked_line() -> str:
    """Temporarily restores cooked terminal mode to read a line of text cleanly."""
    if sys.platform == "win32" or termios is None or tty is None:
        return sys.stdin.readline().strip()

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return sys.stdin.readline().strip()
    finally:
        tty.setcbreak(fd)
        termios.tcflush(fd, termios.TCIFLUSH)
        sys.stdout.write("\033[?25l")
        sys.stdout.flush()


def _add_new_mounts(
    workspace_root: str,
    mounts: dict[str, str],
    checked_states: dict[str, bool],
) -> bool:
    """Runs the directory picker and prompts for aliases without key bleeding."""
    new_paths = show_directory_picker(workspace_root)
    if not new_paths:
        return False

    for new_path in new_paths:
        base_name = os.path.basename(new_path)
        default_alias = _slugify_alias(base_name)
        sys.stdout.write(
            f"\rEnter mount alias for {base_name} (default: {default_alias}): \033[?25h"
        )
        sys.stdout.flush()
        alias_input = _read_cooked_line()
        alias = (_slugify_alias(alias_input) if alias_input else default_alias) or "mount"
        mounts[alias] = new_path
        checked_states[alias] = True
    return True


def _build_directory_picker_rows(
    current_dir: str,
    selected_paths: set[str],
) -> list[dict[str, Any]]:
    """Constructs directory navigation and confirmation rows for current_dir."""
    rows: list[dict[str, Any]] = [
        {
            "label": f"[Confirm Selection ({len(selected_paths)} folders checked)]",
            "path": None,
            "is_confirm": True,
            "is_parent": False,
            "is_dir": False,
        }
    ]
    parent = os.path.dirname(current_dir)
    if parent != current_dir:
        rows.append(
            {
                "label": ".. (Up one level)",
                "path": parent,
                "is_confirm": False,
                "is_parent": True,
                "is_dir": False,
            }
        )
    try:
        for item in sorted(os.listdir(current_dir)):
            if item.startswith("."):
                continue
            full_path = os.path.join(current_dir, item)
            if os.path.isdir(full_path):
                rows.append(
                    {
                        "label": f"{item}/",
                        "path": full_path,
                        "is_confirm": False,
                        "is_parent": False,
                        "is_dir": True,
                    }
                )
    except OSError:
        pass
    return rows


def _format_picker_special_row(label: str, color: str, is_active: bool) -> str:
    """Formats a confirm or parent navigation row for the directory picker."""
    prefix = "  [accent]→[/accent] " if is_active else "     "
    if is_active:
        return f"{prefix}[{color}][bold]{label}[/bold][/{color}]"
    return f"{prefix}[{color}]{label}[/{color}]"


def _render_directory_picker_row(
    row: dict[str, Any],
    is_active: bool,
    selected_paths: set[str],
) -> None:
    """Renders a single row inside the directory picker browser."""
    if row["is_confirm"]:
        console.print(_format_picker_special_row(row["label"], "success", is_active))
        return
    if row["is_parent"]:
        console.print(_format_picker_special_row(row["label"], "muted", is_active))
        return

    checked = row["path"] in selected_paths
    checkbox = "[success]✔[/success]" if checked else "[muted]☐[/muted]"
    if is_active:
        console.print(
            f"  [accent]→[/accent] {checkbox} [accent][bold]{row['label']}[/bold][/accent]"
        )
    else:
        item_style = "info" if checked else "muted"
        console.print(f"     {checkbox} [{item_style}]{row['label']}[/{item_style}]")


def _render_directory_picker_frame(
    current_dir: str,
    rows: list[dict[str, Any]],
    active_idx: int,
    scroll_offset: int,
    selected_paths: set[str],
) -> str:
    """Captures a complete frame of the directory picker TUI."""
    max_viewport = 10
    visible_rows = rows[scroll_offset : scroll_offset + max_viewport]
    with console.capture() as capture:
        console.print("[bold]━━━ Select Directories to Mount ━━━[/bold]")
        console.print(f"Current Path: [accent]{current_dir}[/accent]\n")
        console.print("   [accent]▲ (more items above)[/accent]" if scroll_offset > 0 else "")

        for idx, row in enumerate(visible_rows):
            _render_directory_picker_row(row, (scroll_offset + idx) == active_idx, selected_paths)

        has_more_below = scroll_offset + max_viewport < len(rows)
        console.print("   [accent]▼ (more items below)[/accent]" if has_more_below else "")
        console.print(
            "\n[muted][Space] Toggle Checkbox | [Enter] Navigate/Confirm | [Left] Go Up | [Esc/q] Cancel[/muted]"
        )
    return capture.get()


def _toggle_selected_path(selected_paths: set[str], path: str | None) -> None:
    """Adds or removes a directory path in the selected_paths set."""
    if not path:
        return
    if path in selected_paths:
        selected_paths.remove(path)
    else:
        selected_paths.add(path)


def _step_directory_picker_navigation(
    key: str,
    current_dir: str,
    rows: list[dict[str, Any]],
    active_idx: int,
    scroll_offset: int,
) -> tuple[str, int, int]:
    """Updates directory path, active index, and scroll offset for navigation keys."""
    if key == "\x1b[D":
        parent = os.path.dirname(current_dir)
        if parent != current_dir:
            return parent, 0, 0
        return current_dir, active_idx, scroll_offset
    if key in ("\r", "\n", "\x1b[C"):
        row = rows[active_idx]
        if row["is_parent"] or row["is_dir"]:
            return row["path"], 0, 0
    return current_dir, _step_selection_index(key, active_idx, len(rows)), scroll_offset


def _is_picker_confirm_key(key: str, row: dict[str, Any]) -> bool:
    """Returns True when the user presses Enter or Right Arrow on the Confirm row."""
    return key in ("\r", "\n", "\x1b[C") and bool(row["is_confirm"])


def show_directory_picker(start_dir: str) -> list[str] | None:
    """Renders a keyboard-interactive directory selection browser TUI with checkboxes."""
    current_dir = os.path.abspath(start_dir)
    selected_paths: set[str] = set()
    active_idx = 0
    scroll_offset = 0
    max_viewport = 10
    last_printed_lines = 0

    while True:
        rows = _build_directory_picker_rows(current_dir, selected_paths)
        active_idx = max(0, min(active_idx, len(rows) - 1))
        scroll_offset = _clamp_viewport_offset(active_idx, scroll_offset, max_viewport)
        frame = _render_directory_picker_frame(
            current_dir, rows, active_idx, scroll_offset, selected_paths
        )
        last_printed_lines = _present_captured_frame(frame, last_printed_lines)

        key = read_key()
        if key in ("q", "Q", "\x1b"):
            _clear_rendered_lines(last_printed_lines)
            return None
        if key == " ":
            _toggle_selected_path(selected_paths, rows[active_idx].get("path"))
        elif _is_picker_confirm_key(key, rows[active_idx]):
            _clear_rendered_lines(last_printed_lines)
            return list(selected_paths)
        else:
            current_dir, active_idx, scroll_offset = _step_directory_picker_navigation(
                key, current_dir, rows, active_idx, scroll_offset
            )
