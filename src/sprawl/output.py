"""Sprawl CLI Output — Unified Rich + JSON structured output engine.

Centralizes all terminal output: log levels, context fields, and --json
structured mode. All modules import from here instead of utils.py.
Single dependency: rich>=13.0.0.
"""

import json
import contextlib
from typing import Any

from rich.console import Console
from rich.panel import Panel

from .config import config
from .theme import SDS_THEME

console = Console(theme=SDS_THEME)


# ---------------------------------------------------------------------------
# Log Level Definitions
# ---------------------------------------------------------------------------

_LOG_STYLES: dict[str, dict[str, str]] = {
    "debug":   {"prefix": "[~]", "style": "debug"},
    "info":    {"prefix": "[*]", "style": "accent"},
    "success": {"prefix": "[✓]", "style": "success"},
    "warning": {"prefix": "[!]", "style": "warning"},
    "error":   {"prefix": "[X]", "style": "error"},
}


# ---------------------------------------------------------------------------
# Core Output Engine
# ---------------------------------------------------------------------------

def _emit(
    level: str,
    message: str,
    context: dict[str, Any] | None = None,
) -> None:
    """Internal emission engine — routes to JSON or Rich based on config.

    Args:
        level: Log level key (debug, info, success, warning, error).
        message: Human-readable message string.
        context: Optional key-value pairs for structured logging.
    """
    if config.json_logging:
        payload: dict[str, Any] = {
            "level": level,
            "message": message,
        }
        if context:
            payload["context"] = context
        print(json.dumps(payload))
        return

    # Rich output path
    style_def = _LOG_STYLES.get(level, _LOG_STYLES["info"])
    prefix = style_def["prefix"]
    style = style_def["style"]

    if level == "warning":
        console.print(f"[{style}]\\{prefix} WARNING: {message}[/{style}]")
    elif level == "error":
        text = f"[bold error]{message}[/bold error]\n\n[dim]Tip: run [accent]sprawl doctor[/accent] to diagnose environment issues.[/dim]"
        console.print()
        console.print(Panel(text, title="[error]Sprawl Execution Error[/error]", border_style="error"))
        console.print()
    else:
        msg_style = "info" if level != "debug" else "debug"
        console.print(f"[{style}]\\{prefix}[/{style}] [{msg_style}]{message}[/{msg_style}]")

    # Debug context rendering (verbose mode only)
    if context and config.verbose:
        for key, value in context.items():
            console.print(f"    [debug]{key}={value}[/debug]")


# ---------------------------------------------------------------------------
# Public API — Drop-in replacements for old utils.print_* functions
# ---------------------------------------------------------------------------

@contextlib.contextmanager
def operation_spinner(message: str) -> Any:
    """Context manager for a rich spinner during long operations."""
    if config.json_logging:
        print(json.dumps({"level": "info", "message": f"{message} (started)"}))
        yield
        print(json.dumps({"level": "info", "message": f"{message} (completed)"}))
        return

    with console.status(f"[accent]{message}[/accent]", spinner="dots"):
        yield

def print_debug(msg: str, context: dict[str, Any] | None = None) -> None:
    """Prints a debug-level message (only visible in verbose mode).

    Args:
        msg: Debug message string.
        context: Optional structured context fields.
    """
    if config.verbose:
        _emit("debug", msg, context)


def print_status(msg: str, context: dict[str, Any] | None = None) -> None:
    """Prints a standard info-level status message.

    Args:
        msg: Status message string.
        context: Optional structured context fields.
    """
    _emit("info", msg, context)


def print_success(msg: str, context: dict[str, Any] | None = None) -> None:
    """Prints a success confirmation message.

    Args:
        msg: Success message string.
        context: Optional structured context fields.
    """
    _emit("success", msg, context)


def print_warning(msg: str, context: dict[str, Any] | None = None) -> None:
    """Prints a non-fatal warning message.

    Args:
        msg: Warning message string.
        context: Optional structured context fields.
    """
    _emit("warning", msg, context)


def print_error(msg: str, context: dict[str, Any] | None = None) -> None:
    """Prints a fatal error message.

    Args:
        msg: Error message string.
        context: Optional structured context fields.
    """
    _emit("error", msg, context)


from .tui.formatter import format_panel, format_checklist_item

