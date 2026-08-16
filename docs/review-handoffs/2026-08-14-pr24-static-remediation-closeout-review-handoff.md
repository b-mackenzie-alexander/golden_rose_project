# Review handoff — PR #24 solo-maintainer static remediation closeout

**Date:** 2026-08-14
**Branch:** `security/pr24-solo-maintainer-terraform-remediation`
**Target base:** protected `develop`
**Planning base / merged tip:** `origin/develop` at `090667dc1c0f958c435514a5411053fa42338b3c` (`docs: accept solo-maintainer remediation boundary (#28)`)
**Review surface:** exact uncommitted local working tree
**Ahead commits vs `origin/develop` at handoff creation:** `0`
**Behind commits vs `origin/develop` at handoff creation:** `0`
**PR status:** no PR yet; the prior closeout rereviews returned `NOT READY`, this working tree remediates the latest step-level workflow `continue-on-error` High, and fresh independent rereview is required before any stage/commit/push/PR-open closeout

> Supersession addendum (2026-08-15): this historical working-tree handoff cleared, was committed as `13e55740d35036e937daa579398e7d84e241d140`, and opened as PR #29 against `develop`. PR #29's initial `application` run failed at `uv run ruff format --check .` only; backend-SBOM absence was downstream fail-fast output. The current PR recovery formats the two reported Python files and scopes E501 exclusions to their exact policy/workflow fixtures. The recovery itself requires a new commit, exact-head qualification, and latest-head CI evidence.

> Final supersession addendum (2026-08-15): PR #29's recovery committed at `4643d30c4c3e773fbb3f4bcebd01cfb8b2333970`; all required statuses passed, and PR #29 merged into protected `develop` at `08fe3056e1637d3cab4d1f82ad3081a8a324948e`. This handoff is historical. Proposed ADR-0012 and `.hermes/plans/2026-08-15_210257-consolidated-predeployment-foundation-plan.md` now control the next planning lane.

## 1. Current branch truth

This handoff covers the exact uncommitted validate-without-apply remediation surface only.

Observed live branch state at handoff creation:
- `git status --short --branch` → `## security/pr24-solo-maintainer-terraform-remediation`
- `git rev-parse HEAD` → `090667dc1c0f958c435514a5411053fa42338b3c`
- `git rev-parse origin/develop` → `090667dc1c0f958c435514a5411053fa42338b3c`
- `git rev-list --count origin/develop..HEAD` → `0`
- `git rev-list --count HEAD..origin/develop` → `0`

Interpretation:
- the remediation is not yet a committed PR range
- exact-range `origin/develop...HEAD` review is not yet meaningful
- review must target the live working-tree diff and current local evidence

## 2. Scope of this rereview

This rereview covers the bounded solo-maintainer static remediation authorized by:
- `docs/adr/ADR-0011-pr24-solo-maintainer-remediation-boundary.md`
- `.hermes/plans/2026-08-14_174830-pr24-solo-maintainer-remediation-amendment-plan.md`
- `infra/gcp/README.md`

It is limited to local/static validate-without-apply remediation of the already-merged PR #24 Terraform scaffold.

It must confirm the lane did not widen into:
- Terraform `plan`, `apply`, or backend migration
- cloud authentication, API enablement, or provisioning
- image push, service start, or deployment
- real identity, live/client data, public access, or production claims
- bootstrap/state/WIF implementation
- review/CODEOWNER theater to paper over the accepted same-repository-CI High residual risk

## 3. Static sequence completed in this working tree

The approved exact-node sequence is fully implemented and locally qualified:
1. semantic Terraform/workflow policy hardening
2. deterministic `uv`
3. Direct VPC/private-SQL declaration
4. exact API ordering
5. Cloud SQL backup baseline
6. managed Artifact Registry image authority

There is no remaining approved implementation node in this validate-without-apply sequence. This handoff is for closeout/rereview only.

## 4. Primary files in the uncommitted review surface

### Workflows / policy / tests
- `.github/workflows/application-quality.yml`
- `.github/workflows/infrastructure-quality.yml`
- `scripts/validate_terraform_static.py`
- `tests/unit/test_terraform_hygiene.py`

### Terraform root / module files
- `infra/gcp/variables.tf`
- `infra/gcp/develop.tf`
- `infra/gcp/develop/variables.tf`
- `infra/gcp/develop/artifact_registry.tf`
- `infra/gcp/develop/cloud_run.tf`
- `infra/gcp/develop/cloud_sql.tf`
- `infra/gcp/develop/identities.tf`
- `infra/gcp/develop/locals.tf`
- `infra/gcp/develop/network.tf`
- `infra/gcp/develop/secrets.tf`

### Living docs / evidence
- `CURRENT_WORK.md`
- `ROADMAP.md`
- `NOTES.md`

## 5. Closeout summary of completed remediation evidence

### Semantic policy hardening
- parser and duplicate-key fail-closed behavior now covers workflow YAML, Terraform JSON, and native Terraform HCL
- native HCL labels/values are decoded and normalized before forbidden semantic-construct evaluation, including Unicode-escaped labels such as `google_service_account_\u006bey`
- workflow authority rejects mutable action references, forbidden auth/deploy authority, and exact field mutations for reviewed workflow contracts
- exact reviewed contracts now cover each reviewed job's required ordered step inventory, reject missing/duplicate/reordered reviewed steps, and bind each reviewed step's execution shape (`run` with no `uses`, or `uses` with no `run`) plus `runs-on`, step `if`, action `with`, reviewed step `env`, named-step command, `shell`, `working-directory`, `continue-on-error`, `timeout-minutes`, and `id`
- job-level execution-affecting fields are fail-closed: current jobs do not allow `if`, `continue-on-error`, `needs`, job `permissions`, `environment`, `defaults`, `container`, `strategy`, `concurrency`, or job `uses`, and reviewed job `services`, `env`, `timeout-minutes`, and `name` must match exactly where present
- error output redacts canary/policy-sensitive values

### Deterministic tooling
- both required workflows pin `astral-sh/setup-uv` to the reviewed SHA and require:
  - `version: "0.12.5"`
  - checksum `68a509da24b06b4223a1c0175fb5eb5bc79342b76cbeff0cfe51ac3f5b17b6b2`
  - pre-use `uv --version`

### Direct VPC / private SQL declaration
- root and child modules require `direct_vpc_subnet_cidr` with no committed default
- validation permits representative RFC1918 `/26`-or-broader ranges such as `10.1.0.0/24`, `10.24.0.0/26`, and `172.20.0.0/24`, while rejecting public, too-narrow, and non-network-base candidates
- `network.tf` now declares a dedicated subnetwork and private service access scaffold
- `cloud_run.tf` uses Direct VPC with `PRIVATE_RANGES_ONLY` and no connector/NAT/public route/public SQL path

### Exact API ordering
- exact `depends_on` edges now cover:
  - Artifact Registry
  - Secret Manager
  - IAM service-account creation
  - Compute-backed network resources
  - Service Networking private service access
  - Cloud Run
  - Cloud SQL
- no sleeps, provisioners, `local-exec`, or blanket shortcut dependencies were introduced

### Cloud SQL backup baseline
- `infra/gcp/develop/cloud_sql.tf` now adds only:
  - `backup_configuration { enabled = true }`
- no `start_time`, PITR, retention, or restore-policy claims were added

### Managed Artifact Registry image authority
- `container_image_digest` now accepts only `sha256:<64 lowercase hex>` at root and child module boundaries
- `infra/gcp/develop/locals.tf` derives `local.managed_container_image` from:
  - `${var.region}-docker.pkg.dev`
  - `${var.project_id}`
  - `${google_artifact_registry_repository.application_images.repository_id}`
  - fixed image name `staff-tracer`
  - `@${var.container_image_digest}`
- Cloud Run now uses `image = local.managed_container_image`
- arbitrary host/project/region/repository/image/tag selection is not accepted by the input contract

## 6. Current local verification evidence

Observed latest passing local verification after remediating the independent review's step-level workflow `continue-on-error` High:
- `env -u PYTHONPATH uv lock --check`
  - Result: passed (`Resolved 90 packages in 30ms` on the latest rerun)
- `env -u PYTHONPATH uv run --locked python scripts/validate_terraform_static.py`
  - Result: `Terraform static validation passed`
- `env -u PYTHONPATH uv run pytest tests/unit/test_terraform_hygiene.py -q`
  - Result: `134 passed in 13.18s`
- `terraform fmt -recursive infra/gcp && terraform fmt -check -recursive infra/gcp`
  - Result: passed; the earlier rereview formatting blocker on `infra/gcp/variables.tf` and `infra/gcp/develop/variables.tf` is closed
- `terraform -chdir=infra/gcp validate`
  - Result: `Success! The configuration is valid.`
- `env -u PYTHONPATH uv run --locked python -m py_compile scripts/validate_terraform_static.py tests/unit/test_terraform_hygiene.py`
  - Result: passed with exit `0`
- `git diff --check`
  - Result: passed with exit `0`

These are working-tree results only. They do not replace exact committed-head evidence.

## 7. Deferred truths that must remain explicit

The rereview must confirm docs and any later PR text do not overclaim:
- no Terraform `plan`, `apply`, or backend migration occurred
- no cloud authentication, API enablement, or provisioning occurred
- no deployment, service start, image push, or Cloud SQL use occurred
- no real identity, live/client data, public access, or production work occurred
- the open same-repository-CI High remains accepted residual risk, not a cleared governance finding
- this lane provides local/static quality evidence only; it does not authorize the bootstrap/state/WIF lane or cloud implementation

## 8. Secret-scan posture at this handoff

- Exact committed-range Gitleaks has not been rerun for this closeout surface because there are still `0` commits ahead of `origin/develop`.
- Per the closeout boundary, do not substitute a whole-directory scan of the live working tree for exact-range evidence when ignored/local credential files may exist outside the review surface.
- After rereview clears the exact working tree and a closeout commit exists, rerun committed-range diff hygiene and exact-range Gitleaks against that committed head.

## 9. Reviewer focus areas

1. Confirm the six approved static tasks are all implemented and no seventh implementation node was added.
2. Confirm workflow-policy guards remain exact and fail closed rather than reverting to name-only heuristics, including required step presence/order/multiplicity, named run-step action-substitution rejection, job-level `if` and `continue-on-error` rejection, step-level `continue-on-error` rejection, and no unexpected job/step execution fields.
3. Confirm native HCL parsing is semantic/fail-closed and rejects decoded Unicode-escaped forbidden labels.
4. Confirm parser dependencies are direct locked dev dependencies and infrastructure CI runs the scanner through `uv run --locked` rather than bare system Python.
5. Confirm Direct VPC/private-SQL declaration adds no connector/NAT/public route/public SQL authority and that RFC1918 `/26`-or-broader validation accepts valid private subnets beyond the three private supernet bases.
6. Confirm every API-ordering edge is exact and no shortcut dependency/provisioner/local-exec authority was introduced.
7. Confirm Cloud SQL backup scope stays limited to `backup_configuration.enabled = true`.
8. Confirm managed image authority accepts only digest syntax and derives the final Cloud Run image from the managed repo inputs instead of allowing arbitrary image references.
9. Confirm living docs accurately state that the implementation sequence is complete, the working tree is uncommitted, and review/commit/push/PR remain separate closeout steps.

## 10. Suggested next step after rereview

Request fresh focused independent rereview of this remediated exact local surface. Only after that rereview clears should the next step become a closeout commit followed by exact-head verification, committed-range diff hygiene, exact-range Gitleaks, push, and PR creation under explicit approval.
