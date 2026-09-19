# Senior-team guardrails

The platform should make the safe path the easy path and should not rely on a
human remembering every repository rule.

## Risk policy

`.github/workflows/reusable-risk-policy.yml` classifies pull requests from
changed paths. High-risk changes include CI/workflow, security, container and
dependency/toolchain files by default. Consumers can add application-specific
patterns.

For high-risk pull requests:

- `Risk: high` must be declared;
- `Auto-merge: manual` must be declared;
- `Auto-merge: eligible` is rejected;
- understating the risk is rejected.

Overstating risk is allowed.

## Consumer contract

`.github/workflows/reusable-consumer-contract.yml` protects the caller from
configuration drift.

It can require:

- at least one `karnalooch/engineering-platform` workflow reference;
- every platform reference to use a full 40-character commit SHA;
- all platform workflow calls in the repository to use one platform SHA;
- exactly one local workflow containing the exact `Aggregate CI gate`;
- that aggregate to use `if: ${{ always() }}`;
- no `continue-on-error: true` in workflow files;
- optionally, every external GitHub Action to be pinned to a 40-character SHA.

The final aggregate remains consumer-owned. Shared workflows do not decide which
application-specific jobs are required.

## Rollout sequence

A shared guardrail change follows this order:

1. engineering-platform PR;
2. platform self-CI and manual merge;
3. immutable merge SHA;
4. YetAnotherCyclingSim canary consumer PR;
5. full CyclingSim CI and manual merge;
6. 4VELO consumer PR;
7. full 4VELO CI and manual merge.

A failure in one consumer does not force another consumer to upgrade.

## Breaking changes

Do not replace a widely consumed contract in place when a migration is needed.
Introduce a compatible new workflow/contract, migrate consumers one at a time,
then remove the old contract after all supported consumers have moved.

## Human memory is not a control

Checklists and documentation are useful, but critical invariants belong in
GitHub branch protection, CI gates, immutable pins and scheduled drift audits.
