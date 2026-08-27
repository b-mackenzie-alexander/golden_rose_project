# Gate 3 Source/Live Terraform Adoption Ceremony Implementation Plan

> **For Hermes:** Use `subagent-driven-development` only after this packet is independently reviewed, accepted, and merged. This packet plans the later bounded operator ceremony; it does not itself authorize GCP authentication, inventory collection, backend/state actions, imports, Terraform planning/apply, or cloud mutation.

**Goal:** Establish a reviewable, one-root-at-a-time procedure to reconcile the already-created partial non-executable foundation into Terraform's future sole desired-state authority, so that a later exact `foundation` saved plan can be truthfully generated and reviewed.

**Architecture:** The durable bootstrap root (`infra/gcp/bootstrap`) and disposable workload root (`infra/gcp`) remain separate state domains. An approved read-only private inventory first classifies the reviewed live candidate universe and proves bootstrap-state provenance; only then may a separate explicit ceremony adopt each root into its own approved remote state and stop on any source/live mismatch. The later exact `foundation` plan is a distinct gate after adoption is complete, not an output of this ceremony.

**Tech Stack:** Terraform `>= 1.9.0, < 2.0.0` (record the exact installed version privately at execution); pinned Google provider from `infra/gcp/.terraform.lock.hcl`; GCS backend supplied only from operator-held configuration; approved `gcloud` read-only commands; `scripts/verify_gcp_foundation.py`; `scripts/validate_terraform_static.py`; pytest; encrypted private operator-held deployment record; value-safe repository documentation.

**Status:** Proposed planning packet. It authorizes only independent review and protected planning publication after Beatrice's explicit acceptance; no implementation, cloud, state, or Terraform execution authority exists until later separately approved gates.

---

## 1. Status, decision, and boundaries

### Current truth

- PR #45 merged the source/live adoption-reconciliation planning boundary at `develop@3c897e4`.
- PR #46 merged the prerequisite source amendment at `develop@58aed28`: `deployment_stage=foundation` now omits network, private-service-access, Cloud SQL, and application-database resources and their deferred inputs.
- Private operator-held evidence records a partial, non-executable foundation. The tracked repository does not and must not reproduce resource identifiers, principal values, backend configuration, state, plan output, endpoints, raw cloud output, credentials, or secret payloads.
- `ROADMAP.md`'s next unchecked line is the future exact `foundation` plan. It is **not** the next executable action: `CURRENT_WORK.md:5-6` and the merged PR #45 plan require separate approval for the private source/live inventory and adoption ceremony first.
- **Current source/verifier stop condition:** `scripts/verify_gcp_foundation.py` still makes `--mode foundation` reject an absent Cloud SQL instance, while PR #46's accepted stage contract makes Cloud SQL absent from the evaluated `foundation` root. This packet does not choose or implement a resolution. Before any exact `foundation` plan is generated, a separately accepted source-only verifier-reconciliation packet must align the verifier, its tests, `ROADMAP.md`'s foundation-mode verification claim, and the accepted stage contract without weakening later private-SQL verification.

### Authority sequence

1. Independently review this proposed execution-plan packet; Beatrice explicitly accepts it, then a narrow acceptance-delta audit confirms that only status/governance language changed before protected planning publication.
2. Obtain an explicit, bounded operator approval for **read-only** private source/live inventory collection.
3. Perform, classify, and independently review the private inventory. Stop on any mismatch or uncertainty.
4. Obtain a new explicit approval bundle for the **bootstrap-root** adoption ceremony only.
5. Complete and read back bootstrap-root state privately; prove it has bootstrap addresses only and is independent from the workload root.
6. Obtain a new explicit approval bundle for the **workload-root** adoption ceremony only.
7. Complete and read back workload-root state privately; stop before generating a `foundation` plan.
8. Prepare a separate Gate 3 exact-foundation-plan packet. Its approval must be separate from every adoption approval.

### Non-negotiable stop boundaries

This plan must never authorize by implication:

- any plan/apply, `terraform state *`, import, backend initialization/migration, state pull/push, or GCP command during the planning/review lane;
- GCP resource/IAM/API mutation, resource creation, deletion, drift repair, or bootstrap-authority retirement;
- enabling private network, private-service access, Cloud SQL, application database, secret payloads, images, Cloud Run job/service, tester access, migration, service activation, qualification, client/live data, or production;
- moving to the next root when the previous root's inventory, provenance, readback, lineage, backend key/prefix, lock scope, or state address set is missing, ambiguous, mixed, or mismatched;
- treating a state import/adoption, a non-empty plan, or an existing manual resource as approval for apply.

A source/live difference, unexpected address, effective-IAM gap, extra credential/key, missing provenance record, import representation uncertainty, or a resource outside the reviewed candidate universe is a **stop-and-record finding**, not repair authority.

---

## 2. Private evidence design

### Private operator-held files (do not create under Git)

The approved execution run must establish these files in the encrypted operator-held deployment-record area, with access limited to the approved operator(s):

- `source-live-adoption-inventory.<UTC-date>.md` — minimized per-resource inventory and classification.
- `source-live-adoption-inventory.<UTC-date>.json` — machine-readable inventory containing only private references/digests, never raw responses in the repository.
- `raw/<UTC-run-id>/` — captured command transcripts and raw provider output, restricted to the approved operator-held custody area.
- `adoption-preflight.<UTC-run-id>.md` — source/lock/input/inventory/backend approval binding and explicit go/no-go outcome.
- `bootstrap-state-readback.<UTC-run-id>.md` and `workload-state-readback.<UTC-run-id>.md` — state provenance, lineage, serial, root/address classification, and recovery-reference findings.
- `adoption-exceptions.<UTC-run-id>.md` — any unknown, blocked, or mismatch record; each item must contain a disposition owner and an explicit non-action statement.

Every value-safe tracked summary may refer only to a private record type, run date, artifact digest, status, and decision. It must never expose an identifier, principal, endpoint, command output, state address inventory, or secret-adjacent value.

### Required private inventory schema

For each resource in the reviewed foundation candidate universe, record:

| Field | Required rule |
| --- | --- |
| Terraform root | `bootstrap` or `workload`, exactly one |
| Terraform address / instance key | Current source address; do not place in tracked docs |
| Source resource type | Terraform provider type |
| Observed identity reference | Private reference to raw evidence, not copied output |
| Classification | `candidate_for_adoption`, `deferred_absent`, `retirement_candidate`, or `unmatched_manual_divergence` |
| Import representation reference | Pinned-version documentation/probe reference; no guessed import ID |
| Evidence digest | Hash of the private evidence snapshot used for the classification |
| Root/state ownership | Exact root and intended state custody, never mixed |
| Backend binding | Private canonical backend-config digest plus an opaque fingerprint of the resolved backend identity, state object/key/prefix, and lock scope; both must match the approval record before any state action |
| Sensitive-field handling | What raw response handling/redaction applies |
| Disposition and approval reference | Explicit owner and gate reference |

The inventory must classify every **in-scope live resource** exactly once. Network/private-service access/Cloud SQL/application database and all executable workload classes must be recorded as `deferred_absent`, not as missing adoption candidates.

---

## 3. Task plan

### Task 1: Publish and independently review this Gate 3 execution packet

**Objective:** Create a reviewable, no-execution packet that makes inventory/adoption prerequisites and stop conditions mechanically explicit.

**Files:**
- Create: `.hermes/plans/2026-08-26_210433-gate3-source-live-adoption-ceremony-plan.md`
- Create: `docs/review-handoffs/<UTC-date>-gate3-source-live-adoption-ceremony-plan-review-handoff.md`
- Modify: `CURRENT_WORK.md`
- Modify: `ROADMAP.md`
- Modify: `NOTES.md`
- Modify: `TECHNOLOGY_DECISIONS.md`
- Modify: `infra/gcp/README.md`
- Modify: `deploy/gcp/staged-plan-approval.md`
- Inspect: `.hermes/plans/2026-08-26_164654-source-live-adoption-reconciliation-plan.md`
- Inspect: `docs/adr/ADR-0013-post-pr33-deployment-path-remediation.md`
- Inspect: `deploy/gcp/bootstrap-state-runbook.md`
- Inspect: `deploy/gcp/staged-plan-approval.md`

**Steps:**
1. Keep the plan planning-only: do not add backend values, live inventory, identifiers, resource addresses, principals, or raw provider output.
2. Update only value-safe living-doc status after independent review confirms the packet does not conflate the future foundation plan with prerequisite inventory/adoption work.
3. Create a review handoff identifying this as a documentation-only, uncommitted/committed surface as applicable; state that no cloud action occurred.
4. Require focused independent review of: root separation, inventory completeness criteria, import/state stop conditions, stage authority, private evidence custody, and the distinction between adoption and the later saved plan.
5. Obtain Beatrice's explicit acceptance after the technical review clears. Preserve the proposed-artifact hash and review verdict, then perform a narrow semantic acceptance-delta audit; it may change only status/governance/current-lane language and must not add technical execution authority.
6. Publish only through the protected `develop` flow after the acceptance delta and ordinary planning-review gates succeed.

**Acceptance:** The merged packet describes a deterministic and bounded later ceremony without granting it through implied authority.

---

### Task 2: Obtain and record the read-only inventory approval bundle

**Objective:** Obtain an approval that permits only private, read-only collection against the specified control-plane and workload project scopes.

**Files:**
- Create privately after approval: `adoption-preflight.<UTC-run-id>.md`
- Create privately after approval: `source-live-adoption-inventory.<UTC-date>.{md,json}`
- Inspect: `infra/gcp/bootstrap/{state.tf,iam.tf,wif.tf,providers.tf,variables.tf,versions.tf}`
- Inspect: `infra/gcp/{backend.tf,develop.tf,providers.tf,variables.tf,versions.tf}`
- Inspect: `infra/gcp/develop/{apis.tf,identities.tf,artifact_registry.tf,secrets.tf,iam.tf,budgets.tf,observability.tf,network.tf,cloud_sql.tf}`

**Approval bundle must name privately:**

1. operator identity and the exact approved control-plane and workload project scopes;
2. source commit SHA and provider-lock digest;
3. allowed read-only command families and prohibited mutation commands;
4. the reviewed address candidate universe and explicit deferred-absent classes;
5. private evidence-custody reference, authorized-reader constraints, disposal timeframe, and run identifier;
6. explicit no-import/no-backend/no-state/no-plan/no-apply/no-mutation boundary;
7. stop conditions and the owner who receives a mismatch report.

**Read-only collection requirements:**

1. Record the active identity and project scope privately, then stop if either conflicts with approval.
2. Collect only the facts necessary to classify the reviewed source candidate universe: project/API posture; bootstrap/workload service identities and effective IAM; WIF provider/pool/conditions; user-managed key absence; registry and metadata-only-secret posture; budget, notification, alert, logging, and label posture; and state-bucket recovery/IAM posture.
3. Compare each observation to the reviewed Terraform source and classify it exactly once using the schema in section 2.
4. Treat Google-managed/default services outside the approved API set as observed evidence, not automatic drift; fail only on a missing required API or reviewed-contract conflict.
5. Confirm executable workload resources are absent; confirm network/private-service-access/Cloud SQL/application-database resources are absent and remain deferred.
6. Never write raw command output into Git, chat, or tracked notes. Do not remediate, import, or change configuration while collecting.
7. Independently review the private inventory before any adoption approval is requested.

**Acceptance:** A private, complete, independently reviewed inventory exists; every in-scope resource is classified once; no cloud/state mutation occurred.

---

### Task 3: Prove bootstrap-root provenance and decide import representation

**Objective:** Determine whether the existing durable state control plane can be safely and truthfully adopted by the bootstrap root without guessing state/import semantics.

**Files:**
- Inspect: `infra/gcp/bootstrap/{state.tf,iam.tf,wif.tf,outputs.tf,providers.tf,variables.tf,versions.tf}`
- Inspect: `infra/gcp/.terraform.lock.hcl`
- Create privately after read-only approval: `bootstrap-state-provenance.<UTC-run-id>.md`
- Create privately after a version-compatible isolated probe approval, if needed: `import-representation-probe.<UTC-run-id>.md`

**Steps:**
1. Compare the bootstrap candidate inventory with current bootstrap source. Stop on a source/live mismatch; do not update source or live controls in the same gate.
2. Prove whether a prior bootstrap local-state artifact exists, is authentic, and maps only to the bootstrap candidate universe. Record absence as a blocker rather than creating a substitute provenance narrative.
3. Determine the exact intended remote backend identity privately and prove it will be distinct from the workload root in bucket/object or prefix, locking scope, lineage, ownership, and recovery path.
4. Check pinned Terraform and Google-provider documentation for the exact current import semantics. Prefer declarative `import` blocks only if the representation preserves reviewability, policy compatibility, and a safe one-resource-at-a-time ceremony. Otherwise, document the specific reason for a narrowly scoped CLI import in the private execution record.
5. If import behavior is version-sensitive or uncertain, request a separately approved, isolated non-production compatibility probe. Do not test against the reviewed target by trial-and-error.
6. Prepare a bootstrap-only adoption approval request that lists the exact source/lock/inventory/backend evidence digests and stop conditions, but does not include a foundation plan.

**Acceptance:** Bootstrap adoption is either demonstrably safe to request under a separate approval, or honestly blocked with a private evidence-backed reason.

---

### Task 4: Execute the separately approved bootstrap-root adoption ceremony

**Objective:** Establish or reconcile remote Terraform state for bootstrap resources only, then prove readback and recovery posture before workload-root operations.

**Files:**
- Operate privately after explicit approval: `infra/gcp/bootstrap/`
- Create privately: `bootstrap-adoption-preflight.<UTC-run-id>.md`
- Create privately: `bootstrap-state-readback.<UTC-run-id>.md`
- Inspect: `deploy/gcp/bootstrap-state-runbook.md`

**Approval preconditions:**

- The private inventory and bootstrap provenance are independently reviewed and current.
- The source SHA, exact Terraform version, provider-lock digest, non-secret-input digest, canonical backend-configuration digest, and opaque resolved-backend identity/state-object-or-prefix/lock-scope fingerprint are immutable in the approval record.
- The approved address set is bootstrap-only and exact; the state recovery reference and approved lockout rollback are present.
- The approval explicitly permits the narrowly described backend/state/import operations. It does **not** permit workload-root initialization/import, foundation planning, apply, retirement, or remediation.

**Ceremony steps after approval:**

1. Verify the execution checkout equals the approved source SHA and the lock digest equals the approval record; stop on mismatch.
2. Verify the approved backend configuration is supplied from the operator-held path, recompute its canonical digest, resolve its backend identity/state object-or-prefix/lock scope, and compare the resulting opaque fingerprint to the approval record. Stop before initialization on any mismatch; never print or copy the configuration to a tracked location.
3. Establish the approved bootstrap backend using the least-privilege identity and the documented state-migration representation. Preserve private pre-action recovery evidence before any state transition.
4. Reconcile only the exact approved bootstrap resource set, one resource at a time where import/adoption is required. Read back the resulting state privately after each step and stop on the first mismatch.
5. Confirm bootstrap state lineage/serial, backend key/prefix, lock scope, and address set are bootstrap-only.
6. Verify successor state/recovery access privately. Do **not** retire bootstrap authority in this task.
7. Produce a value-safe result: `complete`, `blocked`, or `unknown`; list the next approval needed, not an inferred action.

**Acceptance:** The bootstrap root has independently evidenced state provenance/custody and contains no workload-root addresses. Any mismatch remains blocked without live/source repair.

---

### Task 5: Execute the separately approved workload-root adoption ceremony

**Objective:** Establish or reconcile remote Terraform state for the already-existing partial non-executable workload foundation only.

**Files:**
- Operate privately after explicit approval: `infra/gcp/`
- Create privately: `workload-adoption-preflight.<UTC-run-id>.md`
- Create privately: `workload-state-readback.<UTC-run-id>.md`
- Inspect: `infra/gcp/backend.tf`
- Inspect: `infra/gcp/develop.tf`
- Inspect: `infra/gcp/develop/{apis.tf,identities.tf,artifact_registry.tf,secrets.tf,iam.tf,budgets.tf,observability.tf,network.tf,cloud_sql.tf}`

**Approval preconditions:**

- Task 4 is complete with a reviewed bootstrap-only readback and no unresolved bootstrap blocker.
- The workload backend is proven distinct from the bootstrap backend in object/key/prefix, lock scope, lineage, access boundary, and recovery reference.
- The approved workload address set includes only privately inventoried existing partial-foundation resources.
- The approved deferred-absent set explicitly includes network/private-service-access/Cloud SQL/application-database resources, all Cloud Run jobs/services, images, payloads, database logins, tester access, migration, and qualification.
- The approval permits only the named workload backend/state/import operations, not plan/apply or any remediation.

**Ceremony steps after approval:**

1. Repeat exact source/lock/non-secret-input/backend-config-digest/resolved-backend-fingerprint preflight; stop on any changed digest or scope.
2. Initialize only the approval-bound workload backend privately; verify its resolved identity/state object-or-prefix/lock scope differs from bootstrap and that no bootstrap state is selected or discoverable through this root.
3. Reconcile each approved existing workload candidate according to the reviewed import representation; read state privately after each adoption and stop on the first unexpected address or source/live difference.
4. Confirm all deferred-absent classes remain absent in both inventory and state. Do not create dummy resources or use `-target` to force a partial outcome.
5. Confirm workload state contains no bootstrap addresses and has a distinct lineage, backend key/prefix, lock scope, and recovery reference.
6. Do not run `terraform plan` in this task. Record only the adoption/readback result and whether a separate plan-generation approval may now be requested.

**Acceptance:** The private workload state contains exactly the approved existing partial-foundation candidate set and preserves all deferred classes as absent. The exact foundation-plan gate remains unopened until a separate approval.

---

### Task 6: Prepare, but do not execute, the exact foundation-plan gate

**Objective:** Convert completed adoption evidence into a later Gate 3 planning request without generating a real plan in the adoption ceremony.

**Files:**
- Create later after Tasks 4-5: `.hermes/plans/<UTC-timestamp>-foundation-saved-plan-generation-plan.md`
- Inspect: `deploy/gcp/staged-plan-approval.md`
- Inspect: `scripts/verify_gcp_foundation.py`
- Inspect: `tests/unit/test_terraform_hygiene.py`
- Inspect: `tests/unit/test_verify_gcp_foundation.py`

**The later plan-generation approval bundle must require:**

1. exact source SHA, Terraform version, provider-lock digest, non-secret-input digest, backend/state readback references, and complete reviewed inventory digest;
2. `deployment_stage=foundation` only, with no image digest and null deferred private-network/Cloud SQL/application-database/tester inputs;
3. a separately accepted source-only verifier-reconciliation result that resolves the current foundation-stage Cloud SQL absence versus verifier-presence contradiction; without it, stop before plan generation;
4. a saved binary plan plus JSON inventory held privately and hashes bound to the same source/lock/input state;
5. an explicit JSON-inventory proof that no Cloud Run job or service is present, and that deferred network/private-service-access/Cloud SQL/application-database resources are absent;
6. review of planned create/change/delete/replace actions, API/IAM/state/registry/secrets/budget/observability/labels/recovery implications and cost assumptions;
7. invalidation if source, lock, inputs, backend/state, inventory, plan artifact, or approval reference changes.

**Acceptance:** A later exact `foundation` plan can be proposed only when adoption evidence is complete and a new approval explicitly authorizes its generation.

---

## 4. Planned validation and review gates

### Planning-packet validation only

These source-local checks may run while preparing the planning packet; they do not initialize a remote backend or contact GCP:

```text
terraform fmt -check -recursive infra/gcp
terraform -chdir=infra/gcp init -backend=false -input=false -lockfile=readonly
terraform -chdir=infra/gcp validate
terraform -chdir=infra/gcp/bootstrap init -backend=false -input=false -lockfile=readonly
terraform -chdir=infra/gcp/bootstrap validate
env -u PYTHONPATH uv run python scripts/validate_terraform_static.py
env -u PYTHONPATH uv run pytest tests/unit/test_terraform_hygiene.py tests/unit/test_verify_gcp_foundation.py -q
git diff --check
```

After a planning commit exists, run the exact committed-range secret scan before opening a protected documentation PR:

```text
/opt/homebrew/bin/gitleaks git --no-banner --redact --log-opts 'origin/develop..HEAD'
```

### Required independent review questions

1. Does the plan keep inventory collection, bootstrap adoption, workload adoption, foundation-plan generation, and foundation apply as distinct approvals?
2. Does it prove the two roots never share backend identity, state object/key/prefix, lock scope, lineage, address universe, or import operation?
3. Does the inventory schema make every in-scope resource classifiable once while preserving private evidence custody?
4. Does every mismatch result in a stop-and-record outcome rather than a repair, IAM broadening, recreation, or import guess?
5. Does it retain the foundation-stage absence of Cloud Run job/service and all network/private-service-access/Cloud SQL/application-database/workload deferrals?
6. Does it preserve the same-repository-CI High/open residual risk without presenting CI as independent authorization?
7. Does the tracked packet exclude all project/billing IDs, principals, endpoints, backend values, state, plans, raw output, credentials, and secret values?

---

## 5. Risks and open questions

1. **Bootstrap local-state provenance may be absent.** This is a blocker for trusted state migration/adoption; no invented history, overwrite, or import experiment is acceptable.
2. **Provider normalization/import behavior may differ from source.** Verify the exact pinned Terraform/provider behavior before any target operation; use an approved isolated compatibility probe if documentation does not settle it.
3. **Manual/live drift may be correct but unauditable.** Classify as `unmatched_manual_divergence` and stop rather than broadening source or reconciling by mutation.
4. **State is sensitive operational data.** Treat it as credential-bearing architecture inventory even when individual outputs are marked sensitive; maintain encryption, least privilege, logging, recovery, and disposal controls in private custody.
5. **Backend credentials/configuration can persist in `.terraform`.** Supply them only from approved operator-held configuration; verify ignored status and never expose or commit them.
6. **Notification-channel existence does not prove delivery.** Retain delivery confirmation as later observability/qualification evidence, not as an adoption criterion.
7. **The exact foundation plan is time/state-sensitive.** It cannot be pre-approved from this packet: it must bind to the completed private adoption evidence, current source/lock/input state, and its own saved-plan digest.
8. **Foundation verifier contract contradiction.** The present verifier requires Cloud SQL in `foundation` mode even though PR #46 intentionally omits it from the evaluated foundation root. Preserve the conflict as a Blocker; a future accepted source-only reconciliation must establish stage-correct verifier expectations before a foundation saved plan or foundation-mode verification is requested.

## Final stop boundary

This proposed packet stops after technical review, Beatrice's explicit acceptance, its narrow acceptance-delta audit, and protected planning publication. Even after later inventory/adoption execution, it does not authorize a Terraform plan/apply, foundation apply, bootstrap-authority retirement, private networking, Cloud SQL, image publication, secret payload/database preparation, migration, service activation, tester access, qualification, production, or any live/client-data action. Each must receive its own reviewed plan and explicit approval.

> **Subsequent planning-granularity governance:** ADR-0014 and the Proposed `.hermes/plans/2026-08-27_124046-private-develop-activation-human-feedback-plan.md` retain this packet's Tasks 2–5 ceremony detail and every exact operational approval/readback. If that later master plan is independently reviewed, explicitly accepted, and merged, its predeclared Gates B–F supersede only this paragraph's requirement for a new standalone planning document per action. Until then, this historical packet grants no later action.
