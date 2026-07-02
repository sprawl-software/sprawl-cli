import unittest
import os
import shutil
import tempfile
import sys
from unittest.mock import patch

# Ensure the local src is available
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from src.sprawl.utils.registry_scanner import RegistryScanner


class TestRegistryScanner(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.workspace_dir = os.path.join(self.test_dir, "my-workspace")
        self.manifest_dir = os.path.join(self.workspace_dir, ".agents")
        os.makedirs(self.manifest_dir)
        self.manifest_path = os.path.join(self.manifest_dir, "sprawl_manifest.yml")

        # Create a mock global DNA vault
        self.dna_dir = os.path.join(self.test_dir, "mock-dna-vault")
        os.makedirs(os.path.join(self.dna_dir, "rules"))
        os.makedirs(os.path.join(self.dna_dir, "skills"))

        # Add some mock DNA files
        with open(os.path.join(self.dna_dir, "rules", "rule_a.md"), "w") as f:
            f.write("# Rule A")
        with open(os.path.join(self.dna_dir, "rules", "rule_b.md"), "w") as f:
            f.write("# Rule B")
        with open(os.path.join(self.dna_dir, "rules", ".hidden_rule"), "w") as f:
            f.write("# Hidden")
        
        # Skill folder
        os.makedirs(os.path.join(self.dna_dir, "skills", "skill_one"))
        os.makedirs(os.path.join(self.dna_dir, "skills", "skill_two"))

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch("src.sprawl.utils.registry_scanner.get_active_dna_context")
    def test_scan_no_manifest(self, mock_get_context):
        """Verify scan handles missing sprawl_manifest.yml gracefully (all items unchecked)."""
        mock_get_context.return_value = self.dna_dir
        
        scanner = RegistryScanner(self.workspace_dir)
        res = scanner.scan()

        # Check rules
        self.assertEqual(len(res["rules"]), 2)
        self.assertEqual(res["rules"][0], ("rule_a.md", False))
        self.assertEqual(res["rules"][1], ("rule_b.md", False))

        # Check skills
        self.assertEqual(len(res["skills"]), 2)
        self.assertEqual(res["skills"][0], ("skill_one", False))
        self.assertEqual(res["skills"][1], ("skill_two", False))

    @patch("src.sprawl.utils.registry_scanner.get_active_dna_context")
    def test_scan_with_manifest_checked(self, mock_get_context):
        """Verify scan correctly identifies checked items based on manifest."""
        mock_get_context.return_value = self.dna_dir

        # Write a manifest
        with open(self.manifest_path, "w") as f:
            f.write("""
rules:
  - rule_a.md
skills:
  - skill_two
""")

        scanner = RegistryScanner(self.workspace_dir)
        res = scanner.scan()

        # rule_a.md should be True, rule_b.md should be False
        self.assertEqual(res["rules"][0], ("rule_a.md", True))
        self.assertEqual(res["rules"][1], ("rule_b.md", False))

        # skill_one should be False, skill_two should be True
        self.assertEqual(res["skills"][0], ("skill_one", False))
        self.assertEqual(res["skills"][1], ("skill_two", True))


if __name__ == "__main__":
    unittest.main()
