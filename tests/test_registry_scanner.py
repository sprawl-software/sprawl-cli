import unittest
import os
import shutil
import tempfile
from unittest.mock import patch

from sprawl.utils.registry_scanner import RegistryScanner


class TestRegistryScanner(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.workspace_dir = os.path.join(self.test_dir, "my-workspace")
        self.manifest_dir = os.path.join(self.workspace_dir, ".agents")
        os.makedirs(self.manifest_dir)
        self.manifest_path = os.path.join(self.manifest_dir, "sprawl_manifest.yml")

        # Create a mock global DNA vault
        self.dna_dir = os.path.join(self.test_dir, "mock-dna-vault")
        os.makedirs(os.path.join(self.dna_dir, "atoms"))
        os.makedirs(os.path.join(self.dna_dir, "skills"))
        os.makedirs(os.path.join(self.dna_dir, "rules"))

        # Add some mock DNA files
        with open(os.path.join(self.dna_dir, "atoms", "atom_a.json"), "w") as f:
            f.write("{}")
        with open(os.path.join(self.dna_dir, "atoms", "atom_b.json"), "w") as f:
            f.write("{}")
        with open(os.path.join(self.dna_dir, "atoms", ".hidden_atom"), "w") as f:
            f.write("{}")
        
        # Skill folder
        os.makedirs(os.path.join(self.dna_dir, "skills", "skill_one"))
        os.makedirs(os.path.join(self.dna_dir, "skills", "skill_two"))

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch("sprawl.utils.registry_scanner.get_active_dna_context")
    def test_scan_no_manifest(self, mock_get_context):
        """Verify scan handles missing sprawl_manifest.yml gracefully (all items unchecked)."""
        mock_get_context.return_value = self.dna_dir
        
        scanner = RegistryScanner(self.workspace_dir)
        res = scanner.scan()

        # Check atoms
        self.assertEqual(len(res["atoms"]), 2)
        self.assertEqual(res["atoms"][0], ("atom_a.json", False))
        self.assertEqual(res["atoms"][1], ("atom_b.json", False))

        # Check skills
        self.assertEqual(len(res["skills"]), 2)
        self.assertEqual(res["skills"][0], ("skill_one", False))
        self.assertEqual(res["skills"][1], ("skill_two", False))

    @patch("sprawl.utils.registry_scanner.get_active_dna_context")
    def test_scan_with_manifest_checked(self, mock_get_context):
        """Verify scan correctly identifies checked items based on manifest."""
        mock_get_context.return_value = self.dna_dir

        # Write a manifest
        with open(self.manifest_path, "w") as f:
            f.write("""
atoms:
  - atom_a.json
skills:
  - skill_two
""")

        scanner = RegistryScanner(self.workspace_dir)
        res = scanner.scan()

        # atom_a.json should be True, atom_b.json should be False
        self.assertEqual(res["atoms"][0], ("atom_a.json", True))
        self.assertEqual(res["atoms"][1], ("atom_b.json", False))

        # skill_one should be False, skill_two should be True
        self.assertEqual(res["skills"][0], ("skill_one", False))
        self.assertEqual(res["skills"][1], ("skill_two", True))


if __name__ == "__main__":
    unittest.main()
