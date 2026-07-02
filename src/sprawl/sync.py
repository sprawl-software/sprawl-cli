import os
import shutil
import filecmp
import subprocess
import sys

from .config import config
from .output import print_status, print_warning, print_error
from .utils import CATEGORIES
from .exceptions import SprawlError

def parse_sprawl_manifest(file_path: str) -> dict[str, list[str]]:
    """
    Core Schema Evaluation: Dynamically parses a given `.agents/sprawl_manifest.yml` identifying listed dependencies.
    """
    required_files = {cat: [] for cat in CATEGORIES}

    if not os.path.exists(file_path):
        return required_files

    with open(file_path, "r") as f:
        content = f.read()

    from .validation import parse_yaml_frontmatter
    # Wrap in --- to use the frontmatter parser for basic YAML list parsing
    manifest_data = parse_yaml_frontmatter(f"---\n{content}\n---")

    for category in CATEGORIES:
        items = manifest_data.get(category, [])
        if isinstance(items, list):
            sanitized_items = []
            for item in items:
                if isinstance(item, str):
                    stripped = item.strip()
                    if stripped.lower() == "none":
                        continue
                    if ".." in stripped or "/" in stripped or "\\" in stripped:
                        raise SprawlError(f"Security Violation: Path traversal detected in '{stripped}'. Execution aborted.")
                    sanitized_items.append(stripped)
            required_files[category] = sanitized_items

    return required_files


def _sync_app_directory_impl(app_dir: str, local_agents_dir: str, manifest_path: str) -> dict:
    """
    File Orchestration Protocol:
    Injects and mirrors DNA logic from the remote global vault deep into the local working space context.
    """
    if not os.path.exists(manifest_path):
        print_warning(f"No sprawl_manifest.yml found in {local_agents_dir}. Skipping.")
        return {"copied": 0, "pruned": 0, "venv_provisioned": False}

    print_status(f"Syncing {app_dir}...")

    from .workspace import Workspace
    workspace = Workspace(app_dir)
    
    reqs = parse_sprawl_manifest(manifest_path)
        
    from .utils import get_active_dna_context
    source_dna_dir = get_active_dna_context(app_dir)
    
    if config.verbose:
        print_status(f"Resolved workspace DNA context: {source_dna_dir}")

    global_design = os.path.join(source_dna_dir, "DESIGN.md")
    local_design = os.path.join(app_dir, "design.md")
    if os.path.exists(global_design) and not config.dry_run:
        if not os.path.exists(local_design):
            shutil.copy2(global_design, local_design)
            if config.verbose:
                print_status(f"Synced global DESIGN.md -> {local_design}")
        else:
            print_status("[DNA Sync] Preserved local design.md override.")

    copied_files = []
    pruned_count = 0

    for cat in CATEGORIES:
        if not config.dry_run:
            os.makedirs(os.path.join(local_agents_dir, cat), exist_ok=True)

    for category, files in reqs.items():
        if files:
            category_dir = os.path.join(local_agents_dir, category)
            if not config.dry_run:
                os.makedirs(category_dir, exist_ok=True)

            for file_name in files:
                src_path = os.path.join(source_dna_dir, category, file_name)
                dest_path = os.path.join(category_dir, file_name)

                if os.path.exists(src_path):
                    if not config.dry_run:
                        try:
                            if os.path.isdir(src_path):
                                if os.path.exists(dest_path):
                                    shutil.rmtree(dest_path)
                                shutil.copytree(src_path, dest_path, dirs_exist_ok=True)
                                copied_files.append((category, file_name))
                                if config.verbose: print_status(f"[Synced] {file_name} -> {category_dir}/")
                            else:
                                if os.path.exists(dest_path) and filecmp.cmp(src_path, dest_path, shallow=False):
                                    copied_files.append((category, file_name))
                                    if config.verbose: print_status(f"[Skipped] {file_name} is already identical.")
                                else:
                                    shutil.copy2(src_path, dest_path)
                                    copied_files.append((category, file_name))
                                    if config.verbose: print_status(f"[Synced] {file_name} -> {category_dir}/")
                        except Exception as e:
                            print_error(f"Failed to copy {file_name}: {e}")
                    else:
                        print_status(f"[Would sync] {file_name} -> {category_dir}/")
                        copied_files.append((category, file_name))
                else:
                    print_warning(f"Required file/dir {file_name} not found in {os.path.join(source_dna_dir, category)}/")

    # Pruning Engine: Remove local artifacts no longer listed in the manifest
    if not config.dry_run:
        for category in CATEGORIES:
            category_dir = os.path.join(local_agents_dir, category)
            if os.path.exists(category_dir):
                allowed_items = reqs.get(category, [])
                for existing_item in os.listdir(category_dir):
                    if existing_item not in allowed_items:
                        item_path = os.path.join(category_dir, existing_item)
                        try:
                            if os.path.isdir(item_path):
                                shutil.rmtree(item_path)
                            else:
                                os.remove(item_path)
                            pruned_count += 1
                            print_status(f"[Pruned] {existing_item} removed from local {category}/")
                        except Exception as e:
                            print_error(f"Failed to prune {existing_item}: {e}")
    
    venv_dir = os.path.join(local_agents_dir, ".venv")
    venv_pip = os.path.join(venv_dir, "bin", "pip")
    venv_python = os.path.join(venv_dir, "bin", "python3")
    
    provisioned_venv = False
    if not config.dry_run:
        if not os.path.exists(venv_dir):
            print_status(f"Provisioning sandboxed virtual environment at {venv_dir}...")
            subprocess.run([sys.executable, "-m", "venv", venv_dir], check=True)
            provisioned_venv = True

        valid_skills = [f[1] for f in copied_files if f[0] == "skills"]
        for skill in valid_skills:
            skill_dir = os.path.join(local_agents_dir, "skills", skill)
            if not os.path.exists(skill_dir):
                continue
            for root, dirs, files in os.walk(skill_dir):
                if "requirements.txt" in files:
                    req_file = os.path.join(root, "requirements.txt")
                    print_status(f"Installing Python dependencies from {os.path.relpath(req_file, app_dir)}...")
                    subprocess.run([venv_pip, "install", "-r", req_file, "--quiet"], check=True)
                
                if "package.json" in files:
                    npm_path = shutil.which("npm")
                    if npm_path:
                        print_status(f"Installing Node dependencies in {os.path.relpath(root, app_dir)}...")
                        subprocess.run([npm_path, "install", "--silent"], cwd=root, check=True)
                    else:
                        print_warning(f"npm not found. Skipping Node dependencies in {root}")

                if "Cargo.toml" in files:
                    cargo_path = shutil.which("cargo")
                    if cargo_path:
                        print_status(f"Fetching Rust dependencies in {os.path.relpath(root, app_dir)}...")
                        subprocess.run([cargo_path, "fetch", "--quiet"], cwd=root, check=True)
                    else:
                        print_warning(f"cargo not found. Skipping Rust dependencies in {root}")

    agents_md_path = os.path.join(app_dir, "agent.md")
    if config.verbose and config.dry_run:
        print_status(f"DRY RUN: Would generate agent.md registry mapping.")
    elif not config.dry_run:
        persona_content = None
        for skill in reqs.get("skills", []):
            if skill.startswith("persona-"):
                persona_path = os.path.join(source_dna_dir, "skills", skill, "SKILL.md")
                if os.path.exists(persona_path):
                    try:
                        with open(persona_path, "r") as pf:
                            persona_content = pf.read()
                        break
                    except Exception as e:
                        print_warning(f"Failed to read persona file {persona_path}: {e}")

        from .generators.agents_md import generate_agents_md
        generate_agents_md(agents_md_path, reqs, app_dir, persona_content)

        if config.verbose:
            print_status(f"Generated standardized registry payload at {agents_md_path}")

    # Generate MCP Configuration
    mcp_config_path = os.path.join(app_dir, "mcp_config.json")
    if config.verbose and config.dry_run:
        print_status(f"DRY RUN: Would generate mcp_config.json registry.")
    elif not config.dry_run:
        from .generators.mcp_config import generate_mcp_config
        generate_mcp_config(
            mcp_config_path, 
            reqs, 
            app_dir, 
            local_agents_dir, 
            venv_python,
            config.vault_path
        )
        # Double-check JSON structure validity
        try:
            import json
            with open(mcp_config_path, "r") as f:
                json.loads(f.read())
        except Exception as e:
            raise SprawlError(f"Generated mcp_config.json is not valid JSON: {e}")

        if config.verbose:
            print_status(f"Generated Claude Desktop standard MCP configuration at {mcp_config_path}")

    return {
        "copied": len(copied_files),
        "pruned": pruned_count,
        "venv_provisioned": provisioned_venv
    }


def sync_app_directory(app_dir: str) -> dict:
    """
    File Orchestration Protocol:
    Injects and mirrors DNA logic from the remote global vault deep into the local working space context.
    """
    local_agents_dir = os.path.join(app_dir, ".agents")
    if not os.path.exists(local_agents_dir) and not config.dry_run:
        os.makedirs(local_agents_dir)

    manifest_path = os.path.join(local_agents_dir, "sprawl_manifest.yml")
    legacy_manifest = os.path.join(app_dir, "sprawl_package.md")

    if not os.path.exists(manifest_path) and os.path.exists(legacy_manifest):
        if not config.dry_run:
            shutil.move(legacy_manifest, manifest_path)
            print_status(f"Migrated legacy manifest sprawl_package.md -> .agents/sprawl_manifest.yml")

    if not os.path.exists(manifest_path):
        print_warning(f"No sprawl_manifest.yml found in {local_agents_dir}. Skipping.")
        return {"copied": 0, "pruned": 0, "venv_provisioned": False}

    backup_dir = None
    if os.path.exists(local_agents_dir) and not config.dry_run:
        import tempfile
        backup_dir = tempfile.mkdtemp(prefix="sprawl_sync_backup_")
        backup_agents_path = os.path.join(backup_dir, ".agents")
        shutil.copytree(local_agents_dir, backup_agents_path, symlinks=True)

    try:
        # Verify sprawl-config.json JSON validity if it exists
        sprawl_config_path = os.path.join(local_agents_dir, "sprawl-config.json")
        try:
            with open(sprawl_config_path, "r") as f:
                content = f.read().strip()
                if content:
                    import json
                    json.loads(content)
        except FileNotFoundError:
            pass
        except Exception as e:
            raise SprawlError(f"sprawl-config.json is not valid JSON: {e}")

        result = _sync_app_directory_impl(app_dir, local_agents_dir, manifest_path)
        
        # Clean up root pollution: delete stray folders if they exist at the workspace root
        if not config.dry_run:
            stray_categories = ["atoms", "molecules", "rules", "skills", "workflows"]
            for cat in stray_categories:
                stray_root_path = os.path.join(app_dir, cat)
                try:
                    if os.path.isdir(stray_root_path) and not os.path.islink(stray_root_path):
                        shutil.rmtree(stray_root_path)
                    else:
                        os.remove(stray_root_path)
                    if config.verbose:
                        print_status(f"Cleaned up stray root directory: {cat}")
                except FileNotFoundError:
                    pass

            # Clean up deprecated categories in .agents/
            deprecated_categories = ["atoms", "molecules"]
            for cat in deprecated_categories:
                dep_path = os.path.join(local_agents_dir, cat)
                try:
                    if os.path.isdir(dep_path):
                        shutil.rmtree(dep_path)
                    else:
                        os.remove(dep_path)
                    if config.verbose:
                        print_status(f"Cleaned up deprecated category in .agents: {cat}")
                except FileNotFoundError:
                    pass

        # Update sync state in management plane
        from .workspace import Workspace, WorkspaceRegistry
        workspace = Workspace(app_dir)
        workspace.update_sync_state({"last_manifest_sync": True})
        WorkspaceRegistry.update_sync_timestamp(workspace.path)
        
        if backup_dir and not config.dry_run:
            shutil.rmtree(backup_dir, ignore_errors=True)
            
        return result

    except Exception as e:
        if backup_dir and not config.dry_run:
            print_warning("Sync failed. Rolling back .agents/ to previous state...")
            if os.path.exists(local_agents_dir):
                shutil.rmtree(local_agents_dir)
            shutil.copytree(os.path.join(backup_dir, ".agents"), local_agents_dir, symlinks=True)
            shutil.rmtree(backup_dir, ignore_errors=True)
        raise SprawlError(f"Synchronization failed and was rolled back: {str(e)}")
