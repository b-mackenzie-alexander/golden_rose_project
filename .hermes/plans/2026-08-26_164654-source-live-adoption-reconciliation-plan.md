# Source/Live Terraform Adoption-Reconciliation Implementation Plan

> **For Hermes:** Use `subagent-driven-development` only after this packet is independently reviewed, accepted, and merged. This packet is planning-only and grants no import, Terraform plan/apply, backend migration, or cloud mutation authority.

**Goal:** Establish the reviewable boundary by which Terraform becomes the future sole desired-state authority for the already-created partial non-executable foundation, without treating current live resources as Terraform-managed or mutating them during planning.

**Architecture:** The durable control-plane bootstrap root and disposable workload root remain separate. A private operator-held reconciliation inventory will map each already-created resource to exactly one of: later Terraform adoption, later operator-approved retirement, or explicitly deferred/non-managed evidence. The later adoption ceremony must establish/reconcile remote state before any Terraform import or plan; it will use exact operator-held input, state, and inventory evidence and preserve `foundation` as workload-free.

**Tech Stack:** Terraform 1.15.8; Google provider 6.50.0; repository Terraform roots under `infra/gcp/` and `infra/gcp/bootstrap/`; `scripts/verify_gcp_foundation.py`; `scripts/validate_terraform_static.py`; pytest; private Obsidian deployment records.

**Status:** Accepted by Beatrice on 2026-08-26 as the planning-only boundary for the current source/live adoption work. Acceptance does not authorize imports, backend/state actions, Terraform plan/apply, GCP mutation, or the separately required source amendment.

---

## Authority and current facts

### Observed, private operator-held evidence

- Initial Gate 2 read-only qualification is complete and Gate 2 is closed at `develop@4e0b6a5`.
- Separately approved manual operator phases established a **partial non-executable foundation**: durable state controls, control-plane identities/WIF, required workload APIs/identities, Artifact Registry, metadata-only secrets, and budget/observability controls.
- No private VPC, Direct VPC subnet, private-service-access reservation/connection, Cloud SQL instance/application database, secret payload, image, Cloud Run job/service, tester grant, migration, or qualification exists.
- The currently recorded state-bucket recovery posture is provisional. Final RTO/RPO, restore-test cadence, and handoff acceptance are deferred to their later recovery/qualification gate.
- Terraform is the accepted future sole desired-state authority. The private operator-held deployment-record area is the custody location for later saved plans, inventories, hashes, approval records, and redacted evidence.

### Source facts to reconcile

- The workload root has only a partial GCS backend declaration in `infra/gcp/backend.tf`; backend values must remain operator-held.
- The bootstrap root declares the state bucket and state-bucket IAM in `infra/gcp/bootstrap/state.tf` and `infra/gcp/bootstrap/iam.tf`.
- The roots model control-plane WIF/identity, workload APIs/identities, registry, metadata-only secrets, budgets, monitoring, and logging; the private inventory must establish whether each live object corresponds exactly to the reviewed resource address and attributes.
- `infra/gcp/develop/network.tf` and `infra/gcp/develop/cloud_sql.tf` are intentionally future resources, but the current always-loaded module declares them unconditionally. Before any adoption or `foundation` saved-plan gate, a separately accepted source amendment must stage-gate or otherwise remove those resources from the evaluated foundation root. Until that amendment merges, no foundation plan may be generated, signed, reviewed, or approved.
- `deployment_stage=foundation` must create no Cloud Run job/service and require no image digest. The stage contract is enforced by `infra/gcp/develop/variables.tf`, graph/static tests, ADR-0013, and `deploy/gcp/staged-plan-approval.md`.

## Non-negotiable stop boundaries

This plan does **not** authorize:

- `terraform import`, `terraform state *`, remote/backend initialization or migration, `terraform plan`, or `terraform apply`;
- GCP authentication, API/resource/IAM mutation, deletion, or drift repair;
- copying resource identifiers, state values, plans, raw output, principal values, endpoints, or credential material into Git, chat, or ordinary evidence;
- enabling private network, Cloud SQL, database, image, Cloud Run job/service, secret version, tester access, migration, or qualification;
- treating an imported resource, an existing manual resource, or a saved plan as Gate 4 approval.

A source/live mismatch is a stop-and-record finding. It never permits an ad hoc import, broad IAM grant, source rewrite, or resource recreation.

---

## Task 1: Publish this planning-only adoption boundary

**Objective:** Merge a documentation-only packet that makes Terraform’s future authority, the private reconciliation inventory, and the hard stop boundaries explicit.

**Files:**
- Create: `.hermes/plans/2026-08-26_164654-source-live-adoption-reconciliation-plan.md`
- Modify: `CURRENT_WORK.md`
- Modify: `ROADMAP.md`
- Modify: `NOTES.md`
- Modify: `infra/gcp/README.md` to state that an unconditional foundation-root network/Cloud SQL evaluation blocks any future foundation plan pending a separate accepted source amendment
- Modify: `deploy/gcp/bootstrap-state-runbook.md` to state that the later adoption ceremony must prove distinct bootstrap/workload backend identity, lineage, key/prefix, and lock scope before any import
- Modify: `deploy/gcp/staged-plan-approval.md` to make a source amendment that removes/stage-gates network/Cloud SQL/database actions from foundation a precondition for a foundation saved plan
- Modify: `TECHNOLOGY_DECISIONS.md` to record the source/live adoption boundary as planning-only and the unconditional foundation-root resource defect as a stop condition
- Create: `docs/review-handoffs/<date>-source-live-adoption-plan-review-handoff.md`

**Steps:**
1. Update `CURRENT_WORK.md` so the active objective is the planning-only source/live adoption boundary and the next operational action is not an implicit import.
2. Update `ROADMAP.md` so the adoption-plan item remains unchecked until protected planning publication; list the unconditional network/Cloud SQL/database evaluation as an explicit stop before every future foundation plan.
3. Append a concise value-safe `NOTES.md` record that the partial foundation is not yet Terraform state-managed and that no adoption action occurred.
4. State that Terraform is the future sole desired-state authority while preserving every later gate: private network/Cloud SQL, final recovery, monitoring delivery, image, migration, service, tester authority, and qualification.
5. Update only value-safe milestone status in tracked documentation; leave identifiers and raw inventory evidence in the private deployment record.
6. Run the named static checks in Task 5, `git diff --check`, and after the planning commit exists run `/opt/homebrew/bin/gitleaks git --no-banner --redact --log-opts 'origin/develop..HEAD'`.
7. Obtain focused independent review, then publish through a protected documentation-only PR.

**Acceptance:** The merged repository documents one future Terraform authority without claiming current state ownership or authorizing cloud action.

---

## Task 2: Define the source-only private inventory schema and candidate universe

**Objective:** Define the private inventory schema and source-derived candidate address universe without collecting new live data in this planning lane.

**Files:**
- Create later under separately approved read-only/adoption scope: `<operator-held deployment record>/source-live-adoption-inventory.<date>.md`
- Create later under separately approved read-only/adoption scope: minimized command/output references and hashed inventory snapshot
- Inspect: `infra/gcp/bootstrap/{state.tf,iam.tf,wif.tf,variables.tf,providers.tf}`
- Inspect: `infra/gcp/{backend.tf,providers.tf,variables.tf,develop.tf}`
- Inspect: `infra/gcp/develop/{apis.tf,identities.tf,artifact_registry.tf,secrets.tf,iam.tf,budgets.tf,observability.tf,network.tf,cloud_sql.tf}`

**Steps:**
1. Define the required private inventory fields: Terraform root; Terraform address and any instance key; source-resource type; observed-identity reference; classification; predecessor addresses; import-identity-format reference; evidence digest; sensitive-field handling; root/state ownership; disposition owner; and approval reference.
2. Derive from current source the candidate address universe for the reviewed foundation scope. For each address, define one future classification:
   - **candidate for later adoption**;
   - **must remain absent/deferred**;
   - **candidate for separately approved retirement**; or
   - **unmatched/manual divergence requiring design decision**.
3. Define the future approved-read-only inventory collection criterion: classify exactly once every **live resource within the approved reviewed Terraform-foundation scope**, not unrelated project/account resources. Capture only minimized private evidence references; do not copy raw output into the inventory.
4. Require the future collection to compare state-bucket protection/retention/IAM, WIF issuer/audience/subject-or-attribute conditions and effective bindings, service-account keys/IAM, approved API presence, registry IAM/cleanup, metadata-only secret/version posture, budget/alert/logging controls, and resource labels.
5. Mark the intentionally absent network/Cloud SQL and all workload resources as **deferred**, not missing adoption candidates. The inventory cannot reclassify them without a separately accepted source amendment and later authority gate.
6. Define the future private dependency order: bootstrap and workload roots must never share a state object/file, backend key/prefix, lock scope, lineage, or import operation.

**Acceptance:** The source-only candidate universe and private inventory schema are concrete enough for later approved read-only collection. This planning packet does not claim that any live resource has been newly inventoried or classified.

---

## Task 3: Design the later adoption ceremony without executing it

**Objective:** Specify one bounded, reversible-before-mutation ceremony that will establish authoritative Terraform state only after a separate approval.

**Files:**
- Create later after Task 2 review: `.hermes/plans/<timestamp>-terraform-adoption-ceremony-execution-plan.md`
- Inspect: `deploy/gcp/bootstrap-state-runbook.md`
- Inspect: `deploy/gcp/staged-plan-approval.md`
- Inspect: `scripts/verify_gcp_foundation.py`
- Inspect: `tests/unit/test_terraform_hygiene.py`

**Steps for the future execution plan:**
1. Require an approval bundle containing: exact source SHA, provider-lock digest, private inventory digest, non-secret input digest, backend/state custody reference, approved resource-address set, and explicit exclusions.
2. Require a no-mutation preflight that checks the private inventory is current and source attributes still match the reviewed source SHA.
3. Identify and verify bootstrap-only local-state provenance, or record its absence as a blocker; do not assume a manually created bucket is a trusted Terraform backend.
4. Verify the approved remote backend identity/custody is distinct from the workload state, then migrate/read back the bootstrap state privately and prove its inventory, lineage, backend key/prefix, and lock scope contain bootstrap addresses only. Stop on a missing provenance record, backend mismatch, unexpected pre-existing address, or mixed-root address.
5. Permit bootstrap-root adoption only after Step 4 passes. Permit workload-root backend initialization/import only after bootstrap-root state identity and ownership are proven distinct.
6. Before any later adoption action, decide and test the reviewed import representation against the pinned Terraform/provider versions. Prefer declarative `import` blocks when they preserve reviewability and policy compatibility; otherwise document why a narrowly scoped CLI import is required. Do not select a state representation from generic Terraform advice alone.
7. For each approved candidate, require an exact one-resource import/adoption step followed by private normalized-state-versus-source comparison. Preserve a private pre-action state recovery reference and stop on the first mismatch.
8. Require a post-adoption plan generated only after all approved resources for that root are reconciled. A non-empty plan is a stop-and-review result, not an auto-repair instruction.
9. Permit bootstrap-authority retirement only after private evidence proves: approved successor state and recovery principals have least-privilege effective access; successor-path state read/write and restore recovery were exercised; every bootstrap IAM binding, credential/key, impersonation path, and break-glass path is inventoried/dispositioned; rollback/lockout recovery is approved; the temporary bootstrap binding is removed; and no provisioner GitHub WIF binding exists. Stop on any access gap, extra binding, key, or unapproved WIF path.
10. End the ceremony before the later exact `foundation` saved-plan gate. Do not coalesce adoption and foundation-plan creation in one approval.

**Acceptance:** A future executor can perform no state/import action without an exact resource set, private evidence, and a separate approval, and has deterministic stop conditions for drift.

---

## Task 4: Define the future exact foundation-plan and Gate 4 packets

**Objective:** Make the later Gate 3 and Gate 4 review materials mechanically complete, while not producing a plan in this planning phase.

**Files:**
- Inspect: `deploy/gcp/staged-plan-approval.md`
- Inspect: `scripts/verify_gcp_foundation.py`
- Inspect: `infra/gcp/develop/{variables.tf,network.tf,cloud_sql.tf,cloud_run.tf,migration_job.tf,iam.tf,observability.tf}`
- Test later: `tests/unit/test_terraform_hygiene.py`
- Test later: `tests/unit/test_verify_gcp_foundation.py`

**Future Gate 3 plan packet must require:**
- a separately accepted source amendment that stage-gates/removes network, private-service-access, Cloud SQL, and application-database actions from the evaluated `foundation` root; absent that amendment, stop before generating, signing, reviewing, or approving a foundation plan;
- one `deployment_stage=foundation` saved plan generated only after the source amendment and adoption/reconciliation are approved and complete;
- no image digest, Cloud Run job, Cloud Run service, workload invoker IAM, or service-stage uptime check in its JSON inventory;
- operator-held plan binary, JSON inventory, source/lock/input/plan digests, and plan-artifact custody reference;
- explicit inventory review of APIs, state controls, IAM/WIF, registry, metadata-only secrets, budgets/alerts/logging, labels, recovery/deletion controls, and destruction/replacement actions;
- explicit deferral of private network/Cloud SQL until their own inputs and authority are accepted, unless a later amendment deliberately and separately changes that boundary.

**Future Gate 4 packet must require:**
- the immutable saved-plan hash and matching source/lock/input/inventory digests;
- reviewed monthly-cost assumptions, alert-recipient ownership, replacement/destroy actions, effective IAM, teardown implications, and all unresolved Blocker/High dispositions;
- an approval record that grants only the exact foundation apply followed by foundation-mode verification;
- invalidation on any source, lock, input, plan, inventory, or approval-reference change.

**Acceptance:** Future Gate 3/Gate 4 requirements are specified without generating or approving a real plan.

---

## Task 5: Review and publication closeout

**Objective:** Publish the planning packet only after it documents bounded state ownership, deterministic stop conditions, private evidence custody, and no implicit execution authority.

**Files:**
- Modify: this plan and its review handoff only if review identifies a planning contradiction
- Verify: `infra/gcp/`, `infra/gcp/bootstrap/`, `scripts/validate_terraform_static.py`, `tests/unit/test_terraform_hygiene.py`, `tests/unit/test_verify_gcp_foundation.py`

**Validation:**

```text
# No remote/backend initialization or migration, plan, apply, import, state command, or GCP command in this planning lane. `init -backend=false` below is source-local static validation only.
terraform fmt -check -recursive infra/gcp
terraform -chdir=infra/gcp init -backend=false -input=false -lockfile=readonly
terraform -chdir=infra/gcp validate
terraform -chdir=infra/gcp/bootstrap init -backend=false -input=false -lockfile=readonly
terraform -chdir=infra/gcp/bootstrap validate
env -u PYTHONPATH uv run python scripts/validate_terraform_static.py
env -u PYTHONPATH uv run pytest tests/unit/test_terraform_hygiene.py tests/unit/test_verify_gcp_foundation.py -q
git diff --check
```

Before publication, the review must answer:

1. Does the packet keep Terraform’s future sole desired-state authority distinct from current live ownership?
2. Does it require a complete private resource inventory and one-root-at-a-time state boundary before any import?
3. Does it make source/live differences stop conditions rather than repair authority?
4. Does it preserve no-workload foundation and all private-network/Cloud SQL, secret, tester, migration, service, and qualification gates?
5. Does it exclude all identifiers, state, plans, raw outputs, credentials, and secret values from tracked content?
6. Does it preserve the High/open same-repository-CI residual risk and avoid claiming independent authorization?
7. Does it fail closed while network/Cloud SQL/database actions remain unconditionally evaluated by the foundation root?

---

## Risks and open questions

1. **Existing state bucket differs from reviewed source.** The private inventory must detect and disposition control differences (including recovery/retention and IAM) before a later adoption request; do not edit source or live state merely to align them.
2. **Manual resource ownership.** A live resource can be correctly configured yet unsafe to adopt if its import identity, dependency order, or root ownership is uncertain. Classify it as blocked rather than guessing.
3. **Provider/import semantics.** Import IDs, declarative import-block support, and normalized provider representations are version-sensitive. Verify against the pinned Terraform/provider documentation and the repository static policy during the later approved ceremony; do not copy state/import IDs into this plan.
4. **Network/Cloud SQL gap.** These resources remain deliberately absent. Their later authority requires fresh CIDR/private-service-access collision evidence, recovery inputs, and a separate decision; adoption must not broaden into their creation.
5. **Bootstrap authority.** Retirement is not a cleanup convenience. It requires private effective-IAM/credential/break-glass inventory, successor-path state and restore verification, approved lockout rollback, removed temporary bindings, and proof that no provisioner GitHub WIF path exists.
6. **Private custody.** The operator-held record must use approved encryption/access controls, restrict custody to named authorized operators, define retention/disposal, and provide only digest-bound redacted/value-safe review derivatives. It must never publish state, plan JSON, raw inventory, or raw command output.
7. **CI concurrency flake.** PR #44’s first application run failed in unrelated concurrent revision tests but an exact local 25-iteration stress run and GitHub rerun passed. Treat it as a separately tracked CI reliability issue; do not conflate it with this planning packet.

## Final stop boundary

This planning packet stops after protected planning publication. It does not authorize imports, state actions, backend migration, Terraform plans/applies, GCP mutation, private networking, Cloud SQL, database actions, image publication, workload creation, tester access, migration, service activation, qualification, live/client data, or production.
