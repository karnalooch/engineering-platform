from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / "tools" / "authority-policy.json"


def main() -> int:
    problems: list[str] = []

    try:
        policy = json.loads(POLICY.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FAIL tooling authority policy: {exc}")
        return 1

    expected_order = [
        "proven_public_pattern_or_reviewed_tool",
        "platform_native_capability",
        "proven_open_source_or_dcc",
        "minimal_project_owned_custom",
    ]

    checks = [
        (policy.get("schema_version") == 1, "schema_version must be 1"),
        (policy.get("authority") == "repository", "repository must be authoritative"),
        (policy.get("admission_order") == expected_order, "tool admission order drifted"),
        (
            policy.get("external_tool_eligibility", {}).get(
                "repository_native_or_deterministic_return_path"
            )
            is True,
            "authoritative external tooling needs deterministic repository return path",
        ),
        (
            policy.get("external_tool_eligibility", {}).get("saas_only_authority")
            == "research-only",
            "SaaS-only state must remain research-only",
        ),
        (
            policy.get("generated_artifacts", {}).get("freshness")
            == "content-or-digest",
            "generated artifact freshness must use content/digest",
        ),
        (
            policy.get("generated_artifacts", {}).get("mtime_only_forbidden") is True,
            "mtime-only freshness must be forbidden",
        ),
        (
            policy.get("provenance", {}).get("exact_upstream_revision") is True
            and policy.get("provenance", {}).get("license_evidence") is True
            and policy.get("provenance", {}).get(
                "lock_production_tool_dependency_graph"
            )
            is True,
            "tool provenance/lock contract drifted",
        ),
        (
            policy.get("lifecycle", {}).get(
                "dev_editor_proof_tools_shipping_default"
            )
            == "excluded",
            "dev/editor/proof tooling must be excluded from shipping by default",
        ),
        (
            policy.get("agent_api", {}).get("prefer_bounded_domain_operations")
            is True,
            "bounded domain operations must be preferred",
        ),
        (
            policy.get("validation", {}).get("ambiguous_required_boundary")
            == "fail-closed",
            "ambiguous required tooling boundary must fail closed",
        ),
    ]

    for ok, detail in checks:
        if not ok:
            problems.append(detail)

    surfaces = {
        "docs/TOOLING_AUTHORITY.md": (
            "## Admission order",
            "## Repository return path",
            "content equality",
            "excluded from shipping/runtime artifacts by default",
        ),
        "docs/VISUAL_ENGINEERING.md": (
            "asset-off test",
            "production components",
            "deterministic fixtures",
            "hard dev/vision-only boundary",
        ),
        "profiles/mobile.yaml": (
            "visual_composition_authority: recommended",
            "deterministic_visual_workbench: recommended",
            "deterministic_design_interchange: recommended",
        ),
        "profiles/unreal.yaml": (
            "proven_tooling_first: required",
            "editor_tool_shipping_boundary: required",
            "production_tool_dependency_lock: required",
            "tool_provenance: required",
        ),
        "tools/capabilities.yaml": (
            "proven-tooling-before-custom-invention",
            "accepted-tool-output-requires-deterministic-repository-return-path",
            "generated-artifact-freshness-is-content-or-digest-not-mtime",
            "dev-editor-proof-tools-excluded-from-shipping-by-default",
        ),
    }

    for relative, markers in surfaces.items():
        path = ROOT / relative
        if not path.is_file():
            problems.append(f"missing tooling authority surface: {relative}")
            continue
        text = path.read_text(encoding="utf-8")
        for marker in markers:
            if marker not in text:
                problems.append(f"{relative}: missing contract marker: {marker}")

    if problems:
        for problem in problems:
            print(f"FAIL tooling authority: {problem}")
        return 1

    print("PASS tooling authority: repo authority, provenance, lifecycle and visual contracts locked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
