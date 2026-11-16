import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import ANY, MagicMock, patch

# Ensure the local src is available
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from src.sprawl.config import config
from src.sprawl.core import cmd_create, cmd_graft, cmd_init, cmd_update
from src.sprawl.exceptions import SprawlError
from src.sprawl.sync import parse_sprawl_manifest, sync_app_directory
from src.sprawl.utils import CATEGORIES


class TestSprawlCLI(unittest.TestCase):
    def test_categories_constant(self):
        self.assertEqual(CATEGORIES, ["rules", "skills", "workflows"])

    def test_parse_sprawl_manifest(self):
        test_content = """# test app
dna: core

rules:
  - engineering.md

skills:
  - web_artifacts_builder

workflows:
  - execution.md
"""
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp_file:
            temp_file.write(test_content)
            temp_path = temp_file.name

        try:
            reqs = parse_sprawl_manifest(temp_path)
            self.assertIn("engineering.md", reqs["rules"])
            self.assertIn("web_artifacts_builder", reqs["skills"])
            self.assertIn("execution.md", reqs["workflows"])
        finally:
            os.remove(temp_path)

    def test_parse_sprawl_manifest_traversal(self):
        test_content = """# test app
dna: core

rules:
  - ../../.ssh/id_rsa
"""
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp_file:
            temp_file.write(test_content)
            temp_path = temp_file.name

        try:
            with self.assertRaises(SprawlError):
                parse_sprawl_manifest(temp_path)
        finally:
            os.remove(temp_path)

    @patch("src.sprawl.commands.workspace.register_workspace")
    def test_cmd_graft(self, mock_register):
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                os.chdir(temp_dir)
                app_name = os.path.basename(temp_dir)

                with open("requirements.txt", "w") as f:
                    f.write("requests==2.31.0")

                config.dry_run = False
                cmd_graft()

                sprawl_package_md_path = os.path.join(temp_dir, ".agents", "sprawl_manifest.yml")
                self.assertTrue(os.path.exists(sprawl_package_md_path))

                with open(sprawl_package_md_path) as f:
                    content = f.read()

                self.assertTrue(content.startswith(f"# {app_name}"))
                self.assertIn("rules:", content)
                self.assertIn("workflows:", content)
                self.assertIn("- python.md", content)

                self.assertEqual(mock_register.call_args[0][0], app_name)
                self.assertTrue(os.path.samefile(mock_register.call_args[0][1], temp_dir))

                with self.assertRaises(SprawlError):
                    cmd_graft()

            finally:
                os.chdir(original_cwd)

    @patch("src.sprawl.commands.workspace.register_workspace")
    def test_cmd_create(self, mock_register):
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                os.chdir(temp_dir)
                config.dry_run = False

                cmd_create("TestWorkspace")

                workspace_dir = os.path.abspath("TestWorkspace")
                self.assertTrue(os.path.exists(workspace_dir))
                self.assertTrue(
                    os.path.exists(os.path.join(workspace_dir, ".agents", "sprawl_manifest.yml"))
                )

                with self.assertRaises(SprawlError):
                    cmd_create("TestWorkspace")
            finally:
                os.chdir(original_cwd)

    @patch("src.sprawl.commands.workspace.get_all_workspaces")
    @patch("src.sprawl.commands.workspace.console.print")
    def test_cmd_ws_list(self, mock_print, mock_get_all):
        from src.sprawl.commands.workspace import cmd_ws_list

        mock_get_all.return_value = {
            "ws1": {"path": "/tmp/ws1", "dna_source": None, "last_sync_timestamp": None},
            "ws2": {
                "path": "/tmp/ws2",
                "dna_source": "custom",
                "last_sync_timestamp": "2024-01-01T00:00:00Z",
            },
        }
        cmd_ws_list()
        mock_print.assert_called_once()
        table = mock_print.call_args[0][0]
        from rich.table import Table

        self.assertIsInstance(table, Table)
        self.assertEqual(len(table.rows), 2)

    @patch("src.sprawl.commands.workspace.get_all_workspaces")
    @patch("src.sprawl.commands.workspace.print_status")
    def test_cmd_ws_list_empty(self, mock_print_status, mock_get_all):
        from src.sprawl.commands.workspace import cmd_ws_list

        mock_get_all.return_value = {}
        cmd_ws_list()
        mock_print_status.assert_called_with("No workspaces currently tracked in the registry.")

    def _run_ws_remove_scenario(self, ws_info, name: str, delete: bool = False):
        """Executes cmd_ws_remove under controlled registry/filesystem state."""
        from src.sprawl.commands.workspace import cmd_ws_remove

        deregistered: list[str] = []
        removed_dirs: list[str] = []
        with (
            patch("src.sprawl.commands.workspace.get_workspace_info", return_value=ws_info),
            patch(
                "src.sprawl.commands.workspace.deregister_workspace",
                side_effect=deregistered.append,
            ),
            patch("src.sprawl.commands.workspace.os.path.exists", return_value=True),
            patch(
                "src.sprawl.commands.workspace.shutil.rmtree",
                side_effect=removed_dirs.append,
            ),
        ):
            cmd_ws_remove(name, delete=delete)
        return deregistered, removed_dirs

    def test_cmd_ws_remove(self):
        dereg, rmtree = self._run_ws_remove_scenario(None, "missing")
        self.assertEqual(dereg, [])

        dereg, rmtree = self._run_ws_remove_scenario({"path": "/fake/path"}, "existing")
        self.assertEqual(dereg, ["existing"])
        self.assertEqual(rmtree, [])

        dereg, rmtree = self._run_ws_remove_scenario(
            {"path": "/fake/path"}, "existing_del", delete=True
        )
        self.assertEqual(dereg, ["existing_del"])
        self.assertEqual(rmtree, ["/fake/path"])

    def _run_ws_push_scenario(self, workspaces: dict, target_name: str | None = None) -> list[str]:
        """Executes cmd_ws_push and records synced target directories."""
        from src.sprawl.commands.workspace import cmd_ws_push

        synced_dirs: list[str] = []
        with (
            patch("src.sprawl.commands.workspace.get_all_workspaces", return_value=workspaces),
            patch("src.sprawl.commands.workspace.os.path.exists", return_value=True),
            patch(
                "src.sprawl.commands.sync_cmd.cmd_sync",
                side_effect=lambda target_dir=None: synced_dirs.append(target_dir),
            ),
        ):
            cmd_ws_push(target_name)
        return synced_dirs

    def test_cmd_ws_push(self):
        self.assertEqual(self._run_ws_push_scenario({}), [])

        ws_map = {"ws1": {"path": "/fake/ws1"}, "ws2": {"path": "/fake/ws2"}}
        self.assertEqual(self._run_ws_push_scenario(ws_map, "ws1"), ["/fake/ws1"])
        self.assertEqual(self._run_ws_push_scenario(ws_map), ["/fake/ws1", "/fake/ws2"])

        with self.assertRaises(SprawlError):
            self._run_ws_push_scenario(ws_map, "missing")

    def test_cmd_create_sanitization(self):
        invalid_names = ["../../../etc", "my/workspace", "workspace name", "workspace;rm-rf/"]
        for name in invalid_names:
            with self.assertRaises(SprawlError):
                cmd_create(name)

    @patch.dict(os.environ, {}, clear=True)
    def test_sprawl_test_command_gated_by_default(self):
        from src.sprawl.cli import get_parser

        parser = get_parser()
        with self.assertRaises(SystemExit):
            parser.parse_args(["test"])

    @patch.dict(os.environ, {"SPRAWL_DEV": "1"})
    def test_sprawl_test_command_allowed_in_dev(self):
        from src.sprawl.cli import get_parser

        parser = get_parser()
        args = parser.parse_args(["test"])
        self.assertEqual(args.command, "test")

    def _run_cmd_update_scenario(self, run_side_effect=None):
        """Runs cmd_update with controlled subprocess mocks."""
        config.dry_run = False
        with (
            patch("src.sprawl.config.config.agents_dir_global", "/fake/sprawl/core"),
            patch("src.sprawl.commands.diagnostics.os.path.exists", return_value=True),
            patch(
                "src.sprawl.commands.diagnostics.subprocess.check_output", return_value="main"
            ) as mock_check_output,
            patch("src.sprawl.commands.diagnostics.subprocess.run") as mock_run,
        ):
            if run_side_effect is not None:
                mock_run.side_effect = run_side_effect
            with contextlib.suppress(SprawlError):
                cmd_update()
            return mock_check_output, mock_run

    def test_cmd_update(self):
        mock_check_output, mock_run = self._run_cmd_update_scenario()
        mock_check_output.assert_any_call(
            ["git", "-C", "/fake/sprawl/core", "rev-parse", "--abbrev-ref", "HEAD"],
            text=True,
            env=ANY,
            timeout=30,
        )
        mock_run.assert_any_call(
            ["git", "-C", "/fake/sprawl/core", "pull", "origin", "main"],
            check=True,
            env=ANY,
            timeout=60,
        )
        _, mock_run_err = self._run_cmd_update_scenario(
            subprocess.CalledProcessError(1, ["git", "pull"])
        )
        self.assertTrue(mock_run_err.called)

    def _run_production_github_update(self, returncodes: list[int]):
        """Runs production cmd_update on Linux with specified subprocess return codes."""
        config.dry_run = False
        with (
            patch("src.sprawl.commands.diagnostics.resolve_repo_root", return_value=None),
            patch("src.sprawl.commands.diagnostics.os.path.exists", return_value=False),
            patch("sys.platform", "linux"),
            patch("src.sprawl.commands.diagnostics.subprocess.run") as mock_run,
        ):
            mock_run.side_effect = [MagicMock(returncode=rc) for rc in returncodes]
            cmd_update()
            return [c.args[0] for c in mock_run.call_args_list]

    def test_cmd_update_production_github(self):
        """cmd_update in production runs pipx install from github via HTTPS, then SSH on fallback."""
        https_calls = self._run_production_github_update([0])
        self.assertIn(
            [
                "pipx",
                "install",
                "git+https://github.com/sprawl-software/sprawl-cli.git",
                "--force",
                "--pip-args=--no-cache-dir",
            ],
            https_calls,
        )

        fallback_calls = self._run_production_github_update([1, 0])
        self.assertIn(
            [
                "pipx",
                "install",
                "git+ssh://git@github.com/sprawl-software/sprawl-cli.git",
                "--force",
                "--pip-args=--no-cache-dir",
            ],
            fallback_calls,
        )

    def test_cmd_init_error_handling(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config.agents_dir_global = os.path.join(tmpdir, "core")
            config.config_path = os.path.join(tmpdir, "config.json")
            config.dry_run = False
            with (
                patch(
                    "src.sprawl.commands.init_cmd.subprocess.run",
                    side_effect=subprocess.CalledProcessError(128, ["git", "clone"]),
                ),
                self.assertRaises(SprawlError),
            ):
                cmd_init("git@github.com:test/repo.git", target_dir=os.path.join(tmpdir, "ws"))

    def test_get_git_env_allows_interactive_prompts(self):
        """get_git_env does not force BatchMode=yes or GIT_TERMINAL_PROMPT=0 so SSH passphrases can be entered."""
        from src.sprawl.utils import get_git_env

        env = get_git_env()
        self.assertNotIn("GIT_TERMINAL_PROMPT", env)
        self.assertNotIn("BatchMode=yes", env.get("GIT_SSH_COMMAND", ""))
        self.assertIn("ConnectTimeout", env.get("GIT_SSH_COMMAND", ""))

    @patch("src.sprawl.utils.os.path.exists")
    @patch("src.sprawl.workspace.Workspace.get_dna_alias", return_value=None)
    def test_active_dna_context_fallback_to_registry_default(self, mock_alias, mock_exists):
        """get_active_dna_context falls back to registry default if core hub does not exist."""
        from src.sprawl.utils import get_active_dna_context

        def exists_side_effect(path):
            if path == config.agents_dir_global:
                return False
            return path == os.path.join(config.dna_registry_dir, "default")

        mock_exists.side_effect = exists_side_effect

        result = get_active_dna_context("/fake/dir")
        self.assertEqual(result, os.path.join(config.dna_registry_dir, "default"))

    def _run_sync_idempotency_scenario(self, cmp_equal: bool, copy_side_effect=None):
        """Runs sync_app_directory with controlled filecmp and copy2 behavior."""
        config.agents_dir_global = "/fake/global"
        config.dry_run = False
        reqs = {"rules": ["rule1.md"], "skills": [], "workflows": []}
        with (
            patch("src.sprawl.sync.parse_sprawl_manifest", return_value=reqs),
            patch("src.sprawl.sync.os.path.exists", return_value=True),
            patch("src.sprawl.sync.os.makedirs"),
            patch("src.sprawl.sync.filecmp.cmp", return_value=cmp_equal),
            patch("src.sprawl.sync.shutil.copy2", side_effect=copy_side_effect) as mock_copy2,
        ):
            with contextlib.suppress(Exception):
                sync_app_directory("/fake/app")
            return mock_copy2.call_count

    def test_sync_idempotency_error_handling(self):
        self.assertEqual(self._run_sync_idempotency_scenario(True), 0)
        try:
            self._run_sync_idempotency_scenario(False, PermissionError("Access Denied"))
        except PermissionError:
            self.fail("sync_app_directory failed to catch PermissionError!")

    def test_sync_updates_timestamp(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            app_dir = os.path.join(tmpdir, "app")
            agents_dir = os.path.join(app_dir, ".agents")
            os.makedirs(agents_dir)
            with open(os.path.join(agents_dir, "sprawl_manifest.yml"), "w") as f:
                f.write("dna: core\nrules:\nskills:\nworkflows:\n")

            config.dry_run = False
            with (
                patch(
                    "src.sprawl.sync._sync_app_directory_impl",
                    return_value={"copied": 0, "pruned": 0, "venv_provisioned": False},
                ),
                patch("src.sprawl.workspace.update_workspace_sync_timestamp") as mock_timestamp,
                patch("src.sprawl.workspace.Workspace.update_sync_state") as mock_state,
            ):
                sync_app_directory(app_dir)
                mock_timestamp.assert_called_once_with(os.path.abspath(app_dir))
                mock_state.assert_called_once_with({"last_manifest_sync": True})

    def _run_sync_rce_scenario(self) -> list:
        """Runs sync_app_directory with an unapproved skill containing package.json."""
        config.agents_dir_global = "/fake/global"
        config.dry_run = False
        reqs = {"rules": [], "skills": ["approved_skill"], "workflows": []}
        walk_rows = [("/fake/app/.agents/skills/malicious_skill", [], ["package.json"])]
        with (
            patch("src.sprawl.sync.parse_sprawl_manifest", return_value=reqs),
            patch("src.sprawl.sync.os.path.exists", return_value=True),
            patch("src.sprawl.sync.os.walk", return_value=walk_rows),
            patch("src.sprawl.sync.os.makedirs"),
            patch("src.sprawl.sync.shutil.copytree"),
            patch("src.sprawl.sync.subprocess.run") as mock_run,
        ):
            with contextlib.suppress(Exception):
                sync_app_directory("/fake/app")
            return mock_run.call_args_list

    def test_sync_rce_prevention(self):
        calls = self._run_sync_rce_scenario()
        npm_calls = [call for call in calls if "npm" in str(call)]
        self.assertEqual(len(npm_calls), 0)

    def test_cmd_init_argument_injection(self):
        with self.assertRaises(SprawlError):
            cmd_init("--upload-pack=foo", target_dir="/fake/dir")

    def test_cmd_init_credential_masking(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config.agents_dir_global = os.path.join(tmpdir, "global")
            config.config_path = os.path.join(tmpdir, "config.json")
            with patch("src.sprawl.config.config.dry_run", True):
                secret_url = "https://user:SUPER_SECRET_TOKEN@github.com/org/repo.git"
                cmd_init(secret_url, target_dir=os.path.join(tmpdir, "hub"))

            loaded = config.load()
            self.assertEqual(loaded["remote_dna_url"], "https://***:***@github.com/org/repo.git")

    @patch("src.sprawl.output.config.json_logging", True)
    def test_json_logging(self):
        from src.sprawl import output

        captured_output = io.StringIO()
        sys.stdout = captured_output
        try:
            output.print_status("Test status message")
            output.print_error("Test error message")
        finally:
            sys.stdout = sys.__stdout__

        output_lines = captured_output.getvalue().strip().split("\n")

        log1 = json.loads(output_lines[0])
        self.assertEqual(log1["level"], "info")
        self.assertEqual(log1["message"], "Test status message")

        log2 = json.loads(output_lines[1])
        self.assertEqual(log2["level"], "error")
        self.assertEqual(log2["message"], "Test error message")

    def _run_init_alias_scenario(self, alias_arg: str):
        """Runs cmd_init with an @alias inside an isolated temporary directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config.dna_registry_dir = os.path.join(tmpdir, "dna")
            config.agents_dir_global = os.path.join(tmpdir, "core")
            os.makedirs(config.agents_dir_global, exist_ok=True)
            config.dry_run = False
            expected_target = os.path.join(config.dna_registry_dir, alias_arg.lstrip("@"))
            with (
                patch("src.sprawl.commands.init_cmd.subprocess.run") as mock_run,
                patch("src.sprawl.validation.validate_dna_directory"),
                patch("src.sprawl.workspace.Workspace") as mock_ws,
            ):
                cmd_init(alias_arg, target_dir=os.path.join(tmpdir, "ws"))
                return mock_run.call_args_list, expected_target, mock_ws

    def test_cmd_init_resolves_alias(self):
        calls, expected_target_dir, mock_workspace = self._run_init_alias_scenario(
            "@python-fastapi"
        )
        clone_cmds = [c.args[0] for c in calls]
        self.assertIn(
            [
                "git",
                "clone",
                "https://github.com/sprawl-software/aaf-python-fastapi.git",
                expected_target_dir,
            ],
            clone_cmds,
        )
        mock_workspace.return_value.bind_dna.assert_called_with("python-fastapi")

    def test_cmd_init_unknown_alias(self):
        with self.assertRaises(SprawlError) as cm:
            cmd_init("@unknown-alias", target_dir="/fake/dir")
        self.assertIn("Unknown DNA alias", str(cm.exception))

    def test_cmd_list(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            skills_dir = os.path.join(tmpdir, "skills")
            os.makedirs(os.path.join(skills_dir, "web_scraper"))
            os.makedirs(os.path.join(skills_dir, "parser"))

            from src.sprawl.commands.artifacts import cmd_list

            with (
                patch("src.sprawl.commands.artifacts.get_active_dna_context", return_value=tmpdir),
                patch("sys.stdout", new_callable=io.StringIO) as mock_stdout,
            ):
                cmd_list()
                output = mock_stdout.getvalue()

            self.assertIn("web_scraper", output)
            self.assertIn("parser", output)

    def _setup_dna_and_workspace(self, tmpdir: str) -> tuple[str, str, str]:
        """Creates a real DNA directory and workspace manifest for artifact tests."""
        dna_dir = os.path.join(tmpdir, "dna")
        os.makedirs(os.path.join(dna_dir, "skills", "web_scraper"))
        os.makedirs(os.path.join(dna_dir, "skills", "data_processor"))
        os.makedirs(os.path.join(dna_dir, "skills", "target_persona"))
        os.makedirs(os.path.join(dna_dir, "skills", "keep_persona"))
        os.makedirs(os.path.join(dna_dir, "rules"))
        with open(os.path.join(dna_dir, "rules", "seo_rules.md"), "w") as f:
            f.write("# SEO\n")

        ws_dir = os.path.join(tmpdir, "ws")
        agents_dir = os.path.join(ws_dir, ".agents")
        os.makedirs(agents_dir)
        manifest_path = os.path.join(agents_dir, "sprawl_manifest.yml")
        with open(manifest_path, "w", encoding="utf-8") as f:
            f.write("skills:\n  - existing_skill\n  - target_persona\n  - keep_persona\n\nrules:\n")
        return dna_dir, ws_dir, manifest_path

    def test_cmd_add(self):
        from src.sprawl.commands.artifacts import cmd_add

        with tempfile.TemporaryDirectory() as tmpdir:
            dna_dir, ws_dir, manifest_path = self._setup_dna_and_workspace(tmpdir)
            config.dry_run = False
            with (
                patch("src.sprawl.commands.artifacts.get_active_dna_context", return_value=dna_dir),
                patch("src.sprawl.commands.artifacts.cmd_sync") as mock_sync,
            ):
                cmd_add(["web_scraper", "seo_rules"], target_dir=ws_dir)
                mock_sync.assert_called_once()

            with open(manifest_path, encoding="utf-8") as f:
                written_content = f.read()
            self.assertIn("- web_scraper", written_content)
            self.assertIn("- seo_rules.md", written_content)

    def test_cmd_add_all(self):
        from src.sprawl.commands.artifacts import cmd_add

        with tempfile.TemporaryDirectory() as tmpdir:
            dna_dir, ws_dir, manifest_path = self._setup_dna_and_workspace(tmpdir)
            config.dry_run = False
            with (
                patch("src.sprawl.commands.artifacts.get_active_dna_context", return_value=dna_dir),
                patch("src.sprawl.commands.artifacts.cmd_sync") as mock_sync,
            ):
                cmd_add(["*"], target_dir=ws_dir)
                mock_sync.assert_called_once()

            with open(manifest_path, encoding="utf-8") as f:
                written_content = f.read()
            self.assertIn("- web_scraper", written_content)
            self.assertIn("- data_processor", written_content)
            self.assertIn("- seo_rules.md", written_content)

    def test_cmd_add_missing_item(self):
        from src.sprawl.commands.artifacts import cmd_add

        with tempfile.TemporaryDirectory() as tmpdir:
            dna_dir, ws_dir, _ = self._setup_dna_and_workspace(tmpdir)
            with (
                patch("src.sprawl.commands.artifacts.get_active_dna_context", return_value=dna_dir),
                self.assertRaises(SprawlError),
            ):
                cmd_add(["missing_item"], target_dir=ws_dir)

    def test_cmd_scaffold_persona(self):
        from src.sprawl.commands.artifacts import cmd_scaffold

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("src.sprawl.commands.artifacts.get_active_dna_context", return_value=tmpdir):
                cmd_scaffold("persona", "GTM Specialist")

            expected_skill = os.path.join(tmpdir, "skills", "persona-gtm_specialist", "SKILL.md")
            self.assertTrue(os.path.isfile(expected_skill))

    def test_cmd_remove(self):
        from src.sprawl.commands.artifacts import cmd_remove

        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as tmpdir:
            dna_dir, ws_dir, manifest_path = self._setup_dna_and_workspace(tmpdir)
            try:
                os.chdir(ws_dir)
                with (
                    patch(
                        "src.sprawl.commands.artifacts.get_active_dna_context",
                        return_value=dna_dir,
                    ),
                    patch("src.sprawl.commands.artifacts.cmd_sync") as mock_sync,
                ):
                    cmd_remove(["target_persona"])
                    mock_sync.assert_called_once()

                with open(manifest_path, encoding="utf-8") as f:
                    written_content = f.read()
                self.assertNotIn("- target_persona", written_content)
                self.assertIn("- keep_persona", written_content)
            finally:
                os.chdir(original_cwd)

    def _run_demo_scenario(self):
        """Executes cmd_demo with choice '1' and isolated squad provisioning."""
        from src.sprawl.commands.diagnostics import cmd_demo

        provisioned: list[str] = []
        with (
            patch("builtins.input", return_value="1"),
            patch("src.sprawl.demo_engine.cmd_init") as mock_init,
            patch("src.sprawl.demo_engine.cmd_clean_test") as mock_clean,
            patch("src.sprawl.demo_engine.generate_dummy_dna", return_value="/tmp/fake_dummy"),
            patch(
                "src.sprawl.demo_engine._provision_squad_workspace",
                side_effect=lambda _d, name, _a: provisioned.append(name),
            ),
            patch("sys.stdout", new_callable=io.StringIO),
        ):
            cmd_demo()
            return mock_clean.called, mock_init.called, len(provisioned)

    def test_cmd_demo(self):
        cleaned, initialized, squad_count = self._run_demo_scenario()
        self.assertTrue(cleaned)
        self.assertTrue(initialized)
        self.assertEqual(squad_count, 4)

    @patch("src.sprawl.commands.diagnostics.cmd_clean_test")
    @patch("src.sprawl.commands.diagnostics.shutil.rmtree")
    def test_cmd_clean_demo_security(self, mock_rmtree, mock_clean_test):
        from src.sprawl.commands.diagnostics import cmd_clean_demo

        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                os.chdir(temp_dir)
                demo_dir = os.path.join(temp_dir, "sprawl_demo")

                os.makedirs(demo_dir)
                cmd_clean_demo()
                mock_rmtree.assert_called_with(os.path.realpath(demo_dir))
                mock_clean_test.assert_called_once()

                os.rmdir(demo_dir)
                mock_rmtree.reset_mock()
                mock_clean_test.reset_mock()

                os.makedirs("actual_target")
                try:
                    os.symlink("actual_target", "sprawl_demo")
                    with self.assertRaises(SprawlError) as cm:
                        cmd_clean_demo()
                    self.assertIn("symbolic link", str(cm.exception))
                    os.unlink("sprawl_demo")
                except OSError:
                    pass

            finally:
                os.chdir(original_cwd)

    def test_cmd_bind(self):
        from src.sprawl.bind import bind_adapters

        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                os.chdir(temp_dir)

                self.assertFalse(bind_adapters(temp_dir))
                os.makedirs(os.path.join(temp_dir, ".agents"))
                self.assertTrue(bind_adapters(temp_dir))

                self.assertTrue(os.path.exists(os.path.join(temp_dir, ".agent")))
                self.assertTrue(os.path.islink(os.path.join(temp_dir, ".cursorrules")))
                self.assertTrue(os.path.islink(os.path.join(temp_dir, ".clinerules")))
                self.assertTrue(os.path.islink(os.path.join(temp_dir, ".windsurfrules")))
                self.assertTrue(
                    os.path.islink(os.path.join(temp_dir, ".github", "copilot-instructions.md"))
                )

            finally:
                os.chdir(original_cwd)

    def test_cmd_diff_and_doctor_and_man(self):
        """Verifies diff_files, diff_recursive, cmd_diff, cmd_doctor, and cmd_man."""
        from src.sprawl.commands.diff import cmd_diff, diff_files, diff_recursive
        from src.sprawl.commands.doctor import cmd_doctor
        from src.sprawl.commands.man import cmd_man

        with tempfile.TemporaryDirectory() as tmpdir:
            dna_dir = os.path.join(tmpdir, "dna")
            os.makedirs(os.path.join(dna_dir, "rules"))
            with open(os.path.join(dna_dir, "rules", "r1.md"), "w") as f:
                f.write("# Rule 1\n")

            ws_dir = os.path.join(tmpdir, "ws")
            os.makedirs(os.path.join(ws_dir, ".agents", "rules"))
            with open(os.path.join(ws_dir, ".agents", "rules", "r1.md"), "w") as f:
                f.write("# Rule 1 Modified\n")
            with open(os.path.join(ws_dir, ".agents", "sprawl_manifest.yml"), "w") as f:
                f.write("dna: core\nrules:\n  - r1.md\nlocal_rules:\n  - local_custom.md\n")

            self.assertTrue(
                diff_files(
                    os.path.join(dna_dir, "rules", "r1.md"),
                    os.path.join(ws_dir, ".agents", "rules", "r1.md"),
                    "rules/r1.md",
                )
            )
            self.assertTrue(
                diff_recursive(
                    os.path.join(dna_dir, "rules"),
                    os.path.join(ws_dir, ".agents", "rules"),
                    "rules",
                )
            )
            with patch("src.sprawl.commands.diff.get_active_dna_context", return_value=dna_dir):
                self.assertIsNone(cmd_diff(ws_dir))

            self.assertIsNone(cmd_doctor())
            self.assertIsNone(cmd_man())


if __name__ == "__main__":
    unittest.main()
