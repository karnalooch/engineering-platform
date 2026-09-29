from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts import gumball


class GumballTests(unittest.TestCase):
    def test_apply_is_dry_run_by_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            results = gumball.apply_baseline(root, "standard", write=False)
            self.assertTrue(all("dry-run" in result for _, result in results))
            self.assertFalse((root / "AGENTS.md").exists())

    def test_apply_never_overwrites_existing_agents(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            original = "# local rules\n"
            (root / "AGENTS.md").write_text(original, encoding="utf-8")

            gumball.apply_baseline(root, "standard", write=True)

            self.assertEqual((root / "AGENTS.md").read_text(encoding="utf-8"), original)
            self.assertTrue((root / "gumball.yaml").exists())
            self.assertTrue((root / "docs" / "README.md").exists())
            self.assertTrue((root / "docs" / "DIAGRAM_STYLE.md").exists())
            self.assertTrue((root / ".gumball" / "repository-os.json").exists())
            self.assertTrue((root / ".gumball" / "proof-broker.json").exists())
            self.assertTrue((root / "scripts" / "ops" / "repository_os.py").exists())
            self.assertTrue((root / "scripts" / "ops" / "github_ops.py").exists())
            self.assertTrue((root / ".github" / "workflows" / "repository-ops.yml").exists())
            self.assertTrue((root / ".github" / "workflows" / "proof-broker.yml").exists())
            self.assertTrue((root / "scripts" / "ops" / "proof_broker.py").exists())
            self.assertTrue((root / "docs" / "PROOF_BROKER.md").exists())
            self.assertTrue((root / "templates" / "release-manifest.json").exists())

    def test_doctor_accepts_minimal_fail_closed_repository(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / ".github" / "workflows").mkdir(parents=True)
            (root / "gumball.yaml").write_text("schema_version: 1\n", encoding="utf-8")
            (root / "AGENTS.md").write_text("# rules\n", encoding="utf-8")
            (root / "docs" / "README.md").write_text("# docs\n", encoding="utf-8")
            (root / "docs" / "DIAGRAM_STYLE.md").write_text("# diagrams\n", encoding="utf-8")
            (root / ".gumball").mkdir(exist_ok=True)
            (root / ".gumball" / "repository-os.json").write_text("{}\n", encoding="utf-8")
            (root / ".gumball" / "proof-broker.json").write_text("{}\n", encoding="utf-8")
            (root / ".github" / "workflows" / "ci.yml").write_text(
                """name: CI
permissions: {}
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: echo ok
  aggregate:
    name: Aggregate CI gate
    if: ${{ always() }}
    needs: [test]
    runs-on: ubuntu-latest
    steps:
      - run: test "${{ needs.test.result }}" = success
""",
                encoding="utf-8",
            )

            ok, checks = gumball.doctor_repository(root)

            self.assertTrue(ok, checks)

    def test_doctor_rejects_mutable_external_action_ref(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / ".github" / "workflows").mkdir(parents=True)
            (root / "gumball.yaml").write_text("schema_version: 1\n", encoding="utf-8")
            (root / "AGENTS.md").write_text("# rules\n", encoding="utf-8")
            (root / "docs" / "README.md").write_text("# docs\n", encoding="utf-8")
            (root / "docs" / "DIAGRAM_STYLE.md").write_text("# diagrams\n", encoding="utf-8")
            (root / ".gumball").mkdir(exist_ok=True)
            (root / ".gumball" / "repository-os.json").write_text("{}\n", encoding="utf-8")
            (root / ".gumball" / "proof-broker.json").write_text("{}\n", encoding="utf-8")
            (root / ".github" / "workflows" / "ci.yml").write_text(
                """name: CI
permissions: {}
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@main
  aggregate:
    name: Aggregate CI gate
    if: ${{ always() }}
    needs: [test]
    runs-on: ubuntu-latest
    steps:
      - run: echo aggregate
""",
                encoding="utf-8",
            )

            ok, checks = gumball.doctor_repository(root)

            self.assertFalse(ok)
            safety = next(item for item in checks if item[0] == "workflow safety")
            self.assertEqual(safety[1], "FAIL")
            self.assertIn("not pinned", safety[2])

    def test_gumball_source_requires_self_dogfooding_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "scripts").mkdir()
            (root / ".github" / "workflows").mkdir(parents=True)
            (root / "VERSION").write_text("0.4.0\\n", encoding="utf-8")
            (root / "scripts" / "gumball.py").write_text("# source\\n", encoding="utf-8")
            (root / ".github" / "workflows" / "reusable-governance.yml").write_text(
                "name: reusable\\npermissions: {}\\n",
                encoding="utf-8",
            )
            (root / "gumball.yaml").write_text("schema_version: 1\\n", encoding="utf-8")
            (root / "AGENTS.md").write_text("# rules\\n", encoding="utf-8")
            (root / "docs" / "README.md").write_text("# docs\\n", encoding="utf-8")
            (root / "docs" / "DIAGRAM_STYLE.md").write_text("# diagrams\\n", encoding="utf-8")
            (root / ".github" / "workflows" / "ci.yml").write_text(
                """name: CI
permissions: {}
jobs:
  aggregate:
    name: Aggregate CI gate
    if: ${{ always() }}
    runs-on: ubuntu-latest
    steps:
      - run: echo ok
""",
                encoding="utf-8",
            )

            ok, checks = gumball.doctor_repository(root)

            self.assertFalse(ok)
            dogfood = next(item for item in checks if item[0] == "Gumball dogfooding")
            self.assertEqual(dogfood[1], "FAIL")
            self.assertIn("DOGFOODING.md", dogfood[2])

    def test_gumball_source_detects_version_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "scripts").mkdir()
            (root / ".github" / "workflows").mkdir(parents=True)
            (root / ".gumball").mkdir()
            (root / "VERSION").write_text("0.5.0\n", encoding="utf-8")
            (root / "gumball.yaml").write_text(
                "platform_version: 0.4.0\n",
                encoding="utf-8",
            )
            (root / "scripts" / "gumball.py").write_text("# source\n", encoding="utf-8")
            (root / ".github" / "workflows" / "reusable-governance.yml").write_text(
                "name: reusable\npermissions: {}\n",
                encoding="utf-8",
            )
            (root / ".gumball" / "repository-os.json").write_text(
                '{"lifecycle":{},"projects":{},"labels":{},"release":{},"ci_cost":{}}\n',
                encoding="utf-8",
            )

            problems = gumball._gumball_self_problems(root)

            self.assertTrue(
                any("VERSION (0.5.0)" in problem for problem in problems),
                problems,
            )

    def test_audit_detects_existing_mcp_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".cursor").mkdir()
            (root / ".cursor" / "mcp.json").write_text("{}", encoding="utf-8")

            audit = gumball.audit_repository(root)

            self.assertTrue(audit["capabilities"]["mcp_config"])

    def test_candidate_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidates = root / ".gumball" / "candidates"
            candidates.mkdir(parents=True)
            payload = {
                "id": "ci-anti-noop",
                "source": "owner/repo",
                "category": "ci",
                "problem": "filtered command matched nothing",
                "invariant": "expected work must execute",
                "evidence": ["PR #1"],
                "do_not_copy": ["workspace name"],
                "failure_behavior": "fail when expected match count is zero",
                "status": "candidate",
            }
            (candidates / "ci-anti-noop.json").write_text(
                json.dumps(payload),
                encoding="utf-8",
            )

            ok, messages = gumball.scan_candidates(root)

            self.assertTrue(ok, messages)
            self.assertIn("candidate / ci / ci-anti-noop", messages[0])


if __name__ == "__main__":
    unittest.main()
