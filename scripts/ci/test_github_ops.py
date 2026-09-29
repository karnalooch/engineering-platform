from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.ops import github_ops, repository_os


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "repository-ops.yml"


class GithubOpsContractTests(unittest.TestCase):
    def test_closing_reference_parser_supports_common_keywords(self):
        body = "Closes #12\nFixes #13\nresolves #14"
        self.assertEqual(
            github_ops.CLOSING_REF.findall(body),
            ["12", "13", "14"],
        )

    def test_semantic_project_alias_maps_todo_to_ready(self):
        policy = {
            "projects": {
                "semantic_statuses": {
                    "backlog": ["Backlog"],
                    "ready": ["Ready", "Todo"],
                    "in_progress": ["In Progress"],
                    "in_review": ["In Review"],
                    "done": ["Done"],
                    "blocked": ["Blocked"],
                }
            }
        }
        self.assertEqual(
            github_ops._semantic_from_project_status(policy, "Todo"),
            "ready",
        )

    def test_disabled_project_sync_is_explicit(self):
        with tempfile.TemporaryDirectory() as tmp:
            event = Path(tmp) / "event.json"
            event.write_text("{}", encoding="utf-8")
            result = github_ops.project_event(
                "owner/repo",
                "repo-token",
                None,
                {"projects": {"enabled": False}},
                event,
                apply=False,
            )
        self.assertEqual(result, ["projects: DISABLED"])

    def test_repository_ops_workflow_runs_trusted_default_branch_code(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("pull_request_target:", text)
        self.assertIn(
            "ref: ${{ github.event.repository.default_branch }}",
            text,
        )
        self.assertIn("persist-credentials: false", text)
        self.assertNotIn("github.event.pull_request.head.sha", text)
        self.assertNotIn("github.head_ref", text)

    def test_repository_ops_workflow_uses_pinned_actions(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn(
            "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1",
            text,
        )
        self.assertIn(
            "actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97",
            text,
        )

    def test_policy_has_unique_label_definitions(self):
        policy = repository_os.load_policy(ROOT / ".gumball" / "repository-os.json")
        names = [item["name"] for item in policy["labels"]["definitions"]]
        self.assertEqual(len(names), len(set(names)))
        required = set(policy["labels"]["required_pr_dimensions"])
        self.assertEqual(required, {"type", "area", "risk", "ci"})


if __name__ == "__main__":
    unittest.main()
