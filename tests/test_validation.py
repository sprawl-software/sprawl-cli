"""Tests for validation module — TASK-001-05 (pydantic drop) + TASK-001-06 (pyyaml drop)."""

import os
import sys
import json
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from src.sprawl.validation import (
    parse_yaml_frontmatter,
    AtomSchema,
    SkillSchema,
    MoleculeSchema,
    validate_dna_directory,
)
from src.sprawl.exceptions import SprawlError


class TestParseYamlFrontmatter(unittest.TestCase):
    """Tests for the stdlib YAML frontmatter parser."""

    def test_basic_key_value(self) -> None:
        content = "---\nname: Test\ndescription: A test\n---\n# Body"
        result = parse_yaml_frontmatter(content)
        self.assertEqual(result["name"], "Test")
        self.assertEqual(result["description"], "A test")

    def test_no_frontmatter(self) -> None:
        content = "# Just a markdown file\nNo frontmatter here."
        result = parse_yaml_frontmatter(content)
        self.assertEqual(result, {})

    def test_empty_frontmatter(self) -> None:
        content = "---\n---\n# Body"
        result = parse_yaml_frontmatter(content)
        self.assertEqual(result, {})

    def test_boolean_values(self) -> None:
        content = "---\nenabled: true\ndisabled: false\nyes_val: yes\nno_val: no\n---"
        result = parse_yaml_frontmatter(content)
        self.assertTrue(result["enabled"])
        self.assertFalse(result["disabled"])
        self.assertTrue(result["yes_val"])
        self.assertFalse(result["no_val"])

    def test_null_values(self) -> None:
        content = "---\nempty: null\nnone_val: none\ntilde: ~\n---"
        result = parse_yaml_frontmatter(content)
        self.assertIsNone(result["empty"])
        self.assertIsNone(result["none_val"])
        self.assertIsNone(result["tilde"])

    def test_numeric_values(self) -> None:
        content = "---\ncount: 42\npi: 3.14\n---"
        result = parse_yaml_frontmatter(content)
        self.assertEqual(result["count"], 42)
        self.assertAlmostEqual(result["pi"], 3.14)

    def test_list_values(self) -> None:
        content = "---\nitems:\n- alpha\n- beta\n- gamma\n---"
        result = parse_yaml_frontmatter(content)
        self.assertEqual(result["items"], ["alpha", "beta", "gamma"])

    def test_quoted_strings(self) -> None:
        content = '---\ntitle: "Hello World"\nsingle: \'Test\'\n---'
        result = parse_yaml_frontmatter(content)
        self.assertEqual(result["title"], "Hello World")
        self.assertEqual(result["single"], "Test")

    def test_real_skill_frontmatter(self) -> None:
        """Parse actual SKILL.md-style frontmatter."""
        content = """---
name: Master Engineer
type: skill
domain: engineering
version: 2026.5.2
description: Lens override for the Master Engineer persona.
activation: model_decision
---

# System Prompt
Content here.
"""
        result = parse_yaml_frontmatter(content)
        self.assertEqual(result["name"], "Master Engineer")
        self.assertEqual(result["type"], "skill")
        self.assertEqual(result["version"], "2026.5.2")
        self.assertEqual(result["description"], "Lens override for the Master Engineer persona.")

    def test_comment_lines_ignored(self) -> None:
        content = "---\n# This is a comment\nname: Test\n---"
        result = parse_yaml_frontmatter(content)
        self.assertEqual(result["name"], "Test")
        self.assertNotIn("#", str(result.keys()))


class TestSchemaValidation(unittest.TestCase):
    """Tests for dataclass schema validation (pydantic replacement)."""

    def test_atom_schema_valid(self) -> None:
        schema = AtomSchema(name="test", description="A test atom", type="config")
        schema.validate()  # Should not raise

    def test_atom_schema_missing_field(self) -> None:
        schema = AtomSchema(name="", description="A test", type="config")
        with self.assertRaises(ValueError):
            schema.validate()

    def test_skill_schema_valid(self) -> None:
        schema = SkillSchema(name="test", description="A skill")
        schema.validate()

    def test_skill_schema_empty_name(self) -> None:
        schema = SkillSchema(name="", description="A skill")
        with self.assertRaises(ValueError):
            schema.validate()

    def test_molecule_schema_valid(self) -> None:
        schema = MoleculeSchema(name="test", version="1.0.0", atoms=["a", "b"])
        schema.validate()

    def test_molecule_schema_bad_atoms(self) -> None:
        schema = MoleculeSchema(name="test", version="1.0.0", atoms="not_a_list")
        with self.assertRaises(ValueError):
            schema.validate()

    def test_molecule_schema_empty_version(self) -> None:
        schema = MoleculeSchema(name="test", version="  ", atoms=[])
        with self.assertRaises(ValueError):
            schema.validate()


class TestValidateDnaDirectory(unittest.TestCase):
    """Tests for the DNA directory validation engine."""

    def test_valid_dna_directory(self) -> None:
        """Valid DNA directory passes without errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            atoms_dir = os.path.join(tmpdir, "atoms")
            os.makedirs(atoms_dir)
            atom_file = os.path.join(atoms_dir, "test_atom.json")
            with open(atom_file, "w") as f:
                json.dump({"name": "test", "description": "A test", "type": "config"}, f)

            validate_dna_directory(tmpdir)  # Should not raise

    def test_invalid_atom_raises(self) -> None:
        """Invalid atom data triggers SprawlError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            atoms_dir = os.path.join(tmpdir, "atoms")
            os.makedirs(atoms_dir)
            atom_file = os.path.join(atoms_dir, "bad_atom.json")
            with open(atom_file, "w") as f:
                json.dump({"name": "", "description": "", "type": ""}, f)

            with self.assertRaises(SprawlError):
                validate_dna_directory(tmpdir)

    def test_valid_skill_md(self) -> None:
        """Valid SKILL.md with frontmatter passes validation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skills_dir = os.path.join(tmpdir, "skills", "test-skill")
            os.makedirs(skills_dir)
            skill_file = os.path.join(skills_dir, "SKILL.md")
            with open(skill_file, "w") as f:
                f.write("---\nname: Test\ndescription: A test skill\n---\n# Content")

            validate_dna_directory(tmpdir)

    def test_invalid_skill_md_raises(self) -> None:
        """SKILL.md with empty name triggers SprawlError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skills_dir = os.path.join(tmpdir, "skills", "bad-skill")
            os.makedirs(skills_dir)
            skill_file = os.path.join(skills_dir, "SKILL.md")
            with open(skill_file, "w") as f:
                f.write("---\nname:\ndescription:\n---\n# Content")

            with self.assertRaises(SprawlError):
                validate_dna_directory(tmpdir)

    def test_malformed_json_raises(self) -> None:
        """Malformed JSON file triggers SprawlError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            atoms_dir = os.path.join(tmpdir, "atoms")
            os.makedirs(atoms_dir)
            atom_file = os.path.join(atoms_dir, "bad.json")
            with open(atom_file, "w") as f:
                f.write("{not valid json")

            with self.assertRaises(SprawlError):
                validate_dna_directory(tmpdir)

    def test_git_directory_skipped(self) -> None:
        """Files inside .git are ignored during validation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            git_dir = os.path.join(tmpdir, ".git", "objects")
            os.makedirs(git_dir)
            with open(os.path.join(git_dir, "pack.json"), "w") as f:
                f.write("{corrupted}")

            validate_dna_directory(tmpdir)  # Should not raise


if __name__ == "__main__":
    unittest.main()
