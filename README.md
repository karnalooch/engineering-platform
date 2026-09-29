# Gumball

**Gumball** is the shared, versioned engineering platform for repositories owned by `karnalooch`.

It is not a static project template. Gumball is a living control plane for CI, security, governance, documentation, agent workflows and tooling. Consumer repositories both **adopt** platform contracts and **feed proven reusable improvements back upstream**.

> Compatibility: the repository is currently hosted at `karnalooch/engineering-platform`. Existing reusable-workflow consumers must keep that coordinate until a dedicated repository-rename migration updates and proves their immutable pins.

## The loop

```mermaid
flowchart LR
    G["🎮 GUMBALL<br/>Shared contracts"] -->|"ADOPT / UPDATE"| P["⬢ CONSUMER<br/>Repository"]
    P --> Y["YACS<br/>Unreal / world / proof"]
    P --> V["4VELO<br/>monorepo / mobile / release"]
    P --> O["ONICS · KAROO<br/>future projects"]
    Y -.->|"PROMOTE"| C["↩ CANDIDATE<br/>Reusable invariant"]
    V -.->|"PROMOTE"| C
    O -.->|"PROMOTE"| C
    C -.->|"PROVEN"| G

    classDef core fill:#172554,stroke:#60a5fa,color:#ffffff,stroke-width:4px;
    classDef consumer fill:#34373d,stroke:#9da4ae,color:#ffffff,stroke-width:2px;
    classDef tool fill:#4b2f69,stroke:#b77cff,color:#ffffff,stroke-width:3px;

    class G core;
    class P,Y,V,O consumer;
    class C tool;

    linkStyle default stroke-width:2px;
```

Application code and product-specific runtime proof stay in product repositories. Gumball contains reusable engineering contracts and tools.

## Start here

- [Documentation map](docs/README.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Dogfooding contract](docs/DOGFOODING.md)
- [Blueprint diagram style](docs/DIAGRAM_STYLE.md)
- [Adoption contract](docs/ADOPTION.md)
- [CI model](docs/CI_MODEL.md)
- [Downstream -> upstream promotion](docs/UPSTREAM_PROMOTION.md)
- [One-prompt bootstrap](docs/ONE_PROMPT_BOOTSTRAP.md)
- [MCP and tool capability contract](docs/MCP_AND_TOOLS.md)
- [Repository lifecycle](docs/REPOSITORY_LIFECYCLE.md)
- [GitHub Projects flow](docs/PROJECTS_FLOW.md)
- [Release and artifact lineage](docs/RELEASE_LINEAGE.md)
- [Labels contract](docs/LABELS.md)
- [CI Cost Governor](docs/CI_COST_GOVERNOR.md)
- [Proof Broker](docs/PROOF_BROKER.md)

## CLI

The initial standard-library-only helper supports conservative repository adoption:

```bash
python scripts/gumball.py audit
python scripts/gumball.py plan
python scripts/gumball.py apply
python scripts/gumball.py apply --write --profile standard
python scripts/gumball.py doctor
python scripts/gumball.py promote
```

`apply` is dry-run by default and only creates missing baseline files. It never overwrites an existing `AGENTS.md`, docs index or Gumball config.

Repository OS primitives:

```bash
python scripts/ops/repository_os.py ci-plan docs/README.md
python scripts/ops/repository_os.py labels-plan --title "feat: example" .github/workflows/ci.yml
python scripts/ops/repository_os.py release-create --help
python scripts/ops/repository_os.py release-promote --help
python scripts/ops/github_ops.py --help
python scripts/ops/proof_broker.py validate
```

## Existing reusable contracts

- `.github/workflows/reusable-repo-policy.yml` — repository hygiene, Git LFS and oversized-blob enforcement.
- `.github/workflows/reusable-security.yml` — Dependency Review, CodeQL, Trivy and CycloneDX SBOM.
- `.github/workflows/reusable-scorecard.yml` — OpenSSF Scorecard + SARIF upload.
- `.github/workflows/reusable-governance.yml` — PR risk classification, immutable-ref enforcement and fail-closed governance.
- `docs/AGGREGATE_GATE.md` — caller-local fail-closed aggregate pattern.
- `docs/GOVERNANCE_GUARD.md` — governance and high-risk merge contract.
- `docs/AUTO_MERGE.md` — trusted, fail-closed low-risk auto-merge contract.

## Consumers / laboratories

Current repositories that provide both consumption and real-world feedback include:

- `karnalooch/YetAnotherCyclingSim`;
- `karnalooch/stunning-pancake` (4VELO);
- `karnalooch/Karoo-Nexus-Suite`;
- `karnalooch/onics-ecommerce` (ONICS / CEL-TRONICS).

Reusable ideas discovered downstream should be evaluated using [UPSTREAM_PROMOTION.md](docs/UPSTREAM_PROMOTION.md). Promote the invariant and reusable mechanism, not product-specific scripts.

## Immutable consumption

Callers pin reusable workflows to a reviewed immutable commit SHA. Do **not** consume this repository from `@main`.

The final `Aggregate CI gate` stays local to every consumer so application-specific checks cannot be silently dropped by a shared workflow.

See [CONTRACT.md](docs/CONTRACT.md) for the executable caller contract.

## Repository OS

Gumball v0.5 adds a repository operating layer:

- stale/merged branch, PR and issue lifecycle;
- GitHub Projects status reconciliation;
- canonical PR labels;
- application version/stage/artifact lineage;
- CI Cost Governor with heavy-build fingerprint reuse.

The trusted `.github/workflows/repository-ops.yml` workflow runs default-branch code only. Projects integration is disabled until a consumer supplies project owner/number and an authorized Project token.

## Proof Broker

Gumball v0.6 removes routine Actions-UI clicking from heavyweight proofs.

A configured proof can be requested directly from a pull request:

```text
/gumball proof <proof-id>
```

or with its `proof:<proof-id>` label.

The broker runs trusted default-branch orchestration, binds the exact PR SHA, reuses existing artifacts/runs, blocks duplicates and defers non-critical automatic heavy work. Manual `workflow_dispatch` stays available only as a recovery fallback.

See [PROOF_BROKER.md](docs/PROOF_BROKER.md).
