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
- `docs/AGGREGATE_GATE.md` — fail-closed caller-side aggregate pattern.

## Consumer rule

Callers must pin reusable workflows to a reviewed immutable commit SHA. Do **not** consume this repository from `@main`.

See `docs/CONTRACT.md` and `docs/ROLLOUT.md`.

Bootstrap tracking: #1.
