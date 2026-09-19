## Summary

<!-- What shared contract changes and why? -->

Closes #

## Contract impact

- [ ] No caller-visible behavior change
- [ ] Backward-compatible caller change
- [ ] Breaking caller change

## Risk

Risk: high

Platform/CI/security/governance changes are treated as high risk by default.
If this PR is truly docs-only, the automated classifier may report normal risk;
overstating risk is allowed, understating it is not.

## Verification

- [ ] Self-CI executes the changed workflow/policy path
- [ ] External actions remain pinned to immutable SHAs
- [ ] Token permissions remain least-privilege
- [ ] No caller is required to consume `@main`
- [ ] No application-specific implementation leaked into the platform
- [ ] Rollout/migration notes are updated when the caller contract changes

## Merge policy

Auto-merge: manual

Platform/CI/security/governance changes remain manual-merge.
