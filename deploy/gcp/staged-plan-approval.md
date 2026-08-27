# Staged plan approval procedure

This document defines the value-safe approval procedure for every future `foundation`, `migration`, and `service` Terraform transition after the post-PR33 remediation merges. It does not authorize any current cloud action from the unmerged remediation branch.

## Purpose

Ensure every later cloud transition is tied to one reviewed saved plan, one exact source state, one exact workload digest posture, and one explicit approval record.

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
4. **Stage and workload binding**
   - target stage: `foundation`, `migration`, or `service`
   - exact workload image digest when executable workload is present
5. **Approval record**
   - approving owner
   - approval timestamp
   - approved target stage
   - saved-plan artifact references
   - explicit go/no-go note
6. **Post-apply verification record**
   - exact verifier command used
   - observed pass/fail result
   - any residual blockers
7. **Reverse-transition review record**
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
2. Generate the saved plan using only reviewed non-secret inputs.
3. Record the plan digest, lock digest, source SHA, and stage.
4. Export the JSON inventory from that exact saved plan.
5. Verify stage/workload binding before any approval request is sent.
6. Present the approval bundle to Beatrice with:
   - target stage
   - artifact references
   - exact digests
   - expected inventory
   - destructive/replacement summary
7. Record explicit approval or rejection.
8. If approved, apply only that exact saved plan.
9. Immediately run the reviewed post-apply verifier and record its result.
10. Stop before the next gate unless that next gate receives its own explicit approval.

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

This procedure is source-controlled guidance only. PR #37 merged the no-cloud remediation into protected `develop` at `caf96a7`; no saved Terraform plan, apply, migration execution, service activation, or qualification has been performed. PR #46 subsequently merged the required source amendment at `58aed28`, so `foundation` now omits network, private-service-access, Cloud SQL, and application-database actions from the evaluated root. PR #47 then merged the Gate 3 source/live adoption-ceremony planning packet at `d7952b4`, preserving separate approvals for private inventory, bootstrap-root adoption, workload-root adoption, and the later exact foundation-plan request. The active source-only verifier reconciliation now aligns `scripts/verify_gcp_foundation.py` to that stage contract, so foundation-mode verification is workload-free and Cloud-SQL-free while later verifier stages retain private Cloud SQL posture checks. A foundation saved plan nevertheless remains blocked until separately approved private source/live inventory and one-root-at-a-time backend/state adoption are complete.