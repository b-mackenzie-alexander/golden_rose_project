# Review handoff — consolidated pre-deployment closeout

**Date:** 2026-08-16
**Branch:** `feat/consolidated-predeployment-foundation`
**Target base:** protected `develop`
**Planning base / merged tip:** `origin/develop` at `f9b7903a92fed894f4b48f4521e2734d359858c2` (`docs: consolidate solo-maintainer pre-deployment planning (#30)`)
**Review surface:** exact uncommitted local working tree
**Ahead commits vs `origin/develop` at handoff creation:** `0`
**Behind commits vs `origin/develop` at handoff creation:** `0`
**PR status:** no PR yet; this working tree is locally qualified through Task 15 and prepared for fresh independent review before any stage/commit/push/PR-open closeout

> Supersession addendum (2026-08-17): the exact working tree received post-handoff remediation for the review's critical/high and remaining medium/doc findings. Additional local evidence on this same branch now includes `env -u PYTHONPATH uv run pytest tests/unit/test_verify_gcp_foundation.py -q` (`10 passed in 1.13s`), a clean-copy Terraform graph probe from disposable root `/tmp/golden-rose-graph.aR3wh3` after replacing the partial backend file with a graph-only stub, and explicit teardown of the leftover local containers `golden-rose-task15tj7qop-postgres-test-1` and `golden-rose-test-postgres`. ADR-0012 acceptance wording and read-only evidence-output handling were reconciled after this original handoff was written, so reviewers should assess the current live working tree rather than treating this 2026-08-16 note as the final state.

## 1. Current branch truth

Observed live branch state at handoff creation:
- `git status --short --branch` → `## feat/consolidated-predeployment-foundation`
- `git rev-parse HEAD` → `f9b7903a92fed894f4b48f4521e2734d359858c2`
- `git rev-parse origin/develop` → `f9b7903a92fed894f4b48f4521e2734d359858c2`
- `git rev-list --count origin/develop..HEAD` → `0`
- `git rev-list --count HEAD..origin/develop` → `0`

Interpretation:
- this is not yet a committed PR range
- exact-range `origin/develop...HEAD` review is not yet meaningful
- exact-range Gitleaks over `origin/develop..HEAD` would scan zero commits until a closeout commit exists
- review must target the live working-tree diff and the observed local evidence below

## 2. Governing scope

This rereview covers the consolidated pre-deployment implementation authorized by:
- `docs/adr/ADR-0012-solo-maintainer-consolidated-predeployment-boundary.md`
- `.hermes/plans/2026-08-15_210257-consolidated-predeployment-foundation-plan.md`
- `infra/gcp/README.md`

It includes the source-controlled local/no-cloud lane through Task 15:
1. authority manifest and static validation inventory
2. bootstrap/state control-plane source contracts
3. exact GitHub OIDC/WIF trust contracts
4. least-privilege workload IAM contracts
5. serialized Cloud Run migration-job plus advisory-lock runtime
6. PostgreSQL authority lifecycle and drift verification
7. Cloud SQL metadata and recovery-input contracts
8. budgets and value-safe observability contracts
9. immutable build/SBOM/provenance workflow contracts
10. migrate/deploy workflow gate contracts
11. read-only foundation/effective-authority verification tooling
12. bounded private-synthetic deployment qualification tooling
13. out-of-band secret-injection and private-tester procedure docs
14. rollback/forward-recovery and teardown/rebuild runbooks
15. clean-room local pre-deployment qualification

## 3. Explicit non-scope preserved

This working tree must still be reviewed as no-cloud, no-apply, no-secret-injection source control only. It must not imply that any of the following occurred:
- Terraform `plan`, `apply`, or backend migration
- cloud authentication, GCP API calls, API enablement, or provisioning
- image push, Cloud Run deployment, Cloud SQL use outside approved local Docker-backed tests, or public access
- secret injection, real identity, live/client data, or production work
- independent human authorization beyond the accepted solo-maintainer posture

The same-repository-CI issue remains High/open accepted residual risk; agent/separate-session review and CI are quality evidence, not independent authorization.

## 4. Primary review surface

### Workflows and verifier scripts
- `.github/workflows/build-image.yml`
- `.github/workflows/deploy-develop.yml`
- `scripts/validate_terraform_static.py`
- `scripts/verify_database_authority.py`
- `scripts/verify_gcp_foundation.py`
- `scripts/verify_image_provenance.py`
- `scripts/qualify_develop_deployment.py`

### Terraform / policy / migration contracts
- `infra/gcp/backend.tf`
- `infra/gcp/bootstrap/`
- `infra/gcp/develop.tf`
- `infra/gcp/develop/cloud_run.tf`
- `infra/gcp/develop/cloud_sql.tf`
- `infra/gcp/develop/iam.tf`
- `infra/gcp/develop/migration_job.tf`
- `infra/gcp/develop/budgets.tf`
- `infra/gcp/develop/observability.tf`
- `infra/gcp/develop/outputs.tf`
- `infra/gcp/develop/variables.tf`
- `infra/gcp/outputs.tf`
- `infra/gcp/variables.tf`
- `infra/policy/predeployment-authority-manifest.json`
- `migrations/versions/0005_database_authority.py`

### Runtime / application support
- `Dockerfile`
- `pyproject.toml`
- `src/golden_rose/migration_runtime.py`
- `src/golden_rose/api/health.py`

### Tests and review-facing evidence
- `tests/unit/test_terraform_hygiene.py`
- `tests/unit/test_container_contract.py`
- `tests/unit/test_image_provenance.py`
- `tests/unit/test_migration_runtime.py`
- `tests/unit/test_qualify_develop_deployment.py`
- `tests/unit/test_verify_database_authority.py`
- `tests/unit/test_verify_gcp_foundation.py`
- `tests/unit/api/test_health.py`
- `tests/integration/test_database_authority.py`
- `tests/integration/test_initial_migration.py`
- `tests/integration/application/test_create_employer_contact.py`
- `deploy/gcp/first-deployment-runbook.md`
- `deploy/gcp/private-tester-access.md`
- `deploy/gcp/rollback-forward-recovery-runbook.md`
- `deploy/gcp/teardown-rebuild-runbook.md`
- `deploy/gcp/bootstrap-state-runbook.md`
- `deploy/gcp/evidence-template.md`
- `CURRENT_WORK.md`
- `ROADMAP.md`
- `NOTES.md`
- `README.md`

## 5. Review focus from the latest closeout work

1. Confirm the Task 15 clean-room local qualification is now truly complete and remains no-cloud:
   - disposable repo copy only
   - synthetic-only env file
   - Docker-backed local `postgres-test`
   - no secret payloads in tracked source or ordinary evidence
2. Confirm the Terraform contract enforcement remains exact but no longer depends on brittle literal spacing after `terraform fmt`:
   - `tests/unit/test_terraform_hygiene.py`
   - `scripts/validate_terraform_static.py`
3. Confirm the image-provenance verifier now truthfully accepts the current local BuildKit metadata shape without weakening reviewed digest/base-image/SBOM requirements.
4. Confirm the qualification harness does not overclaim CI parity by requiring non-CI Terraform backend/provider graph commands.
5. Confirm git/Gitleaks evidence is anchored to the real source repo, not the `.git`-less temp copy.
6. Confirm the migration/authority test adjustments remain bounded to the 0005 fail-closed contract and do not reopen downgrade or authority scope.
7. Confirm living docs now state the truthful next step: independent review of an uncommitted working tree, then closeout commit/final-head verification, then push/PR.

## 6. Local verification actually observed

### Focused closeout evidence
- `env -u PYTHONPATH uv run pytest tests/unit/test_terraform_hygiene.py -q`
  - Result: `172 passed in 32.66s`
- `env -u PYTHONPATH uv run --locked python scripts/validate_terraform_static.py`
  - Result: `Terraform static validation passed`
- `env -u PYTHONPATH uv run pytest tests/unit/test_image_provenance.py -q`
  - Result: `7 passed in 0.65s`
- `env -u PYTHONPATH uv run ruff check scripts/verify_image_provenance.py tests/unit/test_image_provenance.py`
  - Result: `All checks passed!`

### Full Task 15 clean-room qualification evidence
Observed from `/tmp/task15_qualification.sh` against disposable repo copy `/tmp/golden-rose-task15.TJ7qop`:
- uv lock/sync
- frontend npm ci / verify / ls / audit / SBOM
- Ruff format/check
- mypy
- Bandit
- Alembic upgrade
- full pytest coverage
- fail-closed downgrade proof
- Alembic re-upgrade
- database-authority tests
- database-authority verifier
- pip-audit
- backend SBOM
- Terraform fmt
- Terraform root init/validate
- Terraform bootstrap init/validate
- Terraform static validation
- Terraform hygiene tests
- image-build provenance
- `git diff --check`
- `gitleaks git --no-banner --redact --log-opts 'origin/develop..HEAD'`
- `gitleaks dir --no-banner --redact .`

Final harness result:
- `Task 15 clean-room qualification PASS`

Task 15 logs were written under:
- `/tmp/golden-rose-task15.TJ7qop/build/task15-logs/`

### Post-doc-update hygiene
- `git diff --check`
  - Result: passed

## 7. Range-hygiene caveat

Because `origin/develop..HEAD` currently contains `0` commits, the branch is ready for review handoff but not yet for final-head PR evidence. After independent review clears this working tree and a closeout commit exists, rerun:
- `git diff --check origin/develop...HEAD`
- `git rev-list --count origin/develop..HEAD`
- exact-range `gitleaks git --no-banner --redact --log-opts 'origin/develop..HEAD'`
- the relevant final-head quality/security gates for the committed head

## 8. Remediation addendum — 2026-08-17

Independent re-review found additional High/Medium issues. The local working tree has been remediated without staging/commit/push:
- deploy source gate moved before Google authentication/gcloud setup;
- deploy publish-run input now validates run metadata, repository, develop ref, workflow path, successful conclusion, single successful `publish-image` job, and records bounded run identity/head SHA in deploy evidence;
- database-authority verification now requires both authenticated runtime and migration probe URLs for a full pass;
- qualification now requires an exact reviewed service URL and rejects other syntactically valid Cloud Run hosts;
- qualification/foundation evidence writers reject symlink components before resolution and clean temporary files on failed atomic writes;
- foundation verification now derives the cross-project Artifact Registry publisher from `control_plane_project_id`, verifies state-bucket IAM, and supports bootstrap-active/bootstrap-retired semantics;
- Terraform source now models bucket-level state authority/recovery/bootstrap operator IAM and derives the develop registry writer from the control-plane project;
- `TECHNOLOGY_DECISIONS.md` now distinguishes completed source contracts from still-gated cloud operations.

Observed remediation verification:
- `env -u PYTHONPATH uv run ruff check scripts/qualify_develop_deployment.py scripts/verify_gcp_foundation.py scripts/verify_database_authority.py scripts/verify_image_provenance.py src/golden_rose/migration_runtime.py migrations/env.py tests/unit/test_qualify_develop_deployment.py tests/unit/test_verify_gcp_foundation.py tests/unit/test_verify_database_authority.py` → `All checks passed!`
- `env -u PYTHONPATH uv run ruff format --check scripts/qualify_develop_deployment.py scripts/verify_gcp_foundation.py scripts/verify_database_authority.py scripts/verify_image_provenance.py src/golden_rose/migration_runtime.py migrations/env.py tests/unit/test_qualify_develop_deployment.py tests/unit/test_verify_gcp_foundation.py tests/unit/test_verify_database_authority.py` → `9 files already formatted`
- `env -u PYTHONPATH uv run --locked python scripts/validate_terraform_static.py` → `Terraform static validation passed`
- `env -u PYTHONPATH uv run pytest tests/unit/test_qualify_develop_deployment.py tests/unit/test_verify_database_authority.py tests/unit/test_verify_gcp_foundation.py tests/unit/test_terraform_hygiene.py tests/unit/test_image_provenance.py -q` → `216 passed in 34.89s`

This addendum updates the local working-tree review packet only. The remediation itself still requires independent re-review before staging or commit.

## 9. Parallel re-review remediation addendum — 2026-08-17

The subsequent parallel re-review found additional High/Medium issues. The local working tree has been remediated again without staging/commit/push:
- deploy now requires the reviewed publish run `head_sha` to equal the deployment invocation `${{ github.sha }}` before artifact download and persists both values in deploy evidence;
- foundation IAM parsing aggregates duplicate same-role bindings, rejects conditional IAM bindings, rejects extra privileged Artifact Registry repository roles, and checks user-managed keys on both workload and control-plane service accounts;
- database-authority verification compares stable database identities for authority, runtime-login, and migration-login connections before combining evidence;
- `terraform fmt` corrected `infra/gcp/develop.tf`, and the exact `terraform fmt -check -recursive infra/gcp` gate now passes;
- the policy manifest deploy-step order now matches the reviewed workflow/static contract, and the static validator compares manifest order against `REQUIRED_WORKFLOW_STEP_ORDER`;
- static workflow checks now require the publish-SHA equality guard plus the image-reference equality, managed-repository case guard, and digest extraction;
- static Terraform checks now require exact state-bucket IAM role/principal/bootstrap-retirement fragments and reject broad state-bucket IAM drift;
- qualification/foundation evidence writers revalidate parent/destination ancestry before temp creation and again immediately before replace;
- six predecessor migration regressions are enabled again with clean predecessor-schema setup, and `0005_database_authority` forces pending constraints immediate before ownership changes so populated predecessor upgrades can proceed into the authority migration.

Observed remediation verification:
- `env -u PYTHONPATH uv run --locked python scripts/validate_terraform_static.py` → `Terraform static validation passed`
- `env -u PYTHONPATH uv run ruff check ...` → `All checks passed!`
- `env -u PYTHONPATH uv run ruff format --check ...` → `12 files already formatted`
- `env -u PYTHONPATH uv run pytest tests/unit/test_terraform_hygiene.py tests/unit/test_qualify_develop_deployment.py tests/unit/test_verify_database_authority.py tests/unit/test_verify_gcp_foundation.py tests/unit/test_image_provenance.py -q` → `229 passed in 35.98s`
- `env -u PYTHONPATH GOLDEN_ROSE_DATABASE_URL='[REDACTED]' uv run pytest tests/integration/test_initial_migration.py -q` → `30 passed in 2.12s`
- `terraform fmt -check -recursive infra/gcp` → passed
- `git diff --check origin/develop` → passed

This addendum updates the local working-tree review packet only. The remediation still requires independent re-review before staging or commit.

## 10. Final remediation and independent rereview — 2026-08-18

The final two findings from the fresh rereview were remediated on the same local working tree:
- both evidence writers now capture the opened parent directory device/inode identity and immediately re-stat the requested parent without following symlinks before descriptor-relative replacement;
- rename-preserving parent-substitution regressions replace the requested parent with a symlink after opening it and prove that the writers fail without writing evidence through the substituted path or into the displaced directory;
- Ruff formatted `scripts/validate_terraform_static.py` and `tests/unit/test_terraform_hygiene.py`.

Fresh observed local evidence after those changes:
- `env -u PYTHONPATH uv run pytest tests/unit/test_verify_gcp_foundation.py tests/unit/test_qualify_develop_deployment.py tests/unit/test_terraform_hygiene.py -q` → `215 passed in 31.75s`
- `env -u PYTHONPATH uv run ruff format --check scripts/validate_terraform_static.py tests/unit/test_terraform_hygiene.py scripts/verify_gcp_foundation.py scripts/qualify_develop_deployment.py tests/unit/test_verify_gcp_foundation.py tests/unit/test_qualify_develop_deployment.py` → `6 files already formatted`
- corresponding `ruff check` → `All checks passed!`
- `terraform fmt -check -recursive infra/gcp` → passed
- `env -u PYTHONPATH uv run --locked python scripts/validate_terraform_static.py` → `Terraform static validation passed`
- `git diff --check origin/develop` → passed

Fresh independent rereview found no remaining Blocker, High, or Medium issue in the final remediation surface. The current branch remains an uncommitted local working tree restored on `origin/develop@659f1368aa1b0e82d52af1bc7531e3f0a7b5bcb6`; the original approved planning base remains `f9b7903`. No cloud authentication, Terraform plan/apply, provisioning, deployment, secret action, staging, commit, push, or PR creation occurred during this remediation/review sequence.

## 11. Required closeout sequence

The independent rereview is complete. The next steps are:
1. stage the reviewed scope
2. create the closeout commit
3. rerun final-head verification on the committed range
4. push the branch
5. open/update the PR with evidence tied to that committed head

## 12. Application-quality remediation addendum — 2026-08-19

PR #33 was opened against `develop` at `a59c23b` and its Application quality job failed before its post-pytest migration checks:
- the develop-only environment-marker and runtime tests omitted the now-required fictional immutable image digest, so `Settings` rejected their intended develop configuration;
- after those fixtures were corrected, local CI-parity reproduction reached the stale `alembic downgrade base` command. Migration `0005_database_authority` intentionally refuses downgrade without an operator-reviewed role handoff, so requiring its success contradicted the reviewed migration boundary.

The current working-tree remediation:
- supplies a synthetic `sha256:` digest in both affected develop test fixtures;
- makes Application quality prove the expected downgrade refusal, require its exact safe message, and then re-upgrade;
- updates the static workflow contract and adds a regression that requires that fail-closed proof.

Observed local verification on this remediation: CI-pinned `uv==0.12.5` lock/sync; frontend verification (`116 passed`), audit, and SBOM validation; repository Ruff format/check, mypy, Bandit; full pytest coverage (`552 passed`, `95.92%`); expected downgrade refusal/re-upgrade; pip-audit; backend SBOM validation; static policy regression; and `git diff --check` all passed. No cloud action occurred.

This addendum describes an uncommitted working tree. It requires a fresh independent rereview of the exact current files, then a closeout commit, final-head exact-range quality/security verification, and push to update existing PR #33. It does not authorize merge, cloud access, Terraform plan/apply, deployment, secret injection, or live data.

### Addendum rereview closure

The initial independent rereview found one Medium coverage gap: the source test established the downgrade-proof text in the live workflow but did not prove that a mutated proof fails static validation. The remediation adds a fixture-driven regression that changes the required refusal-message `grep` to `true`, invokes the static validator against that isolated fixture, and requires its named Application-quality run-mutation failure. The focused proof passed (`2 passed`), the complete Terraform-hygiene suite passed (`182 passed`), and the follow-up independent rereview accepted the exact uncommitted surface with no Blocker, High, or Medium finding. Final-head verification remains required after the closeout commit.

### Final-head local evidence

The closeout commit passed the full local Application quality sequence with CI-pinned tools: `553 passed` at `95.92%` coverage, the expected authority-downgrade refusal/re-upgrade proof, repository Ruff format/check, mypy, Bandit, static workflow validation, Terraform formatting, frontend verify (`116 passed`), frontend/backend SBOM validation, and dependency audits. Exact-range and working-tree Gitleaks scans found no leaks, and `git diff --check origin/develop...HEAD` passed. The remaining action is to push this exact head to update PR #33 and assess the remote required checks. Local Docker test-service teardown awaits container-lifecycle confirmation and is not a source-control gate.
