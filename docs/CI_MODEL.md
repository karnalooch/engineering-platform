# Gumball CI model

Status: **ACTIVE / AUTHORITATIVE**

## Principle

Run the smallest trustworthy validation surface for a change, while failing closed when classification is uncertain.

This combines two proven patterns:

- a stable caller-local aggregate gate;
- change-aware PR validation separated from heavyweight full/release evidence.

## Pull-request validation

A consumer may classify changed paths into lanes such as documentation/policy, Python, JavaScript/TypeScript, native/mobile, assets/visual, infrastructure and unknown/CI-core.

Rules:

- mixed changes take the union of matching lanes;
- CI-core and unknown runtime/configuration changes expand to broad/full coverage;
- expected jobs that are skipped unexpectedly fail the aggregate;
- path filtering is an optimization, never proof by itself;
- a command that matches zero intended packages/tests must fail rather than create a false green result.

## Aggregate gate

The authoritative merge check remains named `Aggregate CI gate` where branch protection depends on that name.

It must:

1. run with a job-level `always()` condition;
2. include every required job in `needs`;
3. validate the expected job set against the change classification when classification is dynamic;
4. fail on missing, unknown, cancelled or unexpectedly skipped required evidence;
5. never turn a required failure into success.

## Full / release validation

Heavy whole-system evidence belongs in an explicit lane rather than every routine pull request.

Typical examples:

- full monorepo regression;
- release/native packaging;
- hardware or emulator proof;
- environment/home-lab proof;
- performance or visual evidence;
- deployment manifest/release validation.

A release/full gate is additional evidence. It must never justify weakening the PR merge contract.

## Cost rule

Default profiles should not enable expensive visual, hardware or runtime proofs on every pull request. Those proofs are opt-in through a profile or consumer-local policy.

## Anti-no-op contract

A validation command is invalid when it reports success without executing the intended target.

Consumers should add assertions for:

- zero workspace/package matches;
- zero discovered tests when tests were expected;
- missing required artifacts;
- missing required generated outputs;
- unexpectedly skipped capability jobs.

This is a reusable invariant and should be preferred over technology-specific assumptions.


## Reference primitives

Gumball ships standard-library-only reference implementations:

- `scripts/ci/evaluate_aggregate.py` — validates a dynamic expected job set and fails closed on missing/unknown/unexpectedly skipped required evidence;
- `scripts/ci/assert_nonempty.py` — rejects selectors that unexpectedly resolve to zero work.

They were generalized from failure modes proven in downstream CI. Consumers may adapt them, but must preserve the documented invariants.

## Cost governance

The proof graph is also a cost graph.

Before expensive work, consumers should use the [CI Cost Governor](CI_COST_GOVERNOR.md) to classify impact, reuse an exact build fingerprint when available and defer non-merge-critical runtime/visual/hardware proof to manual, release or nightly lanes.

A cost optimization may reduce work; it may not weaken the caller-local expected-proof contract.
