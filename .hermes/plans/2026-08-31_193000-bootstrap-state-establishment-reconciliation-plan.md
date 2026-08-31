# Bootstrap State Establishment and Reconciliation Plan

> **For Hermes:** This packet is source-only planning. It may be reviewed and published through the protected `develop` flow, but it does not authorize GCP authentication, backend initialization, Terraform state commands, imports, plans, applies, or cloud mutation.

**Goal:** Replace the retired prior-state adoption premise with a bounded, separately approved bootstrap-state establishment/reconciliation path that creates new Terraform state lineage only for the existing durable bootstrap controls.

**Architecture:** A2 established that the durable bucket was manually created before Terraform state existed. The next state operation must therefore establish a new bootstrap-root lineage against the existing approved bootstrap inventory, preserving the bucket and its recovery posture rather than claiming to recover or import prior state. The later workload-root state path remains a distinct approval and must prove separate backend targeting, lock scope, lineage, recovery evidence, and address set.

**Tech Stack:** Terraform and the pinned Google provider already tracked under `infra/gcp/`; partial GCS backend configuration supplied only from private operator-held inputs; value-safe tracked Markdown; private encrypted operator evidence.

---

## Current authority and non-goals

- PR #57 closed A1; PR #58 bound the existing workload target; PR #59 preserved A1 through the bounded workload-scope delta.
- Separately approved WP-2 and WP-3 completed without mutation.
- A2 is complete: manual bootstrap plus empty bucket and no local Terraform state retire prior-state adoption/import.
- This packet prepares only the next decision and publication lane. It cannot authorize state creation, resource reconciliation, resource import, plan generation, apply, bootstrap-authority retirement, or workload-state activity.
- The private fictional-synthetic demo lane remains independent. Nothing in this packet delays its product work.

## Required private approval inputs for a later execution decision

Before any bootstrap-state establishment/reconciliation approval, the operator-held record must bind:

1. the exact current source SHA, Terraform version, provider-lock digest, and non-secret-input digest;
2. the approved existing bootstrap candidate inventory and its private evidence digest;
3. the canonical backend-configuration digest and opaque resolved bucket/state-object-or-prefix/lock-scope fingerprint;
4. a new-lineage statement: no claimed local state, no claimed prior remote Terraform state, and no adoption/import representation;
5. a bootstrap-only state address set and explicit no-workload boundary;
6. private recovery/custody references, successor access, and lockout rollback; and
7. exact allowed state-operation commands, mandatory readbacks, expiry, stop conditions, and result owner.

No tracked file, chat response, Terraform variable, plan, or ordinary log may contain identifiers, principals, backend values, state, resource addresses, raw provider output, credentials, or secret payloads.

## Ordered gates

### Gate E1 — Decision-packet review and publication

**Objective:** Publish the state-establishment decision without carrying forward retired adoption language.

**Files:**
- Create: this plan; `docs/review-handoffs/2026-08-31-bootstrap-state-establishment-reconciliation-review-handoff.md`
- Modify: `AGENTS.md`, `ARCHITECTURE.md`, `CURRENT_WORK.md`, `NOTES.md`, `README.md`, `ROADMAP.md`, `SECURITY.md`, `TECHNICAL_REQUIREMENTS.md`, `TECHNOLOGY_DECISIONS.md`
- Modify: `deploy/gcp/bootstrap-state-runbook.md`, `deploy/gcp/first-deployment-runbook.md`, `deploy/gcp/staged-plan-approval.md`, `infra/gcp/README.md`

**Verification:** Markdown/reference integrity, `git diff --check`, exact committed-range secret scan after commit, and independent review focused on retirement of adoption/import, root separation, private evidence custody, and preserved operational gates.

**Stop boundary:** No GCP or Terraform action.

### Gate E2 — Separate bootstrap-state establishment/reconciliation approval

**Objective:** Obtain one bounded operator approval to establish new Terraform state lineage for the bootstrap root only.

**Allowed only after approval:**
1. verify the approved checkout and input/backend fingerprint bundle privately;
2. initialize only the approved bootstrap backend with operator-held configuration;
3. establish bootstrap-root state from the exact approved existing inventory without representing it as an import/adoption of prior state;
4. read back lineage/serial, backend target, lock scope, bootstrap-only addresses, recovery access, and no-workload separation; and
5. write a minimized private result as `complete`, `blocked`, or `unknown`.

**Prohibited:** workload backend/state operations; Terraform plan/apply; resource, IAM, API, or bucket mutation beyond the specifically approved state-establishment operation; bootstrap-authority retirement; images, secrets, database, Cloud Run, tester, or production actions.

**Stop conditions:** any source/lock/input/backend mismatch; any unexpected pre-existing state; candidate inventory mismatch; shared or ambiguous backend/lock scope; unexpected address; missing recovery evidence; or any need to infer an import representation.

### Gate E3 — Separate workload-state path

This gate cannot start until E2 has an independently reviewed complete readback. It needs a new approval, distinct backend target/lock scope/lineage/recovery evidence, exact workload candidate set, and a no-bootstrap-address proof. It may not inherit bootstrap state assumptions.

### Gate E4 — Later bootstrap augmentation and foundation plan

ADR-0013 Amendment B's bootstrap augmentation remains separate after both state paths. The exact workload `foundation` plan follows only after verified state readbacks and any required augmentation; it remains a separate saved-plan, review, and apply sequence.

## Definition of done

- The repository’s active procedures consistently distinguish A2’s completed decision from E2’s later new-lineage state-establishment decision.
- The planning packet is independently reviewed and merged through `develop`.
- The next cloud-facing action is one explicit E2 approval request, not a presumed execution authority.
- The private synthetic demo path is not represented as blocked by this documentation work.
