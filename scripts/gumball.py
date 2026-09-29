#!/usr/bin/env python3
"""Gumball repository audit, adoption and promotion helper.

The tool is intentionally standard-library-only so it can run before a consumer
repository has installed project dependencies.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

SHA40 = re.compile(r"^[0-9a-f]{40}$")
USES = re.compile(r"^\s*(?:-\s*)?uses:\s*([^\s#]+)", re.MULTILINE)
FAIL_OPEN = re.compile(
    r"^\s*continue-on-error:\s*true\s*(?:#.*)?$",
    re.IGNORECASE | re.MULTILINE,
)
WRITE_ALL = re.compile(
    r"^\s*permissions:\s*write-all\s*(?:#.*)?$",
    re.IGNORECASE | re.MULTILINE,
)
AGGREGATE_NAME = re.compile(
    r"""^\s*name:\s*["']?Aggregate CI gate["']?\s*(?:#.*)?$""",
    re.MULTILINE,
)
AGGREGATE_ALWAYS = re.compile(
    r"""^\s*if:\s*["']?\$\{\{\s*always\(\)\s*\}\}["']?\s*(?:#.*)?$""",
    re.MULTILINE,
)

PROFILE_CHOICES = (
    "standard",
    "monorepo",
    "mobile",
    "unreal",
    "release-critical",
)

CANDIDATE_FIELDS = {
    "id",
    "source",
    "category",
    "problem",
    "invariant",
    "evidence",
    "do_not_copy",
    "failure_behavior",
    "status",
}
CANDIDATE_STATES = {"candidate", "proven", "platform"}


def _workflow_files(root: Path) -> list[Path]:
    workflows = root / ".github" / "workflows"
    if not workflows.exists():
        return []
    return sorted([*workflows.glob("*.yml"), *workflows.glob("*.yaml")])


def _has_fail_closed_aggregate(root: Path) -> bool:
    for path in _workflow_files(root):
        text = path.read_text(encoding="utf-8")
        if not AGGREGATE_NAME.search(text):
            continue

        lines = text.splitlines()
        for index, line in enumerate(lines):
            if not AGGREGATE_NAME.fullmatch(line):
                continue
            indent = len(line) - len(line.lstrip(" "))
            start = index
            while start > 0:
                candidate = lines[start - 1]
                if candidate.strip() and len(candidate) - len(candidate.lstrip(" ")) < indent:
                    break
                start -= 1
            end = index + 1
            while end < len(lines):
                candidate = lines[end]
                if candidate.strip() and len(candidate) - len(candidate.lstrip(" ")) < indent:
                    break
                end += 1
            if any(AGGREGATE_ALWAYS.fullmatch(candidate) for candidate in lines[start:end]):
                return True
    return False


def _workflow_problems(root: Path) -> list[str]:
    problems: list[str] = []
    for path in _workflow_files(root):
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(root)

        if FAIL_OPEN.search(text):
            problems.append(f"{rel}: fail-open continue-on-error: true")
        if WRITE_ALL.search(text):
            problems.append(f"{rel}: permissions: write-all")

        for match in USES.finditer(text):
            target = match.group(1)
            if target.startswith("./") or target.startswith("docker://"):
                continue
            if "@" not in target:
                problems.append(f"{rel}: external use lacks immutable ref: {target}")
                continue
            _, ref = target.rsplit("@", 1)
            if not SHA40.fullmatch(ref):
                problems.append(f"{rel}: external use is not pinned to 40-char SHA: {target}")
    return problems


def _detect_capabilities(root: Path) -> dict[str, bool]:
    return {
        "python": (root / "pyproject.toml").exists()
        or any(root.glob("requirements*.txt"))
        or any(root.glob("**/requirements*.txt")),
        "node": (root / "package.json").exists()
        or (root / "pnpm-workspace.yaml").exists()
        or (root / "yarn.lock").exists(),
        "monorepo": (root / "pnpm-workspace.yaml").exists()
        or (root / "turbo.json").exists()
        or (root / "nx.json").exists(),
        "unreal": any(root.glob("*.uproject")) or any(root.glob("**/*.uproject")),
        "mobile": (root / "eas.json").exists()
        or (root / "mobile" / "eas.json").exists()
        or (root / "android").exists()
        or (root / "mobile" / "android").exists(),
        "docker": bool(list(root.glob("Dockerfile*")))
        or bool(list(root.glob("**/Dockerfile*")))
        or bool(list(root.glob("docker-compose*.yml")))
        or bool(list(root.glob("compose*.yml"))),
        "mcp_config": any(
            (root / candidate).exists()
            for candidate in (".mcp.json", "mcp.json", ".cursor/mcp.json", ".vscode/mcp.json")
        ),
    }


def audit_repository(root: Path) -> dict[str, Any]:
    root = root.resolve()
    workflow_files = _workflow_files(root)
    return {
        "root": str(root),
        "capabilities": _detect_capabilities(root),
        "contracts": {
            "gumball_config": (root / "gumball.yaml").exists(),
            "agents": (root / "AGENTS.md").exists(),
            "docs_index": (root / "docs" / "README.md").exists(),
            "aggregate_gate": _has_fail_closed_aggregate(root),
            "workflow_count": len(workflow_files),
            "workflow_problems": _workflow_problems(root),
        },
    }


def plan_repository(audit: dict[str, Any]) -> list[dict[str, str]]:
    contracts = audit["contracts"]
    actions: list[dict[str, str]] = []

    for key, path in (
        ("gumball_config", "gumball.yaml"),
        ("agents", "AGENTS.md"),
        ("docs_index", "docs/README.md"),
    ):
        if contracts[key]:
            actions.append({"action": "KEEP", "path": path, "reason": "already present; inspect before modifying"})
        else:
            actions.append({"action": "ADD", "path": path, "reason": "missing baseline contract"})

    if contracts["aggregate_gate"]:
        actions.append({"action": "KEEP", "path": ".github/workflows/*", "reason": "fail-closed Aggregate CI gate detected"})
    else:
        actions.append({"action": "MODIFY", "path": ".github/workflows/*", "reason": "caller-local fail-closed Aggregate CI gate is missing"})

    if contracts["workflow_problems"]:
        actions.append({"action": "MODIFY", "path": ".github/workflows/*", "reason": "workflow safety violations detected"})

    if audit["capabilities"]["monorepo"]:
        actions.append({"action": "PLAN", "path": "CI classifier", "reason": "monorepo detected; evaluate affected-test and anti-no-op contracts"})
    if audit["capabilities"]["unreal"]:
        actions.append({"action": "PLAN", "path": "unreal profile", "reason": "Unreal project detected; keep runtime/visual proof consumer-owned"})
    if audit["capabilities"]["mobile"]:
        actions.append({"action": "PLAN", "path": "mobile profile", "reason": "mobile/native surface detected; separate PR smoke from release proof"})
    if audit["capabilities"]["mcp_config"]:
        actions.append({"action": "KEEP", "path": "MCP/tool config", "reason": "existing MCP configuration detected; preserve endpoints/secrets and map capabilities instead of replacing it"})

    return actions


def doctor_repository(root: Path) -> tuple[bool, list[tuple[str, str, str]]]:
    audit = audit_repository(root)
    contracts = audit["contracts"]
    checks: list[tuple[str, str, str]] = []

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append((name, "PASS" if ok else "FAIL", detail))

    add("gumball config", contracts["gumball_config"], "gumball.yaml")
    add("agent contract", contracts["agents"], "AGENTS.md")
    add("docs index", contracts["docs_index"], "docs/README.md")
    add("workflow discovery", contracts["workflow_count"] > 0, f"{contracts['workflow_count']} workflow(s)")
    add("aggregate gate", contracts["aggregate_gate"], "caller-local fail-closed Aggregate CI gate")

    workflow_problems = contracts["workflow_problems"]
    add(
        "workflow safety",
        not workflow_problems,
        "no mutable external refs / fail-open controls"
        if not workflow_problems
        else "; ".join(workflow_problems),
    )

    return all(status == "PASS" for _, status, _ in checks), checks


def _generated_config(profile: str) -> str:
    return f"""schema_version: 1
name: Gumball
profile: {profile}
adoption:
  mode: preserve-local
ci:
  aggregate_gate: caller-local
  fail_closed: true
  anti_noop: true
agents:
  preserve_local_instructions: true
  evaluate_upstream_promotion: true
"""


def _generated_agents() -> str:
    return """# Repository agent rules

## Gumball baseline

- Read the repository and its documentation entry point before editing.
- Preserve project-specific contracts and stronger local safety controls.
- Do not weaken tests or CI to obtain green results.
- Keep the final Aggregate CI gate caller-local and fail closed.
- Use immutable external Action/workflow references.
- Treat heavy runtime, visual, emulator and hardware proof as explicit project/profile policy.
- Evaluate reusable CI, governance, security, docs, tooling, MCP and agent-workflow improvements for promotion back to Gumball.
- Report validation as PASS, FAIL, BLOCKED or NOT RUN.
"""


def _generated_docs_index() -> str:
    return """# Documentation

This file is the documentation entry point.

Before implementation, identify the authoritative document for the affected area.
Historical snapshots and evidence do not override a current SSOT.

## Authority map

Populate this table with project-owned sources of truth before treating Gumball adoption as complete.

| Area | Authoritative document |
|---|---|
| Product / scope | TODO |
| Architecture | TODO |
| Development | TODO |
| CI / release | TODO |
"""


def apply_baseline(root: Path, profile: str, write: bool) -> list[tuple[str, str]]:
    root = root.resolve()
    planned = [
        (root / "gumball.yaml", _generated_config(profile)),
        (root / "AGENTS.md", _generated_agents()),
        (root / "docs" / "README.md", _generated_docs_index()),
        (root / ".gumball" / "candidates" / "README.md",
         "# Gumball promotion candidates\n\nRecord reusable downstream engineering improvements here.\n"),
    ]

    results: list[tuple[str, str]] = []
    for path, content in planned:
        rel = str(path.relative_to(root))
        if path.exists():
            results.append((rel, "KEEP existing"))
            continue
        if not write:
            results.append((rel, "ADD (dry-run)"))
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        results.append((rel, "ADDED"))
    return results


def scan_candidates(root: Path) -> tuple[bool, list[str]]:
    candidate_dir = root.resolve() / ".gumball" / "candidates"
    messages: list[str] = []
    ok = True

    if not candidate_dir.exists():
        return True, ["no candidate directory"]

    files = sorted(candidate_dir.glob("*.json"))
    if not files:
        return True, ["no JSON promotion candidates"]

    for path in files:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            ok = False
            messages.append(f"{path.name}: invalid JSON: {exc}")
            continue

        missing = sorted(CANDIDATE_FIELDS - set(payload))
        if missing:
            ok = False
            messages.append(f"{path.name}: missing fields: {', '.join(missing)}")
            continue

        if payload.get("status") not in CANDIDATE_STATES:
            ok = False
            messages.append(f"{path.name}: invalid status {payload.get('status')!r}")
            continue

        messages.append(f"{path.name}: {payload['status']} / {payload['category']} / {payload['id']}")

    return ok, messages


def _repo_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--repo", default=".", help="Repository root (default: current directory)")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="gumball", description="Gumball engineering-platform helper")
    sub = parser.add_subparsers(dest="command", required=True)

    audit = sub.add_parser("audit", help="Inspect repository capabilities and baseline contracts")
    _repo_arg(audit)

    plan = sub.add_parser("plan", help="Produce a conservative adoption plan")
    _repo_arg(plan)

    doctor = sub.add_parser("doctor", help="Validate required Gumball repository contracts")
    _repo_arg(doctor)

    apply = sub.add_parser("apply", help="Create only missing baseline files; never overwrite existing files")
    _repo_arg(apply)
    apply.add_argument("--profile", choices=PROFILE_CHOICES, default="standard")
    apply.add_argument("--write", action="store_true", help="Actually create missing files; default is dry-run")

    promote = sub.add_parser("promote", help="Validate downstream promotion candidates")
    _repo_arg(promote)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.repo)

    if args.command == "audit":
        print(json.dumps(audit_repository(root), indent=2, sort_keys=True))
        return 0

    if args.command == "plan":
        audit = audit_repository(root)
        for item in plan_repository(audit):
            print(f"{item['action']:>6}  {item['path']}: {item['reason']}")
        return 0

    if args.command == "doctor":
        ok, checks = doctor_repository(root)
        for name, status, detail in checks:
            print(f"{status:4}  {name}: {detail}")
        return 0 if ok else 1

    if args.command == "apply":
        for path, result in apply_baseline(root, args.profile, args.write):
            print(f"{result:13} {path}")
        if not args.write:
            print("dry-run only; re-run with --write to create missing baseline files")
        return 0

    if args.command == "promote":
        ok, messages = scan_candidates(root)
        for message in messages:
            print(message)
        return 0 if ok else 1

    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
