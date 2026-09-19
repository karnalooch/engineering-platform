from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "auto-merge.yml"


class AutoMergeWorkflowContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = WORKFLOW.read_text(encoding="utf-8")

    def test_privileged_workflow_never_checks_out_pr_head(self):
        self.assertIn("pull_request_target:", self.text)
        self.assertIn(
            "ref: ${{ github.event.repository.default_branch }}",
            self.text,
        )
        self.assertIn("persist-credentials: false", self.text)
        self.assertNotIn(
            "github.event.pull_request.head.sha",
            self.text,
        )
        self.assertNotIn("refs/pull/", self.text)

    def test_permissions_are_explicit_and_minimal_for_merge(self):
        self.assertIn("contents: write", self.text)
        self.assertIn("pull-requests: write", self.text)
        self.assertIn("checks: read", self.text)
        self.assertIn("issues: write", self.text)
        self.assertNotIn("actions: write", self.text)
        self.assertNotIn("security-events: write", self.text)

    def test_repository_wide_concurrency_never_cancels(self):
        self.assertIn(
            "group: fail-closed-auto-merge-${{ github.repository }}",
            self.text,
        )
        self.assertIn("cancel-in-progress: false", self.text)
        self.assertNotIn("github.run_id", self.text)

    def test_reacts_to_ci_completion_and_pr_state_changes(self):
        self.assertIn(
            'workflows: ["Engineering Platform CI"]',
            self.text,
        )
        self.assertIn("ready_for_review", self.text)
        self.assertIn("synchronize", self.text)
        self.assertIn("edited", self.text)

    def test_hourly_reconciliation_exists(self):
        self.assertIn("cron: '37 * * * *'", self.text)

    def test_external_actions_are_immutable_sha_pinned(self):
        self.assertIn(
            "actions/checkout@"
            "3d3c42e5aac5ba805825da76410c181273ba90b1",
            self.text,
        )
        self.assertIn(
            "actions/setup-python@"
            "5fda3b95a4ea91299a34e894583c3862153e4b97",
            self.text,
        )
        self.assertNotIn("actions/checkout@v", self.text)
        self.assertNotIn("actions/setup-python@v", self.text)

    def test_executes_only_checked_in_trusted_policy(self):
        self.assertIn(
            "python scripts/ci/auto_merge.py",
            self.text,
        )

    def test_no_external_secrets_are_used(self):
        self.assertNotIn("secrets.", self.text)
        self.assertNotIn("PROJECTS_TOKEN", self.text)


if __name__ == "__main__":
    unittest.main()
