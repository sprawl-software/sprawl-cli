"""Native demonstration engine — zero os.chdir() mutations.

All workspace operations use explicit absolute paths, ensuring the
parent process's working directory is never mutated during demo runs.
"""

import os
import shutil
import subprocess
import tempfile
from .config import config
from .output import print_status, print_error, console
from .utils import CATEGORIES
from .commands.init_cmd import cmd_init, cmd_fetch_dna
from .commands.workspace import cmd_create
from .commands.artifacts import cmd_add
from .commands.sync_cmd import cmd_sync
from .commands.diagnostics import cmd_clean_test

DEMOS = {
    "1": {
        "title": "Cross-Team Scaffolding",
        "description": "Multi-squad (.NET, React, Sales) parallel execution",
        "squads": [
            {"name": "dotnet-squad", "artifacts": ["csharp_standards.md", "entity_framework_optimizer", "ci_cd_azure.yml"]},
            {"name": "web-squad", "artifacts": ["react_best_practices.md", "web_artifacts_builder", "vercel_production_deployment.yml"]},
            {"name": "sales-squad", "artifacts": ["sales_outreach_compliance.md", "hubspot_api_connector", "lead_generation.yml"]},
            {"name": "legacy-squad", "artifacts": []}
        ]
    },
    "2": {
        "title": "E-Commerce & Retail Modernization",
        "description": "Target: Retail clients, E-commerce, Inventory, POS",
        "squads": [
            {"name": "pos-system", "artifacts": ["hardware_interface_protocols.md", "offline_first_sync.md", "receipt_printer_driver", "local_inventory_cache", "end_of_day_reconciliation.yml"]},
            {"name": "storefront-nextjs", "artifacts": ["nextjs_performance_budgets.md", "seo_core_web_vitals.md", "shopify_graphql_optimizer", "vercel_production_deployment.yml"]}
        ]
    },
    "3": {
        "title": "Fintech & Banking Compliance",
        "description": "Target: Banking infra, strict PCI-DSS, zero-trust data",
        "squads": [
            {"name": "fintech-core", "artifacts": ["pci_dss_compliance.md", "zero_trust_architecture.md", "transaction_ledger_auditor", "encryption_key_rotation", "daily_compliance_audit.yml", "fraud_detection_pipeline.yml"]},
            {"name": "risk-analysis", "artifacts": ["data_anonymization_standards.md", "python_pandas_guidelines.md", "anomaly_detection_ml", "nightly_risk_model_training.yml"]}
        ]
    },
    "4": {
        "title": "Healthcare & HIPAA Systems",
        "description": "Target: Hospital IT, EHR integrations, patient privacy",
        "squads": [
            {"name": "ehr-integration", "artifacts": ["hipaa_data_handling.md", "hl7_fhir_standards.md", "epic_api_connector", "patient_record_anonymizer", "nightly_data_lake_sync.yml"]},
            {"name": "patient-portal", "artifacts": ["web_accessibility_wcag.md", "secure_session_management.md", "secure_document_viewer", "frontend_vulnerability_scan.yml"]}
        ]
    },
    "5": {
        "title": "Industrial & Manufacturing IoT",
        "description": "Target: Assembly lines, SCADA, Predictive Maintenance",
        "squads": [
            {"name": "scada-telemetry", "artifacts": ["iot_telemetry_standards.md", "zero_trust_flow_sensors.md", "predictive_maintenance.yml"]},
            {"name": "assembly-robotics", "artifacts": ["cobol_maintenance_guide.md", "shift_scheduling_guidelines.md", "payroll_compliance.md"]}
        ]
    }
}


def generate_dummy_dna() -> str:
    """Generates a transient local git repo in a secure temp dir loaded with all required demo artifacts.

    Returns:
        str: Absolute path to the temporary dummy DNA directory.
    """
    dummy_path = tempfile.mkdtemp(prefix="sprawl_dummy_dna_")

    # Create category directories
    for cat in CATEGORIES:
        os.makedirs(os.path.join(dummy_path, cat))

    # Create empty files for all known artifacts across all demos
    for demo in DEMOS.values():
        for squad in demo["squads"]:
            for item in squad["artifacts"]:
                if item.endswith(".md"):
                    cat = "rules"
                elif item.endswith(".yml") or item.endswith(".yaml"):
                    cat = "workflows"
                else:
                    cat = "skills"

                filepath = os.path.join(dummy_path, cat, item)
                with open(filepath, "w") as f:
                    f.write("# Dummy Content\n")

    # Initialize git
    try:
        subprocess.run(["git", "init", "-q"], cwd=dummy_path, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=dummy_path, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=dummy_path, check=True)
        subprocess.run(["git", "add", "."], cwd=dummy_path, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "init dummy"], cwd=dummy_path, check=True)
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to initialize dummy git repo: {e}")

    return dummy_path


def _provision_squad_workspace(
    demo_dir: str,
    squad_name: str,
    artifacts: list[str],
) -> None:
    """Provisions a single squad workspace without mutating global CWD.

    All filesystem operations use explicit absolute paths derived from
    `demo_dir` and `squad_name`.

    Args:
        demo_dir: Absolute path to the demo isolation directory.
        squad_name: Name of the squad workspace subdirectory.
        artifacts: List of artifact names to inject.
    """
    squad_path = os.path.join(demo_dir, squad_name)

    # Remove existing squad directory if present
    if os.path.exists(squad_path):
        shutil.rmtree(squad_path)

    # Create workspace using explicit path — cmd_create uses target path directly
    cmd_create(squad_name, path=demo_dir)

    if artifacts:
        # cmd_add needs to know the workspace root — pass it explicitly
        cmd_add(artifacts, target_dir=squad_path)
    else:
        cmd_sync(squad_path)

    # Display resulting agent tree
    console.print(f"\n[info][Resulting DNA for {squad_name}]:[/info]")
    agents_dir = os.path.join(squad_path, ".agents")
    if os.path.exists(agents_dir):
        for root, dirs, files in os.walk(agents_dir):
            # Prune hidden/binary dirs
            dirs[:] = [d for d in dirs if d not in (".venv", "__pycache__", ".git")]
            for f in sorted(files):
                rel_dir = os.path.relpath(root, agents_dir)
                rel_path = f if rel_dir == "." else os.path.join(rel_dir, f)
                console.print(f"  [info]{rel_path}[/info]")
    else:
        console.print("  [dim](no .agents directory found)[/dim]")


def run_interactive_demo(selected_key: str | None = None) -> None:
    """Runs the interactive demo engine in a fully isolated temp context.

    Args:
        selected_key: Optional pre-selected demo key. If None, prompts the user.
    """
    if not selected_key:
        console.print("\n[accent]================================================================[/accent]")
        console.print("[accent]  SPRAWL NATIVE DEMONSTRATION ENGINE[/accent]")
        console.print("[accent]================================================================[/accent]")
        console.print("[info]Select an industry scenario to simulate an automated agentic rollout:[/info]\n")

        for key, demo in DEMOS.items():
            console.print(f"[accent]  [{key}][/accent] [info]{demo['title']}[/info]")
            console.print(f"      [info]{demo['description']}[/info]\n")

        console.print("  [info][q] Quit[/info]")
        console.print("[accent]================================================================[/accent]")

        try:
            selected_key = input("Enter your choice: ").strip()
        except EOFError:
            # Handle non-interactive environments gracefully
            return

    if selected_key.lower() == 'q':
        return

    demo = DEMOS.get(selected_key)
    if not demo:
        print_error("Invalid selection.")
        return

    # Enforce test mode globally to isolate the demo from real paths
    os.environ["SPRAWL_TEST_MODE"] = "1"
    config.reinitialize()  # Re-evaluate paths based on updated environment

    print_status(f"Starting Demo: {demo['title']}")

    # Clean previous test environment
    print_status("Ensuring clean test environment...")
    try:
        cmd_clean_test()
    except Exception as e:  # nosec B110 - best-effort cleanup
        print_status(f"Warning: could not reset test environment: {e}")

    print_status("Generating Transient Dummy DNA...")
    dummy_dna_url = "file://" + generate_dummy_dna()

    print_status("Initializing Central Hub...")
    cmd_init(dummy_dna_url, target_dir=config.sprawl_dir)

    # Create a dedicated isolated demo directory inside a tempfile context
    # This avoids polluting the user's working directory
    with tempfile.TemporaryDirectory(prefix="sprawl_demo_") as demo_dir:
        print_status(f"Isolating demo workspaces in {demo_dir}...")

        # Process each squad inside the isolated context
        for i, squad in enumerate(demo["squads"], 1):
            squad_name = squad["name"]
            console.print(f"\n[accent]=========================================[/accent]")
            console.print(f"[accent]   TEAM {i}: {squad_name.upper()}[/accent]")
            console.print("[accent]=========================================[/accent]")

            try:
                _provision_squad_workspace(demo_dir, squad_name, squad["artifacts"])
            except Exception as e:  # nosec B110 - best-effort demo, log and continue
                print_error(f"Squad '{squad_name}' provisioning failed: {e}")

        console.print(f"\n[accent]=========================================[/accent]")
        console.print("[accent]   DEMO COMPLETE                        [/accent]")
        console.print("[accent]=========================================[/accent]")
        console.print("[info]The isolated environments have been successfully scaffolded.[/info]")
        console.print("[info]Demo artifacts are automatically cleaned up on exit.[/info]\n")
