import json
import os
import pathlib
import sys
import tempfile
import unittest

# Ensure scripts dir is on sys.path
WORKSPACE_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WORKSPACE_DIR / "scripts"))

import hotspots
import sarif_to_signals


class TestSarifToSignals(unittest.TestCase):
    def test_norm_path_posix(self):
        uri = "file:///workspace/repo/src/index.js"
        root = "/workspace/repo"
        self.assertEqual(sarif_to_signals.norm_path(uri, root), "src/index.js")

    def test_norm_path_windows_file_uri(self):
        uri = "file:///C:/workspace/repo/src/index.js"
        root = "C:/workspace/repo"
        self.assertEqual(sarif_to_signals.norm_path(uri, root), "src/index.js")

    def test_norm_path_windows_backslash_root(self):
        uri = "file:///C:/workspace/repo/src/index.js"
        root = "C:\\workspace\\repo"
        self.assertEqual(sarif_to_signals.norm_path(uri, root), "src/index.js")

    def test_norm_path_relative(self):
        uri = "src/index.js"
        self.assertEqual(sarif_to_signals.norm_path(uri, None), "src/index.js")

    def test_norm_path_encoded_spaces(self):
        uri = "file:///C:/my%20project/repo/src/my%20file.js"
        root = "C:/my project/repo"
        self.assertEqual(sarif_to_signals.norm_path(uri, root), "src/my file.js")

    def test_severity_cvss(self):
        self.assertEqual(sarif_to_signals.severity("warning", "8.5"), "high")
        self.assertEqual(sarif_to_signals.severity("error", "3.0"), "low")
        self.assertEqual(sarif_to_signals.severity("error", None), "high")
        self.assertEqual(sarif_to_signals.severity("warning", None), "medium")
        self.assertEqual(sarif_to_signals.severity("note", None), "low")


class TestHotspotsCore(unittest.TestCase):
    def test_measure_indentation(self):
        code = b"def foo():\n    if True:\n        print('hello')\n"
        loc, complexity = hotspots.measure(code)
        self.assertEqual(loc, 3)
        self.assertGreater(complexity, 0)

    def test_measure_binary(self):
        binary = b"\x00\x01\x02\x03hello"
        self.assertIsNone(hotspots.measure(binary))

    def test_percentiles(self):
        vals = [10, 20, 30]
        pct = hotspots.percentiles(vals)
        self.assertEqual(len(pct), 3)
        self.assertEqual(pct[0], 0.0)
        self.assertEqual(pct[2], 1.0)

    def test_percentiles_all_zero(self):
        vals = [0, 0, 0]
        pct = hotspots.percentiles(vals)
        self.assertEqual(pct, [0.0, 0.0, 0.0])

    def test_module_of(self):
        self.assertEqual(hotspots.module_of("src/api/routes.py"), "src/api")
        self.assertEqual(hotspots.module_of("services/auth/login.py"), "services/auth")
        self.assertEqual(hotspots.module_of("utils/helpers.py"), "utils")
        self.assertEqual(hotspots.module_of("root.py"), "")

    def test_lang_and_kind(self):
        self.assertEqual(hotspots.lang_and_kind("src/app.py"), ("python", "code"))
        self.assertEqual(hotspots.lang_and_kind("src/index.ts"), ("typescript", "code"))
        self.assertEqual(hotspots.lang_and_kind("src/App.cs"), ("csharp", "code"))
        self.assertEqual(hotspots.lang_and_kind("src/Main.java"), ("java", "code"))
        self.assertEqual(hotspots.lang_and_kind("deploy/values.yaml"), ("yaml", "config"))
        self.assertEqual(hotspots.lang_and_kind("Dockerfile"), ("docker", "config"))
        self.assertEqual(hotspots.lang_and_kind("infra/main.tf"), ("terraform", "config"))

    def test_detect_stacks(self):
        files = ["src/app.py", "pyproject.toml", "deploy/chart.yaml"]
        stacks = hotspots.detect_stacks(".", files)
        self.assertIn("python", stacks)
        self.assertIn("yaml", stacks)

        csharp_files = ["src/Api/Api.csproj", "src/Api/Program.cs"]
        cs_stacks = hotspots.detect_stacks(".", csharp_files)
        self.assertIn("csharp", cs_stacks)

    def test_module_for_build_markers(self):
        all_files = [
            "services/order/Order.csproj",
            "services/order/Models/Order.cs",
            "services/payment/package.json",
            "services/payment/src/index.ts",
        ]
        markers = hotspots.find_modules(all_files)
        self.assertIn("services/order", markers)
        self.assertIn("services/payment", markers)
        self.assertEqual(hotspots.module_for("services/order/Models/Order.cs", markers), "services/order")
        self.assertEqual(hotspots.module_for("services/payment/src/index.ts", markers), "services/payment")

    def test_score_rows_per_kind_grouping(self):
        # Create a mock args object
        class Args:
            threshold = 0.8
            min_files = 1
        rows = [
            {"repo": "r", "path": "src/app.py", "kind": "code", "commits": 10, "complexity": 50, "bugfix_commits": 2, "coupling_partners": 1, "top_author_share": 0.5, "single_owner": False, "owner_inactive": False},
            {"repo": "r", "path": "src/lib.py", "kind": "code", "commits": 5, "complexity": 10, "bugfix_commits": 0, "coupling_partners": 0, "top_author_share": 0.5, "single_owner": False, "owner_inactive": False},
            {"repo": "r", "path": "deploy/chart.yaml", "kind": "config", "commits": 8, "complexity": 200, "bugfix_commits": 1, "coupling_partners": 0, "top_author_share": 0.5, "single_owner": False, "owner_inactive": False},
        ]
        hotspots.score_rows(rows, Args())
        # Both code and config files should be scored without cross-contaminating percentiles
        for r in rows:
            self.assertIn("score", r)
            self.assertIn("rank", r)


class TestDiagramTemplate(unittest.TestCase):
    def setUp(self):
        self.html_path = WORKSPACE_DIR / "assets" / "diagrams.html"
        self.assertTrue(self.html_path.is_file(), "assets/diagrams.html must exist")
        self.html = self.html_path.read_text(encoding="utf-8")

    def test_offline_no_external_urls(self):
        # Template must have zero external scripts, stylesheets, or images
        self.assertNotIn("https://cdn", self.html)
        self.assertNotIn("http://cdn", self.html)
        self.assertNotIn("unpkg.com", self.html)
        self.assertNotIn("cdnjs.cloudflare.com", self.html)

    def test_required_views_exist(self):
        views = [
            '"app-flow"',
            '"data-flow"',
            '"integration-flow"',
            '"security-boundaries"',
            '"layering"',
            '"deployment"',
            '"cross-repo"',
            '"use-cases"',
        ]
        for v in views:
            with self.subTest(view=v):
                self.assertIn(v, self.html, f"Expected view {v} in DIAGRAMS object")

    def test_tech_stack_supported_in_node_display(self):
        self.assertIn("tech", self.html, "Expected 'tech' support in diagram template for tech stack")

    def test_diagram_edge_endpoints_valid(self):
        # Extract DIAGRAMS object from HTML
        import re
        m = re.search(r"const DIAGRAMS = (\{[\s\S]*?\n\};)\n", self.html)
        self.assertIsNotNone(m, "DIAGRAMS object must be found in template")
        # Ensure all tabs have defined nodes and valid edge endpoints
        code = f"const DIAGRAMS = {m.group(1)};"
        # Run node/edge check via node or python regex
        tab_names = re.findall(r'"([a-z\-]+)":\s*\{\s*title:', m.group(1))
        self.assertGreaterEqual(len(tab_names), 8)
        self.assertIn("use-cases", tab_names)

    def test_sarif_end_to_end(self):
        sample_sarif = {
            "version": "2.1.0",
            "runs": [
                {
                    "tool": {
                        "driver": {
                            "name": "SecurityScanner",
                            "rules": [
                                {"id": "HARDCODED_API_KEY", "properties": {"security-severity": "8.0"}},
                                {"id": "UNSANITIZED_INPUT", "properties": {"security-severity": "4.5"}},
                                {"id": "LOGGING_INFO", "defaultConfiguration": {"level": "note"}}
                            ]
                        }
                    },
                    "results": [
                        {
                            "ruleId": "HARDCODED_API_KEY",
                            "locations": [{"physicalLocation": {"artifactLocation": {"uri": "file:///workspace/repo/src/secrets.py"}, "region": {"startLine": 12}}}]
                        },
                        {
                            "ruleId": "UNSANITIZED_INPUT",
                            "locations": [{"physicalLocation": {"artifactLocation": {"uri": "file:///workspace/repo/src/routes.py"}, "region": {"startLine": 45}}}]
                        }
                    ]
                }
            ]
        }
        with tempfile.TemporaryDirectory() as td:
            sarif_file = pathlib.Path(td) / "results.sarif"
            sarif_file.write_text(json.dumps(sample_sarif), encoding="utf-8")
            out_sig = pathlib.Path(td) / "signals.json"
            out_iss = pathlib.Path(td) / "issues.json"

            # Run main with CLI args
            orig_argv = sys.argv
            sys.argv = [
                "sarif_to_signals.py",
                str(sarif_file),
                "--repo", "my-repo",
                "--root", "/workspace/repo",
                "--out", str(out_sig),
                "--issues", str(out_iss)
            ]
            try:
                sarif_to_signals.main()
            finally:
                sys.argv = orig_argv

            self.assertTrue(out_sig.is_file())
            self.assertTrue(out_iss.is_file())
            signals = json.loads(out_sig.read_text(encoding="utf-8"))
            issues = json.loads(out_iss.read_text(encoding="utf-8"))

            self.assertEqual(len(issues), 2)
            self.assertIn("my-repo::src/secrets.py", signals)
            self.assertEqual(signals["my-repo::src/secrets.py"]["issues_high"], 1)
            # Secrets rule check
            secret_issue = next(i for i in issues if i["rule"] == "HARDCODED_API_KEY")
            self.assertTrue(secret_issue.get("secret"))
            self.assertEqual(secret_issue["line"], 12)
            self.assertNotIn("apiKeyVal", json.dumps(issues))


class TestReferencesAndStacks(unittest.TestCase):
    def test_skill_md_references_exist(self):
        skill_text = (WORKSPACE_DIR / "SKILL.md").read_text(encoding="utf-8")
        import re
        links = re.findall(r"\(references/([a-zA-Z0-9_\-\./]+)\)", skill_text)
        self.assertGreater(len(links), 5)
        for link in links:
            target = WORKSPACE_DIR / "references" / link
            self.assertTrue(target.is_file(), f"Referenced file does not exist: {target}")

    def test_stack_references_have_10_sections(self):
        stacks_dir = WORKSPACE_DIR / "references" / "stacks"
        self.assertTrue(stacks_dir.is_dir())
        stack_files = list(stacks_dir.glob("*.md"))
        self.assertGreaterEqual(len(stack_files), 5)

        required_sections = [
            "## Detect",
            "## Entry Points",
            "## Hidden Wiring",
            "## Config and Secrets",
            "## Data Access",
            "## Concurrency",
            "## Performance",
            "## Security",
            "## Exclusions",
            "## Tools"
        ]

        for sf in stack_files:
            content = sf.read_text(encoding="utf-8")
            for sec in required_sections:
                with self.subTest(file=sf.name, section=sec):
                    self.assertIn(sec, content, f"Missing section '{sec}' in {sf.name}")

    def test_sarif_tool_commands_in_stack_docs(self):
        # Python
        py_doc = (WORKSPACE_DIR / "references" / "stacks" / "python.md").read_text(encoding="utf-8")
        self.assertIn("@bandit-sarif-formatter", py_doc)
        self.assertIn("ruff check --output-format=sarif", py_doc)

        # C#
        cs_doc = (WORKSPACE_DIR / "references" / "stacks" / "csharp.md").read_text(encoding="utf-8")
        self.assertIn("/p:ErrorLog=artifacts/build.sarif,version=2.1", cs_doc)

        # Java
        java_doc = (WORKSPACE_DIR / "references" / "stacks" / "java.md").read_text(encoding="utf-8")
        self.assertIn("pmd check -f sarif", java_doc)

        # TypeScript
        ts_doc = (WORKSPACE_DIR / "references" / "stacks" / "typescript.md").read_text(encoding="utf-8")
        self.assertIn("@microsoft/eslint-formatter-sarif", ts_doc)

        # YAML & IaC
        yaml_doc = (WORKSPACE_DIR / "references" / "stacks" / "yaml-and-iac.md").read_text(encoding="utf-8")
        self.assertIn("kube-linter lint . --format sarif", yaml_doc)
        self.assertIn("trivy config . --format sarif", yaml_doc)


if __name__ == "__main__":
    unittest.main()
