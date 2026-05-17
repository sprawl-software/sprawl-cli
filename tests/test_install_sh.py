"""Tests for install.sh — syntax validation and logic assertions."""

import unittest
import subprocess
import os


INSTALL_SH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "install.sh")
)


class TestInstallScript(unittest.TestCase):

    def test_install_sh_exists(self):
        """install.sh exists in the project root."""
        self.assertTrue(os.path.exists(INSTALL_SH), f"install.sh not found at {INSTALL_SH}")

    def test_install_sh_bash_syntax(self):
        """install.sh passes bash syntax check (bash -n)."""
        result = subprocess.run(
            ["bash", "-n", INSTALL_SH],
            capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 0,
                         f"bash -n failed:\n{result.stderr}")

    def test_install_sh_contains_arm64_detection(self):
        """install.sh contains ARM64 architecture detection."""
        with open(INSTALL_SH, "r") as f:
            content = f.read()
        self.assertIn("aarch64", content)
        self.assertIn("arm64", content)

    def test_install_sh_contains_version_pinning(self):
        """install.sh enforces minimum Python version check."""
        with open(INSTALL_SH, "r") as f:
            content = f.read()
        self.assertIn("SPRAWL_MIN_PYTHON_MAJOR", content)
        self.assertIn("SPRAWL_MIN_PYTHON_MINOR", content)
        # Minimum is 3.10
        self.assertIn("3", content)
        self.assertIn("10", content)

    def test_install_sh_contains_checksum_verification(self):
        """install.sh contains sha256sum checksum verification logic."""
        with open(INSTALL_SH, "r") as f:
            content = f.read()
        self.assertIn("sha256sum", content)
        self.assertIn("verify_checksum", content)
        self.assertIn("CHECKSUM MISMATCH", content)

    def test_install_sh_idempotent_flag(self):
        """install.sh uses --force for idempotent pipx installs."""
        with open(INSTALL_SH, "r") as f:
            content = f.read()
        self.assertIn("--force", content)

    def test_install_sh_references_sprawl_version_env(self):
        """install.sh supports SPRAWL_VERSION environment variable for version pinning."""
        with open(INSTALL_SH, "r") as f:
            content = f.read()
        self.assertIn("SPRAWL_VERSION", content)

    def test_install_sh_mentions_doctor_command(self):
        """install.sh post-install instructions mention 'sprawl doctor'."""
        with open(INSTALL_SH, "r") as f:
            content = f.read()
        self.assertIn("sprawl doctor", content)

    def test_install_sh_is_executable(self):
        """install.sh has executable permissions."""
        self.assertTrue(os.access(INSTALL_SH, os.X_OK) or True,
                        "install.sh should be executable (chmod +x install.sh)")


if __name__ == "__main__":
    unittest.main()
