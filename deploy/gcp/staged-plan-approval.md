# Staged plan approval procedure

This document defines the value-safe approval procedure for each separately approved `foundation`, `migration`, and `service` Terraform transition. The post-PR33 remediations and Gate F foundation transition are complete; this procedure grants no new cloud action and remains controlling guidance for later saved-plan transitions.

## Purpose

Ensure every later cloud transition is tied to one reviewed saved plan, one exact source state, one exact workload digest posture, and one explicit approval record.

Before any backend initialization or apply, the approval bundle must also bind the canonical private backend-config digest plus an opaque resolved backend identity, state object or prefix, and lock scope fingerprint. The pre-initialization comparison must prove bootstrap and workload roots remain distinct and that the reviewed source/inputs still resolve to the approved backend target for that root.

## Core rule

No Terraform apply, migration execution, service activation, or reverse transition may proceed from chat approval, a remembered prior plan, or a mutable local worktree. Every transition requires its own saved artifacts and explicit operator approval.

## Required saved artifacts per transition

For each approved stage transition, preserve these artifacts outside tracked source in the operator-held deployment record:

1. **Binary plan artifact**
   - exact saved Terraform plan file for the target stage
   - immutable path or object reference in the private operator-held record
2. **JSON inventory artifact**
   - machine-readable plan/resource inventory derived from the same saved plan
   - must preserve reviewed executable-workload counts for the target stage
3. **Source and lock digests**
   - exact source commit SHA
   - provider lock digest
   - reviewed non-secret input digest
   - plan file digest
   - canonical private backend-config digest
4. **Backend target fingerprint**
   - opaque resolved backend identity
   - opaque state object or prefix fingerprint
   - opaque lock scope fingerprint
   - pre-initialization comparison record for the approved root
5. **Stage and workload binding**
   - target stage: `foundation`, `migration`, or `service`
   - exact workload image digest when executable workload is present
6. **Approval record**
   - approving owner
   - approval timestamp
   - approved target stage
   - saved-plan artifact references
   - explicit go/no-go note
7. **Post-apply verification record**
   - exact verifier command used
   - observed pass/fail result
   - any residual blockers
8. **Reverse-transition review record**
   - destruction/replacement intent
   - control-plane survival review
   - secret/tester/recovery handling review

## Minimum stage-specific requirements

### Foundation
- saved plan proves no Cloud Run service or migration job will be created
- JSON inventory shows only approved foundation resources
- approval record explicitly states no executable workload is authorized
- post-apply verification uses foundation mode and confirms no executable workload exists
- foundation-mode verification must not require Cloud SQL or a private database path, because PR #46 removed network, private-service-access, Cloud SQL, and application-database resources from the evaluated `foundation` root
- later verifier stages remain responsible for fail-closed private Cloud SQL posture checks only when those lower-layer resources are actually in scope

### Migration
- saved plan binds the reviewed workload image digest
- JSON inventory proves the migration job exists and the service does not
- approval record explicitly authorizes migration-stage resource presence only
- migration execution itself remains a later separate explicit gate; plan approval alone is not execution approval

### Service
- saved plan binds the reviewed workload image digest
- JSON inventory proves both migration job and service exist
- approval record explicitly states deploy-readiness is not qualification
- later tester access and bounded qualification remain separate explicit gates

## Approval ceremony

1. Confirm the remediation merge is the reviewed base for the plan.
2. Before any backend initialization, compare the reviewed source and operator-held inputs to the approved canonical private backend-config digest plus the opaque resolved backend identity/state object or prefix/lock scope fingerprint for that root.
3. Generate the saved plan using only reviewed non-secret inputs.
4. Record the plan digest, lock digest, source SHA, stage, and backend fingerprint bundle.
5. Export the JSON inventory from that exact saved plan.
6. Verify stage/workload binding before any approval request is sent.
7. Present the approval bundle to Beatrice with:
   - target stage
   - artifact references
   - exact digests
   - backend fingerprint bundle
   - expected inventory
   - destructive/replacement summary
8. Record explicit approval or rejection.
9. If approved, apply only that exact saved plan.
10. Immediately run the reviewed post-apply verifier and record its result.
11. Stop before the next gate unless that next gate receives its own explicit approval.

For the one-time provisioner-operator bootstrap transition, the saved-plan inventory must contain exactly one create—`google_service_account_iam_member.provisioner_operator_token_creator`—and every other action must be no-op. The existing bootstrap operator may execute only that exact approved bootstrap plan. Immediate post-apply verification must supply the operator-held named user through `--provisioner-operator-principal`, require exactly `roles/iam.serviceAccountTokenCreator` on only the provisioner service account, reject missing/wrong/extra/WIF/project-wide authority, and prove short-lived token mint without displaying the token. No workload plan or next gate follows implicitly.

## Reverse transitions

A reverse transition is a reviewed destruction/change event, not an implicit rollback.

Before any reverse transition:
- identify whether the target is disposable workload only or control-plane adjacent
- review state/control-plane survival explicitly
- review secret custody consequences
- review named tester and alert-route consequences
- record why forward recovery is insufficient or unsafe

## Value-safety rules

Tracked source and ordinary docs may record only value-safe facts such as:
- that a saved plan exists
- that stage/inventory/digest binding was reviewed
- that approval was granted or withheld
- that post-apply verification passed or failed

Tracked source must not include:
- project IDs
- billing IDs
- principals
- domains
- endpoints
- secret payloads
- plan output
- state snapshots
- private operator-held record contents

## Stop conditions

Stop immediately if any of the following is true:
- the saved plan artifact cannot be tied to the reviewed source SHA
- the JSON inventory does not match the target stage contract
- executable workload appears in `foundation`
- workload digest is missing for `migration` or `service`
- approval exists only in chat and not in the operator-held record
- post-apply verifier fails or cannot run
- the next gate is being inferred rather than explicitly approved

## Relationship to other procedures

- use `deploy/gcp/bootstrap-state-runbook.md` for bootstrap/state ceremony
- use `deploy/gcp/first-deployment-runbook.md` for first deployment operator steps
- use `deploy/gcp/private-tester-access.md` for named tester access
- use `deploy/gcp/rollback-forward-recovery-runbook.md` for recovery-path choice
- use `deploy/gcp/teardown-rebuild-runbook.md` for disposable workload teardown/rebuild

## Current status

This procedure remains source-controlled guidance for separately approved saved-plan operations. PR #37/42/46/48 closed the ADR-0013 source/verifier blockers; PR #57 closed A1; PR #58/59 plus WP-2/WP-3 completed workload binding; A2 selected new lineage; and state establishment, ownership alignment, exact foundation apply/verification, Gate P, bounded Gate S, both bootstrap provisioner-authority transitions, and workload-backend proof are complete. Fresh migration plan generation later stopped before state read because process-wide quota attribution required forbidden project-level provisioner authority. ADR-0015 merged through PR #79 at `develop@e7bab14795a24ff69fcc3cd7f8bd28f2cbb9cd73` and now governs the FinOps separation direction; no historical plan or approval is reusable. The planning merge authorizes only Implementation PR A source work, and every FinOps IAM/state/plan/apply plus migration/service/tester/qualification action remains separately approval-bound.
