# Versioning policy

The engineering platform follows Semantic Versioning for its human-facing contract version.

## Current lines

- `v0.1.0` — bootstrap baseline; canonical commit `b34fda2ef31bf62e00422f8531202e2cccc3bc73`.
- `v0.2.0` — governance guard and non-bypassable shared governance baseline introduced by PR #9. The canonical consumer SHA is the squash-merge commit produced when PR #9 lands on `main`.

## Consumer pinning

Semantic versions are for humans, changelogs and upgrade intent.

Consumers execute reusable workflows from a reviewed immutable 40-character commit SHA. They do not use `@main`, moving major tags, or mutable release refs as the active executable pin.

Example:

```yaml
uses: karnalooch/engineering-platform/.github/workflows/reusable-security.yml@<reviewed-40-char-sha>
```

## SemVer rules

- PATCH: bug fix with no intended caller-contract change.
- MINOR: backward-compatible new capability or stronger default safety contract that callers can adopt without application redesign.
- MAJOR: incompatible caller contract, required-input removal/rename, workflow removal, or behavior that requires coordinated consumer migration.

Until `v1.0.0`, the platform is explicitly pre-stable. Even so, breaking changes must be called out and rolled out through a compatibility period rather than silently replacing a working caller contract.

## Release process

1. Change the platform on a dedicated branch and PR.
2. Set the intended version in `VERSION`.
3. Update `CHANGELOG.md`.
4. Self-prove the platform CI.
5. Merge manually.
6. Treat the resulting `main` merge SHA as the canonical immutable SHA for that version.
7. Upgrade YetAnotherCyclingSim as the canary consumer.
8. Only after canary proof, roll the version into other consumers such as 4VELO.

A Git tag or GitHub Release may mirror the semantic version for discovery, but the consumer's active workflow reference remains the immutable commit SHA.
