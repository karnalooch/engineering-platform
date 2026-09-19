# Changelog

All notable engineering-platform contract changes are recorded here.

## 0.2.0

Planned in PR #9.

- add reusable governance guard;
- classify high-risk pull requests from the actual diff;
- require `Auto-merge: manual` for high-risk changes;
- enforce immutable 40-character SHA refs for external Actions/workflows;
- enforce immutable engineering-platform consumer refs;
- reject fail-open `continue-on-error: true`;
- reject workflow-level `permissions: write-all`;
- verify a real caller-local `Aggregate CI gate` with a job-level fail-closed `always()` path;
- make the platform's own aggregate depend on governance;
- make baseline governance non-disableable by caller input;
- improve structural platform validation to avoid false positives in embedded scripts.

Canonical consumer SHA: assigned from the PR #9 squash-merge commit after merge.

## 0.1.0

Bootstrap baseline.

Canonical commit: `b34fda2ef31bf62e00422f8531202e2cccc3bc73`.

- reusable repository/LFS policy;
- reusable Dependency Review, CodeQL, Trivy and CycloneDX SBOM baseline;
- reusable OpenSSF Scorecard;
- platform self-validation;
- fail-closed local `Aggregate CI gate` contract;
- immutable consumer-SHA policy.
