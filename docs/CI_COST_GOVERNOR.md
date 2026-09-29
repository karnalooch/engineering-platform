# CI Cost Governor

Status: **ACTIVE / AUTHORITATIVE**

## Objective

The cheapest trustworthy proof wins.

Gumball avoids heavyweight builds by planning evidence before executing expensive work.

## Evidence ladder

```mermaid
flowchart LR
    CHG["CHANGE<br/>Paths + metadata"] --> CLASS["CLASSIFY<br/>Impact"]
    CLASS --> L0["L0<br/>Policy / docs"]
    CLASS --> L1["L1<br/>Static + contracts"]
    CLASS --> L2["L2<br/>Unit / affected tests"]
    CLASS --> L3["L3<br/>Package build"]
    CLASS --> L4["L4<br/>Runtime / native"]
    CLASS --> L5["L5<br/>Visual / hardware / release"]

    L0 --> GATE["EXPECTED PROOF SET"]
    L1 --> GATE
    L2 --> GATE
    L3 --> GATE
    L4 --> GATE
    L5 --> GATE
    GATE -->|"within budget"| RUN["RUN<br/>Only required proof"]
    GATE -->|"too expensive"| DEFER["DEFER HEAVY<br/>release / manual / nightly"]

    classDef input fill:#303846,stroke:#8ea1b8,color:#f7f9fc,stroke-width:2px;
    classDef decision fill:#69470e,stroke:#f0a72f,color:#ffffff,stroke-width:3px;
    classDef exec fill:#123f73,stroke:#49a2ff,color:#ffffff,stroke-width:3px;
    classDef danger fill:#6b2429,stroke:#ff6b73,color:#ffffff,stroke-width:3px;
    class CHG input;
    class CLASS,GATE decision;
    class L0,L1,L2,L3,L4,L5,RUN exec;
    class DEFER danger;
    linkStyle default stroke-width:2px;
```

## Core rules

### 1. Preflight before build

Cheap checks run first. A heavy build must not start while deterministic policy/static/unit checks are already red.

### 2. Affected surface, not whole repository

Classify changed paths/capabilities and construct the exact expected proof set. Mixed/unknown runtime changes broaden coverage fail-safely.

### 3. Build fingerprint

Heavy build identity is derived from relevant source inputs, lockfiles, toolchain version/configuration and build profile.

If the fingerprint already has a verified artifact, reuse it instead of rebuilding.

### 4. Build once per fingerprint

Multiple downstream proofs consume the same artifact. Runtime smoke, packaging checks, visual proof and release promotion must not independently compile identical source when one immutable artifact can be shared.

### 5. Heavy proof lanes

L4/L5 evidence runs automatically only when required by change classification or release policy.

Otherwise route it to one of:

- manual dispatch;
- release candidate gate;
- nightly verification;
- dedicated self-hosted runner proof.

### 6. Superseded work cancellation

New commits cancel obsolete PR runs. Heavy work must use concurrency groups keyed to repository/PR/profile.

### 7. Lazy matrices

Generate only matrix entries for affected components/platforms. Do not start an all-platform matrix when one component changed.

### 8. Budget

Profiles declare soft CI budgets, for example:

- light PR: target <= 5 runner-minutes;
- standard PR: target <= 15 runner-minutes;
- heavy automatic PR: at most one heavyweight build lane;
- release/full proof: separate budget and event.

When an automatic plan exceeds its PR budget, Gumball should defer non-merge-critical heavy evidence instead of silently burning the budget.

### 9. Cache is not proof

Caches accelerate computation. Reusable immutable artifacts plus manifests are proof inputs. Never treat a cache hit alone as release provenance.

## Output

The planner should expose a machine-readable plan including:

- impact classes;
- required capabilities;
- proof tier;
- estimated cost class;
- heavy build fingerprint;
- reusable artifact candidate;
- deferred proofs;
- resulting `ci:light|standard|heavy` label.

The caller-local Aggregate Gate validates the planned expected proof set; it must not require intentionally deferred non-merge-critical evidence.


## Build broker convention

Verified heavyweight artifacts use the canonical name:

```text
gumball-build-<64-char-build-fingerprint>
```

A CI lane can ask Gumball whether the exact artifact already exists before compiling:

```bash
python scripts/ops/github_ops.py artifact-find \
  --fingerprint <64-char-build-fingerprint>
```

The command returns `REUSE` with the artifact id/download URL when a non-expired exact match exists, otherwise `BUILD`.

The policy decision can then choose:

- `SKIP` — no heavy build is required;
- `REUSE` — consume the verified artifact;
- `BUILD` — one heavy build is merge/release-critical and no reusable artifact exists;
- `DEFER` — heavy proof is not merge-critical and moves to manual/release/nightly.

Example:

```bash
python scripts/ops/repository_os.py ci-decision \
  --artifact-available \
  Source/Game/Foo.cpp
```

The artifact registry is a reuse mechanism, not a trust shortcut: the artifact still needs the exact build fingerprint and release/proof manifest expected by the consumer.

## Proof Broker integration

The CI Cost Governor decides **whether** heavyweight evidence should run; the [Proof Broker](PROOF_BROKER.md) decides **how** an approved proof request is safely dispatched.

For heavyweight proofs:

- automatic + merge-critical -> broker may dispatch once for the exact revision;
- automatic + non-merge-critical -> `DEFER`;
- explicit authorized PR request -> broker may dispatch even when non-merge-critical;
- existing exact artifact/successful run -> `REUSE`;
- identical queued/running request -> `ALREADY_RUNNING`;
- failed existing request -> no automatic loop; explicit retry required.

This prevents cost optimization from turning into silent loss of evidence, while removing routine Actions-UI clicking.
