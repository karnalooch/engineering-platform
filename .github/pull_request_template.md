## Summary

<!-- What shared contract changes and why? -->

Closes #

## Contract impact

- [ ] No caller-visible behavior change
- [ ] Backward-compatible caller change
- [ ] Breaking caller change

## Verification

- [ ] Self-CI executes the changed workflow/policy path
- [ ] External actions remain pinned to immutable SHAs
- [ ] Token permissions remain least-privilege
- [ ] No caller is required to consume `@main`
- [ ] No application-specific implementation leaked into the platform
- [ ] Rollout/migration notes are updated when the caller contract changes

## Merge policy

Auto-merge: manual

Default is manual.

Only a demonstrably low-risk PR may replace the marker above with exactly
`Auto-merge: eligible`. CI/security/governance/versioning/dependency/toolchain
and other high-risk paths remain manual and the trusted auto-merge controller
independently re-checks eligibility.
