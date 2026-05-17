import unittest
import subprocess
import os
import sys
import shutil
import tempfile

class TestLifecycle(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        # Prepare dummy dna
        self.dummy_dna = os.path.join(self.test_dir, ".dummy_dna")
        os.makedirs(self.dummy_dna)
        # Create a basic structure
        os.makedirs(os.path.join(self.dummy_dna, "rules"))
        os.makedirs(os.path.join(self.dummy_dna, "skills"))
        with open(os.path.join(self.dummy_dna, "rules", "architecture.md"), "w") as f:
            f.write("# Architecture")
        with open(os.path.join(self.dummy_dna, "DESIGN.md"), "w") as f:
            f.write("# DESIGN")
        
        # init git repo
        subprocess.run(["git", "init", "-q"], cwd=self.dummy_dna, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=self.dummy_dna, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=self.dummy_dna, check=True)
        subprocess.run(["git", "add", "."], cwd=self.dummy_dna, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=self.dummy_dna, check=True)

        self.env = os.environ.copy()
        self.env["HOME"] = self.test_dir
        self.env["PYTHONPATH"] = self.original_cwd

    def tearDown(self):
        os.chdir(self.original_cwd)
        subprocess.run([sys.executable, "-m", "src.sprawl.cli", "clean-test", "--testmode"], env=self.env, check=False, capture_output=True)
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_end_to_end_lifecycle(self):
        # 1. sprawl init
        init_res = subprocess.run(
            [sys.executable, "-m", "src.sprawl.cli", "--testmode", "init", f"file://{self.dummy_dna}"],
            env=self.env, cwd=self.test_dir, capture_output=True, text=True
        )
        self.assertEqual(init_res.returncode, 0, f"Init failed: {init_res.stderr}\n{init_res.stdout}")

        # 2. sprawl create
        create_res = subprocess.run(
            [sys.executable, "-m", "src.sprawl.cli", "--testmode", "create", "test-project"],
            env=self.env, cwd=self.test_dir, capture_output=True, text=True
        )
        self.assertEqual(create_res.returncode, 0, f"Create failed: {create_res.stderr}\n{create_res.stdout}")
        
        project_dir = os.path.join(self.test_dir, "test-project")
        self.assertTrue(os.path.exists(project_dir), f"Directory not found! Output: {create_res.stdout}")

        # 3. sprawl add
        add_res = subprocess.run(
            [sys.executable, "-m", "src.sprawl.cli", "--testmode", "add", "architecture"],
            env=self.env, cwd=project_dir, capture_output=True, text=True
        )
        self.assertEqual(add_res.returncode, 0, f"Add failed: {add_res.stderr}\n{add_res.stdout}")

        # 4. sprawl sync
        sync_res = subprocess.run(
            [sys.executable, "-m", "src.sprawl.cli", "--testmode", "sync"],
            env=self.env, cwd=project_dir, capture_output=True, text=True
        )
        self.assertEqual(sync_res.returncode, 0, f"Sync failed: {sync_res.stderr}\n{sync_res.stdout}")
        self.assertTrue(os.path.exists(os.path.join(project_dir, ".agents", "rules", "architecture.md")), f"File missing. Sync out: {sync_res.stdout} err: {sync_res.stderr}")

        # 5. sprawl status
        status_res = subprocess.run(
            [sys.executable, "-m", "src.sprawl.cli", "--testmode", "status"],
            env=self.env, cwd=project_dir, capture_output=True, text=True
        )
        self.assertEqual(status_res.returncode, 0, f"Status failed: {status_res.stderr}\n{status_res.stdout}")
        self.assertIn("architecture.md", status_res.stdout)

if __name__ == "__main__":
    unittest.main()
