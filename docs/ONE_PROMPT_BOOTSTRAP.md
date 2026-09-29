# One-prompt bootstrap

Status: **ACTIVE / AUTHORITATIVE PROMPT CONTRACT**

Use this prompt when asking an agent to introduce Gumball into a new or existing repository.

```text
Read the repository before modifying anything.

Read all applicable AGENTS.md files, README files, docs indexes, manifests,
CI workflows, build/test scripts, release configuration and security policy.

Then read the current Gumball adoption, CI, governance and agent contracts.

Determine the repository's actual architecture and select only applicable
Gumball profiles.

Run an audit first. Do not edit during audit.

Produce an adoption plan that marks proposed changes as ADD, MODIFY, KEEP,
DEFER or CONFLICT.

Preserve intentional project-specific behavior. Do not blindly replace
AGENTS.md, documentation, CI, security configuration, release workflows or
runtime proof.

Required baseline:
- a clear documentation entry point / SSOT map;
- explicit agent operating rules;
- deterministic CI;
- a fail-closed caller-local Aggregate CI gate;
- anti-no-op assertions where filtered tests/packages can match nothing;
- immutable external workflow/action references;
- security and repository-governance baseline;
- Gumball doctor / contract verification;
- a path for recording reusable downstream improvements as Gumball promotion
  candidates;
- repository lifecycle policy for branches, PRs, issues and GitHub Projects;
- shared PR label taxonomy and trusted automatic classification;
- application version/stage/artifact lineage for release-capable repositories;
- CI Cost Governor planning that minimizes heavy builds, reuses build fingerprints
  and defers non-merge-critical heavy proof.

Keep heavyweight runtime, visual, emulator, hardware and environment-specific
proof outside routine PR CI unless the repository already requires it or the
selected profile explicitly enables it.

Unknown runtime/configuration surfaces fail safe toward broader validation.

Do not weaken a failing test or gate merely to obtain green CI.

Implement the reviewed plan on a dedicated branch. Run the smallest trustworthy
validation plus all repository-required gates. Update the authoritative docs in
the same change when behavior or policy changes.

At the end report:
- what was adopted;
- what existing controls were preserved;
- conflicts or deferred items;
- tests/gates actually executed;
- remaining unverified behavior;
- reusable improvements discovered that should be proposed back to Gumball.
```

The prompt intentionally does not prescribe a technology stack. Repository evidence decides the profile and implementation.

