"""Styled TUI console formatter for Sprawl CLI diagnostics.

Enforces a strict 100-character line-width layout with Sovereign Violet borders
and Emerald pass/fail indicators without using external dependencies like Rich.
"""

import textwrap


def format_panel(
    title: str,
    content: str,
    border_color: str = "\033[38;2;93;92;255m",
    text_color: str = "\033[0m",
) -> str:
    """Formats a text string inside a unicode panel of exactly 100 characters width.

    Args:
        title: Title of the panel.
        content: Text content to display inside.
        border_color: ANSI escape sequence for the border.
        text_color: ANSI escape sequence for the text.
    """
    width = 100
    reset = "\033[0m"

    # Total width of content is 100 - 2 (left/right borders) - 2 (padding) = 96 characters.
    content_width = width - 4

    # Construct top border
    if title:
        title_str = f" {title} "
        if len(title_str) > content_width:
            title_str = title_str[:content_width]
        left_len = (content_width - len(title_str)) // 2
        right_len = content_width - len(title_str) - left_len
        top = f"╭{'─' * (left_len + 1)}{title_str}{'─' * (right_len + 1)}╮"
    else:
        top = f"╭{'─' * (width - 2)}╮"

    lines = []
    lines.append(f"{border_color}{top}{reset}")

    # Process content line by line
    raw_lines = content.splitlines()
    if not raw_lines:
        lines.append(f"{border_color}│{reset} {' ' * content_width} {border_color}│{reset}")
    for raw_line in raw_lines:
        wrapped = textwrap.wrap(raw_line, width=content_width)
        if not wrapped:
            lines.append(f"{border_color}│{reset} {' ' * content_width} {border_color}│{reset}")
        for wrap_line in wrapped:
            padded = wrap_line.ljust(content_width)
            lines.append(f"{border_color}│{reset} {text_color}{padded}{reset} {border_color}│{reset}")

    # Bottom border
    bottom = f"╰{'─' * (width - 2)}╯"
    lines.append(f"{border_color}{bottom}{reset}")

    return "\n".join(lines)


def format_checklist_item(success: bool, label: str) -> str:
    """Returns a styled doctor checklist item with ✓/✗ icons."""
    emerald = "\033[38;2;16;185;129m"
    crimson = "\033[38;2;239;68;68m"
    reset = "\033[0m"

    if success:
        return f" {emerald}✓{reset} {label}"
    else:
        return f" {crimson}✗{reset} {label}"
