# Adopting Gumball

Status: **ACTIVE / AUTHORITATIVE**

## Modes

Gumball supports two adoption modes:

- **greenfield** — establish the baseline before product CI grows around it;
- **existing repository** — inspect, preserve and incrementally strengthen an existing project.

Existing repositories are the harder case and define the safety standard.

## Required flow

Use the sequence:

```text
audit -> plan -> apply -> verify
```

### Audit

Discover the actual repository before proposing changes:

- stack and package managers;
- existing `AGENTS.md` files;
- documentation entry points and SSOTs;
- workflow graph and required checks;
- security tooling;
- release/runtime/hardware/visual proof;
- repository-specific automation;
- existing Gumball/engineering-platform pins;
- open branch/PR/issue lifecycle and GitHub Projects usage;
- application version sources, delivery stages and artifact provenance;
- existing PR label taxonomy;
- heavyweight CI/build lanes and their current cost/reuse behavior.

Do not infer a missing rule from the absence of a familiar filename.

### Plan

Classify each proposed change as:

- ADD;
- MODIFY;
- KEEP;
- DEFER;
- CONFLICT.

The plan must preserve stronger local controls and call out incompatible assumptions.

### Apply

Application is conservative:

- never blindly replace an existing `AGENTS.md`;
- never replace an existing docs index with a generic one;
- never delete product-specific proof because a shared equivalent exists;
- keep the final aggregate local;
- keep application-specific runtime/release proof downstream;
- add generated/managed sections only where ownership is explicit.

### Verify

A migration is incomplete until:

- Gumball doctor passes for required contracts;
- existing project tests/gates still pass;
- documentation describes the resulting state;
- no required check was weakened or silently skipped;
- immutable shared-workflow pins are recorded;
- `.gumball/repository-os.json` documents lifecycle, labels, release lineage and CI cost policy;
- trusted repository-ops automation is present when the project opts into automatic reconciliation;
- release-capable profiles can generate and validate artifact manifests;
- heavy build lanes have an explicit reuse/defer strategy.

## Profiles

Profiles are additive presets, not complete application architectures.

Recommended starting profiles:

- `standard` — baseline governance/security/docs;
- `monorepo` — change classification and anti-no-op emphasis;
- `mobile` — native/runtime boundary and release-proof guidance;
- `unreal` — LFS, self-hosted/toolchain and expensive proof guidance;
- `release-critical` — explicit full/release validation and stricter evidence.

## Existing repository rule

When Gumball and local policy disagree, do not automatically choose the shared version. Determine which invariant is stronger, document the conflict and preserve the safer behavior until an explicit migration is reviewed.

