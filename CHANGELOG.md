# Changelog

All notable Gumball / engineering-platform contract changes are recorded here.

## 0.6.0 — Proof Broker

- add `.gumball/proof-broker.json` allow-list and broker policy;
- add trusted `.github/workflows/proof-broker.yml` orchestration from the default branch;
- allow authorized PR proof intent through `proof:<id>` labels and `/gumball proof <id>` comments;
- bind every broker request to the exact PR branch, 40-character source SHA and deterministic request id;
- require broker-managed target workflows to expose workflow_dispatch inputs and include the request id in `run-name`;
- block branch-local workflow definitions by default while the broker holds `actions: write`;
- reuse exact non-expired artifacts and successful proof runs instead of duplicating heavyweight work;
- refuse duplicate queued/running proofs and require explicit retry for failed runs;
- integrate automatic heavyweight proof dispatch with the CI Cost Governor: non-merge-critical automatic proof is deferred;
- keep manual workflow_dispatch on target workflows as an emergency fallback;
- add broker-owned proof request/status labels and hourly status reconciliation;
- propagate broker policy, workflow, runtime script and documentation through conservative `gumball apply`;
- require the broker in the Unreal profile, recommend it for mobile native proof and use it for heavyweight release-critical proof;
- fix Repository OS namespace label replacement to use atomic set-label semantics instead of additive label mutation;
- self-test broker authorization boundaries, exact-SHA inputs, trusted workflow definition, dedupe/reuse/defer/retry behavior and permission scoping.

Canonical consumer SHA: assigned from the v0.6.0 merge commit after merge.

## 0.5.0 — Repository OS

- add machine-readable `.gumball/repository-os.json` policy;
- add safe branch, pull-request and issue lifecycle planning plus trusted daily housekeeping;
- add GitHub Projects v2 semantic flow reconciliation for Backlog/Ready/In Progress/In Review/Done/Blocked;
- allow Project `Done` to close an issue only when explicit policy enables it;
- add canonical PR label namespaces for type, area, risk, CI cost and lifecycle;
- add trusted `pull_request_target` label/project automation that checks out only the default branch;
- add release manifests binding application SemVer, delivery stage, exact source SHA and artifact SHA-256;
- add `release-create` and `release-promote` primitives implementing build-once/promote-many;
- add CI Cost Governor classification, build fingerprints, lazy/affected validation guidance and a one-heavy-lane automatic budget;
- propagate repository OS policy, scripts, trusted workflow and release-manifest template through conservative `gumball apply`;
- extend standard, monorepo, mobile, Unreal and release-critical profiles with lifecycle/release/cost controls;
- self-test repository OS policy, trusted workflow behavior, Project flow, release lineage and CI-cost classification.

Canonical consumer SHA: assigned from the v0.5.0 merge commit after merge.

## 0.4.0 — Gumball

- rebrand the engineering platform product as **Gumball** while preserving the current `karnalooch/engineering-platform` repository coordinate for consumer compatibility;
- add `AGENTS.md` with platform invariants, documentation rules, conservative adoption and downstream-to-upstream promotion obligations;
- add `docs/README.md` as an authoritative documentation router and promote the docs-index contract proven in YACS;
- add Gumball architecture, adoption, CI-cost/proof, MCP/tooling and one-prompt bootstrap contracts;
- add an explicit dogfooding contract: Gumball must satisfy its own baseline and self-prove it through `gumball doctor` and CI;
- add a reusable Unreal-Blueprint-inspired Mermaid diagram language and propagate `docs/DIAGRAM_STYLE.md` through conservative `gumball apply` adoption;
- add profile presets for standard, monorepo, mobile, Unreal and release-critical repositories;
- add a tool/MCP capability manifest and conservative discovery of existing MCP configuration without copying private endpoints or secrets;
- add a standard-library-only `gumball` helper with `audit`, `plan`, `apply`, `doctor` and `promote`;
- make `apply` dry-run by default and non-destructive: existing AGENTS/docs/config files are preserved;
- add a formal `.gumball/candidates/` contract so reusable improvements discovered downstream can be promoted back into Gumball;
- promote the 4VELO fail-closed dynamic aggregate pattern into `scripts/ci/evaluate_aggregate.py`;
- add `scripts/ci/assert_nonempty.py` to prevent false-green zero-work CI selectors;
- self-test Gumball bootstrap, promotion, aggregate and anti-no-op contracts in platform CI;
- classify Gumball policy/config files as high-risk governance surfaces;
- close a pre-existing immutable-ref scanning gap so valid YAML inline list syntax such as `- uses: action@ref` is also checked.

Canonical consumer SHA: assigned from the v0.4.0 merge commit after merge.

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
