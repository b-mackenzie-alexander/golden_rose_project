# Review handoff — post-PR33 deployment-path remediation implementation

**Date:** 2026-08-20
**Branch:** `fix/post-pr33-deployment-path-remediation`
**Target base:** protected `develop`
**Exact approved base:** `develop@fd7b89dd848a1eb12e2eb6ba082d2dcb3d3b8ea0` (`docs: close post-pr35 planning packet route (#36)`)
**Review surface:** exact uncommitted local working tree above the approved base
**Ahead commits vs base at handoff creation:** `0`
**Cloud status:** no cloud action authorized or performed
**PR status:** no PR yet; this handoff describes the local remediation surface before closeout commit / push / PR

## 1. Objective

Review the bounded no-cloud remediation implementation governed by accepted ADR-0013 and `.hermes/plans/2026-08-20_002931-post-pr33-deployment-path-remediation-plan.md`. This handoff covers the local branch after Tasks 1–12 and the Task 13 pre-closeout qualification/remediation work, before any commit, push, PR creation, or cloud gate progression.

## 2. Status truth

- PR #33 merged into protected `develop` at `3c0118abb8b84472141992d2238033b1312d5af2`; its branch is retired.
- A post-merge audit found F1–F17 deployment-path defects, including four Blockers.
- PR #34 and PR #35 merged the ADR-0013 planning/amendment packet; those planning handoffs are now historical context only.
- The active implementation lane is this local branch from exact merge tip `fd7b89dd848a1eb12e2eb6ba082d2dcb3d3b8ea0`.
- Tasks 1–12 now have local no-cloud source/test evidence on this branch.
- Task 13 pre-closeout qualification is now green on the uncommitted working tree, but the closeout commit and exact-head rerun have not happened yet.
- Same-repository CI remains High/open accepted residual risk.
- No GCP auth, Terraform plan/apply, provisioning, publication, secret handling, service start, deployment, or live qualification occurred in this remediation lane.

## 3. Governing scope

This review surface is controlled by:
- `docs/adr/ADR-0013-post-pr33-deployment-path-remediation.md`
- `.hermes/plans/2026-08-20_002931-post-pr33-deployment-path-remediation-plan.md`
- `CURRENT_WORK.md`
- `ROADMAP.md`
- `SECURITY.md`
- `TECHNICAL_REQUIREMENTS.md`
- `TECHNOLOGY_DECISIONS.md`
- `ARCHITECTURE.md`
- `README.md`
- `GIT_WORKFLOW.md`
- `infra/gcp/README.md`

## 4. Implemented task summary on this branch

### Task 1–3
- staged `foundation → migration → service` authority model
- stage-gated Cloud Run service/job and IAM
- split runtime vs migration secret/reference wiring
- exact env allowlist/static enforcement

### Task 4–5
- exact `workflow_ref` WIF separation
- `workflow_dispatch` trust only
- no provisioner GitHub WIF path
- narrow deploy executor authority
- approved Budget API inventory/dependency
- bounded Cloud SQL recovery inputs

### Task 6–8
- stage-aware foundation verifier
- budget notification-channel identity vs display-name distinction
- IAM-private named tester access boundary
- failure-safe deploy evidence and stage-plan receipt checks
- no-drift deploy workflow behavior

### Task 9–11
- reviewed static cardinality evaluation
- exact CI parity including bootstrap-root validation
- digest-bound provenance/SBOM verification contracts
- authenticated readiness uptime monitoring contract
- enforceable UUID-bearing request-log exclusion posture
- monitoring service-agent invoker boundary

## 5. Changed-path manifest

Observed current local working-tree paths in this review surface:

```text
.github/workflows/build-image.yml
.github/workflows/deploy-develop.yml
.github/workflows/infrastructure-quality.yml
CURRENT_WORK.md
NOTES.md
deploy/gcp/bootstrap-state-runbook.md
deploy/gcp/evidence-template.md
deploy/gcp/first-deployment-runbook.md
deploy/gcp/private-tester-access.md
deploy/gcp/rollback-forward-recovery-runbook.md
deploy/gcp/staged-plan-approval.md
deploy/gcp/teardown-rebuild-runbook.md
docs/review-handoffs/2026-08-16-consolidated-predeployment-closeout-review-handoff.md
docs/review-handoffs/2026-08-20-post-pr33-deployment-path-remediation-planning-review-handoff.md
docs/review-handoffs/2026-08-20-post-pr33-deployment-path-remediation-review-handoff.md
docs/security/dependency-purpose-license-review.md
infra/gcp/README.md
infra/gcp/bootstrap/iam.tf
infra/gcp/bootstrap/outputs.tf
infra/gcp/bootstrap/wif.tf
infra/gcp/develop.tf
infra/gcp/develop/apis.tf
infra/gcp/develop/budgets.tf
infra/gcp/develop/cloud_run.tf
infra/gcp/develop/iam.tf
infra/gcp/develop/migration_job.tf
infra/gcp/develop/observability.tf
infra/gcp/develop/outputs.tf
infra/gcp/develop/secrets.tf
infra/gcp/develop/variables.tf
infra/gcp/variables.tf
infra/policy/predeployment-authority-manifest.json
scripts/qualify_develop_deployment.py
scripts/validate_terraform_static.py
scripts/verify_gcp_foundation.py
scripts/verify_image_provenance.py
tests/unit/test_image_provenance.py
tests/unit/test_qualify_develop_deployment.py
tests/unit/test_terraform_hygiene.py
tests/unit/test_verify_gcp_foundation.py
```

## 6. Finding ledger / disposition status

| Finding family | Status in local surface | Notes |
| --- | --- | --- |
| F1–F3 staged authority / workload gating | remediated in source | covered by Task 1–3 tests + static validator |
| F4–F6 runtime/migration config / secret authority | remediated in source | exact env/secret/IAM separation implemented |
| F7 WIF / deploy authority drift | remediated in source | exact `workflow_ref` separation + least privilege |
| F8–F10 deploy workflow mutation/evidence drift | remediated in source | deploy is non-mutating and failure-safe |
| F11–F13 cardinality / CI parity / provenance drift | remediated in source | static cardinality + CI parity + digest-bound provenance implemented |
| F14–F17 tester / monitoring / availability / docs drift | remediated in source | IAM-private tester boundary, authenticated readiness evidence, and living-doc reconciliation implemented locally |
| Same-repository CI High | accepted residual risk | still open; never describe as independent authorization |

## 7. Local evidence actually observed

Focused provenance/workflow evidence:
- `env -u PYTHONPATH uv run pytest tests/unit/test_image_provenance.py tests/unit/test_terraform_hygiene.py -q -k 'image_provenance or build_image_workflow or deploy_develop_workflow or terraform_static_validation_harness_runs_without_cloud_access' --tb=line`
  - observed: `23 passed`

Focused observability/verifier evidence:
- `env -u PYTHONPATH uv run pytest tests/unit/test_verify_gcp_foundation.py tests/unit/test_terraform_hygiene.py -q --tb=line`
  - observed: `267 passed`

Full current four-suite evidence:
- `env -u PYTHONPATH uv run pytest tests/unit/test_image_provenance.py tests/unit/test_terraform_hygiene.py tests/unit/test_verify_gcp_foundation.py tests/unit/test_qualify_develop_deployment.py -q --tb=line`
  - observed: `307 passed in 64.40s`

Static / formatting / diff evidence:
- `env -u PYTHONPATH uv run --locked python scripts/validate_terraform_static.py`
  - observed: `Terraform static validation passed`
- `terraform fmt -check -recursive infra/gcp`
  - observed: clean after formatting `infra/gcp/develop/observability.tf` and `infra/gcp/develop/outputs.tf`
- `git diff --check`
  - observed: clean

Terraform provider-schema and graph/evaluated-inventory evidence:
- `terraform -chdir=infra/gcp init -backend=false -input=false -lockfile=readonly && terraform -chdir=infra/gcp validate`
  - observed: provider-schema valid
- `terraform -chdir=infra/gcp/bootstrap init -backend=false -input=false -lockfile=readonly && terraform -chdir=infra/gcp/bootstrap validate`
  - observed: provider-schema valid
- `env -u PYTHONPATH uv run pytest tests/unit/test_terraform_hygiene.py tests/unit/test_verify_gcp_foundation.py tests/unit/test_image_provenance.py tests/unit/test_qualify_develop_deployment.py -q -k 'foundation_graph_contains_no_cloud_run_job_or_service or migration_graph_contains_job_without_service_or_invoker_binding or service_graph_contains_job_service_and_named_invoker_binding or publish_evidence_binds_source_commit_builder_and_subject_digest or deploy_rejects_wrong_attestation_subject_predicate_identity_issuer_or_transparency_proof or foundation_verifier_requires_authenticated_readiness_uptime_check or service_stage_has_exactly_one_uptime_check_and_monitoring_invoker or qualification_contract_requires_reviewed_authenticated_proxy_or_token_path or main_reads_token_from_environment_and_writes_bounded_evidence' --tb=line`
  - observed: `9 passed`

Application-quality local CI parity evidence:
- local Docker-backed PostgreSQL service `golden-rose-task13-postgres` started, reached healthy state, and was removed after qualification
- exact workflow-order application-quality sequence ran under `env -u NODE_ENV` with pinned local Node/npm path `/Users/genie/.local/bin`
- observed results from the full sequence:
  - frontend lock validation tests: `24 pass`
  - frontend verify: `116 passed`
  - repo-wide mypy: `Success: no issues found in 77 source files`
  - backend/application pytest with coverage: `634 passed`, total coverage `95.92%`
  - expected fail-closed Alembic downgrade refusal observed and re-upgrade succeeded
  - backend/frontend SBOM validation passed
  - `pip-audit --skip-editable`: `No known vulnerabilities found`

Image/provenance and secret-hygiene evidence:
- `docker buildx build --load --platform linux/amd64 --metadata-file build/image-metadata.json --tag golden-rose:workflow-pr .`
  - observed: local `linux/amd64` Buildx image built successfully
- `env -u PYTHONPATH uv run python scripts/verify_image_provenance.py --mode pr --dockerfile Dockerfile --metadata-path build/image-metadata.json --backend-sbom-path build/backend-sbom.cdx.json --frontend-sbom-path build/frontend-sbom.cdx.json`
  - observed: PR-mode provenance verification passed
- `/opt/homebrew/bin/gitleaks dir . --redact --no-banner`
  - observed: `no leaks found`

## 8. Deferred gate facts

Still deferred beyond this local review surface:
- Gate 2 read-only cloud qualification
- bootstrap/backend ceremony
- every saved Terraform plan/apply
- image publication
- secret/database preparation
- migration execution
- service activation
- named tester access window
- bounded live qualification

## 9. Primary review focus now

1. Confirm the staged Terraform authority and static cardinality controls remain fail-closed.
2. Confirm runtime/migration secret authority and deploy executor/WIF separation remain exact.
3. Confirm deploy workflow evidence is non-mutating, failure-safe, and distinct from qualification.
4. Confirm provenance/SBOM trust boundaries are exact-digest and do not overclaim local PR-mode evidence.
5. Confirm observability and authenticated readiness monitoring remain honest, stage-gated, and non-public.
6. Confirm the living docs and historical handoffs now tell the truth about PR #33, PR #34/35, the active remediation branch, and the still-blocked cloud gates.

## 10. Explicit non-scope preserved

This handoff does **not** claim that any of the following occurred:
- GCP authentication or inspection
- Terraform plan/apply
- provisioning
- image push or publication
- secret/database action
- service start or deployment
- tester access
- live qualification
- real identity or live/client data
- production readiness or production activation

## 11. Required next sequence

1. independent rereview of this exact local working tree
2. remediate any substantiated remaining finding
3. create the closeout commit
4. rerun exact-head no-cloud qualification evidence on the committed head
5. run exact-range diff/secret hygiene on the committed range
6. push and open/update the remediation PR
7. merge only after Beatrice's explicit approval
