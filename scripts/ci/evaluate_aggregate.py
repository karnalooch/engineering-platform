#!/usr/bin/env python3
"""Fail-closed aggregate evaluation reusable across Gumball consumers."""

from __future__ import annotations

import json
import os
import sys
from typing import Any


KNOWN_RESULTS = {"success", "failure", "cancelled", "skipped"}


def _string_list(value: Any, name: str) -> tuple[list[str] | None, str | None]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        return None, f"{name}: expected a JSON array of non-empty strings"
    if len(set(value)) != len(value):
        return None, f"{name}: duplicate job names are not allowed"
    return value, None


def evaluate(
    needs: Any,
    expected_jobs: Any,
    allowed_skipped_jobs: Any | None = None,
) -> tuple[bool, list[str]]:
    reasons: list[str] = []

    if not isinstance(needs, dict):
        return False, ["needs: expected a JSON object"]

    expected, error = _string_list(expected_jobs, "expected_jobs")
    if error:
        return False, [error]
    assert expected is not None
    if not expected:
        return False, ["expected_jobs: empty required set would create a no-op aggregate"]

    allowed_raw = [] if allowed_skipped_jobs is None else allowed_skipped_jobs
    allowed, error = _string_list(allowed_raw, "allowed_skipped_jobs")
    if error:
        return False, [error]
    assert allowed is not None

    unknown_allowed = sorted(set(allowed) - set(expected))
    if unknown_allowed:
        reasons.append(
            "allowed_skipped_jobs contains non-required jobs: "
            + ", ".join(unknown_allowed)
        )

    for job in expected:
        entry = needs.get(job)
        if not isinstance(entry, dict):
            reasons.append(f"{job}: missing required job result")
            continue

        result = entry.get("result")
        if result not in KNOWN_RESULTS:
            reasons.append(f"{job}: missing or unknown result {result!r}")
            continue

        if result == "success":
            continue
        if result == "skipped" and job in allowed:
            continue

        expected_text = "success or explicit skipped" if job in allowed else "success"
        reasons.append(f"{job}: expected {expected_text}, got {result}")

    return (not reasons), reasons


def _load_json_env(name: str, default: Any = None) -> Any:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{name}: invalid JSON: {exc}") from exc


def main() -> int:
    try:
        needs = _load_json_env("CI_NEEDS_JSON", {})
        expected = _load_json_env("CI_EXPECTED_JOBS_JSON", [])
        allowed = _load_json_env("CI_ALLOWED_SKIPPED_JOBS_JSON", [])
    except ValueError as exc:
        print(f"aggregate: FAIL - {exc}", file=sys.stderr)
        return 1

    ok, reasons = evaluate(needs, expected, allowed)
    if ok:
        print("aggregate: PASS")
        return 0

    print("aggregate: FAIL", file=sys.stderr)
    for reason in reasons:
        print(f"  - {reason}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
