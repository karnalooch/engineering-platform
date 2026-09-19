# engineering-platform

Shared, versioned CI/security/governance building blocks for repositories owned by `karnalooch`.

Application code stays in its product repository. This repository contains reusable engineering controls only.

## Consumers

- `karnalooch/YetAnotherCyclingSim`
- `karnalooch/stunning-pancake` (4VELO), migrated incrementally after live proof

## Available contracts

- `.github/workflows/reusable-repo-policy.yml` — parameterized repository hygiene, Git LFS and oversized-blob enforcement.
- `.github/workflows/reusable-security.yml` — Dependency Review, CodeQL, Trivy and CycloneDX SBOM.
- `.github/workflows/reusable-scorecard.yml` — OpenSSF Scorecard + SARIF upload.
- `.github/workflows/reusable-governance.yml` — PR risk classification, immutable-ref enforcement and fail-closed governance checks.
- `docs/AGGREGATE_GATE.md` — fail-closed caller-side aggregate pattern.
- `docs/GOVERNANCE_GUARD.md` — governance and high-risk merge contract.

## Consumer rule

Callers must pin reusable workflows to a reviewed immutable commit SHA. Do **not** consume this repository from `@main`.

The final `Aggregate CI gate` stays local to every consumer so application-specific checks cannot be silently dropped by a shared workflow.

See `docs/CONTRACT.md`, `docs/GOVERNANCE_GUARD.md` and `docs/ROLLOUT.md`.
