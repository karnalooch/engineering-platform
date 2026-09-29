# Fail-closed aggregate gate

The final gate stays in each consumer repository and is named exactly `Aggregate CI gate` where that name is used by branch protection.

It must:

1. use a job-level `always()` condition;
2. declare every required caller/reusable job in `needs`;
3. fail unless every required result satisfies the current change-classification contract;
4. fail on missing, unknown, cancelled or unexpectedly skipped required jobs;
5. never convert failures into success with `continue-on-error`;
6. include application-specific jobs such as a real Unreal build when those become required.

A skipped required job is not success unless the consumer contract explicitly classifies that job as not applicable for the current change.

## Dynamic expected sets

Consumers with change-aware CI may use the reference evaluator in `scripts/ci/evaluate_aggregate.py`.

The evaluator accepts:

- `CI_NEEDS_JSON` — caller job results;
- `CI_EXPECTED_JOBS_JSON` — the exact required job list for this change;
- `CI_ALLOWED_SKIPPED_JOBS_JSON` — an explicit, narrow list of required jobs that may be skipped for this classification.

An empty expected set fails closed because it would otherwise create a green no-op aggregate.

The consumer still owns its local `needs` graph and classification logic. The reference evaluator does not decide which application-specific proof is required.

## Anti-no-op

A filtered command that resolves to zero intended work must not silently pass.

`scripts/ci/assert_nonempty.py` is the reference primitive for asserting a non-zero workspace, package, test or artifact match count.

This pattern deliberately makes configuration mistakes visible instead of producing a green no-op pipeline.
