"""Interactive first-run onboarding wizard for lead generation."""

from .config import config
from .tui.formatter import format_panel


def _prompt_non_empty_field(prompt_label: str) -> str:
    """Prompts repeatedly until the user enters a non-empty text response."""
    value = ""
    while not value:
        try:
            value = input(prompt_label).strip()
        except (KeyboardInterrupt, EOFError) as e:
            raise KeyboardInterrupt from e
    return value


def _prompt_numbered_option(
    header_label: str,
    select_prompt: str,
    options: list[str],
) -> str:
    """Prints a numbered menu and prompts until a valid 1-based choice is entered."""
    print(f"\n{header_label}")
    for idx, option in enumerate(options, 1):
        print(f"  {idx}) {option}")

    while True:
        try:
            choice = input(select_prompt).strip()
            idx = int(choice) - 1
            if 0 <= idx < len(options):
                return options[idx]
        except (KeyboardInterrupt, EOFError) as e:
            raise KeyboardInterrupt from e
        except ValueError:
            continue


def run_onboarding_wizard() -> None:
    """Launches the premium first-run interactive onboarding flow."""
    cfg = config.load()
    if cfg.get("onboarding_completed"):
        return

    header_text = (
        "Welcome to SPRAWL! Since this is your first time starting up, please take a "
        "moment to complete this quick onboarding questionnaire. Your answers will be "
        "stored in ~/.sprawl/config.json."
    )
    panel_str = format_panel(
        "SPRAWL Onboarding Protocol",
        header_text,
        border_color="\033[38;2;93;92;255m",
        text_color="\033[0m",
    )
    print(panel_str)
    print()

    name = _prompt_non_empty_field("\033[38;2;93;92;255m[1/4] Name:\033[0m ")
    email = _prompt_non_empty_field("\033[38;2;93;92;255m[2/4] Business Email:\033[0m ")
    size_choice = _prompt_numbered_option(
        "\033[38;2;93;92;255m[3/4] Company Size:\033[0m",
        "\033[38;2;93;92;255mSelect choice (1-4):\033[0m ",
        ["1-10", "11-50", "51-200", "200+"],
    )
    case_choice = _prompt_numbered_option(
        "\033[38;2;93;92;255m[4/4] Primary Use Case:\033[0m",
        "\033[38;2;93;92;255mSelect choice (1-3):\033[0m ",
        ["AST Compliance", "PII Shielding", "Workspace Virtualization"],
    )

    config.update(
        {
            "onboarding_completed": True,
            "lead_info": {
                "name": name,
                "email": email,
                "company_size": size_choice,
                "primary_use_case": case_choice,
            },
        }
    )

    print("\n\033[38;2;16;185;129m✔ Onboarding complete! Thank you for setting up Sprawl.\033[0m\n")
