from __future__ import annotations

import argparse
import subprocess
from dataclasses import dataclass
from typing import Iterable


DOC_ONLY_ROOT_FILES = frozenset({"README.md", "CHANGELOG.md"})


@dataclass(frozen=True)
class CiPlan:
    classification: str
    security_required: bool
    reason: str


def _normalize(paths: Iterable[str]) -> list[str]:
    normalized: list[str] = []
    for raw in paths:
        path = raw.strip().replace("\\", "/").lstrip("./")
        if path:
            normalized.append(path)
    return normalized


def plan_for_paths(paths: Iterable[str]) -> CiPlan:
    changed = _normalize(paths)
    if not changed:
        return CiPlan(
            classification="full",
            security_required=True,
            reason="empty change set fails closed",
        )

    docs_only = all(
        path.startswith("docs/") or path in DOC_ONLY_ROOT_FILES
        for path in changed
    )
    if docs_only:
        return CiPlan(
            classification="docs-only",
            security_required=False,
            reason="all changed paths are documentation-only",
        )

    return CiPlan(
        classification="full",
        security_required=True,
        reason="non-documentation or mixed change requires security baseline",
    )


def plan_for_event(event_name: str, paths: Iterable[str]) -> CiPlan:
    if event_name != "pull_request":
        return CiPlan(
            classification="full",
            security_required=True,
            reason=f"{event_name or 'unknown'} event fails safe to full validation",
        )
    return plan_for_paths(paths)


def changed_paths(base_sha: str, head_sha: str) -> list[str]:
    if not base_sha or not head_sha:
        raise ValueError("pull_request planning requires base and head SHAs")
    completed = subprocess.run(
        ["git", "diff", "--name-only", base_sha, head_sha],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.splitlines()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Plan Gumball CI from event type and changed paths."
    )
    parser.add_argument("--event-name", required=True)
    parser.add_argument("--base-sha", default="")
    parser.add_argument("--head-sha", default="")
    parser.add_argument("--path", action="append", default=[])
    args = parser.parse_args()

    paths = list(args.path)
    if args.event_name == "pull_request" and not paths:
        try:
            paths = changed_paths(args.base_sha, args.head_sha)
        except (ValueError, subprocess.CalledProcessError) as exc:
            plan = CiPlan(
                classification="full",
                security_required=True,
                reason=f"path discovery failed closed: {type(exc).__name__}",
            )
        else:
            plan = plan_for_event(args.event_name, paths)
    else:
        plan = plan_for_event(args.event_name, paths)

    print(f"classification={plan.classification}")
    print(f"security_required={'true' if plan.security_required else 'false'}")
    print(f"reason={plan.reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
