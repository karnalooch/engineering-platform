# Gumball profiles

Profiles are additive policy presets. They select useful capabilities without replacing consumer-owned architecture.

Available initial profiles:

- `standard.yaml` — general-purpose repository baseline;
- `monorepo.yaml` — change classification and anti-no-op emphasis;
- `mobile.yaml` — native/runtime boundary and release-proof guidance;
- `unreal.yaml` — LFS, toolchain and expensive runtime-proof guidance;
- `release-critical.yaml` — explicit full/release validation.

All profiles inherit repository lifecycle, shared PR labels, the CI Cost Governor and Proof Broker support from `standard`. Unreal requires the broker for heavy runtime/visual proof; mobile recommends it for native proof; release-critical requires it whenever heavyweight proof is broker-managed. Release-capable profiles add artifact/version lineage and build-once/promote-many rules.

Profiles may strengthen the baseline. They must not disable Gumball's fail-closed invariants.

