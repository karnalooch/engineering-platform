# Gumball profiles

Profiles are additive policy presets. They select useful capabilities without replacing consumer-owned architecture.

Available initial profiles:

- `standard.yaml` — general-purpose repository baseline;
- `monorepo.yaml` — change classification and anti-no-op emphasis;
- `mobile.yaml` — native/runtime boundary and release-proof guidance;
- `unreal.yaml` — LFS, toolchain and expensive runtime-proof guidance;
- `release-critical.yaml` — explicit full/release validation.

Profiles may strengthen the baseline. They must not disable Gumball's fail-closed invariants.

