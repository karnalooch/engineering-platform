#!/usr/bin/env python3
"""Pure policy engine for Gumball repository operations."""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import re
from pathlib import Path
from typing import Any

SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")

TYPE_PREFIXES = {
    "feat": "type:feature",
    "fix": "type:fix",
    "chore": "type:chore",
    "docs": "type:docs",
    "refactor": "type:refactor",
    "test": "type:test",
    "release": "type:release",
}

AREA_PATTERNS = {
    "area:ci": [".github/**", "scripts/ci/**"],
    "area:governance": ["AGENTS.md", "**/AGENTS.md", ".gumball/**", "gumball.yaml"],
    "area:docs": ["docs/**", "README.md", "**/*.md"],
    "area:tooling": ["scripts/**", "tools/**"],
    "area:security": ["SECURITY.md", "**/SECURITY.md", "**/*security*", "**/*auth*"],
    "area:release": ["VERSION", "CHANGELOG.md", "**/*release*", "**/eas.json", "**/app.config.*"],
    "area:runtime": ["Source/**", "Content/**", "mobile/**", "android/**", "ios/**", "**/*.uproject", "Dockerfile*", "**/Dockerfile*"],
    "area:project": [".github/ISSUE_TEMPLATE/**", ".github/PULL_REQUEST_TEMPLATE*", "**/*project*"],
}

HIGH_RISK_PATTERNS = [
    ".github/**",
    "AGENTS.md",
    "**/AGENTS.md",
    "gumball.yaml",
    ".gumball/**",
    "SECURITY.md",
    "**/SECURITY.md",
    "**/*release*",
    "VERSION",
]

HEAVY_PATTERNS = [
    "Source/**",
    "Content/**",
    "mobile/**",
    "android/**",
    "ios/**",
    "**/*.uproject",
    "Dockerfile*",
    "**/Dockerfile*",
    "**/gradle*",
    "**/Podfile*",
]

STANDARD_PATTERNS = [
    "scripts/**",
    ".github/**",
    "**/*.py",
    "**/*.ts",
    "**/*.tsx",
    "**/*.js",
    "**/*.jsx",
    "**/*.rs",
    "**/*.cpp",
    "**/*.h",
    "**/*.cs",
]


def load_policy(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _matches(path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)


def classify_pr(title: str, paths: list[str]) -> dict[str, Any]:
    normalized = title.strip().lower()
    prefix = normalized.split(":", 1)[0].split("(", 1)[0]
    type_label = TYPE_PREFIXES.get(prefix)

    areas = sorted(
        label
        for label, patterns in AREA_PATTERNS.items()
        if any(_matches(path, patterns) for path in paths)
    )

    risk = "risk:high" if any(_matches(path, HIGH_RISK_PATTERNS) for path in paths) else "risk:low"
    if risk == "risk:low" and len(set(areas)) >= 3:
        risk = "risk:medium"

    ci_plan = plan_ci(paths)

    labels = [label for label in [type_label, risk, ci_plan["label"]] if label]
    labels.extend(areas)

    return {
        "type": type_label,
        "areas": areas,
        "risk": risk,
        "ci": ci_plan,
        "labels": sorted(set(labels)),
    }


def plan_ci(paths: list[str]) -> dict[str, Any]:
    if not paths:
        return {
            "class": "standard",
            "label": "ci:standard",
            "tier": "L2",
            "reason": "empty/unknown change set fails safe to standard",
            "heavy_build": False,
            "deferred": [],
        }

    docs_only = all(
        path.endswith(".md")
        or path.startswith("docs/")
        or path in {"README.md", "CHANGELOG.md"}
        for path in paths
    )
    if docs_only:
        return {
            "class": "light",
            "label": "ci:light",
            "tier": "L1",
            "reason": "documentation/policy proof only",
            "heavy_build": False,
            "deferred": ["runtime", "visual", "hardware"],
        }

    heavy = any(_matches(path, HEAVY_PATTERNS) for path in paths)
    if heavy:
        return {
            "class": "heavy",
            "label": "ci:heavy",
            "tier": "L4",
            "reason": "runtime/native/build-affecting paths changed",
            "heavy_build": True,
            "deferred": ["visual/hardware proof unless merge-critical or release-required"],
        }

    standard = any(_matches(path, STANDARD_PATTERNS) for path in paths)
    return {
        "class": "standard",
        "label": "ci:standard",
        "tier": "L2" if standard else "L2",
        "reason": "affected static/unit/contract validation",
        "heavy_build": False,
        "deferred": ["runtime", "visual", "hardware"],
    }


def build_fingerprint(
    *,
    source_sha: str,
    profile: str,
    toolchain: str,
    relevant_inputs: dict[str, str],
) -> str:
    payload = {
        "source_sha": source_sha,
        "profile": profile,
        "toolchain": toolchain,
        "inputs": dict(sorted(relevant_inputs.items())),
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def desired_project_state(item: dict[str, Any]) -> str:
    kind = item.get("kind")
    state = item.get("state")
    labels = set(item.get("labels", []))

    if state in {"closed", "merged"}:
        return "done"

    if "lifecycle:blocked" in labels:
        return "blocked"

    if kind == "pull_request":
        if state != "open":
            return "done"
        return "in_progress" if item.get("draft") else "in_review"

    if kind == "issue":
        linked_pr = item.get("linked_pr")
        if isinstance(linked_pr, dict):
            if linked_pr.get("state") == "merged":
                return "done"
            if linked_pr.get("state") == "open":
                return "in_progress" if linked_pr.get("draft") else "in_review"
        if item.get("active_branch"):
            return "in_progress"
        if "status:ready" in labels:
            return "ready"
        return "backlog"

    return "unknown"


def project_action(
    item: dict[str, Any],
    current_semantic_state: str | None,
    *,
    close_issue_on_done: bool,
) -> dict[str, Any]:
    desired = desired_project_state(item)
    if desired == "unknown":
        return {"action": "UNKNOWN", "desired": desired}

    if current_semantic_state != desired:
        action = "MOVE"
    else:
        action = "MATCH"

    close = (
        close_issue_on_done
        and item.get("kind") == "issue"
        and item.get("state") == "open"
        and current_semantic_state == "done"
    )
    if close:
        action = "CLOSE"

    return {"action": action, "desired": desired}


def validate_release_manifest(
    manifest: dict[str, Any],
    policy: dict[str, Any],
) -> list[str]:
    problems: list[str] = []
    release = policy["release"]

    application = manifest.get("application")
    source = manifest.get("source")
    artifact = manifest.get("artifact")

    if not isinstance(application, dict):
        problems.append("application object is required")
        return problems

    stage = application.get("stage")
    if stage not in release["stages"]:
        problems.append(f"unknown release stage: {stage!r}")

    version = application.get("version")
    if not isinstance(version, str) or not version.strip():
        problems.append("application.version is required")

    sha = source.get("sha") if isinstance(source, dict) else None
    if release.get("require_exact_source_sha") and (
        not isinstance(sha, str) or not SHA40.fullmatch(sha)
    ):
        problems.append("source.sha must be an exact 40-character lowercase SHA")

    digest = artifact.get("sha256") if isinstance(artifact, dict) else None
    if release.get("require_artifact_sha256") and (
        not isinstance(digest, str) or not SHA256.fullmatch(digest)
    ):
        problems.append("artifact.sha256 must be a 64-character lowercase SHA-256")

    if not isinstance(artifact, dict) or not artifact.get("name"):
        problems.append("artifact.name is required")

    return problems


def can_promote_stage(current: str, target: str, stages: list[str]) -> bool:
    try:
        current_index = stages.index(current)
        target_index = stages.index(target)
    except ValueError:
        return False
    return target_index >= current_index


def lifecycle_plan(snapshot: dict[str, Any], policy: dict[str, Any]) -> list[dict[str, Any]]:
    """Plan only deterministic lifecycle actions from an externally gathered snapshot."""
    actions: list[dict[str, Any]] = []
    lifecycle = policy["lifecycle"]

    open_pr_branches = {
        pr.get("head")
        for pr in snapshot.get("pull_requests", [])
        if pr.get("state") == "open" and pr.get("head")
    }

    for branch in snapshot.get("branches", []):
        name = branch.get("name")
        if not name:
            continue
        protected = branch.get("protected", False) or any(
            fnmatch.fnmatch(name, pattern)
            for pattern in lifecycle["protected_branch_patterns"]
        )
        if protected or name in open_pr_branches:
            continue

        pr = branch.get("pull_request")
        if isinstance(pr, dict) and pr.get("merged") and pr.get("age_hours", 0) >= lifecycle["merged_branch_delete_after_hours"]:
            actions.append({"action": "DELETE_BRANCH", "branch": name, "reason": "merged PR grace expired"})
        elif isinstance(pr, dict) and pr.get("state") == "closed" and not pr.get("merged") and pr.get("age_days", 0) >= lifecycle["closed_unmerged_branch_delete_after_days"]:
            actions.append({"action": "DELETE_BRANCH", "branch": name, "reason": "closed-unmerged PR grace expired"})
        elif branch.get("orphan_age_days", 0) >= lifecycle["orphan_branch_report_after_days"]:
            actions.append({"action": "REPORT_ORPHAN_BRANCH", "branch": name, "reason": "no active PR"})

    for pr in snapshot.get("pull_requests", []):
        if pr.get("state") != "open":
            continue
        labels = set(pr.get("labels", []))
        if "lifecycle:keep" in labels:
            continue
        age = pr.get("inactive_days", 0)
        if age >= lifecycle["stale_pr_after_days"] + lifecycle["stale_pr_close_after_additional_days"]:
            actions.append({"action": "CLOSE_STALE_PR", "number": pr.get("number")})
        elif age >= lifecycle["stale_pr_after_days"] and "lifecycle:stale" not in labels:
            actions.append({"action": "LABEL_STALE_PR", "number": pr.get("number")})

    for issue in snapshot.get("issues", []):
        if issue.get("state") != "open":
            continue
        labels = set(issue.get("labels", []))
        if "lifecycle:keep" in labels:
            continue
        age = issue.get("inactive_days", 0)
        if age >= lifecycle["stale_issue_after_days"] and "lifecycle:stale" not in labels:
            actions.append({"action": "LABEL_STALE_ISSUE", "number": issue.get("number")})
        if (
            lifecycle.get("stale_issue_auto_close")
            and "lifecycle:auto-close" in labels
            and age >= lifecycle["stale_issue_after_days"]
        ):
            actions.append({"action": "CLOSE_STALE_ISSUE", "number": issue.get("number")})

    return actions


def main() -> int:
    parser = argparse.ArgumentParser(prog="gumball-repository-os")
    parser.add_argument("--policy", default=".gumball/repository-os.json")
    sub = parser.add_subparsers(dest="command", required=True)

    ci = sub.add_parser("ci-plan")
    ci.add_argument("paths", nargs="*")

    labels = sub.add_parser("labels-plan")
    labels.add_argument("--title", required=True)
    labels.add_argument("paths", nargs="*")

    project = sub.add_parser("project-state")
    project.add_argument("--item-json", required=True)
    project.add_argument("--current")

    release = sub.add_parser("release-validate")
    release.add_argument("manifest")

    lifecycle = sub.add_parser("lifecycle-plan")
    lifecycle.add_argument("snapshot")

    args = parser.parse_args()
    policy = load_policy(Path(args.policy))

    if args.command == "ci-plan":
        print(json.dumps(plan_ci(args.paths), indent=2))
        return 0

    if args.command == "labels-plan":
        print(json.dumps(classify_pr(args.title, args.paths), indent=2))
        return 0

    if args.command == "project-state":
        item = json.loads(args.item_json)
        result = project_action(
            item,
            args.current,
            close_issue_on_done=policy["projects"]["close_issue_on_done"],
        )
        print(json.dumps(result, indent=2))
        return 0

    if args.command == "release-validate":
        manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
        problems = validate_release_manifest(manifest, policy)
        if problems:
            for problem in problems:
                print(f"release: FAIL - {problem}")
            return 1
        print("release: PASS")
        return 0

    if args.command == "lifecycle-plan":
        snapshot = json.loads(Path(args.snapshot).read_text(encoding="utf-8"))
        print(json.dumps(lifecycle_plan(snapshot, policy), indent=2))
        return 0

    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
