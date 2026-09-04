# Gate P digest-scan name-binding remediation review handoff

## Objective

Review the bounded source correction after approved Gate P run `33810540964` failed closed before signing. Preserve digest-based Syft scanning while binding the raw SPDX document/package identity to the reviewed managed repository and the package version/checksum/purl semantics to the immutable metadata digest.

## Exact boundary

- Base: protected `develop@b54c4a42376f298c8be89a64acc00733b7c1700f`
- Branch: `fix/gate-p-digest-scan-name-binding`
- Failed run: `33810540964`
- Failed step: `Sign and verify published image attestation set`
- Failure class: pre-sign raw-SPDX validation compared Syft's repository-only digest-scan document name with Buildx's tagged `image.name`
- Publication state: one immutable image exists; backend/frontend SBOM and image metadata exist; no signature or attestation was created
- Retry authority: consumed; no retry is authorized
- Private raw evidence: operator-held Gate P evidence directory; private identifiers and immutable image reference are intentionally omitted here

## RED → GREEN correction

The focused regression uses production-shaped metadata and SPDX semantics:

- Buildx metadata carries a tagged `image.name` and immutable `containerimage.digest`;
- Syft scans the immutable `repository@sha256:...` reference;
- the SPDX document/package name is the repository without tag or digest;
- package `versionInfo` is the immutable digest;
- checksum and OCI purl retain exact AMD64/digest binding.

The regression was RED because PR/pre-sign mode prohibited a reviewed repository override and inferred a tag-bound expected name from Buildx metadata. The first correction permitted a validated Artifact Registry repository in raw-SPDX mode and used the metadata digest as the package version. Adversarial rereview then proved that independently valid metadata and override repositories could diverge and that an unexpected purl tag was accepted for a digest scan. The hardened correction now requires the override to equal the repository portion of Buildx `image.name`, requires its tag to be a commit-shaped SHA, and requires the exact expected purl query: `arch=amd64` only for digest scans or `arch=amd64&tag=<expected>` for tag scans. Deployment admission applies the same exact no-tag digest-scan query contract. Cloud-blind PR validation remains unchanged when no repository override is supplied.

The workflow passes `MANAGED_REPOSITORY` only inside the protected publication job. Static policy contains the exact amended command and refreshed executable-script SHA-256.

## Actual-image evidence

The immutable image produced by failed run `33810540964` was rescanned read-only with checksum-verified Syft `1.37.0`, explicitly selecting `linux/amd64` from the local ARM64 host. The resulting raw SPDX passed the corrected verifier against that run's exact metadata and application SBOMs. Ephemeral registry credentials and temporary Syft files were removed. This proves the source correction against the current artifact but does not create or imply signature, transparency, provenance, or attestation evidence.

## Candidate file inventory

1. `.github/workflows/build-image.yml`
2. `AGENTS.md`
3. `ARCHITECTURE.md`
4. `CURRENT_WORK.md`
5. `NOTES.md`
6. `README.md`
7. `ROADMAP.md`
8. `SECURITY.md`
9. `TECHNICAL_REQUIREMENTS.md`
10. `deploy/gcp/first-deployment-runbook.md`
11. `docs/review-handoffs/2026-09-03-gate-p-digest-scan-name-binding-review-handoff.md`
12. `infra/gcp/README.md`
13. `scripts/validate_terraform_static.py`
14. `scripts/verify_deploy_image_authority.py`
15. `scripts/verify_image_provenance.py`
16. `tests/unit/test_deploy_image_authority.py`
17. `tests/unit/test_image_provenance.py`

## Local verification

- Current immutable `linux/amd64` image read-only Syft scan and corrected raw-SPDX verifier: passed.
- Full unit suite: `629 passed, 1 warning`.
- Focused Gate P generator/deployment/image/workflow suite: `338 passed`.
- Frontend: `116 passed`; coverage thresholds and production build passed.
- `uv lock --check`, Ruff format/check, strict mypy, Bandit, and pip-audit: passed.
- Terraform static validation and recursive formatting: passed.
- Working-tree Gitleaks: no leaks across approximately 16.04 MB.
- Diff hygiene: passed.

## Review questions

1. Does the correction preserve immutable digest authority rather than weakening the scan to a mutable tag?
2. Is the explicit repository override validated and confined to raw-SPDX pre-sign validation?
3. Do document name, package name/version, checksum, architecture, and OCI purl remain mutually bound?
4. Does cloud-blind pull-request validation remain unchanged?
5. Do static policy and workflow command hashes cover the exact protected publication command?
6. Do living documents accurately record PR #72, failed run `33810540964`, consumed approval, missing evidence, and the fresh exact-tip retry boundary?
7. Is any private identifier, credential, registry value, or raw provider output exposed?

## Independent review result

Fresh security rereview found no Blocker, High, or Medium after requiring exact metadata/override repository equality, a commit-shaped metadata tag, and exact purl query parsing with blank values preserved. Fresh documentation/privacy rereview found no Blocker, High, or Medium; the 17-file inventory, current totals, failed-run boundary, consumed approval, and absence of private identifiers are consistent.

## Stop boundary

This is source-only remediation. It authorizes no publication retry, cloud mutation, Secret version, database/migration, service activation, tester access, qualification, live/client data, or production action. After clean review and protected merge, a new exact-tip rebind and explicit one-dispatch Gate P approval are required.
