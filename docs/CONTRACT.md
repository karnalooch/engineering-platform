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

  governance:
    permissions:
      contents: read
    uses: karnalooch/engineering-platform/.github/workflows/reusable-governance.yml@<same-reviewed-sha>

  security:
    permissions:
      contents: read
      security-events: write
    uses: karnalooch/engineering-platform/.github/workflows/reusable-security.yml@<same-reviewed-sha>
    with:
      codeql_languages_json: '["python","c-cpp"]'
```

Do not use `@main`, `@master` or a tag as an active consumer pin. The reusable governance guard enforces full immutable SHA references.

## Permissions

Reusable workflows cannot elevate the caller's `GITHUB_TOKEN`. The caller grants only the permissions required by the selected workflow.

## Repository policy inputs

The generic repository policy always enforces the maximum non-LFS blob size. Required LFS extensions and forbidden path components are caller-owned parameters so Unreal, web/mobile and other repositories can have different rules without forking the platform workflow.

## Governance guard

The reusable governance guard protects process invariants that should not depend on memory:

- high-risk PR path classification;
- exact `Auto-merge: manual` requirement for high-risk changes;
- immutable external Action/workflow refs;
- immutable engineering-platform consumer refs;
- no `continue-on-error: true` fail-open workflow paths;
- no workflow-level `permissions: write-all`;
- preservation of a caller-local `Aggregate CI gate`.

These baseline rules are intentionally non-disableable by consumer inputs. Consumers may only add application-specific high-risk path patterns.

See `docs/GOVERNANCE_GUARD.md` for the versioned policy.

## Security baseline

The reusable security baseline provides:

- Dependency Review on pull requests;
- CodeQL for a caller-provided language matrix using build mode `none`;
- Trivy filesystem vulnerability/secret/misconfiguration scanning;
- CycloneDX source SBOM on non-PR events.

CodeQL build mode `none` is static analysis. It must never be described as proof that Unreal Engine, native mobile code or another toolchain actually compiles.

## Final aggregate

The final required aggregate check belongs to the consumer repository. This keeps the exact dependency graph visible in the caller and prevents a shared workflow from silently deciding that an application-specific required job is optional.

The governance guard verifies the local aggregate boundary exists; the consumer still owns its exact `needs` graph.
