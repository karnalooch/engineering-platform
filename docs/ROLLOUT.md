# Rollout

## v0.1 bootstrap

1. Live-prove this repository's self-CI.
2. Merge manually.
3. Use the resulting immutable merge commit SHA as the first consumer reference.
4. Migrate YetAnotherCyclingSim from local reusable security/repository workflows to the platform SHA.
5. Compare job behavior and keep its exact local `Aggregate CI gate`.
6. Only after CyclingSim is proven, migrate common 4VELO controls one concern at a time.

## 4VELO migration boundary

Keep product-specific jobs local, including Django/PostGIS/Celery topology, telemetry specifics, pnpm/mobile/admin logic, Docker publishing, Kubernetes/home-lab release gates and product-specific planning/review automation.

## Version labels

A semantic release tag may be added after the contract is proven. Tags are navigation/version labels; security-sensitive consumers should still be able to resolve and review the underlying immutable commit.
