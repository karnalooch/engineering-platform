"""Validate engineering-platform workflow contracts without third-party parser dependencies."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = ROOT / ".github" / "workflows"
IMMUTABLE_SHA = re.compile(r"^[0-9a-f]{40}$")
USES = re.compile(r"^\s*uses:\s*([^\s#]+)", re.MULTILINE)
FAIL_OPEN = re.compile(
    r"^\s*continue-on-error:\s*true\s*(?:#.*)?$",
    re.IGNORECASE | re.MULTILINE,
)


def main() -> int:
    problems: list[str] = []
    workflows = sorted([*WORKFLOWS.glob("*.yml"), *WORKFLOWS.glob("*.yaml")])

    if not workflows:
        problems.append("no workflow files discovered")

    for path in workflows:
        text = path.read_text(encoding="utf-8")

        if "permissions:" not in text:
            problems.append(f"{path.relative_to(ROOT)}: missing explicit permissions")

        if FAIL_OPEN.search(text):
            problems.append(
                f"{path.relative_to(ROOT)}: fail-open continue-on-error is forbidden"
            )

        if path.name.startswith("reusable-") and "workflow_call:" not in text:
            problems.append(
                f"{path.relative_to(ROOT)}: reusable workflow lacks workflow_call"
            )

        for match in USES.finditer(text):
            target = match.group(1)
            if target.startswith("./") or target.startswith("docker://"):
                continue
            if "@" not in target:
                problems.append(
                    f"{path.relative_to(ROOT)}: external action lacks a ref: {target}"
                )
                continue
            _, ref = target.rsplit("@", 1)
            if not IMMUTABLE_SHA.fullmatch(ref):
                problems.append(
                    f"{path.relative_to(ROOT)}: external action is not pinned "
                    f"to an immutable 40-char SHA: {target}"
                )

    if problems:
        print("platform contract: FAIL", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        return 1

    print(f"platform contract: PASS ({len(workflows)} workflows checked)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
