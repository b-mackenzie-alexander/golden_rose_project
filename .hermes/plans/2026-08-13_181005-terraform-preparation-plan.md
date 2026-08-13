# Terraform Preparation Planning Plan

> **For Hermes:** This is a planning-only lane from protected `develop` commit `f3cac4de839bf4172754a0bee7f84dd8ab26b622` after PR #22 merged. Do not create Terraform implementation files from this plan until it has been independently reviewed, accepted, and merged, and Beatrice separately authorizes the coding slice.

**Goal:** Prepare a reviewed, non-provisioning Terraform/IaC implementation plan for the private fictional-synthetic-only GCP `develop` foundation.

**Architecture:** Convert ADR-0009 Slice C into exact executable TDD/static-validation tasks while preserving every hard stop from ADR-0009 and the local-only Slice B closeout. This plan should produce planning artifacts and aligned living docs only; the future implementation branch may create Terraform scaffolding and policy tests but must still run with `terraform init -backend=false` and no apply.

**Tech Stack:** Terraform, GCP provider, Cloud Run, Cloud Run Jobs, Cloud SQL PostgreSQL 16, Artifact Registry, Secret Manager, Cloud Logging/Monitoring, Budgets, GitHub Actions, Workload Identity Federation, local static/policy validation.

---

## Authority and hard stops

- Controlling decision: `docs/adr/ADR-0009-gcp-develop-deployment-boundary.md`.
- Prior merged runtime/container contract: PR #22 at `f3cac4de839bf4172754a0bee7f84dd8ab26b622`.
- This lane may edit planning and living-document files only.
- This lane must not create Terraform modules, provider files, workflow deploy credentials, cloud resources, service accounts, billing links, secret versions, Artifact Registry images, Cloud SQL instances, Cloud Run services/jobs, or GCP API calls.
- The next implementation slice, if later accepted, must remain validate-without-apply: `terraform fmt`, `terraform init -backend=false`, `terraform validate`, and policy/static tests only.
- No `terraform apply`, GCP authentication, API enablement, project creation, billing linkage, service identity creation, secret configuration, image push, migration, deployment, service start, public access, real identity, live/client-derived data, or production work is authorized.

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

**The future plan must leave these as later gates:**
- cited and accepted region choice;
- non-production cost estimate and budget/alert thresholds;
- project/billing/organization/folder/domain ownership plan;
- named cloud admins, break-glass owners, support and alert recipients;
- WIF/project identifiers and protected GitHub environment approvals;
- Terraform state backend location, access, backup, and handoff owner;
- service-account and database-role matrix;
- Cloud SQL sizing, backup/PITR, teardown/rebuild, RTO/RPO and recovery test expectations;
- Cloud Run platform request-log minimization and sink/access contract;
- private tester/facilitator access procedure while synthetic auth remains.

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
