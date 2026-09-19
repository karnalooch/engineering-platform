# Fail-closed auto-merge

engineering-platform v0.3.0 adds a repository-local auto-merge controller for explicitly eligible, low-risk pull requests.

## Default stance

The default pull request marker remains:

```text
Auto-merge: manual
```

A pull request may opt in only by replacing that line with:

```text
Auto-merge: eligible
```

The controller never infers eligibility from a title, label, author intent, or passing CI alone.

## Trusted execution model

The privileged workflow uses `pull_request_target` but checks out and executes only the repository default branch.

It never checks out PR-head code before making the merge decision.

This matters because the workflow has the permissions required to update and merge a pull request.

## Required proof

An eligible PR is merged only when all of these are true:

- the current PR body still contains `Auto-merge: eligible`;
- `Auto-merge: manual` is absent;
- the PR is open and no longer Draft;
- base is `main`;
- head repository is this repository, not a fork;
- author is the repository owner;
- the PR changes at least one file;
- independent trusted-main path classification finds no high-risk paths;
- the latest exact `Aggregate CI gate` check is `success`;
- the latest exact `Governance policy / Governance guard` check is `success`;
- no reviewer's latest state is `CHANGES_REQUESTED`;
- all review threads are resolved;
- at least one same-repository Issue is linked with a closing relationship;
- GitHub reports the exact current head SHA as cleanly mergeable.

The merge uses squash and passes the reviewed head SHA to the GitHub merge API.

## High-risk paths

The controller independently blocks auto-merge for:

```text
.github/**
scripts/ci/**
VERSION
CHANGELOG.md
SECURITY.md
docs/AGGREGATE_GATE.md
docs/CONTRACT.md
docs/GOVERNANCE_GUARD.md
docs/ROLLOUT.md
docs/VERSIONING.md
pyproject.toml
package.json
pnpm-lock.yaml
pnpm-workspace.yaml
package-lock.json
yarn.lock
requirements*.txt
*.key
*.pem
*.p12
*.pfx
.env
.env.example
```

Governance and the auto-merge controller intentionally overlap. Governance protects CI; the privileged merge controller makes its own trusted-main decision before writing.

## Behind branches

When every other condition is safe but GitHub reports `mergeable_state=behind`, the controller requests a branch update using the exact head SHA and stops.

It does not merge until fresh checks complete on the updated head.

## Reconciliation

The workflow reacts to:

- PR readiness/reopen/synchronize/body-edit events;
- completion of `Engineering Platform CI`;
- an hourly reconciliation run;
- manual workflow dispatch.

The hourly reconciliation exists so a previously blocked eligible PR can be reconsidered after review-thread resolution without requiring a dummy commit.

## Fail-closed rules

The controller does not merge when:

- any required check is missing, stale, pending or failed;
- GitHub API pagination cannot be fully evaluated;
- check-run counts change during evaluation;
- the PR has more review/files data than the policy safely retrieves;
- mergeability is unknown, dirty, unstable or otherwise not exactly `clean`;
- API data is malformed;
- transport/API errors prevent a complete decision.

Errors are visible as workflow failures; ambiguity never becomes permission to merge.

## Platform changes remain manual

Changes to CI, security, governance, versioning, the auto-merge controller itself, and contract documents are deliberately classified high-risk.

Therefore engineering-platform release PRs such as v0.3.0 remain manual even after auto-merge is active.
