# Consumer contract

## Immutable consumption

Consumer repositories call reusable workflows using a reviewed 40-character commit SHA:

```yaml
jobs:
  repo-policy:
    permissions:
      contents: read
    uses: karnalooch/engineering-platform/.github/workflows/reusable-repo-policy.yml@<40-char-reviewed-sha>
    with:
      max_non_lfs_mib: 10
      required_lfs_extensions: ".uasset,.umap,.fbx,.blend,.wav,.flac,.mp3,.exr,.hdr,.tga"
      forbidden_path_components: ".vs,Binaries,DerivedDataCache,Intermediate,Saved"

  security:
    permissions:
      contents: read
      security-events: write
    uses: karnalooch/engineering-platform/.github/workflows/reusable-security.yml@<same-reviewed-sha>
    with:
      codeql_languages_json: '["python","c-cpp"]'

  risk-policy:
    permissions:
      contents: read
    uses: karnalooch/engineering-platform/.github/workflows/reusable-risk-policy.yml@<same-reviewed-sha>

  consumer-contract:
    permissions:
      contents: read
    uses: karnalooch/engineering-platform/.github/workflows/reusable-consumer-contract.yml@<same-reviewed-sha>
    with:
      require_external_action_sha: true
```

Do not use `@main`, `@master` or a moving tag as the active security-sensitive consumer pin.

## One platform version per consumer

A repository should use one engineering-platform SHA across all active shared workflow calls. Mixing SHAs makes rollbacks and incident analysis ambiguous. The consumer-contract guard can enforce this automatically.

## Permissions

Reusable workflows cannot elevate the caller's `GITHUB_TOKEN`. The caller grants only the permissions required by the selected workflow.

## Repository policy inputs

The generic repository policy always enforces the maximum non-LFS blob size. Required LFS extensions and forbidden path components are caller-owned parameters so Unreal, web/mobile and other repositories can have different rules without forking the platform workflow.

## Risk policy

The shared risk policy detects high-risk paths. High-risk pull requests must explicitly declare:

```text
Risk: high
Auto-merge: manual
```

Consumers can extend the path patterns for application-specific deployment, secrets, native toolchain or release files.

## Security baseline

The reusable security baseline provides:

- Dependency Review on pull requests;
- CodeQL for a caller-provided language matrix using build mode `none`;
- Trivy filesystem vulnerability/secret/misconfiguration scanning;
- CycloneDX source SBOM on non-PR events.

CodeQL build mode `none` is static analysis. It must never be described as proof that Unreal Engine, native mobile code or another toolchain actually compiles.

## Final aggregate

The final required aggregate check belongs to the consumer repository. This keeps the exact dependency graph visible in the caller and prevents a shared workflow from silently deciding that an application-specific required job is optional.

The consumer-contract guard verifies the presence of the exact local `Aggregate CI gate`, its `if: ${{ always() }}` behavior, immutable platform refs and the absence of fail-open `continue-on-error: true`.
