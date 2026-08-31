# Dedicated Workload Project Binding and A1 Scope-Delta Decision Plan

> **For Hermes:** This is a decision-and-publication packet. Its acceptance and merge authorize **only WP-1**. They do not authorize a cloud command or make any private execution-input bundle sufficient for later action: WP-2 and WP-3 each require their own explicit, separately recorded approval before any readback or collection command. Do not exceed the listed read-only binding/scope-delta or later gate boundaries.

**Status:** Decision-and-publication packet. PR #57 remains the closed A1 live-foundation remediation record. The existing private dedicated workload project is the accepted disposable `develop` target and is verified billing-enabled in operator-held evidence. A duplicate created during the retired new-project path is `DELETE_REQUESTED` and must not be reused; no provider quota request was submitted. This packet prohibits another project-creation transaction and a repeat of the completed A1 collection. WP-3 records only the bounded workload-scope delta needed to attach the confirmed target to the closed A1 evidence. A2 provenance/import, state, Terraform, and deployment gates remain separate.

**Goal:** Bind the existing dedicated disposable workload project through a bounded private readback, record only its required workload-scope delta against PR #57's closed A1 evidence, and preserve the lifecycle-independent control-plane/state boundary.

**Architecture:** The existing control-plane project remains the exclusive durable state/bootstrap/WIF candidate. The existing billing-enabled workload project is the disposable workload target; the duplicate under deletion is excluded. The current Terraform workload root remains the authority for later workload resources only. This packet does not authorize creation, billing mutation, labels, IAM, API enablement, or resource creation inside the workload project.

**Controls:** ADR-0009, ADR-0012, ADR-0013, ADR-0014; `.hermes/plans/2026-08-27_124046-private-develop-activation-human-feedback-plan.md`; `deploy/gcp/bootstrap-state-runbook.md`; `scripts/verify_gcp_foundation.py`.

---

## 1. Accepted boundary decision

- Bind **one existing dedicated disposable workload project** to the private fictional-synthetic `develop` environment; do not create another project.
- Confirm through the private custody record that it is under the approved parent/folder relationship and attached to the existing private interim billing custody governing the control-plane project.
- Keep its identifier, private display-name convention, billing-account reference, authorized operator, and readback receipt outside tracked source, ordinary notes, chat, Terraform variables, and state.
- Exclude the duplicate project already under deletion from every binding, inventory, Terraform, and lifecycle decision.
- Keep the workload project separate from the lifecycle-independent control-plane/state project in project identity, billing evidence, IAM, state object/prefix, lock scope, lineage, and teardown lifecycle.
- Treat the workload project as an external organization/billing bootstrap artifact. The current `infra/gcp` Terraform root must not claim to create or adopt the project container merely because it will later own approved resources inside it.

## 2. Non-decisions and preserved boundaries

This decision does **not** authorize:

- project creation, billing attachment/change, labels, API enablement, IAM changes, or resource creation;
- Terraform backend initialization, state migration, import, refresh, plan, or apply;
- Cloud Run, Artifact Registry, Secret Manager, Cloud SQL, networking, secret payloads, database login roles, image publication, migration, service activation, tester access, qualification, live/client data, public access, or production;
- selection, reuse, or adoption of the duplicate or any other candidate returned by historical discovery.

## 3. Required private decision inputs before execution approval

The owner-operated approval bundle must privately record and bind:

1. the existing workload project's exact identity, parent/folder, and a value-safe ownership rationale;
2. billing-enabled readback and interim billing custody/alert ownership;
3. the approved `us-east4` posture for later regional services, without treating it as an authorization to create any regional resource;
4. the explicitly excluded duplicate project's disposition and a prohibition on its reuse;
5. operator identity and the limited read-only permissions needed for custody readback and the bounded workload-scope delta;
6. the readback/evidence location, source SHA, and operator-held run identifier;
7. explicit no-create/no-billing-mutation/no-label/no-API/no-IAM/no-resource/no-state/no-Terraform boundaries;
8. the exact read-only delta collection commands, PR #57 evidence reference, and stop conditions.

## 4. Ordered execution gates

### Gate WP-1: Decision-packet review and protected publication

**Objective:** Independently review and merge this binding/scope-delta amendment before any workload-project binding readback or workload-scope delta collection.

**Files:**
- Create: this plan
- Create: `docs/review-handoffs/<UTC-date>-workload-project-binding-scope-delta-review-handoff.md`
- Modify: `CURRENT_WORK.md`, `ROADMAP.md`, `NOTES.md`, `TECHNOLOGY_DECISIONS.md`, `infra/gcp/README.md`, and relevant ADR/architecture status surfaces

**Verification:**
- Markdown/reference integrity checks
- `git diff --check`
- exact committed-range Gitleaks before protected PR
- independent planning/security review of lifecycle separation, existing-project custody/billing evidence, duplicate exclusion, no-creation authority, bounded workload-scope delta, and preserved A1 closure

**Stop boundary:** No cloud command or workload-project selection, creation, mutation, or adoption action.

### Gate WP-2: Separate binding/readback approval

**Objective:** Obtain explicit approval for one owner-operated, read-only confirmation that the privately recorded existing workload project is the approved disposable target.

**Allowed after approval:**
1. Confirm the exact operator identity and approved private parent/billing scope.
2. Read back the exact existing project's metadata, parent, billing association, and labels into private evidence.
3. Confirm the duplicate is excluded and no candidate substitution occurred.
4. Bind the exact private project identity to the A1 custody record.

**Explicitly prohibited:** Project creation, billing attachment/change, label mutation, API enablement, IAM grants/removals, service-account creation, WIF, bucket creation, Artifact Registry, secret metadata, network, Cloud SQL, Cloud Run, Terraform, state/backend activity, image publication, tester access, database actions, and deployment.

**Stop conditions:** Missing or mismatched private custody/billing readback, duplicate or other candidate substitution, unexpected resource/authority posture, failed readback, or any request to expand the operation.

**Acceptance:** A private readback record proves the existing distinct workload project is the approved target, is billing-enabled under the approved custody, remains separate from control-plane/state, and has no approved resource or authority change from this gate.

### Gate WP-3: Bounded workload-scope delta approval

**Objective:** Under a separate explicit read-only approval, collect only the confirmed workload project's facts and required cross-project binding references, then attach one classified delta to PR #57's closed A1 evidence. This does **not** reopen, repeat, or re-disposition the completed A1 control-plane collection.

**Files:**
- Private only: PR #57 A1 evidence reference, workload-scope delta record, raw run directory, and one delta disposition register
- Value-safe updates: `CURRENT_WORK.md`, `ROADMAP.md`, `NOTES.md`, and the existing Obsidian A1 closeout

**Required collection:** only workload-project labels/IAM, workload service-account and user-managed-key inventory, applicable workload WIF bindings, Artifact Registry IAM needed by the workload root, workload-scoped logging/service-job absence posture, and the readback references required to prove separation from the already-recorded control plane. Reuse PR #57's closed evidence for unchanged control-plane facts.

**Acceptance:** Every workload-scope delta fact is classified exactly once. Expected greenfield absence remains distinct from drift. Unknown/public/broad/state-lineage/unreviewed-action findings block A2. A clean delta preserves PR #57's A1 closure; it is not a second A1 gate.

**Stop boundary:** No state adoption, Terraform operation, remediation, resource mutation, or deployment.

## 5. Material replanning triggers

Return to planning before execution if any of the following changes:

- the existing workload target cannot be proven distinct from the control-plane project, billing authority, or state boundary;
- private custody/readback cannot establish the approved parent/folder or billing relationship;
- the binding requires an unreviewed policy exception, inherited broad IAM, or a different trust model;
- any project creation, billing/label mutation, API, IAM, resource, Terraform, network, database, workload, or public-access action is added to WP-2;
- readback identifies a different project/resource set requiring adoption rather than the accepted existing target.

## 6. Definition of done for this decision packet

- The existing workload-project boundary, duplicate exclusion, and external project-container ownership are accepted.
- WP-1 has passed independent review and merged through protected `develop`.
- WP-2 remains a separate explicit read-only binding/readback approval, not an implied consequence of plan merge.
- The post-WP-2 bounded workload-scope delta, A2 provenance/import, A3/A4 state adoption, A5 augmentation, foundation saved plan/apply, and all later deployment gates remain distinct approvals; PR #57's closed A1 record is not reopened.
