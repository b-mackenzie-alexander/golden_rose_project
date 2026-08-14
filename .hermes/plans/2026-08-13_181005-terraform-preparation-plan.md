# Terraform Preparation Planning Plan

> **For Hermes:** This is a planning-only lane from protected `develop` commit `f3cac4de839bf4172754a0bee7f84dd8ab26b622` after PR #22 merged. Do not create Terraform implementation files from this plan until it has been independently reviewed, accepted, and merged, and Beatrice separately authorizes the coding slice.

**Goal:** Prepare a reviewed, non-provisioning Terraform/IaC implementation plan for the private fictional-synthetic-only GCP `develop` foundation.

**Architecture:** Convert ADR-0009 Slice C into exact executable TDD/static-validation tasks while preserving every hard stop from ADR-0009 and the local-only Slice B closeout. The accepted develop location is `us-east4` / Northern Virginia for Cloud Run, Cloud SQL, and Artifact Registry. This plan should produce planning artifacts and aligned living docs only; the future implementation branch may create Terraform scaffolding and policy tests but must still run with `terraform init -backend=false` and no apply.

**Tech Stack:** Terraform, GCP provider, Cloud Run, Cloud Run Jobs, Cloud SQL PostgreSQL 16, Artifact Registry, Secret Manager, Cloud Logging/Monitoring, Budgets, GitHub Actions, Workload Identity Federation, local static/policy validation.

---

## Authority and hard stops

- Controlling decision: `docs/adr/ADR-0009-gcp-develop-deployment-boundary.md`.
- Prior merged runtime/container contract: PR #22 at `f3cac4de839bf4172754a0bee7f84dd8ab26b622`.
- This lane may edit planning and living-document files only.
- This lane must not create Terraform modules, provider files, workflow deploy credentials, cloud resources, service accounts, billing links, secret versions, Artifact Registry images, Cloud SQL instances, Cloud Run services/jobs, or GCP API calls.
- The next implementation slice, if later accepted, must remain validate-without-apply: `terraform fmt`, `terraform init -backend=false`, `terraform validate`, and policy/static tests only.
- No `terraform apply`, GCP authentication, API enablement, project creation, billing linkage, service identity creation, secret configuration, image push, migration, deployment, service start, public access, real identity, live/client-derived data, or production work is authorized.

## Accepted IaC inputs from 2026-08-13 planning walk-through

1. **API enablement:** Terraform manages the approved API allowlist with destructive-disable safeguards such as `disable_on_destroy = false`; candidate APIs are added only when the reviewed plan proves the need.
2. **Provisioning identity:** a temporary documented bootstrap authority may establish the project/API/WIF foundation; routine IaC uses a dedicated Terraform provisioner service account impersonated through GitHub OIDC/WIF, never service-account JSON keys.
3. **Runtime versus migration identity:** Cloud Run runtime and migration job use distinct Terraform-managed service accounts and distinct PostgreSQL roles. Runtime is non-owner application access only; migration assumes schema-owner authority only through reviewed serialized migration execution.
4. **Artifact Registry:** one private regional Docker repository in `us-east4`, Terraform-managed, with digest-only Cloud Run deployment, repo-scoped writer/pull IAM, no public access, and cleanup policy that preserves current/rollback digests while limiting stale images.
5. **Budgets:** Terraform manages Cloud Billing Budget alerts after billing scope and recipients are approved. Accepted actual-spend thresholds are $50, $75, and $100; alerts are warnings, not hard caps.
6. **Secret Manager:** Terraform manages secret metadata, labels, replication policy, and per-secret IAM only. Secret versions/payloads, PostgreSQL passwords, app keys, and tokens are injected out of band and kept out of Terraform source, state, logs, artifacts, containers, chat, and ordinary docs.
7. **Cloud SQL:** develop baseline is private Cloud SQL PostgreSQL 16 in `us-east4`, zonal `db-f1-micro`, 10 GiB SSD, no public IPv4, and minimal automated backups for develop recovery evidence. `db-g1-small` is evidence-triggered scale-up only.
8. **Networking:** use a minimal dedicated Terraform-managed develop VPC with private service access for Cloud SQL private IP; Cloud Run connects through the approved private/serverless path. Default VPC, public DB IPs, broad firewall rules, NAT, LB/CDN, and VPN stay out of scope unless separately approved.
9. **Cloud Run invocation:** while application auth is synthetic, Cloud Run stays private: no `allUsers` or `allAuthenticatedUsers`; service-level `roles/run.invoker` only for approved tester/facilitator principals managed by Terraform.
10. **GitHub/WIF workflow authority:** PR workflows validate only. Terraform apply, image push, migration execution, and deployment require protected GitHub environment approval and narrowly scoped WIF impersonation.
11. **Logging/Monitoring:** use value-safe default/short-retention Cloud Logging/Monitoring with restricted access/sinks and minimal health/readiness alerts. Synthetic monitors, extended retention, broad log viewers, and unapproved exports are out of scope.
12. **Labels/tags:** Terraform applies standard non-sensitive labels/tags across supported resources for environment, data boundary, managed-by, cost center, owner/contact, service, and teardown inventory.
13. **Teardown/rebuild:** Terraform supports intentional teardown/rebuild through labels, outputs, and a runbook. No automatic scheduled destroy; require data-boundary, backup/export, current artifact/migration, and approval checks before teardown.
14. **Terraform state:** validate-without-apply starts with local state only and no shared backend. Remote state must be selected and approved before any shared apply; state, plan files, real `.tfvars`, billing IDs, emails, project IDs, cloud metadata, and secret values must not be committed.

## Planning deliverables

1. A reviewed implementation plan for ADR-0009 Slice C: Terraform and policy scaffold, validate without apply.
2. Living-doc updates that mark PR #22 as merged/historical and name the Terraform preparation lane.
3. A review checklist that forces future Terraform implementation to prove non-provisioning behavior locally before any PR.
4. A stop-boundary section that keeps pre-provisioning evidence, provisioning, and first deployment as later explicit approval gates.

## Exact planning tasks

### Task 1: Rebaseline from PR #22 merge

**Objective:** Ground Terraform preparation in the actual protected `develop` tip rather than the retired Slice B branch.

**Files:**
- Modify: `CURRENT_WORK.md`
- Modify: `NOTES.md`

**Steps:**
1. Fetch/prune `origin`.
2. Verify PR #22 is merged to `develop` and record its merge SHA.
3. Fast-forward local `develop` to `origin/develop`.
4. Create a fresh `docs/` planning branch from the merged tip.
5. Record that the old `feat/gcp-develop-runtime-container` branch is historical and tree-equivalent to the merge result.

**Expected evidence:** `origin/develop` resolves to `f3cac4d`; PR #22 is `MERGED`; local `develop` equals `origin/develop`; the fresh planning branch has no product-code delta at creation.

### Task 2: Close out Slice B in living docs

**Objective:** Stop authoritative docs from describing Slice B as pending review or pre-merge work.

**Files:**
- Modify: `CURRENT_WORK.md`
- Modify: `ROADMAP.md`
- Modify: `README.md`
- Modify: `ARCHITECTURE.md`
- Modify: `TECHNICAL_REQUIREMENTS.md`
- Modify: `SECURITY.md`
- Modify: `AGENTS.md`
- Modify: `NOTES.md`

**Required content:**
- PR #22 merged to protected `develop` at `f3cac4d`.
- Required checks passed: `application`, `check`, `enforce`, and CodeRabbit.
- Slice B is local runtime/container packageability only: explicit `develop` posture, value-safe marker, `/health`, bounded `/readiness`, same-origin static serving, entrypoint/runtime behavior, non-root local image contract, and local image inspection/probe evidence.
- Task 11 image evidence remains local-only; `/readiness` returning 503 during the image-only probe is expected because no database was wired.
- No cloud resource, Terraform apply, image push, Cloud SQL use, deployment, public access, real identity, live/client data, or production work occurred.

### Task 3: Define the Terraform implementation plan scope

**Objective:** Turn ADR-0009 Slice C into a future coding plan that is exact enough for TDD/static validation but still non-provisioning.

**Future implementation files to name in the plan:**
- `infra/gcp/README.md`
- `infra/gcp/versions.tf`
- `infra/gcp/providers.tf`
- `infra/gcp/variables.tf`
- `infra/gcp/outputs.tf`
- `infra/gcp/develop/*.tf`
- `infra/gcp/tests/` policy fixtures/scripts
- `.github/workflows/infrastructure-quality.yml` only if a reviewed stable CI gate is part of the slice
- `.gitignore` only for local Terraform artifacts if needed

**Future management resources to consider in the plan:**
- API enablement resources for the accepted allowlist, with candidate APIs only after reviewed need.
- Budget resources and $50/$75/$100 alert thresholds after billing-account/project binding details and recipients are approved.
- Least-privilege identity/IAM resources for bootstrap handoff, Terraform provisioner WIF, runtime, migration, image publishing, service-level invocation, and separately approved human break-glass/admin access.
- Guardrails that reject `allUsers`, `allAuthenticatedUsers`, service-account keys, project-wide secret access, broad owner/editor grants, mutable image-only deploys, public DB IPs, default VPC use, missing labels, secret-version resources, extended log retention, risky log sinks, and committed Terraform state/plan/secret variable files.
- Artifact Registry cleanup policies to cap image-retention cost and reduce stale-artifact risk while preserving current and rollback/forward-recovery digests.
- Log bucket retention, sink/access controls, and minimal health/readiness alert policies for value-safe platform evidence.
- Standard label/tag locals and teardown/rebuild runbook support for non-production inventory.

**Future validation commands to require:**
- `terraform fmt -check -recursive infra/gcp`
- `terraform -chdir=infra/gcp init -backend=false`
- `terraform -chdir=infra/gcp validate`
- A pinned/reviewed IaC lint/security command, if introduced by the implementation plan
- Policy/static tests that fail on public invoker, broad IAM, service-account keys, unpinned image tags, public database exposure, secret-like defaults, missing budget posture, and missing state-ownership documentation
- `git diff --check`
- Exact-range secret scan after commit

### Task 4: Keep pre-provisioning evidence separate

**Objective:** Prevent Terraform scaffold work from becoming implicit approval for GCP resources.

**The future plan must leave these as later gates or accepted inputs:**
- accepted region choice is now `us-east4` for develop Cloud Run, Cloud SQL, and Artifact Registry;
- non-production cost estimate and budget/alert thresholds are accepted as initial planning inputs, but pricing must be rechecked before provisioning and budget alert recipients/routing remain open;
- project/billing/organization/folder/domain ownership plan;
- named cloud admins, break-glass owners, support and alert recipients;
- exact GitHub repository/ref/environment claims for WIF and protected GitHub environment approvals;
- Terraform remote-state backend location, access, backup, and handoff owner before any shared apply;
- approved alert recipients/routing and named human break-glass/admin principals;
- exact service-account and database-role matrix implementation details;
- Cloud SQL backup/PITR, teardown/rebuild, RTO/RPO and recovery test expectations beyond the accepted minimal develop baseline;
- Cloud Run platform request-log minimization and sink/access contract;
- private tester/facilitator principal list while synthetic auth remains.

### Task 5: Plan review and acceptance gate

**Objective:** Require independent review before Terraform implementation begins.

**Review focus:**
1. Does the plan preserve all ADR-0009 hard stops?
2. Does it avoid project IDs, billing accounts, domains, user emails, secret values, or environment-specific identifiers in tracked source?
3. Does it keep state ownership unresolved as a blocker to apply, not as a TODO hidden in implementation?
4. Do policy tests cover both declaration-level and future effective-IAM checks?
5. Does it avoid turning local runtime/container evidence into cloud qualification evidence?

**Exit gate:** Beatrice explicitly accepts the exact Terraform implementation plan after independent review, then the planning packet is merged to protected `develop`. Only after that may a fresh implementation branch start from the merged tip.

## Final verification for this planning lane

- `git diff --check`
- Markdown/living-doc consistency review for stale PR #22 or Slice B language
- Exact-range secret scan after commit and before any PR
- Protected PR checks after push/PR

## Stop condition

Stop after the Terraform preparation planning packet and living-doc closeout are complete and verified. Do not start Terraform implementation in this lane.
