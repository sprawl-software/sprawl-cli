import filecmp
import json
import os
import shutil
import subprocess
from typing import Any

from .config import config
from .exceptions import SprawlError
from .generators.agents_md import generate_agents_md
from .generators.mcp_config import generate_mcp_config
from .output import print_error, print_status, print_warning
from .utils import CATEGORIES, get_host_python_executable, get_venv_executable


def _provision_workspace_venv(venv_dir: str) -> bool:
    """Provisions a workspace virtual environment using the host Python interpreter."""
    if os.path.exists(venv_dir):
        return False
    host_python = get_host_python_executable()
    if not host_python:
        print_warning(
            "Host Python interpreter not found on PATH; skipping .agents/.venv provisioning."
        )
        return False
    print_status(f"Provisioning sandboxed virtual environment at {venv_dir}...")
    subprocess.run([host_python, "-m", "venv", venv_dir], check=True, timeout=120)
    return True


def _sanitize_manifest_items(raw_items: Any) -> list[str]:
    """Sanitizes a YAML manifest item list and blocks path traversal sequences."""
    if not isinstance(raw_items, list):
        return []
    sanitized: list[str] = []
    for item in raw_items:
        if not isinstance(item, str):
            continue
        stripped = item.strip()
        if stripped.lower() == "none":
            continue
        if ".." in stripped or "/" in stripped or "\\" in stripped:
            raise SprawlError(
                f"Security Violation: Path traversal detected in '{stripped}'. Execution aborted."
            )
        sanitized.append(stripped)
    return sanitized


def parse_sprawl_manifest(file_path: str) -> dict[str, list[str]]:
    """Dynamically parses `.agents/sprawl_manifest.yml` identifying listed dependencies."""
    required_files: dict[str, list[str]] = {cat: [] for cat in CATEGORIES}
    for cat in CATEGORIES:
        required_files[f"local_{cat}"] = []

    if not os.path.exists(file_path):
        return required_files

    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    from .validation import parse_yaml_frontmatter

    manifest_data = parse_yaml_frontmatter(f"---\n{content}\n---")
    for category in CATEGORIES:
        required_files[category] = _sanitize_manifest_items(manifest_data.get(category, []))
        local_key = f"local_{category}"
        required_files[local_key] = _sanitize_manifest_items(manifest_data.get(local_key, []))

    return required_files


def _sync_design_md(app_dir: str, source_dna_dir: str) -> None:
    """Prunes deprecated lowercase design.md and syncs global DESIGN.md if not overridden."""
    if config.dry_run:
        return
    old_design_path = os.path.join(app_dir, "design.md")
    if os.path.exists(old_design_path):
        try:
            os.remove(old_design_path)
            if config.verbose:
                print_status("Pruned deprecated workspace-root file: design.md")
        except OSError as e:
            if config.verbose:
                print_status(f"Error removing deprecated design.md: {e}")

    global_design = os.path.join(source_dna_dir, "DESIGN.md")
    local_design = os.path.join(app_dir, "DESIGN.md")
    if not os.path.exists(global_design):
        return
    if not os.path.exists(local_design):
        shutil.copy2(global_design, local_design)
        if config.verbose:
            print_status(f"Synced global DESIGN.md -> {local_design}")
    else:
        print_status("[DNA Sync] Preserved local DESIGN.md override.")


def _copy_single_artifact(
    src_path: str,
    dest_path: str,
    category_dir: str,
    file_name: str,
) -> bool:
    """Copies a single file or directory artifact into category_dir."""
    if config.dry_run:
        print_status(f"[Would sync] {file_name} -> {category_dir}/")
        return True
    try:
        if os.path.isdir(src_path):
            if os.path.exists(dest_path):
                shutil.rmtree(dest_path)
            shutil.copytree(src_path, dest_path, dirs_exist_ok=True)
            if config.verbose:
                print_status(f"[Synced] {file_name} -> {category_dir}/")
            return True

        if os.path.exists(dest_path) and filecmp.cmp(src_path, dest_path, shallow=False):
            if config.verbose:
                print_status(f"[Skipped] {file_name} is already identical.")
            return True

        shutil.copy2(src_path, dest_path)
        if config.verbose:
            print_status(f"[Synced] {file_name} -> {category_dir}/")
        return True
    except OSError as e:
        print_error(f"Failed to copy {file_name}: {e}")
        return False


def _sync_single_category(
    category: str,
    files: list[str],
    source_dna_dir: str,
    local_agents_dir: str,
) -> list[tuple[str, str]]:
    """Syncs requested files for a single category into local_agents_dir."""
    category_dir = os.path.join(local_agents_dir, category)
    if not config.dry_run:
        os.makedirs(category_dir, exist_ok=True)

    synced: list[tuple[str, str]] = []
    for file_name in files:
        src_path = os.path.join(source_dna_dir, category, file_name)
        dest_path = os.path.join(category_dir, file_name)
        if not os.path.exists(src_path):
            print_warning(
                f"Required file/dir {file_name} not found in {os.path.join(source_dna_dir, category)}/"
            )
            continue
        if _copy_single_artifact(src_path, dest_path, category_dir, file_name):
            synced.append((category, file_name))
    return synced


def _sync_category_artifacts(
    reqs: dict[str, list[str]],
    source_dna_dir: str,
    local_agents_dir: str,
) -> list[tuple[str, str]]:
    """Syncs all manifest-requested category artifacts from source_dna_dir into local_agents_dir."""
    copied_files: list[tuple[str, str]] = []
    if not config.dry_run:
        for cat in CATEGORIES:
            os.makedirs(os.path.join(local_agents_dir, cat), exist_ok=True)

    for category, files in reqs.items():
        if category in CATEGORIES and files:
            copied_files.extend(
                _sync_single_category(category, files, source_dna_dir, local_agents_dir)
            )
    return copied_files


def _prune_category_dir(category: str, category_dir: str, allowed_items: set[str]) -> int:
    """Removes unlisted files or directories inside a single category directory."""
    if not os.path.exists(category_dir):
        return 0
    pruned = 0
    for existing_item in os.listdir(category_dir):
        if existing_item in allowed_items:
            continue
        item_path = os.path.join(category_dir, existing_item)
        try:
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)
            else:
                os.remove(item_path)
            pruned += 1
            print_status(f"[Pruned] {existing_item} removed from local {category}/")
        except OSError as e:
            print_error(f"Failed to prune {existing_item}: {e}")
    return pruned


def _prune_unlisted_artifacts(reqs: dict[str, list[str]], local_agents_dir: str) -> int:
    """Removes local artifacts no longer listed in the manifest."""
    if config.dry_run:
        return 0
    pruned_count = 0
    for category in CATEGORIES:
        category_dir = os.path.join(local_agents_dir, category)
        allowed = set(reqs.get(category, []) + reqs.get(f"local_{category}", []))
        pruned_count += _prune_category_dir(category, category_dir, allowed)
    return pruned_count


def _install_skill_directory_deps(
    root: str,
    files: list[str],
    app_dir: str,
    venv_pip: str,
) -> None:
    """Installs Python, Node, or Rust dependencies discovered inside a synced skill folder."""
    if "requirements.txt" in files:
        req_file = os.path.join(root, "requirements.txt")
        print_status(f"Installing Python dependencies from {os.path.relpath(req_file, app_dir)}...")
        subprocess.run([venv_pip, "install", "-r", req_file, "--quiet"], check=True, timeout=180)

    if "package.json" in files:
        npm_path = shutil.which("npm")
        if npm_path:
            print_status(f"Installing Node dependencies in {os.path.relpath(root, app_dir)}...")
            npm_subcmd = (
                "ci"
                if ("package-lock.json" in files or "npm-shrinkwrap.json" in files)
                else "install"
            )
            subprocess.run([npm_path, npm_subcmd, "--silent"], cwd=root, check=True, timeout=180)
        else:
            print_warning(f"npm not found. Skipping Node dependencies in {root}")

    if "Cargo.toml" in files:
        cargo_path = shutil.which("cargo")
        if cargo_path:
            print_status(f"Fetching Rust dependencies in {os.path.relpath(root, app_dir)}...")
            subprocess.run([cargo_path, "fetch", "--quiet"], cwd=root, check=True, timeout=180)
        else:
            print_warning(f"cargo not found. Skipping Rust dependencies in {root}")


def _provision_and_install_skill_deps(
    app_dir: str,
    local_agents_dir: str,
    copied_files: list[tuple[str, str]],
) -> tuple[bool, str]:
    """Provisions .agents/.venv and installs runtime dependencies for synced skills."""
    venv_dir = os.path.join(local_agents_dir, ".venv")
    venv_pip = get_venv_executable(venv_dir, "pip")
    venv_python = get_venv_executable(venv_dir, "python3")

    if config.dry_run:
        return False, venv_python

    provisioned_venv = _provision_workspace_venv(venv_dir)
    valid_skills = [f[1] for f in copied_files if f[0] == "skills"]
    for skill in valid_skills:
        skill_dir = os.path.join(local_agents_dir, "skills", skill)
        if not os.path.exists(skill_dir):
            continue
        for root, _dirs, files in os.walk(skill_dir):
            _install_skill_directory_deps(root, files, app_dir, venv_pip)

    return provisioned_venv, venv_python


def _cleanup_obsolete_root_files(app_dir: str) -> None:
    """Removes deprecated agent.md / AGENT.md files at the workspace root."""
    if config.dry_run:
        return
    for old_file in ("agent.md", "AGENT.md"):
        old_path = os.path.join(app_dir, old_file)
        if not os.path.exists(old_path):
            continue
        try:
            os.remove(old_path)
            if config.verbose:
                print_status(f"Pruned deprecated workspace-root file: {old_file}")
        except OSError as e:
            if config.verbose:
                print_status(f"Error removing deprecated workspace-root file {old_file}: {e}")


def _load_allowed_mounts(local_agents_dir: str) -> dict[str, Any]:
    """Loads allowed_mounts from .agents/sprawl-config.json if present."""
    config_path = os.path.join(local_agents_dir, "sprawl-config.json")
    if not os.path.exists(config_path):
        return {}
    try:
        with open(config_path, encoding="utf-8") as f:
            cfg = json.load(f)
            mounts = cfg.get("allowed_mounts", {})
            return mounts if isinstance(mounts, dict) else {}
    except (json.JSONDecodeError, OSError) as e:
        if config.verbose:
            print_status(f"Error loading sprawl-config.json: {e}")
        return {}


def _read_active_persona_content(
    reqs: dict[str, list[str]],
    source_dna_dir: str,
) -> str | None:
    """Reads the first persona-* SKILL.md referenced in reqs['skills']."""
    for skill in reqs.get("skills", []):
        if not skill.startswith("persona-"):
            continue
        persona_path = os.path.join(source_dna_dir, "skills", skill, "SKILL.md")
        if not os.path.exists(persona_path):
            continue
        try:
            with open(persona_path, encoding="utf-8") as pf:
                return pf.read()
        except OSError as e:
            print_warning(f"Failed to read persona file {persona_path}: {e}")
    return None


def _generate_workspace_manifests(
    app_dir: str,
    local_agents_dir: str,
    source_dna_dir: str,
    reqs: dict[str, list[str]],
    venv_python: str,
) -> None:
    """Generates AGENTS.md and mcp_config.json for the target workspace."""
    allowed_mounts = _load_allowed_mounts(local_agents_dir)
    agents_md_path = os.path.join(app_dir, "AGENTS.md")
    mcp_config_path = os.path.join(app_dir, "mcp_config.json")

    if config.dry_run:
        if config.verbose:
            print_status("DRY RUN: Would generate AGENTS.md registry mapping.")
            print_status("DRY RUN: Would generate mcp_config.json registry.")
        return

    persona_content = _read_active_persona_content(reqs, source_dna_dir)
    generate_agents_md(
        agents_md_path, reqs, app_dir, persona_content, allowed_mounts=allowed_mounts
    )
    if config.verbose:
        print_status(f"Generated standardized registry payload at {agents_md_path}")

    generate_mcp_config(
        mcp_config_path,
        reqs,
        app_dir,
        local_agents_dir,
        venv_python,
        config.vault_path,
        allowed_mounts=allowed_mounts,
    )
    try:
        with open(mcp_config_path, encoding="utf-8") as f:
            json.loads(f.read())
    except (json.JSONDecodeError, OSError) as e:
        raise SprawlError(f"Generated mcp_config.json is not valid JSON: {e}") from e

    if config.verbose:
        print_status(f"Generated Claude Desktop standard MCP configuration at {mcp_config_path}")


def _sync_app_directory_impl(
    app_dir: str,
    local_agents_dir: str,
    manifest_path: str,
) -> dict[str, Any]:
    """Injects and mirrors DNA logic from the global vault into the local workspace context."""
    if not os.path.exists(manifest_path):
        print_warning(f"No sprawl_manifest.yml found in {local_agents_dir}. Skipping.")
        return {"copied": 0, "pruned": 0, "venv_provisioned": False}

    print_status(f"Syncing {app_dir}...")
    from .utils import get_active_dna_context
    from .workspace import Workspace

    Workspace(app_dir)
    reqs = parse_sprawl_manifest(manifest_path)
    source_dna_dir = get_active_dna_context(app_dir)

    if config.verbose:
        print_status(f"Resolved workspace DNA context: {source_dna_dir}")

    _sync_design_md(app_dir, source_dna_dir)
    copied_files = _sync_category_artifacts(reqs, source_dna_dir, local_agents_dir)
    pruned_count = _prune_unlisted_artifacts(reqs, local_agents_dir)
    provisioned_venv, venv_python = _provision_and_install_skill_deps(
        app_dir, local_agents_dir, copied_files
    )
    _cleanup_obsolete_root_files(app_dir)
    _generate_workspace_manifests(app_dir, local_agents_dir, source_dna_dir, reqs, venv_python)

    return {
        "copied": len(copied_files),
        "pruned": pruned_count,
        "venv_provisioned": provisioned_venv,
    }


def _create_sync_backup(app_dir: str, local_agents_dir: str) -> str | None:
    """Creates a rollback snapshot of .agents/ in the workspace management plane."""
    if not os.path.exists(local_agents_dir) or config.dry_run:
        return None
    mgt_dir = config.get_workspace_mgt_dir(app_dir)
    os.makedirs(mgt_dir, exist_ok=True)
    backup_dir = os.path.join(mgt_dir, "_sync_backup")
    if os.path.exists(backup_dir):
        shutil.rmtree(backup_dir)
    os.makedirs(backup_dir, exist_ok=True)
    shutil.copytree(local_agents_dir, os.path.join(backup_dir, ".agents"), symlinks=True)
    return backup_dir


def _validate_sprawl_config_json(local_agents_dir: str) -> None:
    """Verifies that .agents/sprawl-config.json contains valid JSON if present."""
    sprawl_config_path = os.path.join(local_agents_dir, "sprawl-config.json")
    try:
        with open(sprawl_config_path, encoding="utf-8") as f:
            content = f.read().strip()
            if content:
                json.loads(content)
    except FileNotFoundError:
        return
    except (json.JSONDecodeError, OSError) as e:
        raise SprawlError(f"sprawl-config.json is not valid JSON: {e}") from e


def _remove_path_entry(target_path: str, preserve_symlink_Target: bool = True) -> bool:
    """Removes a directory or file at target_path if it exists."""
    try:
        if os.path.isdir(target_path) and (
            not preserve_symlink_Target or not os.path.islink(target_path)
        ):
            shutil.rmtree(target_path)
        else:
            os.remove(target_path)
        return True
    except FileNotFoundError:
        return False


def _cleanup_stray_and_deprecated_categories(app_dir: str, local_agents_dir: str) -> None:
    """Cleans up stray root category folders and deprecated atoms/molecules in .agents/."""
    if config.dry_run:
        return
    for cat in ("atoms", "molecules", "rules", "skills", "workflows"):
        stray_root_path = os.path.join(app_dir, cat)
        if _remove_path_entry(stray_root_path, preserve_symlink_Target=True) and config.verbose:
            print_status(f"Cleaned up stray root directory: {cat}")

    for cat in ("atoms", "molecules"):
        dep_path = os.path.join(local_agents_dir, cat)
        if _remove_path_entry(dep_path, preserve_symlink_Target=False) and config.verbose:
            print_status(f"Cleaned up deprecated category in .agents: {cat}")


def _rollback_sync_backup(backup_dir: str | None, local_agents_dir: str) -> None:
    """Restores .agents/ from backup_dir after a failed sync operation."""
    if not backup_dir or config.dry_run:
        return
    print_warning("Sync failed. Rolling back .agents/ to previous state...")
    if os.path.exists(local_agents_dir):
        shutil.rmtree(local_agents_dir)
    shutil.copytree(os.path.join(backup_dir, ".agents"), local_agents_dir, symlinks=True)
    shutil.rmtree(backup_dir, ignore_errors=True)


def sync_app_directory(app_dir: str) -> dict[str, Any]:
    """Injects and mirrors DNA logic from the global vault into the local workspace context."""
    local_agents_dir = os.path.join(app_dir, ".agents")
    if not os.path.exists(local_agents_dir) and not config.dry_run:
        os.makedirs(local_agents_dir)

    manifest_path = os.path.join(local_agents_dir, "sprawl_manifest.yml")
    legacy_manifest = os.path.join(app_dir, "sprawl_package.md")

    if not os.path.exists(manifest_path) and os.path.exists(legacy_manifest) and not config.dry_run:
        shutil.move(legacy_manifest, manifest_path)
        print_status("Migrated legacy manifest sprawl_package.md -> .agents/sprawl_manifest.yml")

    if not os.path.exists(manifest_path):
        print_warning(f"No sprawl_manifest.yml found in {local_agents_dir}. Skipping.")
        return {"copied": 0, "pruned": 0, "venv_provisioned": False}

    backup_dir = _create_sync_backup(app_dir, local_agents_dir)

    try:
        _validate_sprawl_config_json(local_agents_dir)
        result = _sync_app_directory_impl(app_dir, local_agents_dir, manifest_path)
        _cleanup_stray_and_deprecated_categories(app_dir, local_agents_dir)

        from .workspace import Workspace, update_workspace_sync_timestamp

        workspace = Workspace(app_dir)
        workspace.update_sync_state({"last_manifest_sync": True})
        update_workspace_sync_timestamp(workspace.path)

        if backup_dir and not config.dry_run:
            shutil.rmtree(backup_dir, ignore_errors=True)

        return result
    except Exception as e:
        _rollback_sync_backup(backup_dir, local_agents_dir)
        raise SprawlError(f"Synchronization failed and was rolled back: {e}") from e
