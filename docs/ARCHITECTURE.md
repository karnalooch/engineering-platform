# Gumball architecture

Status: **ACTIVE / AUTHORITATIVE**

## Goal

Gumball provides a reusable engineering control plane that can be adopted by a new repository or introduced incrementally into an existing one.

It separates **portable engineering contracts** from **product-specific proof**.

```text
Gumball
  |
  +-- reusable policy / workflows / tools
  +-- adoption and doctor logic
  +-- agent/documentation contracts
  +-- profiles
  |
  +--> consumer repository
         |
         +-- product-specific CI
         +-- runtime / hardware / visual proof
         +-- local SSOT and AGENTS rules
         |
         +--> promotion candidates back to Gumball
```

## Layers

### 1. Platform invariants

Non-negotiable safety properties:

- immutable external workflow/action refs;
- explicit least-privilege permissions;
- fail-closed required checks;
- no silent `continue-on-error: true` bypasses;
- caller-local `Aggregate CI gate`;
- project-specific proof cannot be silently dropped by shared workflows.

### 2. Capabilities

Gumball describes engineering capabilities rather than one technology-specific job graph.

Examples:

- repository policy;
- documentation governance;
- lint/typecheck/unit test;
- security analysis;
- build;
- runtime proof;
- release proof;
- provenance/SBOM.

A consumer maps capabilities to its own implementation.

### 3. Profiles

Profiles enable optional policy bundles such as:

- `standard`;
- `monorepo`;
- `mobile`;
- `unreal`;
- `release-critical`.

Profiles do not grant permission to weaken the baseline.

### 4. Consumer-local proof

Product-specific checks remain downstream. Examples include Unreal runtime proofs, Android emulator evidence, Home Lab validation, visual acceptance and hardware tests.

The platform may standardize the **contract** for those proofs without copying their product-specific implementation.

### 5. Feedback loop

A downstream improvement can become a Gumball capability only after its reusable invariant and failure behavior are understood and covered by contract tests.

See [UPSTREAM_PROMOTION.md](UPSTREAM_PROMOTION.md).

## Compatibility boundary

Gumball's product name is independent from its current GitHub repository coordinate. Until the repository itself is renamed and every consumer pin is migrated, executable references remain under `karnalooch/engineering-platform`.

