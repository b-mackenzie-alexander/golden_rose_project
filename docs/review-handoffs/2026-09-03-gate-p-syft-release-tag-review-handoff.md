# Gate P publication-chain remediation review handoff

## Objective

Review the single source-only remediation assembled after the first post-PR71 Gate P dispatch and complete local preflight. The dispatch exposed a Syft release-tag failure; exact-action, actual-image, and disposable-registry rehearsal then exposed two additional incompatibilities that would have caused later Gate P failures.

## Source of truth

- Accepted outcome plan: `.hermes/plans/2026-09-02_164500-foundation-project-identity-reconciliation-plan.md`
- Base: protected `develop@59d8865d2529cdde999f90bb675cc207411a231e`
- Branch: `fix/gate-p-syft-release-tag`
- Failed protected run: `33779786922`
- Private raw run and actual-image evidence remain outside Git and ordinary documentation.

## Exact candidate inventory

- `.github/workflows/build-image.yml`
- `.github/workflows/deploy-develop.yml`
- `AGENTS.md`
- `ARCHITECTURE.md`
- `CURRENT_WORK.md`
- `NOTES.md`
- `README.md`
- `ROADMAP.md`
- `SECURITY.md`
- `TECHNICAL_REQUIREMENTS.md`
- `deploy/gcp/first-deployment-runbook.md`
- `deploy/gcp/staged-plan-approval.md`
- `infra/gcp/README.md`
- `infra/policy/predeployment-authority-manifest.json`
- `infra/policy/spdx-2.3.schema.json`
- `pyproject.toml`
- `uv.lock`
- `scripts/generate_slsa_provenance.py`
- `scripts/validate_terraform_static.py`
- `scripts/verify_deploy_image_authority.py`
- `scripts/verify_image_provenance.py`
- `tests/unit/test_deploy_image_authority.py`
- `tests/unit/test_generate_slsa_provenance.py`
- `tests/unit/test_image_provenance.py`
- `tests/unit/test_terraform_hygiene.py`
- `docs/review-handoffs/2026-09-03-gate-p-syft-release-tag-review-handoff.md`

## Observed failure and preflight findings

1. The protected dispatch passed source enforcement, WIF authentication, registry login, and immutable `linux/amd64` image build/push. It stopped before signing because Anchore's action requested nonexistent release tag `1.37.0`; upstream publishes `v1.37.0`.
2. The exact commit-pinned Anchore installer successfully installed `v1.37.0` under Linux AMD64. Scanning the exact already-pushed immutable image succeeded, but real Syft SPDX uses a `DESCRIBES` relationship rather than the fixture-only top-level `documentDescribes` form.
3. Disposable loopback-registry rehearsal proved Cosign v3 signature and all three attestation classes can be created and verified locally. It also proved `--type slsaprovenance` emits SLSA v0.2 and treated raw Buildx metadata as an empty predicate; it cannot satisfy the repository's SLSA v1 admission contract.
4. The corrected path generates a validated SLSA v1 predicate from Buildx metadata, normalizes equivalent GitHub repository spellings to one canonical no-`.git` identity, signs it with Cosign's `slsaprovenance1` type, captures raw Cosign verification output, and feeds that output through the deployment-authority verifier. The generator passes against the preserved failed-run metadata, and the complete local signature/SLSA-v1/SPDX/application-SBOM chain passed against one immutable local-registry digest.

## Implemented correction

- Pin Anchore's action input to exact upstream tag `v1.37.0` while retaining the immutable action commit.
- Add cloud-blind PR validation that installs pinned Syft, scans the loaded Linux AMD64 image, validates actual SPDX inventory semantics, and uploads the image SBOM.
- Accept both valid SPDX description representations while retaining fail-closed package and described-subject checks.
- Vendor the official SPDX 2.3 Draft-07 JSON schema from the SPDX `v2.3` specification tag and pin its reviewed SHA-256 (`239208b7ac287b3cf5d9a9af23f9d69863971102a5e1587a27a398b43490b89b`) before semantic image/platform checks.
- Generate a schema-correct SLSA v1 predicate only after validating Buildx digest, source repository/revision, Dockerfile, BuildKit build type, and dependency materials.
- Use `slsaprovenance1` consistently for publication and later direct OCI admission.
- Capture raw signature and attestation verification output instead of synthesizing trust summaries inside the workflow.
- Bind the signed application-SBOM checksums to the exact backend/frontend SBOM files before publication succeeds.
- Keep PR CI cloud-blind: no GCP authentication, registry publication, keyless signing, or protected credentials are added to pull requests.

## Verification completed

- Exact pinned Syft installer: passed under Linux AMD64.
- Exact immutable failed-run image scan: passed with 144 packages; actual SPDX structure inspected.
- Disposable Cosign v3 chain: signature plus SLSA v1, SPDX, and application-SBOM attest/verify all passed.
- Raw verified envelopes through `verify_deploy_image_authority.py`: passed for the immutable local digest.
- Full unit suite: `619 passed, 1 warning`.
- Focused generator/deployment/image/workflow suites: `328 passed`.
- Frontend verification: `116 passed`, coverage thresholds and production build passed.
- Terraform static validation and formatting: passed.
- Ruff format/check: passed.
- Strict mypy: passed for 83 source files.
- Python dependency lock/audit: `uv lock --check` passed; `jsonschema==4.26.0` is a direct dev dependency; `pip-audit --skip-editable` found no known vulnerabilities.
- Bandit: passed with only the existing reviewed `nosec` warning.
- Working-tree Gitleaks: no leaks found across approximately 16.02 MB.
- Tracked diff and untracked-handoff whitespace hygiene: passed.
- Disposable registry, temporary workspace, and ephemeral key material: removed and absence verified.

One initial full-unit attempt reported 605 passes plus one Terraform-provider registry timeout. The exact node passed on retry and the complete suite then passed; this was an external setup failure, not a product regression. PR #72 opened one commit ahead of the base at `6949502`; its exact-range Gitleaks evidence and protected checks passed and remain bound to that head. Only the purl-prefix follow-up described below is currently uncommitted.

## Independent review findings and remediation

The fresh review found one High and two Medium findings:

- High: deployment accepted signed hash-shaped application-SBOM values without independently available inventory content.
- Medium: structural SPDX checks accepted fabricated versions/documents without exact Syft, platform, or image identity.
- Medium: `CURRENT_WORK.md` retained a stale `develop@64f4ae5` active-tip sentence.

The current remediation embeds exact backend/frontend CycloneDX bytes in the signed application-SBOM predicate, validates their schema identity and hashes at deployment, and compares them byte-for-byte with source files during publication. SPDX admission now requires `SPDX-2.3`, `CC0-1.0`, mandatory document/package fields, Syft 1.37.0 creation identity, exactly one described container package, the expected repository/version, a valid SHA-256 checksum, and an amd64 OCI purl. Present-but-malformed alternate description/relationship fields fail closed. The stale active-tip ledger now distinguishes historical PR #69, PR #71's `develop@59d8865` base, the failed dispatch, and the required post-merge exact-tip retry approval.

Focused remediation and full unit tests pass. The complete post-remediation local chain was rerun with the pinned Cosign 3.0.6 installer and checksum-verified Syft 1.37.0: strict actual-image SPDX validation, the approximately 678 KB embedded application-SBOM predicate, signature, all three attestations, all four Cosign verifications, and final deployment-authority admission passed for one immutable loopback-registry digest. All rerun-owned registry, binary, output, and key material was then removed and absence verified.

Final security rereview independently fetched the upstream SPDX `v2.3` schema, detected and caused removal of one initially appended newline, and proved the current 45,312-byte file is byte-identical at SHA-256 `239208b7ac287b3cf5d9a9af23f9d69863971102a5e1587a27a398b43490b89b`. It closed the application-SBOM High, original SPDX-shape Medium, and schema-byte mismatch. Final documentation rereview closed all continuity findings, matched all 26 files, and found no privacy issue.

After PR #72 opened at `6949502` and all protected checks passed, a delayed review result exposed one remaining Medium: both purl validators extracted a digest with `removeprefix` without first proving the required `pkg:oci/<repository>@sha256:` prefix. Exact PR and deployment adversarial regressions failed before the fix and now pass after an explicit prefix check. Full unit and focused totals are updated above. Fresh independent security and documentation rereviews are CLEAN at Blocker/High/Medium. This bounded uncommitted follow-up may now be committed/pushed and exact-head/range plus protected-check evidence refreshed; the PR's current clean evidence remains bound only to `6949502` until then.

## Review focus

1. Confirm the SLSA predicate is schema-correct v1 rather than mislabeled Buildx metadata or Cosign's v0.2 alias.
2. Confirm source commit/ref/repository, Dockerfile, Linux AMD64 output, GitHub-hosted builder, invocation, expected base images, and OCI subject digest all fail closed.
3. Confirm raw Cosign outputs—not workflow-authored trust summaries—are the inputs to publication admission.
4. Confirm real Syft `DESCRIBES` relationships are accepted without accepting empty, undescribed, or malformed inventories.
5. Confirm application-SBOM checksums are compared to the exact reviewed files.
6. Confirm workflow/static-policy/manifest parity and that PR validation remains cloud-blind.
7. Confirm no private identifier, credential, registry reference, or raw provider output entered the repository.

## Hard stop

Do not retry publication from this branch. Protected merge, exact-tip rebind, and fresh one-retry approval are required. GitHub keyless OIDC/Fulcio/transparency behavior remains the final unmockable proof. No Secret version, database, migration, service, tester, qualification, live/client data, or production action is authorized.
