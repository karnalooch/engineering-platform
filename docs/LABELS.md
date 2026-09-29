# Labels contract

Status: **ACTIVE / AUTHORITATIVE**

## Goal

Gumball gives pull requests and issues a small, predictable vocabulary that supports routing, Projects, release planning and CI cost decisions.

## Canonical namespaces

Every active PR should normally have one label from each applicable dimension:

- `type:*` — feature, fix, chore, docs, refactor, test, release;
- `area:*` — ci, governance, docs, tooling, security, release, runtime, project;
- `risk:*` — low, medium, high;
- `ci:*` — light, standard, heavy;
- `lifecycle:*` — blocked, stale, keep, auto-close when applicable.

Projects may add product-specific labels without replacing these semantic namespaces.

## Automatic classification

Trusted automation may derive:

- `type:*` from conventional PR title prefixes plus changed paths;
- `area:*` from changed path ownership;
- `risk:high` from governance/high-risk path rules;
- `ci:*` from the CI Cost Governor;
- lifecycle labels from repository reconciliation.

When classification is ambiguous, omit the uncertain label and report the ambiguity rather than guessing.

## Reconciliation

Gumball maintains label definitions as code. A repository label sync may create or update canonical labels and descriptions.

The label workflow must run trusted default-branch code. It must not execute untrusted PR code with a write token.

## Project integration

Labels are inputs to Projects reconciliation:

- `status:ready` can promote an issue to Ready;
- `lifecycle:blocked` marks work blocked;
- `lifecycle:keep` prevents stale auto-close/cleanup;
- `ci:heavy` signals that automatic PR CI should remain selective.


## Proof Broker labels

Proof-request and proof-status labels are owned by the [Proof Broker](PROOF_BROKER.md), not the general Repository OS label reconciler.

Namespaces:

- `proof:<proof-id>` — explicit proof request configured by the consumer;
- `proof-status:requested`;
- `proof-status:running`;
- `proof-status:passed`;
- `proof-status:failed`;
- `proof-status:deferred`;
- `proof-status:reused`.

Keeping ownership separate prevents the generic label sync from fighting broker-specific colors/descriptions or accidentally deleting dynamic proof-request labels.
