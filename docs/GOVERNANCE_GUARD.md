# Governance guard

The governance guard is a reusable fail-closed workflow that protects process invariants which are easy to forget during normal development.

## What it enforces

On every caller repository it:

- classifies pull requests from the actual changed paths;
- requires the exact PR-body marker `Auto-merge: manual` when high-risk paths are touched;
- rejects mutable or otherwise non-immutable external GitHub Action/workflow refs;
- rejects mutable `engineering-platform` consumer refs such as `@main`, `@master`, or a tag;
- rejects fail-open `continue-on-error: true` in GitHub Actions workflows;
- rejects workflow-level `permissions: write-all`;
- requires a caller-local `Aggregate CI gate` whose own job block contains `if: ${{ always() }}`.

The baseline checks cannot be disabled by caller inputs.

## Default high-risk paths

The built-in contract classifies the following as high-risk:

```text
.github/**
SECURITY.md
**/SECURITY.md
package.json
**/package.json
pnpm-lock.yaml
**/pnpm-lock.yaml
package-lock.json
**/package-lock.json
yarn.lock
**/yarn.lock
pnpm-workspace.yaml
**/pnpm-workspace.yaml
pyproject.toml
**/pyproject.toml
requirements*.txt
**/requirements*.txt
Dockerfile*
**/Dockerfile*
docker-compose*.yml
**/docker-compose*.yml
compose*.yml
**/compose*.yml
.nvmrc
.node-version
.python-version
**/.nvmrc
**/.node-version
**/.python-version
eas.json
**/eas.json
app.config.js
**/app.config.js
```

Consumers may add extra patterns through `additional_high_risk_patterns` for application-specific sensitive surfaces. The built-in defaults remain enforced and cannot be removed by a caller.

## Why high-risk means manual

High-risk classification does not mean the change is bad. It means the change can alter the safety boundary, dependency graph, toolchain, release process, or CI result itself.

A high-risk PR therefore needs:

```text
Auto-merge: manual
```

in its body. This makes accidental eligibility for automated merging a CI failure rather than a memory problem.

## Immutable references

Consumer repositories must call shared workflows with a reviewed full commit SHA:

```yaml
uses: karnalooch/engineering-platform/.github/workflows/reusable-governance.yml@0123456789abcdef0123456789abcdef01234567
```

Mutable refs such as `@main`, `@master`, `@v1` or `@v1.2.3` are rejected by the guard.

## Aggregate ownership

The final `Aggregate CI gate` remains local to every consumer. The shared platform must not silently decide that an application-specific job is optional.

The guard verifies that a real job named `Aggregate CI gate` exists and that the same job block has an `if: ${{ always() }}` fail-closed path. The caller remains responsible for listing all application-specific required jobs in its aggregate `needs` graph.

For defense in depth, branch protection should require both the exact local `Aggregate CI gate` and the governance-guard check after the guard has been live-proven in that repository. This prevents an accidental CI edit from making the governance job merely optional.

## Rollout policy

Governance changes are rolled out platform-first:

1. engineering-platform self-CI;
2. manual platform merge;
3. YetAnotherCyclingSim canary upgrade;
4. full consumer proof;
5. incremental 4VELO adoption.

No governance/platform/security PR is auto-merged.
