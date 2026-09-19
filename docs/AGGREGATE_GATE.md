# Fail-closed aggregate gate

The final gate stays in each consumer repository and is named exactly `Aggregate CI gate` where that name is used by branch protection.

It must:

1. use `if: ${{ always() }}`;
2. declare every required caller/reusable job in `needs`;
3. fail unless every required `needs.<job>.result` equals `success`;
4. never convert failures into success with `continue-on-error`;
5. include application-specific jobs such as a real Unreal build when those become required.

A skipped required job is not success and therefore fails the aggregate.

This pattern deliberately makes configuration mistakes visible instead of producing a green no-op pipeline.
