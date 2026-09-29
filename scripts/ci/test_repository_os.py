from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.ops import repository_os


POLICY = {
    "lifecycle": {
        "merged_branch_delete_after_hours": 24,
        "closed_unmerged_branch_delete_after_days": 14,
        "orphan_branch_report_after_days": 30,
        "stale_pr_after_days": 30,
        "stale_pr_close_after_additional_days": 14,
        "stale_issue_after_days": 60,
        "stale_issue_auto_close": False,
        "protected_branch_patterns": ["main", "release/*"],
    },
    "projects": {"close_issue_on_done": True},
    "release": {
        "stages": ["dev", "preview", "beta", "rc", "stable"],
        "require_exact_source_sha": True,
        "require_artifact_sha256": True,
        "require_semver": True,
    },
}


class CiCostTests(unittest.TestCase):
    def test_docs_only_is_light(self):
        plan = repository_os.plan_ci(["docs/README.md", "README.md"])
        self.assertEqual(plan["class"], "light")
        self.assertFalse(plan["heavy_build"])

    def test_runtime_change_is_heavy(self):
        plan = repository_os.plan_ci(["Source/Game/Foo.cpp"])
        self.assertEqual(plan["class"], "heavy")
        self.assertTrue(plan["heavy_build"])

    def test_unknown_empty_change_set_fails_safe_to_standard(self):
        plan = repository_os.plan_ci([])
        self.assertEqual(plan["class"], "standard")

    def test_fingerprint_is_stable_for_input_order(self):
        first = repository_os.build_fingerprint(
            source_sha="a" * 40,
            profile="release",
            toolchain="ue-5.8",
            relevant_inputs={"B": "2", "A": "1"},
        )
        second = repository_os.build_fingerprint(
            source_sha="a" * 40,
            profile="release",
            toolchain="ue-5.8",
            relevant_inputs={"A": "1", "B": "2"},
        )
        self.assertEqual(first, second)


class LabelTests(unittest.TestCase):
    def test_pr_labels_include_type_area_risk_and_ci(self):
        result = repository_os.classify_pr(
            "feat: add release workflow",
            [".github/workflows/release.yml"],
        )
        self.assertIn("type:feature", result["labels"])
        self.assertIn("area:ci", result["labels"])
        self.assertIn("area:release", result["labels"])
        self.assertIn("risk:high", result["labels"])
        self.assertIn("ci:standard", result["labels"])


class ProjectFlowTests(unittest.TestCase):
    def test_ready_issue_moves_to_ready(self):
        state = repository_os.desired_project_state(
            {"kind": "issue", "state": "open", "labels": ["status:ready"]}
        )
        self.assertEqual(state, "ready")

    def test_draft_pr_is_in_progress(self):
        state = repository_os.desired_project_state(
            {"kind": "pull_request", "state": "open", "draft": True, "labels": []}
        )
        self.assertEqual(state, "in_progress")

    def test_ready_pr_is_in_review(self):
        state = repository_os.desired_project_state(
            {"kind": "pull_request", "state": "open", "draft": False, "labels": []}
        )
        self.assertEqual(state, "in_review")

    def test_merged_pr_is_done(self):
        state = repository_os.desired_project_state(
            {"kind": "pull_request", "state": "merged", "draft": False, "labels": []}
        )
        self.assertEqual(state, "done")

    def test_manual_project_done_can_close_issue_when_enabled(self):
        action = repository_os.project_action(
            {"kind": "issue", "state": "open", "labels": []},
            "done",
            close_issue_on_done=True,
        )
        self.assertEqual(action["action"], "CLOSE")


class ReleaseLineageTests(unittest.TestCase):
    def test_valid_manifest_passes(self):
        manifest = {
            "application": {"name": "app", "version": "1.2.3", "stage": "rc"},
            "source": {"sha": "a" * 40},
            "artifact": {"name": "app.zip", "sha256": "b" * 64},
        }
        self.assertEqual(
            repository_os.validate_release_manifest(manifest, POLICY),
            [],
        )

    def test_invalid_digest_fails(self):
        manifest = {
            "application": {"name": "app", "version": "1.2.3", "stage": "stable"},
            "source": {"sha": "a" * 40},
            "artifact": {"name": "app.zip", "sha256": "bad"},
        }
        problems = repository_os.validate_release_manifest(manifest, POLICY)
        self.assertTrue(any("sha256" in problem for problem in problems))

    def test_non_semver_version_fails_when_required(self):
        manifest = {
            "application": {"name": "app", "version": "banana", "stage": "rc"},
            "source": {"sha": "a" * 40},
            "artifact": {"name": "app.zip", "sha256": "b" * 64},
        }
        problems = repository_os.validate_release_manifest(manifest, POLICY)
        self.assertTrue(any("SemVer" in problem for problem in problems))

    def test_create_manifest_hashes_real_artifact_and_promotion_reuses_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            artifact = Path(tmp) / "app.bin"
            artifact.write_bytes(b"immutable artifact")
            manifest = repository_os.create_release_manifest(
                application="app",
                version="1.2.3",
                stage="beta",
                source_sha="a" * 40,
                build_id="build-17",
                profile="release",
                toolchain="test",
                artifact_path=artifact,
                gumball_version="0.5.0",
            )

        self.assertEqual(
            manifest["artifact"]["sha256"],
            repository_os.hashlib.sha256(b"immutable artifact").hexdigest(),
        )
        promoted = repository_os.promote_release_manifest(manifest, "rc", POLICY)
        self.assertEqual(
            promoted["artifact"]["sha256"],
            manifest["artifact"]["sha256"],
        )
        self.assertFalse(promoted["promotion"]["artifact_rebuilt"])

    def test_stage_promotion_is_monotonic(self):
        stages = POLICY["release"]["stages"]
        self.assertTrue(repository_os.can_promote_stage("beta", "rc", stages))
        self.assertFalse(repository_os.can_promote_stage("stable", "beta", stages))


class LifecycleTests(unittest.TestCase):
    def test_merged_branch_is_deleted_after_grace(self):
        snapshot = {
            "branches": [
                {
                    "name": "feat/done",
                    "pull_request": {
                        "state": "closed",
                        "merged": True,
                        "age_hours": 30,
                    },
                }
            ],
            "pull_requests": [],
            "issues": [],
        }
        actions = repository_os.lifecycle_plan(snapshot, POLICY)
        self.assertEqual(actions[0]["action"], "DELETE_BRANCH")

    def test_open_pr_branch_is_never_deleted(self):
        snapshot = {
            "branches": [
                {
                    "name": "feat/live",
                    "pull_request": {
                        "state": "closed",
                        "merged": True,
                        "age_hours": 100,
                    },
                }
            ],
            "pull_requests": [
                {"number": 2, "state": "open", "head": "feat/live", "inactive_days": 0}
            ],
            "issues": [],
        }
        actions = repository_os.lifecycle_plan(snapshot, POLICY)
        self.assertFalse(any(action["action"] == "DELETE_BRANCH" for action in actions))

    def test_issue_is_labelled_stale_but_not_closed_by_default(self):
        snapshot = {
            "branches": [],
            "pull_requests": [],
            "issues": [
                {"number": 7, "state": "open", "inactive_days": 90, "labels": []}
            ],
        }
        actions = repository_os.lifecycle_plan(snapshot, POLICY)
        self.assertIn("LABEL_STALE_ISSUE", [action["action"] for action in actions])
        self.assertNotIn("CLOSE_STALE_ISSUE", [action["action"] for action in actions])


if __name__ == "__main__":
    unittest.main()
