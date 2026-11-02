"""In-process unit and integration tests for sprawl token-size (TASK-023-02)."""

from __future__ import annotations

import contextlib
import io
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from sprawl.analyzers.context import (
    _read_bounded_text,
    analyze_mcp_json,
    analyze_rule_text,
    analyze_skill_text,
    estimate_tokens,
    scan_workspace_context,
)
from sprawl.cli import get_parser
from sprawl.commands.token_size import cmd_token_size
from sprawl.config import config
from sprawl.exceptions import SprawlError


class TestTokenSizeAuditor(unittest.TestCase):
    """Verifies Turn-1 zero-hop vs. progressive context token auditing."""

    def tearDown(self) -> None:
        config.json_logging = False

    def test_estimate_tokens_deterministic_and_accurate(self) -> None:
        """Verify stdlib BPE approximation is deterministic and within expected token bounds."""
        self.assertEqual(estimate_tokens(""), 0)
        self.assertEqual(estimate_tokens("   \n\t  "), 0)

        prose = "Enforce zero-trust path containment across all MCP workspace mounts."
        prose_tokens = estimate_tokens(prose)
        self.assertGreaterEqual(prose_tokens, 10)
        self.assertLessEqual(prose_tokens, 25)
        self.assertEqual(prose_tokens, estimate_tokens(prose))

        code_snippet = "def check(x: int) -> bool:\n    return x >= 0\n"
        self.assertGreater(estimate_tokens(code_snippet), 8)

    def test_analyze_rule_text_zero_hop_vs_progressive(self) -> None:
        """Verify alwaysApply rules count toward Always-On (Turn 1) vs scoped rules in Lazy-Loaded."""
        always_rule = (
            "---\n"
            "name: Security Rule\n"
            "alwaysApply: true\n"
            "---\n"
            "# Zero-Trust Rule\nNever expose raw credentials.\n"
        )
        m_always = analyze_rule_text(".agents/rules/security.md", always_rule)
        self.assertEqual(m_always.layer, "rule")
        self.assertGreater(m_always.zero_hop_tokens, 10)
        self.assertEqual(m_always.progressive_tokens, 0)
        self.assertEqual(m_always.note, "always-on (loaded every turn)")

        scoped_rule = (
            "---\n"
            "name: Python Rule\n"
            "alwaysApply: false\n"
            "activation: glob\n"
            "---\n"
            "# Python Standards\nUse strict type annotations in all modules.\n"
        )
        m_scoped = analyze_rule_text(".agents/rules/python.md", scoped_rule)
        self.assertEqual(m_scoped.zero_hop_tokens, 0)
        self.assertGreater(m_scoped.progressive_tokens, 10)
        self.assertEqual(m_scoped.note, "on-demand (loaded when relevant)")

    def test_analyze_skill_text_splits_catalog_header_and_body(self) -> None:
        """Verify SKILL.md splits frontmatter catalog header (Turn 1) from markdown body (On-Demand)."""
        skill_md = (
            "---\n"
            "name: sec-auditor\n"
            "description: Static vulnerability and license compliance scanner.\n"
            "---\n"
            "# Security Auditor Skill\n\n"
            + ("Perform deep AST inspection and verify DORA compliance controls. " * 20)
        )
        metric = analyze_skill_text(".agents/skills/sec-auditor/SKILL.md", skill_md)
        self.assertEqual(metric.layer, "skill")
        self.assertGreater(metric.zero_hop_tokens, 0)
        self.assertLess(metric.zero_hop_tokens, 30)
        self.assertGreater(metric.progressive_tokens, 150)
        self.assertEqual(metric.note, "index on Turn 1 + body on-demand")

    def test_symlinked_ide_bindings_add_zero_duplicate_tokens(self) -> None:
        """Verify symlinked IDE bindings add 0 duplicate tokens while physical copies flag overhead."""
        with TemporaryDirectory() as tmp:
            ws = Path(tmp)
            agents_text = "# Canonical AGENTS Manifest\n" + ("Follow strict ReAct loops. " * 15)
            agents_file = ws / "AGENTS.md"
            agents_file.write_text(agents_text, encoding="utf-8")

            # Symlinked bindings -> 0 duplicate tokens
            (ws / ".cursorrules").symlink_to(agents_file)
            (ws / "CLAUDE.md").symlink_to(agents_file)

            # Physical copy -> duplicate overhead counted
            (ws / ".windsurfrules").write_text(agents_text, encoding="utf-8")

            report = scan_workspace_context(ws)
            by_path = {a.relative_path: a for a in report.artifacts}

            base_tokens = by_path["AGENTS.md"].zero_hop_tokens
            self.assertGreater(base_tokens, 40)
            self.assertEqual(by_path[".cursorrules"].zero_hop_tokens, 0)
            self.assertTrue(by_path[".cursorrules"].is_symlink)
            self.assertEqual(by_path["CLAUDE.md"].zero_hop_tokens, 0)
            self.assertEqual(by_path[".windsurfrules"].zero_hop_tokens, base_tokens)
            self.assertIn("duplicate file", by_path[".windsurfrules"].note)

    def test_symlink_containment_and_circular_loop_safety(self) -> None:
        """Verify out-of-bounds symlinks, circular symlink loops, and oversized files are skipped."""
        with TemporaryDirectory() as outer_tmp:
            outer = Path(outer_tmp)
            secret_file = outer / "external_secret.txt"
            secret_file.write_text("TOP_SECRET_CREDENTIAL_PAYLOAD", encoding="utf-8")

            ws = outer / "workspace"
            ws.mkdir()

            # Out-of-bounds symlink pointing outside workspace
            (ws / "CLAUDE.md").symlink_to(secret_file)

            # Circular symlink loop: GEMINI.md <-> AGENTS.md
            (ws / "GEMINI.md").symlink_to(ws / "AGENTS.md")
            (ws / "AGENTS.md").symlink_to(ws / "GEMINI.md")

            # Oversized / binary file safety in _read_bounded_text
            small_file = ws / ".cursorrules"
            small_file.write_text("Valid local rule", encoding="utf-8")
            self.assertIsNone(_read_bounded_text(small_file, max_bytes=4))

            report = scan_workspace_context(ws)
            paths = {a.relative_path for a in report.artifacts}
            self.assertNotIn("CLAUDE.md", paths)
            self.assertNotIn("GEMINI.md", paths)
            self.assertNotIn("AGENTS.md", paths)
            self.assertIn(".cursorrules", paths)

    def test_scan_workspace_context_executes_under_100ms(self) -> None:
        """Verify 4-layer workspace context scan completes in under 100ms with accurate ratios."""
        with TemporaryDirectory() as tmp:
            ws = Path(tmp)
            (ws / "AGENTS.md").write_text("# Root Agent Manifest\nCore rules.\n", encoding="utf-8")
            rules_dir = ws / ".agents" / "rules"
            skills_dir = ws / ".agents" / "skills" / "arch-doc"
            rules_dir.mkdir(parents=True)
            skills_dir.mkdir(parents=True)

            (rules_dir / "always.md").write_text(
                "---\nalwaysApply: true\n---\nAlways active rule.\n", encoding="utf-8"
            )
            (rules_dir / "scoped.md").write_text(
                "---\nalwaysApply: false\n---\n" + ("Progressive rule content. " * 30),
                encoding="utf-8",
            )
            (skills_dir / "SKILL.md").write_text(
                "---\nname: arch-doc\ndescription: Generates architecture diagrams.\n---\n"
                + ("Detailed skill instructions for Mermaid diagrams. " * 40),
                encoding="utf-8",
            )
            mcp_payload = {
                "mcpServers": {
                    "sprawl-workspace-fs": {
                        "command": "python3",
                        "args": ["-m", "sprawl.mcp_server"],
                    }
                }
            }
            (ws / ".agents" / "mcp_config.json").write_text(
                json.dumps(mcp_payload), encoding="utf-8"
            )

            report = scan_workspace_context(ws)
            self.assertLess(report.elapsed_ms, 100.0)
            self.assertGreater(report.zero_hop_tokens, 0)
            self.assertGreater(report.progressive_tokens, report.zero_hop_tokens)
            self.assertGreater(report.pruned_ratio_pct, 50.0)

    def test_cmd_token_size_max_tokens_gate_passes_and_fails(self) -> None:
        """Verify --max-tokens CI budget gate passes under limit and raises SprawlError above limit."""
        with TemporaryDirectory() as tmp:
            ws = Path(tmp)
            (ws / "AGENTS.md").write_text(
                "# Workspace Manifest\n" + (" Mandatory governance invariant." * 20),
                encoding="utf-8",
            )
            # High budget passes
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                cmd_token_size(str(ws), detailed=False, max_tokens=50000)

            # Low budget raises SprawlError
            with contextlib.redirect_stdout(buf), self.assertRaises(SprawlError) as ctx:
                cmd_token_size(str(ws), detailed=False, max_tokens=5)
            self.assertIn("Context budget exceeded", str(ctx.exception))

            # Non-existent directory raises SprawlError
            with self.assertRaises(SprawlError):
                cmd_token_size(str(ws / "nonexistent_dir"))

    def test_cmd_token_size_detailed_and_json_output(self) -> None:
        """Verify --detailed Rich rendering and --json structured output schema."""
        with TemporaryDirectory() as tmp:
            ws = Path(tmp)
            (ws / "AGENTS.md").write_text("# Manifest\n", encoding="utf-8")
            rules_dir = ws / ".agents" / "rules"
            rules_dir.mkdir(parents=True)
            (rules_dir / "python.md").write_text(
                "---\nalwaysApply: false\n---\nUse strict typing.\n", encoding="utf-8"
            )
            mcp_metric = analyze_mcp_json("mcp_config.json", "{invalid json")
            self.assertEqual(mcp_metric.note, "invalid JSON schema")

            # Rich detailed table rendering (json_logging=False)
            config.json_logging = False
            rich_buf = io.StringIO()
            with contextlib.redirect_stdout(rich_buf):
                cmd_token_size(str(ws), detailed=True)

            # Structured JSON rendering (json_logging=True)
            config.json_logging = True
            json_buf = io.StringIO()
            with contextlib.redirect_stdout(json_buf):
                cmd_token_size(str(ws), detailed=True)

            payload = json.loads(json_buf.getvalue().strip())
            self.assertIn("zero_hop_tokens", payload)
            self.assertIn("progressive_tokens", payload)
            self.assertIn("layers", payload)
            self.assertEqual(len(payload["layers"]), 4)

    def test_cli_context_alias_routes_to_token_size(self) -> None:
        """Verify sprawl context alias accepts --detailed and --max-tokens flags."""
        parser = get_parser()
        args = parser.parse_args(["context", "--detailed", "--max-tokens", "4096"])
        self.assertIn(args.command, ("token-size", "context"))
        self.assertTrue(args.detailed)
        self.assertEqual(args.max_tokens, 4096)


if __name__ == "__main__":
    unittest.main()
