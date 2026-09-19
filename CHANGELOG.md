# Changelog

All notable engineering-platform contract changes are recorded here.

## 0.3.1

Planned in issue #17.

- upgrade `actions/setup-python` to v7.0.0 at immutable SHA `5fda3b95a4ea91299a34e894583c3862153e4b97`;
- upgrade `actions/checkout` to v7.0.1 at immutable SHA `3d3c42e5aac5ba805825da76410c181273ba90b1`;
- keep privileged auto-merge on trusted default-branch checkout only;
- update privileged-workflow contract tests for the refreshed action SHAs;
- no intended reusable workflow caller-interface change.

Canonical consumer SHA: assigned from the v0.3.1 squash-merge commit after merge.


## 0.3.0

Planned in issue #10.

- add trusted-default-branch fail-closed auto-merge controller;
- require explicit `Auto-merge: eligible` opt-in;
- independently classify high-risk paths from trusted `main` code;
- require exact green `Aggregate CI gate` and `Governance policy / Governance guard` checks;
- block Draft/fork/non-owner/high-risk/unresolved/changes-requested/unlinked/unknown-mergeability pull requests;
- update behind branches but wait for fresh checks before reconsidering merge;
- require a same-repository closing Issue;
- merge only by squash with the exact reviewed head SHA;
- run hourly reconciliation for safe retry after review-thread resolution;
- self-test auto-merge policy and privileged-workflow safety inside platform CI.

Canonical commit: `ae76f1b9f38368dc8dd21e5b0dccb36fa748ad4f`.


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

Canonical commit: `a4c0f579aa10b495835dca3f78f84a79538392cf`.

## 0.1.0

Bootstrap baseline.

Canonical commit: `b34fda2ef31bf62e00422f8531202e2cccc3bc73`.

- reusable repository/LFS policy;
- reusable Dependency Review, CodeQL, Trivy and CycloneDX SBOM baseline;
- reusable OpenSSF Scorecard;
- platform self-validation;
- fail-closed local `Aggregate CI gate` contract;
- immutable consumer-SHA policy.
