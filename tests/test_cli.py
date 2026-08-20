import unittest
import os
import tempfile
import json
import sys
import subprocess
import io
from unittest.mock import patch, MagicMock, ANY

# Ensure the local src is available
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from src.sprawl.config import config
from src.sprawl.exceptions import SprawlError
from src.sprawl.utils import CATEGORIES
import src.sprawl.utils as utils
from src.sprawl.sync import parse_sprawl_manifest, sync_app_directory
from src.sprawl.core import cmd_graft, cmd_create, cmd_init, cmd_update, cmd_clean_test

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
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_file:
            temp_file.write(test_content)
            temp_path = temp_file.name

        try:
            reqs = parse_sprawl_manifest(temp_path)
            
            self.assertIn('engineering.md', reqs['rules'])
            self.assertIn('web_artifacts_builder', reqs['skills'])
            self.assertIn('execution.md', reqs['workflows'])
        finally:
            os.remove(temp_path)

    def test_parse_sprawl_manifest_traversal(self):
        test_content = """# test app
dna: core

rules:
  - ../../.ssh/id_rsa
"""
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_file:
            temp_file.write(test_content)
            temp_path = temp_file.name

        try:
            with self.assertRaises(SprawlError):
                parse_sprawl_manifest(temp_path)
        finally:
            os.remove(temp_path)

    @patch('src.sprawl.commands.workspace.register_workspace')
    def test_cmd_graft(self, mock_register):
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                os.chdir(temp_dir)
                app_name = os.path.basename(temp_dir)
                
                # Test python fallback
                with open("requirements.txt", "w") as f:
                    f.write("requests==2.31.0")

                config.dry_run = False
                cmd_graft()
                
                sprawl_package_md_path = os.path.join(temp_dir, ".agents", "sprawl_manifest.yml")
                self.assertTrue(os.path.exists(sprawl_package_md_path))
                
                with open(sprawl_package_md_path, "r") as f:
                    content = f.read()
                
                self.assertTrue(content.startswith(f"# {app_name}"))
                self.assertIn("rules:", content)
                self.assertIn("workflows:", content)
                self.assertIn("- python.md", content)
                
                mock_register.assert_called_with(app_name, temp_dir)
                
                with self.assertRaises(SprawlError):
                    cmd_graft()

            finally:
                os.chdir(original_cwd)

    @patch('src.sprawl.commands.workspace.register_workspace')
    def test_cmd_create(self, mock_register):
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                os.chdir(temp_dir)
                config.dry_run = False
                
                cmd_create('TestWorkspace')
                
                workspace_dir = os.path.abspath('TestWorkspace')
                self.assertTrue(os.path.exists(workspace_dir))
                self.assertTrue(os.path.exists(os.path.join(workspace_dir, ".agents", "sprawl_manifest.yml")))
                
                with self.assertRaises(SprawlError):
                    cmd_create('TestWorkspace')
            finally:
                os.chdir(original_cwd)

    @patch('src.sprawl.commands.workspace.get_all_workspaces')
    @patch('src.sprawl.commands.workspace.console.print')
    def test_cmd_ws_list(self, mock_print, mock_get_all):
        from src.sprawl.commands.workspace import cmd_ws_list
        mock_get_all.return_value = {
            "ws1": {"path": "/tmp/ws1", "dna_source": None, "last_sync_timestamp": None},
            "ws2": {"path": "/tmp/ws2", "dna_source": "custom", "last_sync_timestamp": "2024-01-01T00:00:00Z"}
        }
        cmd_ws_list()
        mock_print.assert_called_once()
        table = mock_print.call_args[0][0]
        from rich.table import Table
        self.assertIsInstance(table, Table)
        self.assertEqual(len(table.rows), 2)

    @patch('src.sprawl.commands.workspace.get_all_workspaces')
    @patch('src.sprawl.commands.workspace.print_status')
    def test_cmd_ws_list_empty(self, mock_print_status, mock_get_all):
        from src.sprawl.commands.workspace import cmd_ws_list
        mock_get_all.return_value = {}
        cmd_ws_list()
        mock_print_status.assert_called_with("No workspaces currently tracked in the registry.")

    @patch('src.sprawl.commands.workspace.deregister_workspace')
    @patch('src.sprawl.commands.workspace.get_workspace_info')
    @patch('src.sprawl.commands.workspace.shutil.rmtree')
    def test_cmd_ws_remove(self, mock_rmtree, mock_get, mock_deregister):
        from src.sprawl.commands.workspace import cmd_ws_remove
        
        # Test 1: Untracked workspace
        mock_get.return_value = None
        cmd_ws_remove("missing")
        mock_deregister.assert_not_called()
        
        # Test 2: Tracked workspace, no delete
        mock_get.return_value = {"path": "/fake/path"}
        cmd_ws_remove("existing")
        mock_deregister.assert_called_with("existing")
        mock_rmtree.assert_not_called()
        
        # Test 3: Tracked workspace, with delete
        mock_deregister.reset_mock()
        with patch('src.sprawl.commands.workspace.os.path.exists', return_value=True):
            cmd_ws_remove("existing_del", delete=True)
            mock_deregister.assert_called_with("existing_del")
            mock_rmtree.assert_called_with("/fake/path")

    @patch('src.sprawl.commands.workspace.get_all_workspaces')
    @patch('src.sprawl.commands.sync_cmd.cmd_sync')
    @patch('src.sprawl.commands.workspace.os.path.exists', return_value=True)
    def test_cmd_ws_push(self, mock_exists, mock_sync, mock_get_all):
        from src.sprawl.commands.workspace import cmd_ws_push
        
        # Test 1: Empty
        mock_get_all.return_value = {}
        cmd_ws_push()
        mock_sync.assert_not_called()
        
        # Test 2: Push to specific workspace
        mock_get_all.return_value = {"ws1": {"path": "/fake/ws1"}, "ws2": {"path": "/fake/ws2"}}
        cmd_ws_push("ws1")
        mock_sync.assert_called_once_with(target_dir="/fake/ws1")
        
        # Test 3: Push to all
        mock_sync.reset_mock()
        cmd_ws_push()
        self.assertEqual(mock_sync.call_count, 2)
        
        # Test 4: Missing workspace
        with self.assertRaises(SprawlError):
            cmd_ws_push("missing")

    def test_cmd_create_sanitization(self):
        invalid_names = [
            "../../../etc",
            "my/workspace",
            "workspace name",
            "workspace;rm-rf/"
        ]
        for name in invalid_names:
            with self.assertRaises(SprawlError):
                cmd_create(name)

    @patch.dict(os.environ, {}, clear=True)
    def test_sprawl_test_command_gated_by_default(self):
        from src.sprawl.cli import get_parser
        parser = get_parser()
        # By default (SPRAWL_DEV not set), parsing 'test' should fail (raise SystemExit)
        with self.assertRaises(SystemExit):
            parser.parse_args(["test"])

    @patch.dict(os.environ, {"SPRAWL_DEV": "1"})
    def test_sprawl_test_command_allowed_in_dev(self):
        from src.sprawl.cli import get_parser
        parser = get_parser()
        # When SPRAWL_DEV=1 is set, parsing 'test' should succeed
        args = parser.parse_args(["test"])
        self.assertEqual(args.command, "test")

    @patch('src.sprawl.commands.diagnostics.subprocess.check_output')
    @patch('src.sprawl.commands.diagnostics.subprocess.run')
    @patch('src.sprawl.commands.diagnostics.os.path.exists')
    @patch('src.sprawl.config.config.agents_dir_global', '/fake/sprawl/core')
    def test_cmd_update(self, mock_exists, mock_run, mock_check_output):
        config.dry_run = False
        mock_exists.return_value = True
        mock_check_output.return_value = "main"

        cmd_update()

        mock_check_output.assert_any_call(["git", "-C", "/fake/sprawl/core", "rev-parse", "--abbrev-ref", "HEAD"], text=True, env=ANY)
        mock_run.assert_any_call(["git", "-C", "/fake/sprawl/core", "pull", "origin", "main"], check=True, env=ANY)
        
        mock_run.side_effect = subprocess.CalledProcessError(1, ['git', 'pull'])
        try:
            cmd_update()
        except SprawlError:
            pass # pipx error occurs next, which raises SprawlError

    @patch('src.sprawl.commands.diagnostics.resolve_repo_root', return_value=None)
    @patch('src.sprawl.commands.diagnostics.subprocess.run')
    @patch('src.sprawl.commands.diagnostics.os.path.exists', return_value=False)
    def test_cmd_update_production_github(self, mock_exists, mock_run, mock_resolve):
        """cmd_update in production runs pipx install from github via HTTPS, then SSH on fallback."""
        config.dry_run = False
        
        # 1. Test successful HTTPS path
        mock_run.return_value = MagicMock(returncode=0)
        cmd_update()
        mock_run.assert_any_call(
            ["pipx", "install", "git+https://github.com/sprawl-software/sprawl-cli.git", "--force"],
            env=ANY
        )
        
        # 2. Test fallback to SSH path
        mock_run.reset_mock()
        # Return code 1 for HTTPS, then success (0) for SSH
        mock_run.side_effect = [
            MagicMock(returncode=1),
            MagicMock(returncode=0)
        ]
        cmd_update()
        mock_run.assert_any_call(
            ["pipx", "install", "git+ssh://git@github.com/sprawl-software/sprawl-cli.git", "--force"],
            check=True, env=ANY
        )

    @patch('builtins.input', return_value='n')
    @patch('src.sprawl.commands.init_cmd.subprocess.run')
    @patch('src.sprawl.commands.init_cmd.os.path.exists')
    @patch('src.sprawl.commands.init_cmd.os.makedirs')
    @patch('src.sprawl.commands.init_cmd.config.update')
    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    @patch('src.sprawl.config.config.agents_dir_global', '/fake/sprawl/core')
    def test_cmd_init_error_handling(self, mock_open, mock_update, mock_makedirs, mock_exists, mock_run, mock_input):
        mock_exists.return_value = False
        mock_run.side_effect = subprocess.CalledProcessError(128, ['git', 'clone'])
        
        with self.assertRaises(SprawlError):
            cmd_init('git@github.com:test/repo.git', target_dir="/fake/dir")

    @patch('src.sprawl.sync.shutil.copy2')
    @patch('src.sprawl.sync.filecmp.cmp')
    @patch('src.sprawl.sync.os.path.exists')
    def test_sync_idempotency_error_handling(self, mock_exists, mock_cmp, mock_copy2):
        config.agents_dir_global = '/fake/global'
        config.dry_run = False
        
        mock_exists.return_value = True
        mock_cmp.return_value = True
        
        reqs = {"rules": ["rule1.md"], "skills": [], "workflows": []}
        
        with patch('src.sprawl.sync.parse_sprawl_manifest', return_value=reqs):
            with patch('src.sprawl.sync.os.makedirs'):
                try:
                    sync_app_directory('/fake/app')
                except Exception:
                    pass
        
        mock_copy2.assert_not_called()
        
        mock_cmp.return_value = False
        mock_copy2.side_effect = PermissionError("Access Denied")
        
        with patch('src.sprawl.sync.parse_sprawl_manifest', return_value=reqs):
            with patch('src.sprawl.sync.os.makedirs'):
                try:
                    sync_app_directory('/fake/app')
                except PermissionError:
                    self.fail("sync_app_directory failed to catch PermissionError!")
                except Exception:
                    pass

    @patch('src.sprawl.workspace.update_workspace_sync_timestamp')
    @patch('src.sprawl.workspace.Workspace.update_sync_state')
    @patch('src.sprawl.sync._sync_app_directory_impl')
    @patch('src.sprawl.sync.parse_sprawl_manifest', return_value={})
    @patch('src.sprawl.sync.os.path.exists', return_value=True)
    @patch('src.sprawl.sync.os.makedirs')
    @patch('src.sprawl.sync.shutil.copytree')
    @patch('src.sprawl.sync.shutil.rmtree')
    def test_sync_updates_timestamp(self, mock_rmtree, mock_copytree, mock_makedirs, mock_exists, mock_parse, mock_impl, mock_state, mock_timestamp):
        config.agents_dir_global = '/fake/global'
        config.dry_run = False
        
        from src.sprawl.sync import sync_app_directory
        sync_app_directory('/fake/app')
        
        mock_timestamp.assert_called_once_with('/fake/app')
        mock_state.assert_called_once_with({"last_manifest_sync": True})

    @patch('src.sprawl.sync.subprocess.run')
    @patch('src.sprawl.sync.os.walk')
    @patch('src.sprawl.sync.os.path.exists')
    def test_sync_rce_prevention(self, mock_exists, mock_walk, mock_run):
        config.agents_dir_global = '/fake/global'
        config.dry_run = False
        mock_exists.return_value = True
        
        mock_walk.return_value = [('/fake/app/.agents/skills/malicious_skill', [], ['package.json'])]
        
        reqs = {"rules": [], "skills": ["approved_skill"], "workflows": []}
        
        with patch('src.sprawl.sync.parse_sprawl_manifest', return_value=reqs):
            with patch('src.sprawl.sync.os.makedirs'):
                with patch('src.sprawl.sync.shutil.copytree'):
                    try:
                        sync_app_directory('/fake/app')
                    except Exception:
                        pass
        
        npm_calls = [call for call in mock_run.call_args_list if 'npm' in str(call)]
        self.assertEqual(len(npm_calls), 0)

    def test_cmd_init_argument_injection(self):
        with self.assertRaises(SprawlError):
            cmd_init("--upload-pack=foo", target_dir="/fake/dir")

    @patch('src.sprawl.commands.init_cmd.config.update')
    @patch('src.sprawl.commands.init_cmd.os.makedirs')
    @patch('src.sprawl.commands.init_cmd.subprocess.run')
    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    @patch('src.sprawl.config.config.dry_run', True)
    def test_cmd_init_credential_masking(self, mock_open, mock_run, mock_makedirs, mock_update_config):
        config.agents_dir_global = '/fake/global'
        
        secret_url = "https://user:SUPER_SECRET_TOKEN@github.com/org/repo.git"
        cmd_init(secret_url, target_dir="/fake/dir")
        
        called_args = mock_update_config.call_args[0][0]
        self.assertEqual(called_args['remote_dna_url'], "https://***:***@github.com/org/repo.git")

    @patch('src.sprawl.output.config.json_logging', True)
    def test_json_logging(self):
        import io
        import json
        from src.sprawl import output
        
        captured_output = io.StringIO()
        sys.stdout = captured_output
        try:
            output.print_status("Test status message")
            output.print_error("Test error message")
        finally:
            sys.stdout = sys.__stdout__
            
        output_lines = captured_output.getvalue().strip().split('\n')
        
        log1 = json.loads(output_lines[0])
        self.assertEqual(log1["level"], "info")
        self.assertEqual(log1["message"], "Test status message")
        
        log2 = json.loads(output_lines[1])
        self.assertEqual(log2["level"], "error")
        self.assertEqual(log2["message"], "Test error message")

    @patch('src.sprawl.commands.init_cmd.subprocess.run')
    @patch('src.sprawl.commands.init_cmd.os.path.exists', return_value=False)
    @patch('src.sprawl.commands.init_cmd.os.makedirs')
    @patch('src.sprawl.commands.init_cmd.config.update')
    @patch('src.sprawl.workspace.Workspace')
    def test_cmd_init_resolves_alias(self, mock_workspace, mock_update, mock_makedirs, mock_exists, mock_run):
        config.dry_run = False
        cmd_init("@python-fastapi", target_dir="/fake/dir")
        expected_target_dir = os.path.join(config.dna_registry_dir, "python-fastapi")
        mock_run.assert_any_call(["git", "clone", "https://github.com/sprawl-software/aaf-python-fastapi.git", expected_target_dir], check=True, env=ANY)
        mock_workspace.return_value.bind_dna.assert_called_with("python-fastapi")

    def test_cmd_init_unknown_alias(self):
        with self.assertRaises(SprawlError) as cm:
            cmd_init("@unknown-alias", target_dir="/fake/dir")
        self.assertIn("Unknown DNA alias", str(cm.exception))

    @patch('src.sprawl.commands.artifacts.get_active_dna_context')
    @patch('src.sprawl.commands.artifacts.os.path.exists')
    @patch('src.sprawl.commands.artifacts.os.listdir')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_cmd_list(self, mock_stdout, mock_listdir, mock_exists, mock_context):
        mock_context.return_value = '/fake/dna'
        # exists should return true for the base dir and true for 'skills'
        def exists_side_effect(path):
            if path == '/fake/dna': return True
            if path.endswith('skills'): return True
            return False
        mock_exists.side_effect = exists_side_effect
        mock_listdir.return_value = ['web_scraper', 'parser']

        from src.sprawl.commands.artifacts import cmd_list
        cmd_list()
        
        output = mock_stdout.getvalue()
        self.assertIn("web_scraper", output)
        self.assertIn("parser", output)

    @patch('src.sprawl.commands.artifacts.get_active_dna_context')
    @patch('src.sprawl.commands.artifacts.os.path.exists')
    @patch('src.sprawl.commands.artifacts.os.listdir')
    @patch('src.sprawl.commands.artifacts.cmd_sync')
    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data="skills:\n  - existing_skill\n\nrules:\n")
    def test_cmd_add(self, mock_open, mock_sync, mock_listdir, mock_exists, mock_context):
        mock_context.return_value = '/fake/dna'
        # exists should return true for everything
        mock_exists.return_value = True
        
        # listdir returns web_scraper under skills
        def listdir_side_effect(path):
            if path.endswith('skills'): return ['web_scraper']
            if path.endswith('rules'): return ['seo_rules.md']
            return []
        mock_listdir.side_effect = listdir_side_effect

        from src.sprawl.commands.artifacts import cmd_add
        config.dry_run = False
        cmd_add(['web_scraper', 'seo_rules'])

        # Verify we attempt to open sprawl_manifest.yml to read and then to write
        mock_open.assert_called_with(os.path.join(os.getcwd(), ".agents", "sprawl_manifest.yml"), "w")
        
        # Verify sync is called
        mock_sync.assert_called_once()
        
        # Write was called. Get the written content.
        written_content = "".join(call.args[0] for call in mock_open().write.call_args_list)
        self.assertIn("- web_scraper", written_content)
        self.assertIn("- seo_rules", written_content)

    @patch('src.sprawl.commands.artifacts.get_active_dna_context')
    @patch('src.sprawl.commands.artifacts.os.path.exists')
    @patch('src.sprawl.commands.artifacts.os.listdir')
    @patch('src.sprawl.commands.artifacts.cmd_sync')
    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data="skills:\n  - existing_skill\n\nrules:\n")
    def test_cmd_add_all(self, mock_open, mock_sync, mock_listdir, mock_exists, mock_context):
        mock_context.return_value = '/fake/dna'
        mock_exists.return_value = True
        
        def listdir_side_effect(path):
            if path.endswith('skills'): return ['web_scraper', 'data_processor']
            if path.endswith('rules'): return ['seo_rules.md']
            return []
        mock_listdir.side_effect = listdir_side_effect

        from src.sprawl.commands.artifacts import cmd_add
        config.dry_run = False
        cmd_add(['*'])

        mock_open.assert_called_with(os.path.join(os.getcwd(), ".agents", "sprawl_manifest.yml"), "w")
        mock_sync.assert_called_once()
        
        written_content = "".join(call.args[0] for call in mock_open().write.call_args_list)
        self.assertIn("- web_scraper", written_content)
        self.assertIn("- data_processor", written_content)
        self.assertIn("- seo_rules.md", written_content)

    @patch('src.sprawl.commands.artifacts.get_active_dna_context')
    @patch('src.sprawl.commands.artifacts.os.path.exists')
    def test_cmd_add_missing_item(self, mock_exists, mock_context):
        mock_context.return_value = '/fake/dna'
        mock_exists.return_value = True # let categories exist
        with patch('src.sprawl.commands.artifacts.os.listdir', return_value=[]):
            from src.sprawl.commands.artifacts import cmd_add
            with self.assertRaises(SprawlError):
                cmd_add(['missing_item'])

    @patch('src.sprawl.commands.artifacts.get_active_dna_context')
    @patch('src.sprawl.commands.artifacts.os.path.exists')
    @patch('src.sprawl.commands.artifacts.os.makedirs')
    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    def test_cmd_scaffold_persona(self, mock_open, mock_makedirs, mock_exists, mock_context):
        mock_context.return_value = '/fake/dna'
        # exists should return True for dna context, False for target_dir
        def exists_side_effect(path):
            if path == '/fake/dna': return True
            return False
        mock_exists.side_effect = exists_side_effect
        
        from src.sprawl.commands.artifacts import cmd_scaffold
        cmd_scaffold("persona", "GTM Specialist")
        
        expected_dir = os.path.join("/fake/dna", "skills", "persona-gtm_specialist")
        mock_makedirs.assert_called_with(expected_dir)
        mock_open.assert_called_with(os.path.join(expected_dir, "SKILL.md"), "w")

    @patch('src.sprawl.commands.artifacts.get_active_dna_context')
    @patch('src.sprawl.commands.artifacts.os.path.exists')
    @patch('src.sprawl.commands.artifacts.os.listdir')
    @patch('src.sprawl.commands.artifacts.cmd_sync')
    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data="skills:\n  - target_persona\n  - keep_persona\n")
    def test_cmd_remove(self, mock_open, mock_sync, mock_listdir, mock_exists, mock_context):
        mock_context.return_value = '/fake/dna'
        mock_exists.return_value = True
        
        def listdir_side_effect(path):
            if path.endswith('skills'): return ['target_persona', 'keep_persona']
            return []
        mock_listdir.side_effect = listdir_side_effect

        from src.sprawl.commands.artifacts import cmd_remove
        cmd_remove(['target_persona'])

        written_content = "".join(call.args[0] for call in mock_open().write.call_args_list)
        self.assertNotIn("- target_persona", written_content)
        self.assertIn("- keep_persona", written_content)
        mock_sync.assert_called_once()

    @patch('builtins.input', return_value='1')
    @patch('src.sprawl.demo_engine.cmd_init')
    @patch('src.sprawl.demo_engine._provision_squad_workspace')
    @patch('src.sprawl.demo_engine.cmd_clean_test')
    @patch('src.sprawl.demo_engine.generate_dummy_dna', return_value='/tmp/fake_dummy')
    @patch('src.sprawl.demo_engine.tempfile.TemporaryDirectory')
    def test_cmd_demo(self, mock_td, mock_dummy, mock_clean, mock_provision, mock_init, mock_input):
        mock_td.return_value.__enter__ = lambda s: "/tmp/fake_demo"
        mock_td.return_value.__exit__ = MagicMock(return_value=False)

        from src.sprawl.commands.diagnostics import cmd_demo
        with patch('sys.stdout', new_callable=io.StringIO):
            cmd_demo()
            
        mock_clean.assert_called_once()
        mock_init.assert_called_once()
        # Demo "1" has 4 squads
        self.assertEqual(mock_provision.call_count, 4)

    @patch('src.sprawl.commands.diagnostics.cmd_clean_test')
    @patch('src.sprawl.commands.diagnostics.shutil.rmtree')
    def test_cmd_clean_demo_security(self, mock_rmtree, mock_clean_test):
        from src.sprawl.commands.diagnostics import cmd_clean_demo
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                os.chdir(temp_dir)
                demo_dir = os.path.join(temp_dir, "sprawl_demo")
                
                # Test normal safe deletion
                os.makedirs(demo_dir)
                cmd_clean_demo()
                mock_rmtree.assert_called_with(os.path.abspath(demo_dir))
                # Verify the cleanup function is now called directly (not via subprocess)
                mock_clean_test.assert_called_once()
                
                os.rmdir(demo_dir) # cleanup since rmtree is mocked
                mock_rmtree.reset_mock()
                mock_clean_test.reset_mock()
                
                # Test symlink prevention
                os.makedirs("actual_target")
                os.symlink("actual_target", "sprawl_demo")
                with self.assertRaises(SprawlError) as cm:
                    cmd_clean_demo()
                self.assertIn("symbolic link", str(cm.exception))
                os.unlink("sprawl_demo")
                
            finally:
                os.chdir(original_cwd)
    def test_cmd_bind(self):
        from src.sprawl.bind import bind_adapters
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                os.chdir(temp_dir)
                
                # Should fail if .agents does not exist
                self.assertFalse(bind_adapters(temp_dir))
                
                # Create .agents directory
                os.makedirs(os.path.join(temp_dir, ".agents"))
                
                # Run bind_adapters
                self.assertTrue(bind_adapters(temp_dir))
                
                # Verify files and directories are created
                self.assertTrue(os.path.exists(os.path.join(temp_dir, ".agent")))
                self.assertTrue(os.path.islink(os.path.join(temp_dir, ".cursorrules")))
                self.assertTrue(os.path.islink(os.path.join(temp_dir, ".clinerules")))
                self.assertTrue(os.path.islink(os.path.join(temp_dir, ".windsurfrules")))
                self.assertTrue(os.path.islink(os.path.join(temp_dir, ".github", "copilot-instructions.md")))
                
            finally:
                os.chdir(original_cwd)


if __name__ == '__main__':
    unittest.main()
