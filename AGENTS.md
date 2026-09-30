# Gumball — AI engineering rules

## Purpose

Gumball is the shared engineering platform for repositories owned by `karnalooch`. It provides reusable CI, security, governance, documentation and agent-workflow contracts.

The repository is currently hosted at `karnalooch/engineering-platform` for compatibility with existing immutable consumer pins. Treat **Gumball** as the product name. Do not change consumer repository coordinates without an explicit migration plan.

## Start here

Before changing the platform, read:

1. `docs/README.md`
2. `docs/ARCHITECTURE.md`
3. the authoritative document for the affected contract
4. existing tests for that contract

## Core invariants

- Preserve fail-closed behavior.
- Never weaken a gate merely to obtain green CI.
- External Actions and reusable workflows stay pinned to immutable 40-character SHAs.
- The final `Aggregate CI gate` remains caller-local.
- Shared platform code must not silently decide that an application-specific proof is optional.
- Prefer deterministic, low-cost PR validation. Heavy runtime, visual, hardware or release evidence belongs in explicit profiles or release/full-validation lanes.
- A skipped check is not proof unless the contract explicitly classifies it as not applicable.

## Downstream -> upstream feedback

Consumer repositories are incubation environments for engineering improvements.

When YACS, 4VELO, ONICS, Karoo or another consumer introduces a useful improvement to CI, governance, security, documentation, tooling, MCP usage or agent workflow:

1. decide whether the improvement is project-specific or reusable;
2. preserve project-specific implementation downstream;
3. extract the reusable invariant, interface and failure behavior;
4. record evidence from the downstream repository;
5. add contract tests in Gumball;
6. promote the generalized mechanism only after the contract is clear.

Use `docs/UPSTREAM_PROMOTION.md` for the promotion contract.

## Tooling authority

Before inventing project tooling, apply `docs/TOOLING_AUTHORITY.md`: review proven public patterns/already-reviewed tools, then platform-native capability, then proven OSS/DCC, and only then minimal custom tooling. Accepted tool output must return deterministically to version control; SaaS-only state is not an engineering SSOT.

Keep editor/dev/proof tools outside shipping artifacts by default, record exact upstream/license/lock provenance for production tooling, and prefer bounded domain operations over broad low-level agent APIs.

For visual profiles, use `docs/VISUAL_ENGINEERING.md`: composition first, repo-owned artifacts, production-component workbenches, deterministic fixtures and asset-off inspection.

## Documentation

`docs/README.md` is the documentation router and authority map.

Use `docs/DIAGRAM_STYLE.md` for new or substantially revised architecture, CI, tooling, agent and data-flow diagrams. The shared style is part of the consumer baseline and must be propagated conservatively without overwriting a stronger project-owned visual convention.

Changes to platform behavior, caller contracts, release policy, CI policy, adoption behavior or agent policy must update the relevant authoritative document in the same PR.

Do not create a parallel document when an existing SSOT owns the subject.

## Adoption safety

Gumball must be safe for both greenfield and existing repositories.

- Audit before modifying.
- Plan before applying.
- Preserve local project decisions.
- Never overwrite an existing `AGENTS.md`, documentation index, CI workflow or security policy blindly.
- Unknown or ambiguous runtime/configuration surfaces fail safe toward broader validation.
- Generated or managed sections must be distinguishable from project-owned sections.

## Repository operating system

Gumball-enabled repositories should keep work surfaces and release evidence finite and synchronized.

- branches from merged/closed work are cleaned according to `.gumball/repository-os.json`;
- PRs use the shared `type:*`, `area:*`, `risk:*` and `ci:*` label namespaces;
- GitHub Projects represents repository reality and is reconciled from issue/PR state;
- moving an issue to Project `Done` may close it only when policy explicitly enables that behavior;
- releasable application artifacts carry exact version, stage, source SHA and artifact digest;
- promote the same verified artifact between stages rather than rebuilding;
- plan CI cost before starting heavy work and reuse a verified build fingerprint when possible;
- heavyweight runtime/visual/hardware proofs are deferred to explicit lanes unless merge-critical;
- broker-managed heavy proofs are requested by policy/label/comment, bind the exact PR SHA, dedupe/reuse existing work, and keep manual workflow_dispatch only as fallback.

Read `docs/REPOSITORY_LIFECYCLE.md`, `docs/PROJECTS_FLOW.md`, `docs/RELEASE_LINEAGE.md`, `docs/LABELS.md`, `docs/CI_COST_GOVERNOR.md` and `docs/PROOF_BROKER.md` before changing those contracts.

## Validation

For repository changes:

- run `python scripts/gumball.py doctor`;
- run `python -m unittest scripts/ci/test_gumball.py -v`;
- run the existing platform workflow contract tests relevant to the change;
- review the final diff;
- report checks as PASS, FAIL, BLOCKED or NOT RUN.

Never claim a proof that was not actually executed.

Gumball must also satisfy its own baseline. Changes to platform policy or tooling must keep `docs/DOGFOODING.md` true and `gumball doctor` green on the source repository.
