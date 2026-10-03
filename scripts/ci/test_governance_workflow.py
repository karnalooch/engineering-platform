from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "reusable-governance.yml"


class GovernanceWorkflowContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = WORKFLOW.read_text(encoding="utf-8")

    def test_general_marker_policy_preserves_default_requirement(self):
        self.assertRegex(
            self.text,
            re.compile(
                r"require_manual_merge_marker:\n(?:.*\n){0,5}?\s+default:\s+true",
                re.MULTILINE,
            ),
        )
        self.assertIn("inputs.require_manual_merge_marker", self.text)

    def test_dependabot_exception_is_explicit_opt_in(self):
        self.assertRegex(
            self.text,
            re.compile(
                r"allow_dependabot_high_risk_without_manual_marker:\n"
                r"(?:.*\n){0,5}?\s+default:\s+false",
                re.MULTILINE,
            ),
        )

    def test_dependabot_exception_matches_exact_bot_identity(self):
        self.assertIn('pr_author == "dependabot[bot]"', self.text)
        self.assertNotIn('startswith("dependabot")', self.text)

    def test_manual_marker_contract_still_exists(self):
        self.assertIn(
            "'Auto-merge: manual' in the PR body",
            self.text,
        )

    def test_immutable_ref_scanner_covers_inline_list_uses_syntax(self):
        self.assertIn(
            r"(?:-\s*)?uses:",
            self.text,
        )

    def test_consumer_must_use_one_platform_revision(self):
        self.assertIn("platform_refs: set[str] = set()", self.text)
        self.assertIn("platform_refs.add(ref)", self.text)
        self.assertIn("if len(platform_refs) > 1:", self.text)
        self.assertIn(
            "consumer mixes multiple engineering-platform revisions",
            self.text,
        )

    def test_exception_is_forwarded_through_explicit_environment(self):
        self.assertIn(
            "ALLOW_DEPENDABOT_HIGH_RISK_WITHOUT_MANUAL_MARKER:",
            self.text,
        )
        self.assertIn(
            "inputs.allow_dependabot_high_risk_without_manual_marker",
            self.text,
        )


class GovernanceMarkerBehaviorTests(unittest.TestCase):
    def execute(self, marker=None, tail="", aggregate_if="${{ always() }}"):
        import os
        import subprocess
        import tempfile
        import textwrap

        script = (
            WORKFLOW.read_text()
            .split("python - <<'PY'\n", 1)[1]
            .rsplit("          PY", 1)[0]
        )
        script = textwrap.dedent(script)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workflows = root / ".github/workflows"
            workflows.mkdir(parents=True)
            workflow = workflows / "ci.yml"
            workflow.write_text(
                "name: Fixture\npermissions: {}\njobs:\n  aggregate:\n"
                "    name: Aggregate CI gate\n    if: " + aggregate_if + "\n"
                "    runs-on: ubuntu-latest\n    steps:\n"
                "      - run: true\n" + tail
            )
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            command = [
                "git",
                "-c",
                "user.name=Test",
                "-c",
                "user.email=test@example.invalid",
                "commit",
            ]
            subprocess.run(
                [*command, "--allow-empty", "-qm", "base"], cwd=root, check=True
            )
            base = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=root, text=True
            ).strip()
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run([*command, "-qm", "workflow"], cwd=root, check=True)
            head = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=root, text=True
            ).strip()
            env = dict(
                os.environ,
                EVENT_NAME="pull_request",
                BASE_SHA=base,
                HEAD_SHA=head,
                PR_BODY="",
                PR_AUTHOR="owner",
                ALLOW_DEPENDABOT_HIGH_RISK_WITHOUT_MANUAL_MARKER="false",
                GITHUB_STEP_SUMMARY=str(root / "summary.md"),
            )
            env.pop("REQUIRE_MANUAL_MERGE_MARKER", None)
            if marker is not None:
                env["REQUIRE_MANUAL_MERGE_MARKER"] = marker
            return subprocess.run(
                ["python", "-c", script],
                cwd=root,
                env=env,
                capture_output=True,
                text=True,
            )

    def test_default_and_unknown_policy_require_manual_marker(self):
        for marker in (None, "true", "", "unknown"):
            with self.subTest(marker=marker):
                result = self.execute(marker)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("'Auto-merge: manual' in the PR body", result.stderr)

    def test_explicit_false_accepts_high_risk_without_body_marker(self):
        result = self.execute("false")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("high-risk paths", result.stdout)

    def test_opt_out_still_rejects_mutable_actions(self):
        result = self.execute("false", "      - uses: actions/checkout@main\n")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("must be pinned", result.stderr)

    def test_opt_out_still_rejects_fail_open_and_write_all(self):
        for tail in ("        continue-on-error: true\n", "permissions: write-all\n"):
            with self.subTest(tail=tail):
                result = self.execute("false", tail)
                self.assertNotEqual(result.returncode, 0)

    def test_opt_out_still_requires_job_level_always(self):
        result = self.execute("false", aggregate_if="${{ success() }}")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("job-level always()", result.stderr)


if __name__ == "__main__":
    unittest.main()
