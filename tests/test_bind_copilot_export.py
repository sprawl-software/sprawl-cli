"""Tests for the _export_copilot_prompts and _export_category_to_prompts helpers in bind.py."""

import os
import shutil
import tempfile
import unittest

from src.sprawl.bind import _export_copilot_prompts, _export_category_to_prompts


class TestExportCategoryToPrompts(unittest.TestCase):
    """Unit tests for the shared _export_category_to_prompts() helper."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.prompts_dir = os.path.join(self.temp_dir, ".github", "prompts")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_exports_flat_md_files(self):
        """Exports flat .md files from a category directory as .prompt.md files."""
        category_dir = os.path.join(self.temp_dir, "skills")
        os.makedirs(category_dir)
        with open(os.path.join(category_dir, "debugging.md"), "w") as f:
            f.write("Debugging skill instructions")

        _export_category_to_prompts(category_dir, self.prompts_dir)

        prompt_path = os.path.join(self.prompts_dir, "debugging.prompt.md")
        self.assertTrue(os.path.exists(prompt_path))
        with open(prompt_path) as f:
            self.assertEqual(f.read(), "Debugging skill instructions")

    def test_exports_skill_subdir_with_skill_md(self):
        """Exports SKILL.md from subdirectories when check_skill_subdirs=True."""
        category_dir = os.path.join(self.temp_dir, "skills")
        skill_subdir = os.path.join(category_dir, "testing")
        os.makedirs(skill_subdir)
        with open(os.path.join(skill_subdir, "SKILL.md"), "w") as f:
            f.write("Testing skill content")

        _export_category_to_prompts(category_dir, self.prompts_dir, check_skill_subdirs=True)

        prompt_path = os.path.join(self.prompts_dir, "testing.prompt.md")
        self.assertTrue(os.path.exists(prompt_path))
        with open(prompt_path) as f:
            self.assertEqual(f.read(), "Testing skill content")

    def test_ignores_skill_subdirs_when_disabled(self):
        """Does NOT export SKILL.md subdirectories when check_skill_subdirs=False."""
        category_dir = os.path.join(self.temp_dir, "workflows")
        subdir = os.path.join(category_dir, "deploy")
        os.makedirs(subdir)
        with open(os.path.join(subdir, "SKILL.md"), "w") as f:
            f.write("deploy skill content")

        _export_category_to_prompts(category_dir, self.prompts_dir, check_skill_subdirs=False)

        prompt_path = os.path.join(self.prompts_dir, "deploy.prompt.md")
        self.assertFalse(os.path.exists(prompt_path))

    def test_skips_hidden_files(self):
        """Files starting with '.' are skipped."""
        category_dir = os.path.join(self.temp_dir, "skills")
        os.makedirs(category_dir)
        with open(os.path.join(category_dir, ".hidden.md"), "w") as f:
            f.write("hidden content")

        _export_category_to_prompts(category_dir, self.prompts_dir)

        self.assertFalse(os.path.exists(self.prompts_dir))

    def test_nonexistent_category_dir_is_noop(self):
        """Calling with a nonexistent category directory is a no-op."""
        _export_category_to_prompts(
            os.path.join(self.temp_dir, "nonexistent"),
            self.prompts_dir,
        )
        self.assertFalse(os.path.exists(self.prompts_dir))

    def test_skips_non_md_files(self):
        """Non-.md files are skipped."""
        category_dir = os.path.join(self.temp_dir, "skills")
        os.makedirs(category_dir)
        with open(os.path.join(category_dir, "script.py"), "w") as f:
            f.write("print('hello')")

        _export_category_to_prompts(category_dir, self.prompts_dir)

        self.assertFalse(os.path.exists(self.prompts_dir))


class TestExportCopilotPromptsIntegration(unittest.TestCase):
    """Integration tests for _export_copilot_prompts()."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.agents_dir = os.path.join(self.temp_dir, ".agents")
        os.makedirs(self.agents_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_exports_skills_and_workflows(self):
        """Exports both skills and workflows into .github/prompts/."""
        # Create a skill
        skills_dir = os.path.join(self.agents_dir, "skills")
        os.makedirs(skills_dir)
        with open(os.path.join(skills_dir, "review.md"), "w") as f:
            f.write("Code review skill")

        # Create a workflow
        workflows_dir = os.path.join(self.agents_dir, "workflows")
        os.makedirs(workflows_dir)
        with open(os.path.join(workflows_dir, "deploy.md"), "w") as f:
            f.write("Deploy workflow")

        _export_copilot_prompts(self.temp_dir)

        prompts_dir = os.path.join(self.temp_dir, ".github", "prompts")
        self.assertTrue(os.path.exists(os.path.join(prompts_dir, "review.prompt.md")))
        self.assertTrue(os.path.exists(os.path.join(prompts_dir, "deploy.prompt.md")))

    def test_cleans_stale_prompts_before_export(self):
        """Stale .prompt.md files are cleaned up before re-exporting."""
        prompts_dir = os.path.join(self.temp_dir, ".github", "prompts")
        os.makedirs(prompts_dir)
        stale_file = os.path.join(prompts_dir, "old_skill.prompt.md")
        with open(stale_file, "w") as f:
            f.write("stale content")

        _export_copilot_prompts(self.temp_dir)

        self.assertFalse(os.path.exists(stale_file))

    def test_empty_agents_dir_is_noop(self):
        """Calling on an agents dir with no skills or workflows is a no-op."""
        _export_copilot_prompts(self.temp_dir)
        prompts_dir = os.path.join(self.temp_dir, ".github", "prompts")
        self.assertFalse(os.path.exists(prompts_dir))

    def test_skill_subdir_with_skill_md(self):
        """A skill stored as a subdirectory with SKILL.md is correctly exported."""
        skill_dir = os.path.join(self.agents_dir, "skills", "advanced_debug")
        os.makedirs(skill_dir)
        with open(os.path.join(skill_dir, "SKILL.md"), "w") as f:
            f.write("Advanced debugging instructions")

        _export_copilot_prompts(self.temp_dir)

        prompt_path = os.path.join(self.temp_dir, ".github", "prompts", "advanced_debug.prompt.md")
        self.assertTrue(os.path.exists(prompt_path))
        with open(prompt_path) as f:
            self.assertEqual(f.read(), "Advanced debugging instructions")


if __name__ == "__main__":
    unittest.main()
