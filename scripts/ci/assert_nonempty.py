#!/usr/bin/env python3
"""Fail when a CI selector unexpectedly resolves to zero work."""

from __future__ import annotations

import argparse


def evaluate(count: int, minimum: int = 1) -> tuple[bool, str]:
    if minimum < 0:
        return False, "minimum must be >= 0"
    if count < 0:
        return False, "count must be >= 0"
    if count < minimum:
        return False, f"expected at least {minimum}, got {count}"
    return True, f"matched {count} (minimum {minimum})"


def main() -> int:
    parser = argparse.ArgumentParser(description="Gumball anti-no-op assertion")
    parser.add_argument("--label", required=True)
    parser.add_argument("--count", type=int, required=True)
    parser.add_argument("--minimum", type=int, default=1)
    args = parser.parse_args()

    ok, detail = evaluate(args.count, args.minimum)
    status = "PASS" if ok else "FAIL"
    print(f"{args.label}: {status} - {detail}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
