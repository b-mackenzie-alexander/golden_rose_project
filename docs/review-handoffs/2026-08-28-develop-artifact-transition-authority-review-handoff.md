# Review Handoff — PR A artifact and transition authority interoperability

**Date:** 2026-08-28
**Branch:** `fix/develop-artifact-transition-authority`
**Target PR base:** `develop`
**Planning base / merge tip:** `origin/develop` at `d142bba476753da42e8395a415600c297c65d594` (`fix(terraform): prepare bootstrap state adoption` / PR #50 merge)
**Controlling authorities:**
- `docs/adr/ADR-0014-workflow-scale-planning-and-delivery.md`
- `.hermes/plans/2026-08-27_124046-private-develop-activation-human-feedback-plan.md`
- `docs/adr/ADR-0013-post-pr33-deployment-path-remediation.md`
- `GIT_WORKFLOW.md`
- `AGENTS.md`
**Review surface:** local uncommitted working tree above `origin/develop`
**Ahead commits vs `origin/develop` at handoff creation:** `0`
**Behind commits vs `origin/develop` at handoff creation:** `0`
**PR status:** no PR opened for this slice yet. This packet hands off the bounded PR A source surface for independent review before commit / push / PR.

## 1. Current branch truth

Observed live branch state at handoff creation:
- `git rev-parse HEAD` → `d142bba476753da42e8395a415600c297c65d594`
- `git rev-parse origin/develop` → `d142bba476753da42e8395a415600c297c65d594`
- `git rev-list --count origin/develop..HEAD` → `0`
- `git rev-list --count HEAD..origin/develop` → `0`

Interpretation:
- this slice is **not** a committed PR range yet
- exact-range review over `origin/develop...HEAD` is not yet meaningful
- exact-range Gitleaks is still pending by design
- review must target the **live working-tree diff** and the grounded local verification evidence already recorded in the repo

## 2. Approved scope and explicit non-scope

This handoff covers only Implementation PR A from the accepted master plan:
- real Buildx / Cosign / registry artifact evidence instead of workflow-authored placeholders
- separate `golden-rose-artifact-verifier` authority and exact repository reader posture
- verifier / deployer credential-separation in the deploy workflow
- minimized migration-success receipt production after successful waited migration execution only
- signing and detached-bundle handling for migration-success receipts
- strict service-gate validation of reviewed stage / migration / migration-success inputs
- value-safe runbook and receipt-template alignment for the reviewed service-approval boundary
- living-doc and review-packet alignment for the local review surface

It must confirm the lane did **not** widen into:
- private inventory, backend/state initialization, import, state read/write, or lineage work
- Terraform plan/apply or cloud mutation
- image publication against the real target
- secret/database preparation, migration execution, service activation, tester access, or qualification
- client/live data, real identity, public access, or production activity
- unrelated Terraform resource classes, frontend product work, queue/map/worker scope, or adjacent PR B work

## 3. Primary files in the review surface

### Workflow / policy / runbook / receipts
- `.github/workflows/build-image.yml`
- `.github/workflows/deploy-develop.yml`
- `infra/policy/predeployment-authority-manifest.json`
- `deploy/gcp/first-deployment-runbook.md`
- `deploy/gcp/receipts/README.md`
- `deploy/gcp/receipts/templates/migration-success-receipt.example.json`

### Terraform / authority contracts
- `infra/gcp/bootstrap/iam.tf`
- `infra/gcp/develop/iam.tf`

### Scripts
- `scripts/validate_terraform_static.py`
- `scripts/verify_gcp_foundation.py`
- `scripts/verify_image_provenance.py`
- `scripts/verify_migration_database_readback.py`
- `scripts/verify_stage_receipt.py`
- `scripts/write_migration_success_receipt.py`

### Tests
- `tests/unit/test_image_provenance.py`
- `tests/unit/test_verify_migration_database_readback.py`
- `tests/unit/test_stage_receipt.py`
- `tests/unit/test_terraform_hygiene.py`
- `tests/unit/test_verify_gcp_foundation.py`
- `tests/unit/test_write_migration_success_receipt.py`

### Living docs / evidence / review state
- `CURRENT_WORK.md`
- `ROADMAP.md`
- `NOTES.md`
- `docs/review-handoffs/2026-08-28-develop-artifact-transition-authority-review-handoff.md`

## 4. What changed in this slice

### Actual-shaped artifact evidence
- `scripts/verify_image_provenance.py` now accepts actual-shaped SPDX DSSE image-SBOM attestation output instead of only a synthetic CycloneDX placeholder artifact.
- `.github/workflows/build-image.yml` now captures real `cosign verify-attestation --type https://spdx.dev/Document --output json` output instead of fabricating `build/image-sbom.cdx.json` inline.

### Artifact-verifier authority split
- Added the separate control-plane `golden-rose-artifact-verifier` identity and exact deploy-workflow WIF binding.
- Added exact Artifact Registry reader authority for the artifact verifier while preserving writer-only authority for `golden-rose-image-publisher` and Cloud Run-only authority for `golden-rose-deployer`.
- `scripts/verify_gcp_foundation.py` and `scripts/validate_terraform_static.py` now enforce that writer / reader / deployer split.
- The foundation verifier and static policy now require the Workload Identity Provider `attribute_condition` to equal the reviewed canonical conjunction/disjunction, rejecting additive permissive terms such as `|| true`.

### Verifier / deployer credential separation
- `.github/workflows/deploy-develop.yml` now authenticates first as the artifact verifier for OCI verification only, with a dedicated temporary `DOCKER_CONFIG` and isolated Google credential context.
- The workflow explicitly logs out and removes Docker / Google credential material before the deployer authentication step begins.
- Static policy now pins and allowlists that exact split step ordering and body.

### Migration-success authority production
- Added `scripts/write_migration_success_receipt.py`.
- The workflow binds the direct verified immutable digest into `deploy-result.json` before it writes a minimized migration-success receipt after a successful waited migration execution and only for the migration stage.
- The receipt is bound to the migration receipt SHA-256, source SHA, immutable image digest, and execution reference.

### Signed migration-success artifact set
- The workflow now signs the migration-success receipt with `cosign sign-blob --bundle ...` and uploads both the JSON receipt and detached Sigstore bundle as separate operator-held artifacts.
- Static policy pins the exact signing step and bundle-upload contract.

### Service-gate strictness
- `scripts/verify_stage_receipt.py` now requires the exact reviewed migration-success receipt shape and rejects unreviewed extra fields.
- The service-stage pre-auth verification step now fail-closes on missing:
  - `STAGE_RECEIPT_BASE64`
  - `STAGE_RECEIPT_BUNDLE_BASE64`
  - `STAGE_RECEIPT_CERTIFICATE_IDENTITY`
  - `MIGRATION_SUCCESS_RECEIPT_CERTIFICATE_IDENTITY`
- Migration-success guidance now states that service approval still requires separate database/schema/authority readback and that the signed migration receipt remains a separate required service-gate input.
- The service pre-auth path now requires a separately signed post-migration database/schema/authority readback receipt and detached bundle, verifies the signer, and structurally binds the readback receipt to the migration receipt, migration-success receipt, source SHA, immutable digest, and waited execution reference before any cloud authentication.

### Independent-review remediation (2026-08-28)
- Hardened SPDX DSSE publish evidence so its exact subject repository and SHA-256 must match the reviewed immutable image.
- Hardened static IAM validation to parse and bind the actual `artifact_verifier_reader` resource fields rather than accepting independent fragments or comments.
- Added the artifact verifier to the foundation verifier's expected control-plane inventory, key collection, and service-account IAM collection; a verifier-key drift fixture now fails closed.

## 5. Exact-family completion summary

The approved PR A lane appears locally complete through the bounded source-only artifact / transition authority families implemented on this branch:
1. publish-mode image SBOM evidence switched from placeholder generation to actual-shaped attestation handling
2. artifact-verifier control-plane identity and repository-reader split added and enforced
3. verifier / deployer credential-separation implemented in `deploy-develop.yml`
4. migration-success receipt production added and stage-gated to successful waited migration execution
5. migration-success receipt signing and detached bundle upload added
6. service-gate migration-success receipt shape tightened to exact reviewed fields only
7. operator runbook corrected so migration-success artifacts are necessary but not sufficient for service approval
8. service-stage pre-auth verification now fail-closes on missing migration-success certificate identity
9. pre-auth verification now fail-closes on missing stage-receipt certificate identity
10. pre-auth verification now fail-closes on missing stage-receipt payload and bundle inputs before decode
11. operator runbook now binds migration-success verification to reviewed GitHub Actions certificate identity and OIDC issuer
12. operator runbook now states the signed migration receipt remains a separate service-gate input

No implementation outside the bounded review-remediation families was performed after that boundary.

## 6. Real verification evidence already observed

For the dated RED/GREEN ledger, see the 2026-08-27 and 2026-08-28 PR A entries in `NOTES.md`.

### Broad slice verification
- `env -u PYTHONPATH uv run pytest -q tests/unit/test_terraform_hygiene.py tests/unit/test_verify_gcp_foundation.py tests/unit/test_image_provenance.py tests/unit/test_write_migration_success_receipt.py tests/unit/test_verify_migration_database_readback.py`
  - result: `328 passed in 51.12s`
- `env -u PYTHONPATH uv run ruff format --check scripts tests`
  - result: `53 files already formatted`
- `env -u PYTHONPATH uv run ruff check scripts tests`
  - result: passed
- `env -u PYTHONPATH uv run mypy src tests`
  - result: `Success: no issues found in 82 source files`
- `env -u PYTHONPATH uv run python scripts/validate_terraform_static.py`
  - result: `Terraform static validation passed`
- `git diff --check`
  - result: passed

### Representative focused families already observed
- artifact-verifier authority family
  - focused result: `2 passed`
- deploy-workflow credential-separation family
  - focused result: `2 passed`
- migration-success receipt production / verification family
  - focused result: `7 passed`
- service-approval runbook boundary family
  - focused result: `3 passed`
- migration-success signer-identity runbook family
  - focused result: `3 passed`
- migration-receipt service-gate parity runbook family
  - focused result: `3 passed`

### Key exact selectors the reviewer may care about
- `tests/unit/test_image_provenance.py::test_publish_mode_requires_actual_cosign_image_sbom_attestation`
- `tests/unit/test_terraform_hygiene.py::test_build_image_workflow_captures_actual_cosign_image_sbom_evidence`
- `tests/unit/test_terraform_hygiene.py::test_deploy_workflow_separates_artifact_verifier_credentials_from_deployer_credentials`
- `tests/unit/test_write_migration_success_receipt.py`
- `tests/unit/test_stage_receipt.py::test_service_rejects_migration_success_receipt_with_unreviewed_extra_fields`
- `tests/unit/test_terraform_hygiene.py::test_service_gate_requires_migration_success_bundle_and_certificate_identity_before_cloud_auth`
- `tests/unit/test_terraform_hygiene.py::test_pre_auth_stage_receipt_verification_requires_certificate_identity_before_any_cosign_call`
- `tests/unit/test_terraform_hygiene.py::test_pre_auth_stage_receipt_verification_requires_receipt_and_bundle_inputs_before_decode`
- `tests/unit/test_terraform_hygiene.py::test_gcp_first_deployment_runbook_documents_reviewed_identity_for_migration_success_verification`
- `tests/unit/test_terraform_hygiene.py::test_gcp_first_deployment_runbook_documents_migration_receipt_as_separate_service_gate_input`

## 7. Honest caveats the reviewer should treat carefully

- The review surface is an **uncommitted local working tree**, not a PR diff.
- `origin/develop..HEAD` contains `0` commits, so committed-range review and committed-range secret scanning are still pending.
- `git diff --stat` / `git diff --name-only` do not list the untracked new files; the reviewer should explicitly inspect these as part of the surface:
  - `deploy/gcp/receipts/templates/migration-success-receipt.example.json`
  - `scripts/verify_migration_database_readback.py`
  - `scripts/write_migration_success_receipt.py`
  - `tests/unit/test_verify_migration_database_readback.py`
  - `tests/unit/test_write_migration_success_receipt.py`
- `CURRENT_WORK.md`, `ROADMAP.md`, and `NOTES.md` are part of workflow state in this repo, not optional prose.
- Local automated verification here does **not** qualify any cloud, backend/state, publication, migration execution, service activation, tester, human-browser, accessibility, language, live-data, or production claim.
- This packet is for independent review of the bounded source-only slice; it does not itself certify PR open / merge / operational readiness.

## 8. Reviewer focus areas

The independent review should explicitly verify:
1. `scripts/verify_image_provenance.py` and `.github/workflows/build-image.yml` now rely on actual-shaped attestation evidence rather than placeholder image SBOM generation
2. `infra/gcp/bootstrap/iam.tf`, `infra/gcp/develop/iam.tf`, `scripts/verify_gcp_foundation.py`, and `scripts/validate_terraform_static.py` preserve the exact writer / reader / deployer authority split without broadening IAM
3. `.github/workflows/deploy-develop.yml` uses the artifact verifier only for direct OCI verification, clears verifier credential material before deployer auth, and does not let the deployer inherit repository-reader authority
4. `scripts/write_migration_success_receipt.py` emits success authority only after successful waited migration execution and preserves the reviewed receipt bindings
5. `scripts/verify_stage_receipt.py` fail-closes on missing or unreviewed migration-success receipt fields and preserves exact source/image/receipt binding semantics
6. the pre-auth stage-receipt verification step fail-closes on missing stage and migration-success input material before decode or signature verification
7. `deploy/gcp/first-deployment-runbook.md` now states truthful boundaries: signed migration-success artifacts are necessary but insufficient alone, signer identity / OIDC issuer matter, and the signed migration receipt remains a separate required service-gate input
8. no adjacent backend/state, Terraform apply, cloud mutation, qualification, or PR B scope entered this branch

## 9. Secret-scan / range-hygiene posture at handoff

- `git diff --check` passes on the live working tree.
- Exact committed-range secret scanning has **not** been rerun for this slice because there are still `0` commits ahead of `origin/develop`.
- Per the handoff workflow, exact-range Gitleaks should run only after the reviewed slice is committed and the verification target becomes a real `origin/develop..HEAD` range.

## 10. Final local review-surface verification at handoff creation

Observed commands:

```bash
git status --short --branch
git rev-parse HEAD
git rev-parse origin/develop
git rev-list --count origin/develop..HEAD
git rev-list --count HEAD..origin/develop
git diff --stat
git diff --name-only
git diff --check
env -u PYTHONPATH uv run pytest -q tests/unit/test_terraform_hygiene.py tests/unit/test_verify_gcp_foundation.py tests/unit/test_image_provenance.py tests/unit/test_write_migration_success_receipt.py tests/unit/test_verify_migration_database_readback.py
env -u PYTHONPATH uv run ruff format --check scripts tests
env -u PYTHONPATH uv run ruff check scripts tests
env -u PYTHONPATH uv run mypy src tests
env -u PYTHONPATH uv run python scripts/validate_terraform_static.py
```

Observed truth:
- branch: `fix/develop-artifact-transition-authority`
- review surface: **local uncommitted working tree**
- ahead commits: `0`
- behind commits: `0`
- base `HEAD == origin/develop == d142bba476753da42e8395a415600c297c65d594`
- changed tracked implementation surface: 18 tracked files in the `git diff` output plus 6 untracked new files listed above
- `git diff --check`: passed
- broader local verification: passed as listed above

## 11. Stop boundary before PR open

This slice is being handed off for **independent review**, not declared merged or operationally ready.

Required next sequence:
1. independent review of the live working-tree diff and this handoff packet
2. remediate any findings on the same local branch without widening scope
3. create the closeout commit for the exact reviewed surface
4. rerun final-head focused and broader verification on the committed head
5. run exact-range secret scanning on `origin/develop..HEAD`
6. only then push and open/update the PR

## 12. Handoff disposition

The independent reviews returned **Changes Requested** (one High and five Medium findings). All six defect families have been remediated, including exact WIF-condition enforcement, and the final independent rereview found no Blocker, High, or Medium finding.

The correct current disposition is:
- **cleared for closeout commit and final-head qualification on the local working tree**
- **not yet cleared for push/PR/merge until final-head qualification and exact-range secret scanning pass**
- **final-head verification and exact-range secret scanning still belong after review and commit**
