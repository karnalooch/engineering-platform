#!/usr/bin/env python3
"""Validate the Gumball documentation entrypoint contract."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
INDEX = DOCS / "README.md"
ROOT_README = ROOT / "README.md"
LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")

REQUIRED_HEADINGS = {
    "# Gumball documentation",
    "## What Gumball is",
    "## Authority map",
    "## Operating principles",
    "## Current compatibility note",
}

REQUIRED_LINKS = {
    "ARCHITECTURE.md",
    "DOGFOODING.md",
    "DIAGRAM_STYLE.md",
    "ADOPTION.md",
    "CI_MODEL.md",
    "UPSTREAM_PROMOTION.md",
    "ONE_PROMPT_BOOTSTRAP.md",
    "MCP_AND_TOOLS.md",
    "REPOSITORY_LIFECYCLE.md",
    "PROJECTS_FLOW.md",
    "RELEASE_LINEAGE.md",
    "LABELS.md",
    "CI_COST_GOVERNOR.md",
    "CONTRACT.md",
    "AGGREGATE_GATE.md",
    "GOVERNANCE_GUARD.md",
    "AUTO_MERGE.md",
    "VERSIONING.md",
    "ROLLOUT.md",
}


def read_utf8(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    if "\ufffd" in text:
        raise ValueError(
            f"{path.relative_to(ROOT)} contains Unicode replacement characters"
        )
    return text


def local_targets(source: Path, text: str) -> set[Path]:
    targets: set[Path] = set()
    for raw in LINK_RE.findall(text):
        raw = raw.strip().strip("<>")
        split = urlsplit(raw)
        if split.scheme or raw.startswith("//") or raw.startswith("#") or not split.path:
            continue

        relative = unquote(split.path)
        candidate = (
            ROOT / relative.lstrip("/")
            if relative.startswith("/")
            else source.parent / relative
        ).resolve()

        if not candidate.is_relative_to(ROOT):
            raise ValueError(
                f"{source.relative_to(ROOT)} links outside repository: {raw}"
            )
        targets.add(candidate)
    return targets


def fail(message: str) -> int:
    print(f"docs-index: FAIL - {message}", file=sys.stderr)
    return 1


def main() -> int:
    if not INDEX.is_file():
        return fail("docs/README.md is missing")
    if not ROOT_README.is_file():
        return fail("README.md is missing")

    try:
        index_text = read_utf8(INDEX)
        root_text = read_utf8(ROOT_README)
        print("docs-index: i18n PASS - UTF-8 entrypoints are readable")

        missing_headings = sorted(REQUIRED_HEADINGS - set(index_text.splitlines()))
        if missing_headings:
            return fail("missing headings: " + ", ".join(missing_headings))
        if "(docs/README.md)" not in root_text:
            return fail("README.md must link to docs/README.md")

        index_targets = local_targets(INDEX, index_text)
        root_targets = local_targets(ROOT_README, root_text)
        indexed_docs = {
            path.relative_to(DOCS).as_posix()
            for path in index_targets
            if path.is_relative_to(DOCS)
        }

        missing_required = sorted(REQUIRED_LINKS - indexed_docs)
        if missing_required:
            return fail("missing authority links: " + ", ".join(missing_required))
        print("docs-index: structure PASS")

        broken = sorted(
            str(path.relative_to(ROOT))
            for path in index_targets | root_targets
            if not path.exists()
        )
        if broken:
            return fail("broken local links: " + ", ".join(broken))
        print("docs-index: links PASS")

        top_level = {path.name for path in DOCS.glob("*.md") if path != INDEX}
        indexed_top_level = {
            path.name
            for path in index_targets
            if path.parent == DOCS and path.suffix.lower() == ".md"
        }
        missing_top_level = sorted(top_level - indexed_top_level)
        if missing_top_level:
            return fail(
                "top-level docs missing from index: " + ", ".join(missing_top_level)
            )
        print("docs-index: catalog PASS")
    except (OSError, UnicodeError, ValueError) as exc:
        return fail(str(exc))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
