# Governance guard

The governance guard is a reusable fail-closed workflow that protects process invariants which are easy to forget during normal development.

## What it enforces

On every caller repository it can:

- classify pull requests from the actual changed paths;
- require the exact PR-body marker `Auto-merge: manual` when high-risk paths are touched;
- reject mutable or otherwise non-immutable external GitHub Action/workflow refs;
- reject mutable `engineering-platform` consumer refs such as `@main`, `@master`, or a tag;
- reject `continue-on-error: true` in GitHub Actions workflows;
- require a caller-local `Aggregate CI gate` with an `always()` fail-closed path.

## Default high-risk paths

The default contract classifies these as high-risk:

```text
.github/**
SECURITY.md
**/SECURITY.md
**/package.json
**/pnpm-lock.yaml
**/package-lock.json
**/yarn.lock
**/pyproject.toml
**/requirements*.txt
**/Dockerfile*
**/eas.json
**/app.config.js
```

Consumers may add or replace patterns when their application has additional sensitive surfaces.

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

The guard only verifies that this local safety boundary still exists; the caller remains responsible for listing all required jobs in its aggregate `needs` graph.

## Rollout policy

Governance changes are rolled out platform-first:

1. engineering-platform self-CI;
2. manual platform merge;
3. YetAnotherCyclingSim canary upgrade;
4. full consumer proof;
5. incremental 4VELO adoption.

No governance/platform/security PR is auto-merged.
