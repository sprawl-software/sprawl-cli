"""Interactive first-run onboarding wizard for lead generation."""

import sys
from .output import print_status, print_warning, format_panel
from .config import config


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

    # Question 1: Name
    name = ""
    while not name.strip():
        try:
            name = input("\033[38;2;93;92;255m[1/4] Name:\033[0m ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nAborted.")
            sys.exit(130)

    # Question 2: Business Email
    email = ""
    while not email.strip():
        try:
            email = input("\033[38;2;93;92;255m[2/4] Business Email:\033[0m ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nAborted.")
            sys.exit(130)

    # Question 3: Company Size
    company_sizes = ["1-10", "11-50", "51-200", "200+"]
    print("\n\033[38;2;93;92;255m[3/4] Company Size:\033[0m")
    for i, size in enumerate(company_sizes, 1):
        print(f"  {i}) {size}")

    size_choice = None
    while size_choice is None:
        try:
            choice = input("\033[38;2;93;92;255mSelect choice (1-4):\033[0m ").strip()
            idx = int(choice) - 1
            if 0 <= idx < len(company_sizes):
                size_choice = company_sizes[idx]
        except (KeyboardInterrupt, EOFError):
            print("\nAborted.")
            sys.exit(130)
        except ValueError:
            pass

    # Question 4: Primary Use Case
    use_cases = [
        "AST Compliance",
        "PII Shielding",
        "Workspace Virtualization",
    ]
    print("\n\033[38;2;93;92;255m[4/4] Primary Use Case:\033[0m")
    for i, case in enumerate(use_cases, 1):
        print(f"  {i}) {case}")

    case_choice = None
    while case_choice is None:
        try:
            choice = input("\033[38;2;93;92;255mSelect choice (1-3):\033[0m ").strip()
            idx = int(choice) - 1
            if 0 <= idx < len(use_cases):
                case_choice = use_cases[idx]
        except (KeyboardInterrupt, EOFError):
            print("\nAborted.")
            sys.exit(130)
        except ValueError:
            pass

    # Save to config.json
    config.update({
        "onboarding_completed": True,
        "lead_info": {
            "name": name,
            "email": email,
            "company_size": size_choice,
            "primary_use_case": case_choice,
        },
    })

    print(
        "\n\033[38;2;16;185;129m✔ Onboarding complete! Thank you for setting up Sprawl.\033[0m\n"
    )
