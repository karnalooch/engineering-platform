# Governance guard

The governance guard is a reusable fail-closed workflow that protects process invariants which are easy to forget during normal development.

## What it enforces

On every caller repository it:

- classifies pull requests from the actual changed paths;
- requires the exact PR-body marker `Auto-merge: manual` for high-risk paths by default;
- rejects mutable or otherwise non-immutable external GitHub Action/workflow refs;
- rejects mutable `engineering-platform` consumer refs such as `@main`, `@master`, or a tag;
- rejects consumers that mix multiple valid `engineering-platform` SHAs across active workflow calls;
- rejects fail-open `continue-on-error: true` in GitHub Actions workflows;
- rejects workflow-level `permissions: write-all`;
- requires a caller-local `Aggregate CI gate` whose own job block contains `if: ${{ always() }}`.

The workflow-safety checks cannot be disabled by caller inputs. The PR-body marker requirement is caller-configurable; risk classification remains active.

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

### Consumer-owned marker policy

An owner-approved consumer can remove the mandatory body marker with:

```yaml
with:
  require_manual_merge_marker: false
```

The default is `true`, preserving existing consumers. Only an explicit `false`
disables the body-text requirement. High-risk paths are still classified, and
immutable refs, coherent platform pins, permissions, fail-open rejection and the
caller-local aggregate boundary are still enforced. This input does not grant
merge authorization or change the trusted auto-merge controller's eligibility
rules. The owner/consumer owns authorization and required proof.

YACS requested this policy after a formatting-only marker failure interrupted
iteration on its verified build-cache repair (YACS Issue #355 / PR #356).

### Dependabot high-risk exception

Consumers that use Dependabot for workflow or dependency-file maintenance may opt in to:

```yaml
with:
  allow_dependabot_high_risk_without_manual_marker: true
```

The default is `false`.

When enabled, the guard waives only the PR-body `Auto-merge: manual` marker requirement, and only when the pull request author is exactly `dependabot[bot]`. All other governance checks remain active, including immutable action refs, fail-open rejection, aggregate-gate enforcement and high-risk path classification.

This input does **not** make Dependabot PRs eligible for auto-merge. Merge policy remains caller-owned and must independently block or manually review high-risk changes.

## Why high-risk means manual

High-risk classification does not mean the change is bad. It means the change can alter the safety boundary, dependency graph, toolchain, release process, or CI result itself.

Under the default policy, a high-risk PR needs:

```text
Auto-merge: manual
```

in its body. This makes accidental eligibility for automated merging a CI failure rather than a memory problem.

## Immutable references

Consumer repositories must call shared workflows with a reviewed full commit SHA:

```yaml
uses: karnalooch/engineering-platform/.github/workflows/reusable-governance.yml@0123456789abcdef0123456789abcdef01234567
```

Mutable refs such as `@main`, `@master`, `@v1` or `@v1.2.3` are rejected by the guard. A consumer may contain many active Gumball workflow calls, but every `karnalooch/engineering-platform/.github/workflows/*` call must resolve to the same reviewed 40-character SHA. Two individually valid but different platform SHAs fail closed as a mixed-platform-version configuration.

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

## Auto-merge interaction

The reusable Governance Guard and the repository-local privileged auto-merge controller are separate layers.

- Governance classifies high-risk PRs; its default policy requires `Auto-merge: manual`, while an explicit consumer policy may disable that body-text requirement.
- The privileged controller runs only trusted code from the default branch and independently rejects its own high-risk path set.
- A passing Governance check is necessary but never sufficient for auto-merge.
- The controller also requires the local `Aggregate CI gate`, clean review state, a closing Issue and exact clean mergeability.

See `docs/AUTO_MERGE.md`.
