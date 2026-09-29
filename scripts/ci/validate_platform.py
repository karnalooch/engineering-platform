"""Validate engineering-platform workflow contracts without third-party parser dependencies."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = ROOT / ".github" / "workflows"
IMMUTABLE_SHA = re.compile(r"^[0-9a-f]{40}$")
USES = re.compile(r"^\s*(?:-\s*)?uses:\s*([^\s#]+)", re.MULTILINE)
FAIL_OPEN = re.compile(
    r"^\s*continue-on-error:\s*true\s*(?:#.*)?$",
    re.IGNORECASE | re.MULTILINE,
)

REQUIRED_GUMBALL_PATHS = (
    "AGENTS.md",
    "gumball.yaml",
    "docs/README.md",
    "docs/ARCHITECTURE.md",
    "docs/DOGFOODING.md",
    "docs/DIAGRAM_STYLE.md",
    "docs/ADOPTION.md",
    "docs/CI_MODEL.md",
    "docs/UPSTREAM_PROMOTION.md",
    "docs/ONE_PROMPT_BOOTSTRAP.md",
    "docs/MCP_AND_TOOLS.md",
    "docs/REPOSITORY_LIFECYCLE.md",
    "docs/PROJECTS_FLOW.md",
    "docs/RELEASE_LINEAGE.md",
    "docs/LABELS.md",
    "docs/CI_COST_GOVERNOR.md",
    ".gumball/repository-os.json",
    ".github/workflows/repository-ops.yml",
    "scripts/ops/repository_os.py",
    "scripts/ops/github_ops.py",
    "scripts/ci/test_repository_os.py",
    "scripts/ci/test_github_ops.py",
    "templates/release-manifest.json",
    "profiles/standard.yaml",
    "tools/capabilities.yaml",
    "scripts/gumball.py",
    "scripts/ci/check_docs_index.py",
    "scripts/ci/evaluate_aggregate.py",
    "scripts/ci/assert_nonempty.py",
    "scripts/ci/test_gumball.py",
    "scripts/ci/test_ci_primitives.py",
)


def main() -> int:
    problems: list[str] = []
    workflows = sorted([*WORKFLOWS.glob("*.yml"), *WORKFLOWS.glob("*.yaml")])

    if not workflows:
        problems.append("no workflow files discovered")

    for relative in REQUIRED_GUMBALL_PATHS:
        if not (ROOT / relative).is_file():
            problems.append(f"missing required Gumball contract: {relative}")

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
