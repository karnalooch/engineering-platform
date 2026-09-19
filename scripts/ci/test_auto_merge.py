from __future__ import annotations

import unittest
from unittest.mock import patch

from scripts.ci.auto_merge import (
    AutomationError,
    auto_merge_mode,
    evaluate_eligible_pull_requests,
    evaluate_pull_request,
    has_changes_requested,
    is_risky_path,
    latest_check_conclusions,
    missing_required_checks,
    risky_paths,
)


class AutoMergePolicyTests(unittest.TestCase):
    def test_manual_marker_wins(self):
        self.assertEqual(
            auto_merge_mode("Auto-merge: eligible"),
            "eligible",
        )
        self.assertEqual(
            auto_merge_mode(
                "Auto-merge: eligible\nAuto-merge: manual"
            ),
            "manual",
        )
        self.assertEqual(auto_merge_mode("looks safe"), None)

    def test_high_risk_paths_fail_closed(self):
        paths = [
            ".github/workflows/ci.yml",
            ".github/dependabot.yml",
            "scripts/ci/auto_merge.py",
            "VERSION",
            "CHANGELOG.md",
            "SECURITY.md",
            "docs/AUTO_MERGE.md",
            "docs/CONTRACT.md",
            "docs/GOVERNANCE_GUARD.md",
            "docs/VERSIONING.md",
            "pyproject.toml",
            "package.json",
            "pnpm-lock.yaml",
            "requirements.txt",
            "config/private.key",
            ".env",
        ]
        for path in paths:
            with self.subTest(path=path):
                self.assertTrue(is_risky_path(path))

    def test_low_risk_documentation_can_be_eligible(self):
        paths = [
            "README.md",
            "docs/architecture-notes.md",
            "docs/example-consumer.md",
            "notes/release-idea.txt",
        ]
        for path in paths:
            with self.subTest(path=path):
                self.assertFalse(is_risky_path(path))

    def test_risky_paths_filters_and_sorts(self):
        self.assertEqual(
            risky_paths(
                [
                    "README.md",
                    ".github/workflows/ci.yml",
                    "VERSION",
                ]
            ),
            [".github/workflows/ci.yml", "VERSION"],
        )

    def test_latest_check_run_wins_by_id(self):
        conclusions = latest_check_conclusions(
            [
                {
                    "id": 10,
                    "name": "Aggregate CI gate",
                    "conclusion": "failure",
                },
                {
                    "id": 11,
                    "name": "Aggregate CI gate",
                    "conclusion": "success",
                },
                {
                    "id": 12,
                    "name": "Governance policy / Governance guard",
                    "conclusion": "success",
                },
            ]
        )
        self.assertEqual(
            conclusions["Aggregate CI gate"],
            "success",
        )

    def test_missing_required_check_blocks(self):
        self.assertEqual(
            missing_required_checks(
                [
                    {
                        "id": 11,
                        "name": "Aggregate CI gate",
                        "conclusion": "success",
                    }
                ]
            ),
            ["Governance policy / Governance guard"],
        )

    def test_failed_required_check_blocks(self):
        self.assertEqual(
            missing_required_checks(
                [
                    {
                        "id": 11,
                        "name": "Aggregate CI gate",
                        "conclusion": "success",
                    },
                    {
                        "id": 12,
                        "name": "Governance policy / Governance guard",
                        "conclusion": "failure",
                    },
                ]
            ),
            ["Governance policy / Governance guard"],
        )

    def test_check_without_id_fails_closed(self):
        with self.assertRaisesRegex(
            AutomationError,
            "missing id",
        ):
            missing_required_checks(
                [
                    {
                        "name": "Aggregate CI gate",
                        "conclusion": "success",
                    }
                ]
            )

    def test_latest_changes_requested_blocks(self):
        self.assertTrue(
            has_changes_requested(
                [
                    {
                        "id": 1,
                        "state": "APPROVED",
                        "user": {"login": "reviewer"},
                    },
                    {
                        "id": 2,
                        "state": "CHANGES_REQUESTED",
                        "user": {"login": "reviewer"},
                    },
                ]
            )
        )

    def test_comment_does_not_clear_changes_requested(self):
        self.assertTrue(
            has_changes_requested(
                [
                    {
                        "id": 1,
                        "state": "CHANGES_REQUESTED",
                        "user": {"login": "reviewer"},
                    },
                    {
                        "id": 2,
                        "state": "COMMENTED",
                        "user": {"login": "reviewer"},
                    },
                ]
            )
        )

    def test_later_approval_clears_old_changes_requested(self):
        self.assertFalse(
            has_changes_requested(
                [
                    {
                        "id": 1,
                        "state": "CHANGES_REQUESTED",
                        "user": {"login": "reviewer"},
                    },
                    {
                        "id": 2,
                        "state": "COMMENTED",
                        "user": {"login": "reviewer"},
                    },
                    {
                        "id": 3,
                        "state": "APPROVED",
                        "user": {"login": "reviewer"},
                    },
                ]
            )
        )


class AutoMergeBatchTests(unittest.TestCase):
    @patch("scripts.ci.auto_merge.evaluate_pull_request")
    def test_one_error_does_not_starve_later_prs(self, evaluate):
        evaluate.side_effect = [
            AutomationError("transient"),
            "merged",
        ]
        result = evaluate_eligible_pull_requests(
            object(),
            repository="karnalooch/engineering-platform",
            repository_owner="karnalooch",
            pull_requests=[
                {
                    "number": 41,
                    "body": "Auto-merge: eligible",
                },
                {
                    "number": 42,
                    "body": "Auto-merge: eligible",
                },
            ],
        )
        self.assertEqual(result, 1)
        self.assertEqual(evaluate.call_count, 2)


class FakeApi:
    def __init__(
        self,
        *,
        paths=None,
        checks=None,
        reviews=None,
        unresolved=0,
        mergeable=True,
        mergeable_state="clean",
        author="karnalooch",
        head_repo="karnalooch/engineering-platform",
        body="Auto-merge: eligible",
        head_sha="a" * 40,
        base_sha="c" * 40,
        final_body=None,
        final_base_sha=None,
    ):
        self.paths = paths or ["README.md"]
        self.checks = checks or [
            {
                "id": 10,
                "name": "Aggregate CI gate",
                "conclusion": "success",
            },
            {
                "id": 11,
                "name": "Governance policy / Governance guard",
                "conclusion": "success",
            },
        ]
        self.reviews = reviews or []
        self.unresolved = unresolved
        self.closing_issues = [10]
        self.mergeable = mergeable
        self.mergeable_state = mergeable_state
        self.author = author
        self.head_repo = head_repo
        self.body = body
        self.head_sha = head_sha
        self.base_sha = base_sha
        self.final_body = final_body
        self.final_base_sha = final_base_sha
        self.pr_reads = 0
        self.issue_state_reason = "completed"
        self.calls = []

    def rest(self, method, path, payload=None, *, query=None):
        self.calls.append((method, path, payload, query))

        if method == "GET" and path.endswith("/pulls/42"):
            self.pr_reads += 1
            body = (
                self.final_body
                if self.pr_reads > 1 and self.final_body is not None
                else self.body
            )
            base_sha = (
                self.final_base_sha
                if self.pr_reads > 1 and self.final_base_sha is not None
                else self.base_sha
            )
            return (
                {
                    "number": 42,
                    "body": body,
                    "state": "open",
                    "draft": False,
                    "base": {"ref": "main", "sha": base_sha},
                    "head": {
                        "sha": self.head_sha,
                        "repo": {"full_name": self.head_repo},
                    },
                    "user": {"login": self.author},
                    "mergeable": self.mergeable,
                    "mergeable_state": self.mergeable_state,
                    "title": "safe docs change",
                },
                {},
            )

        if method == "GET" and path.endswith("/pulls/42/files"):
            page = int((query or {}).get("page", 1))
            return (
                (
                    [{"filename": value} for value in self.paths]
                    if page == 1
                    else []
                ),
                {},
            )

        if method == "GET" and path.endswith(
            f"/commits/{self.head_sha}/check-runs"
        ):
            page = int((query or {}).get("page", 1))
            return (
                {
                    "total_count": len(self.checks),
                    "check_runs": (
                        self.checks if page == 1 else []
                    ),
                },
                {},
            )

        if method == "GET" and path.endswith("/pulls/42/reviews"):
            page = int((query or {}).get("page", 1))
            return (
                self.reviews if page == 1 else [],
                {},
            )

        if method == "PUT" and path.endswith(
            "/pulls/42/update-branch"
        ):
            return (
                {"message": "Updating pull request branch."},
                {},
            )

        if method == "PUT" and path.endswith("/pulls/42/merge"):
            return (
                {
                    "merged": True,
                    "sha": "b" * 40,
                },
                {},
            )

        if method == "PATCH" and path.endswith("/issues/10"):
            return (
                {
                    "number": 10,
                    "state": "closed",
                    "state_reason": self.issue_state_reason,
                },
                {},
            )

        raise AssertionError(
            f"unexpected REST call: {method} {path}"
        )

    def graphql(self, query, variables):
        del query, variables
        return {
            "repository": {
                "pullRequest": {
                    "reviewThreads": {
                        "pageInfo": {
                            "hasNextPage": False
                        },
                        "nodes": [
                            {"isResolved": False}
                            for _ in range(self.unresolved)
                        ],
                    },
                    "closingIssuesReferences": {
                        "pageInfo": {
                            "hasNextPage": False
                        },
                        "nodes": [
                            {
                                "number": number,
                                "repository": {
                                    "nameWithOwner": (
                                        "karnalooch/"
                                        "engineering-platform"
                                    )
                                },
                            }
                            for number in self.closing_issues
                        ],
                    },
                }
            }
        }

    def put_paths(self):
        return [
            path
            for method, path, _payload, _query in self.calls
            if method == "PUT"
        ]


class AutoMergeDecisionTests(unittest.TestCase):
    def _evaluate(self, api):
        return evaluate_pull_request(
            api,
            repository="karnalooch/engineering-platform",
            repository_owner="karnalooch",
            pr_summary={
                "number": 42,
                "body": "Auto-merge: eligible",
            },
        )

    def test_safe_green_pr_is_squash_merged(self):
        api = FakeApi()
        self.assertEqual(self._evaluate(api), "merged")
        self.assertEqual(
            api.put_paths(),
            [
                "/repos/karnalooch/"
                "engineering-platform/pulls/42/merge"
            ],
        )

    def test_manual_marker_blocks_even_if_summary_says_eligible(self):
        api = FakeApi(
            body=(
                "Auto-merge: eligible\n"
                "Auto-merge: manual"
            )
        )
        self.assertEqual(self._evaluate(api), "blocked")
        self.assertEqual(api.put_paths(), [])

    def test_high_risk_path_never_reaches_merge(self):
        api = FakeApi(
            paths=[".github/workflows/ci.yml"]
        )
        self.assertEqual(self._evaluate(api), "blocked")
        self.assertEqual(api.put_paths(), [])

    def test_version_change_never_reaches_merge(self):
        api = FakeApi(paths=["VERSION"])
        self.assertEqual(self._evaluate(api), "blocked")
        self.assertEqual(api.put_paths(), [])

    def test_missing_governance_check_blocks(self):
        api = FakeApi(
            checks=[
                {
                    "id": 10,
                    "name": "Aggregate CI gate",
                    "conclusion": "success",
                }
            ]
        )
        self.assertEqual(self._evaluate(api), "blocked")
        self.assertEqual(api.put_paths(), [])

    def test_unresolved_thread_blocks(self):
        api = FakeApi(unresolved=1)
        self.assertEqual(self._evaluate(api), "blocked")
        self.assertEqual(api.put_paths(), [])

    def test_changes_requested_blocks(self):
        api = FakeApi(
            reviews=[
                {
                    "id": 20,
                    "state": "CHANGES_REQUESTED",
                    "user": {"login": "human"},
                }
            ]
        )
        self.assertEqual(self._evaluate(api), "blocked")
        self.assertEqual(api.put_paths(), [])

    def test_missing_closing_issue_blocks(self):
        api = FakeApi()
        api.closing_issues = []
        self.assertEqual(self._evaluate(api), "blocked")
        self.assertEqual(api.put_paths(), [])

    def test_fork_or_non_owner_author_blocks(self):
        for api in (
            FakeApi(head_repo="someone/fork"),
            FakeApi(author="someone-else"),
        ):
            with self.subTest(
                author=api.author,
                head_repo=api.head_repo,
            ):
                self.assertEqual(
                    self._evaluate(api),
                    "blocked",
                )
                self.assertEqual(api.put_paths(), [])

    def test_invalid_head_sha_fails_closed(self):
        api = FakeApi(head_sha="abc123")
        with self.assertRaisesRegex(
            AutomationError,
            "head SHA",
        ):
            self._evaluate(api)

    def test_unknown_mergeability_blocks(self):
        api = FakeApi(
            mergeable=None,
            mergeable_state="unknown",
        )
        self.assertEqual(self._evaluate(api), "blocked")
        self.assertEqual(api.put_paths(), [])

    def test_marker_change_during_final_revalidation_blocks(self):
        api = FakeApi(final_body="Auto-merge: manual")
        self.assertEqual(self._evaluate(api), "blocked")
        self.assertEqual(api.put_paths(), [])

    def test_base_change_during_final_revalidation_blocks(self):
        api = FakeApi(final_base_sha="d" * 40)
        self.assertEqual(self._evaluate(api), "blocked")
        self.assertEqual(api.put_paths(), [])

    def test_behind_pr_updates_branch_and_waits(self):
        api = FakeApi(mergeable_state="behind")
        self.assertEqual(self._evaluate(api), "updated")
        self.assertEqual(
            api.put_paths(),
            [
                "/repos/karnalooch/"
                "engineering-platform/pulls/42/update-branch"
            ],
        )

    def test_successful_merge_closes_linked_issue(self):
        api = FakeApi()
        self.assertEqual(self._evaluate(api), "merged")
        patch_calls = [
            (path, payload)
            for method, path, payload, _query in api.calls
            if method == "PATCH"
        ]
        self.assertEqual(
            patch_calls,
            [
                (
                    "/repos/karnalooch/"
                    "engineering-platform/issues/10",
                    {
                        "state": "closed",
                        "state_reason": "completed",
                    },
                )
            ],
        )

    def test_wrong_issue_state_reason_fails_visibly_after_merge(self):
        api = FakeApi()
        api.issue_state_reason = "not_planned"
        with self.assertRaisesRegex(
            AutomationError,
            "did not close as completed",
        ):
            self._evaluate(api)


if __name__ == "__main__":
    unittest.main()
