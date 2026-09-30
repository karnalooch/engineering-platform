from __future__ import annotations

import unittest
from pathlib import Path

from scripts.ci import assert_nonempty, evaluate_aggregate, plan_gumball_ci


ROOT = Path(__file__).resolve().parents[2]


class AggregateEvaluatorTests(unittest.TestCase):
    def test_required_jobs_must_succeed(self):
        ok, reasons = evaluate_aggregate.evaluate(
            {"lint": {"result": "success"}, "tests": {"result": "success"}},
            ["lint", "tests"],
        )
        self.assertTrue(ok, reasons)

    def test_missing_required_job_fails_closed(self):
        ok, reasons = evaluate_aggregate.evaluate(
            {"lint": {"result": "success"}},
            ["lint", "tests"],
        )
        self.assertFalse(ok)
        self.assertIn("tests: missing required job result", reasons)

    def test_skipped_required_job_fails_without_explicit_allowance(self):
        ok, reasons = evaluate_aggregate.evaluate(
            {"docs": {"result": "skipped"}},
            ["docs"],
        )
        self.assertFalse(ok)
        self.assertIn("expected success, got skipped", reasons[0])

    def test_explicitly_allowed_skip_can_pass(self):
        ok, reasons = evaluate_aggregate.evaluate(
            {"release": {"result": "skipped"}, "policy": {"result": "success"}},
            ["release", "policy"],
            ["release"],
        )
        self.assertTrue(ok, reasons)

    def test_empty_expected_set_is_rejected(self):
        ok, reasons = evaluate_aggregate.evaluate({}, [])
        self.assertFalse(ok)
        self.assertIn("no-op", reasons[0])


class AntiNoopTests(unittest.TestCase):
    def test_zero_matches_fail_by_default(self):
        ok, detail = assert_nonempty.evaluate(0)
        self.assertFalse(ok)
        self.assertIn("expected at least 1", detail)

    def test_positive_match_count_passes(self):
        ok, detail = assert_nonempty.evaluate(3)
        self.assertTrue(ok)
        self.assertIn("matched 3", detail)


class GumballCiPlannerTests(unittest.TestCase):
    def test_docs_only_skips_heavy_security_baseline(self):
        plan = plan_gumball_ci.plan_for_event(
            "pull_request",
            ["docs/CI_MODEL.md", "README.md"],
        )
        self.assertEqual("docs-only", plan.classification)
        self.assertFalse(plan.security_required)

    def test_ci_core_change_forces_full_security(self):
        plan = plan_gumball_ci.plan_for_event(
            "pull_request",
            [".github/workflows/ci.yml"],
        )
        self.assertEqual("full", plan.classification)
        self.assertTrue(plan.security_required)

    def test_scripts_ci_change_forces_full_security(self):
        plan = plan_gumball_ci.plan_for_event(
            "pull_request",
            ["scripts/ci/evaluate_aggregate.py"],
        )
        self.assertTrue(plan.security_required)

    def test_security_policy_document_forces_full_security(self):
        plan = plan_gumball_ci.plan_for_event(
            "pull_request",
            ["SECURITY.md"],
        )
        self.assertEqual("full", plan.classification)
        self.assertTrue(plan.security_required)

    def test_dependency_manifest_forces_full_security(self):
        plan = plan_gumball_ci.plan_for_event(
            \"pull_request\",
            [\"package.json\"],
        )
        self.assertEqual(\"full\", plan.classification)
        self.assertTrue(plan.security_required)

    def test_dependency_lockfile_forces_full_security(self):
        plan = plan_gumball_ci.plan_for_event(
            \"pull_request\",
            [\"pnpm-lock.yaml\"],
        )
        self.assertEqual(\"full\", plan.classification)
        self.assertTrue(plan.security_required)

    def test_mixed_docs_and_code_forces_full_security(self):
        plan = plan_gumball_ci.plan_for_event(
            "pull_request",
            ["docs/README.md", "scripts/gumball.py"],
        )
        self.assertEqual("full", plan.classification)
        self.assertTrue(plan.security_required)

    def test_empty_pr_change_set_fails_closed(self):
        plan = plan_gumball_ci.plan_for_event("pull_request", [])
        self.assertEqual("full", plan.classification)
        self.assertTrue(plan.security_required)

    def test_non_pr_event_always_uses_full_security(self):
        plan = plan_gumball_ci.plan_for_event("push", ["docs/README.md"])
        self.assertEqual("full", plan.classification)
        self.assertTrue(plan.security_required)


class ReusableSecurityLightLaneTests(unittest.TestCase):
    def setUp(self):
        self.workflow = (
            ROOT / ".github/workflows/reusable-security.yml"
        ).read_text(encoding="utf-8")

    def test_light_lane_is_explicit_opt_in(self):
        self.assertIn("enable_docs_only_light_lane:", self.workflow)
        self.assertIn("default: false", self.workflow)

    def test_heavy_security_jobs_depend_on_shared_plan(self):
        for job in ("dependency-review:", "codeql:", "trivy:", "sbom:"):
            self.assertIn(job, self.workflow)
        self.assertGreaterEqual(self.workflow.count("needs: plan"), 4)
        self.assertGreaterEqual(
            self.workflow.count("needs.plan.outputs.run_heavy == 'true'"),
            4,
        )

    def test_docs_only_classification_fails_safe_around_control_plane(self):
        for marker in (
            ".github/*|scripts/ci/*|SECURITY.md|*/SECURITY.md",
            "docs/*|README.md|CHANGELOG.md|*.md",
            'reason="empty change set; failed safe to full"',
            'reason="non-pull-request event always requires full security"',
        ):
            self.assertIn(marker, self.workflow)


if __name__ == "__main__":
    unittest.main()
