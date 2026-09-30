# Visual engineering contract

Status: **ACTIVE / AUTHORITATIVE FOR VISUAL PROFILES**

## Purpose

Gumball treats visual development as an engineering surface: composition, components, assets, generated bridges and visual proof must have clear authority and reproducible repository evidence.

This contract is reusable. It does not prescribe a particular design SaaS, map vendor, DCC package or application style.

## Composition first, assets second

Define screen/world composition before creating decorative assets.

A typical application presentation can be reasoned about as bounded planes such as:

- primary context plane (for example map/world/content);
- data/truth plane;
- control/interaction plane;
- optional brand/emotion plane.

Optional decorative content must pass an **asset-off test**: removing it may reduce polish, but must not destroy hierarchy, truth or operability.

## Repository-owned visual authority

Accepted visual output must return to version control as reviewable artifacts or production code.

Examples include design-token interchange, style JSON, component stories/fixtures, scene/export descriptors or other deterministic representations. External editors are adapters to those artifacts, not independent authorities.

Generated visual bridges must:

- derive from a repository-owned source;
- declare repository authority;
- be reproducible without a paid SaaS dependency in CI when practical;
- validate freshness by deterministic content comparison, not timestamps.

## Repo-native visual workbench

For component/application visual review, prefer a development-only workbench built from production components and production formatting/data registries rather than pixel/mock replicas.

The workbench should provide:

- deterministic fixtures;
- stable proof/test identifiers;
- bounded proof-only overrides for clocks, random values, battery/network/GPS-like state or other live inputs;
- explicit asset-off inspection where optional art is involved;
- representative truth/error/paused/loading states;
- a hard dev/vision-only boundary so the workbench is not a shipping product surface.

When a proof override disables live behavior, the live timer/subscription must also be disabled so screenshots remain deterministic.

Optional tools such as component explorers or cloud visual services may wrap the same repo-owned components and fixtures; they do not create a second source of truth.

## Repository-owned styles and media descriptors

When a consumer stores map styles, scene descriptors, shaders, presets or similar visual artifacts in the repository, it should record:

- upstream provenance when derived from another artifact;
- required attribution/license notices;
- forbidden/unapproved production sources where relevant;
- a deployment/runtime override boundary when infrastructure may replace the default source.

Validation should fail closed on unresolved provenance placeholders, missing mandatory attribution or known-forbidden production sources.

## Visual proof

Visual proof binds to an exact source revision and deterministic fixture/state. Expensive screenshot/runtime proof belongs in an explicit profile or Proof Broker lane unless it is merge-critical.

The visual workbench is a proof surface, not a replacement for product/runtime tests.

## Profile guidance

The mobile profile recommends composition authority, repo-owned design interchange and deterministic component workbenches. Unreal consumers should apply the same authority/provenance rules to DCC/editor/world-building tooling while keeping shipping boundaries explicit.

## Downstream evidence

This contract generalizes 4VELO PRs #398/#400/#402/#403/#407 and is compatible with the YACS proven-tooling/lifecycle rules promoted from PRs #281/#283.
