import unittest
import os
import tempfile
import shutil
from src.sprawl.generators.agents_md import generate_agents_md

class TestGenerators(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.output_path = os.path.join(self.test_dir, "AGENTS.md")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_generate_agents_md_with_persona(self):
        reqs = {
            "rules": ["eng.md"],
            "skills": ["persona-tester", "tool1"],
            "atoms": [],
            "molecules": [],
            "workflows": []
        }
        persona_content = "# I am a Tester\nI test things."
        workspace_path = "/path/to/workspace"
        
        generate_agents_md(self.output_path, reqs, workspace_path, persona_content)
        
        self.assertTrue(os.path.exists(self.output_path))
        with open(self.output_path, "r") as f:
            content = f.read()
            
        self.assertIn("# Persona Overrides", content)
        self.assertIn("I am a Tester", content)
        self.assertIn("## Environment Boundaries", content)
        self.assertIn(f"**Workspace Root:** `/path/to/workspace`", content)
        self.assertIn("Strict Isolation:", content)
        self.assertIn("### Rules", content)
        self.assertIn("- eng.md", content)
        self.assertNotIn("🛑", content)

    def test_generate_agents_md_no_persona(self):
        reqs = {
            "rules": ["eng.md"],
            "skills": ["tool1"],
            "atoms": [],
            "molecules": [],
            "workflows": []
        }
        workspace_path = "/path/to/workspace"
        
        generate_agents_md(self.output_path, reqs, workspace_path, None)
        
        self.assertTrue(os.path.exists(self.output_path))
        with open(self.output_path, "r") as f:
            content = f.read()
            
        self.assertIn("# Workspace Agent Context", content)
        self.assertIn("## Environment Boundaries", content)
        self.assertIn("### Rules", content)

if __name__ == "__main__":
    unittest.main()
