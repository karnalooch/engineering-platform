# Security Policy

## Supported code

The current `main` branch is the supported engineering-platform line during bootstrap.

## Reporting

Prefer GitHub private vulnerability reporting when available. Do not publish credentials, tokens, private keys, exploit details or sensitive proof-of-concept material in public issues.

## Platform security rules

- External GitHub Actions are pinned to immutable 40-character commit SHAs.
- Reusable workflows declare least-privilege permissions.
- Consumers pin this repository to immutable reviewed commit SHAs.
- `@main` is not a supported consumer reference.
- Platform, CI, security and policy changes are manual-merge.
- A caller's final aggregate gate remains local and fail-closed.

A reusable workflow cannot elevate a caller's `GITHUB_TOKEN` permissions. Callers must explicitly grant the permissions documented by each workflow.
