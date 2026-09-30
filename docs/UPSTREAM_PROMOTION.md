# Downstream -> Gumball promotion

Status: **ACTIVE / AUTHORITATIVE**

## Purpose

Consumer repositories are production testbeds for engineering practice. Useful improvements discovered in YACS, 4VELO, ONICS, Karoo or future projects should not remain trapped downstream.

Gumball therefore has an explicit upstream feedback loop.

## What to promote

Good candidates include reusable improvements to:

- CI routing and aggregate behavior;
- anti-no-op validation;
- security or repository governance;
- documentation architecture and freshness;
- agent operating rules;
- MCP/tool capability boundaries;
- release/proof separation;
- developer or repository doctor tooling;
- deterministic automation;
- tooling authority, supply-chain and lifecycle boundaries;
- repo-owned visual/design interchange and deterministic workbench contracts.

## What not to promote

Keep downstream:

- product-specific build steps;
- one-off incident workarounds;
- named environments, maps, devices or services;
- application-specific acceptance thresholds;
- scripts whose useful behavior cannot be stated independently from the product.

Promote the **invariant and reusable mechanism**, not merely the file.

## Promotion states

```text
candidate -> proven -> platform
```

- **candidate** — plausible reusable idea with a stated problem.
- **proven** — used successfully downstream with concrete evidence.
- **platform** — generalized, documented and contract-tested in Gumball.

## Candidate contract

A candidate should record:

- `id`;
- source repository;
- category;
- problem;
- reusable invariant;
- downstream evidence;
- project-specific details that must not be copied;
- expected failure behavior;
- status.

Consumer repositories may store these under `.gumball/candidates/`.

## Promotion test

Before promotion, answer yes to all of the following:

1. Does the problem exist independently of the source product?
2. Can the desired behavior be described as a stable contract?
3. Can failure behavior be tested?
4. Is the generalized solution useful to another repository or profile?
5. Does adoption avoid a disproportionate CI/runtime cost?

If not, leave it downstream.

## Agent obligation

A Gumball-enabled `AGENTS.md` should instruct agents to evaluate reusable CI, governance, security, docs, tooling, MCP and workflow improvements for upstream promotion.

This evaluation is part of finishing the downstream task; actual promotion remains a separate reviewed change.

