# Staged plan approval procedure

This document defines value-safe saved-plan handling for the `foundation`, `migration`, and `service` Terraform transitions. The post-PR33 remediations and Gate F foundation transition are complete. For the current fictional-synthetic target, migration and service plan handling occurs only inside one future explicitly approved eight-hour packet; this procedure grants no cloud action by itself and does not create per-transition approval gates.

## Purpose

Ensure every later cloud transition is tied to one reviewed saved plan, one exact source state, one exact workload digest posture, and the exact still-valid packet approval.

Before any backend initialization or apply, the approval bundle must also bind the canonical private backend-config digest plus an opaque resolved backend identity, state object or prefix, and lock scope fingerprint. The pre-initialization comparison must prove bootstrap and workload roots remain distinct and that the reviewed source/inputs still resolve to the approved backend target for that root.

## Core rule

No Terraform apply, migration execution, service activation, or reverse transition may proceed from chat approval, a remembered prior plan, or a mutable local worktree. Every transition requires its own saved artifacts and must fall within the exact allowlist of the still-valid eight-hour packet. Once that packet is explicitly approved, its ordered internal transitions do not require fresh approval unless a named stop condition ends the packet or an operation falls outside its allowlist.

## Required saved artifacts per transition

For each packet-authorized stage transition, preserve these artifacts outside tracked source in the operator-held deployment record:

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
6. **Packet authority record**
   - approving owner
   - packet approval timestamp and expiry
   - packet-authorized target stages
   - saved-plan artifact references as they are produced and admitted
   - explicit proceed/stop disposition under the packet allowlist
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
- saved plan proves no Cloud Run service, migration job, or database-authority job will be created
- JSON inventory shows only approved foundation resources
- approval record explicitly states no executable workload is authorized
- post-apply verification uses foundation mode and confirms no executable workload exists
- foundation-mode verification must not require Cloud SQL or a private database path, because PR #46 removed network, private-service-access, Cloud SQL, and application-database resources from the evaluated `foundation` root
- later verifier stages remain responsible for fail-closed private Cloud SQL posture checks only when those lower-layer resources are actually in scope

### Migration
- saved plan binds the reviewed workload image digest
- JSON inventory proves the migration and database-authority jobs exist and the service does not
- packet authority record includes the migration stage
- migration execution proceeds later in the same packet only after migration plan/apply/readback and exact live job-image verification succeed; it is not separately approved

### Service
- saved plan binds the reviewed workload image digest
- JSON inventory proves both bounded jobs and the service exist
- packet authority record distinguishes deploy-readiness from qualification
- access and bounded qualification proceed as later ordered stages of the same packet only after service apply/readback succeeds

## Approval ceremony

1. Confirm the remediation merge is the reviewed base for the plan.
2. Before any backend initialization, compare the reviewed source and operator-held inputs to the approved canonical private backend-config digest plus the opaque resolved backend identity/state object or prefix/lock scope fingerprint for that root.
3. Generate the saved plan using only reviewed non-secret inputs.
4. Record the plan digest, lock digest, source SHA, stage, and backend fingerprint bundle.
5. Export the JSON inventory from that exact saved plan.
6. Verify stage/workload binding before any apply or other mutation.
7. Compare the admission bundle to the still-valid packet with:
   - target stage
   - artifact references
   - exact digests
   - backend fingerprint bundle
   - expected inventory
   - destructive/replacement summary
8. Record the proceed or stop disposition under the packet allowlist; this is an internal admission decision, not a fresh approval.
9. If admitted, apply only that exact saved plan.
10. Immediately run the reviewed post-apply verifier and record its result.
11. Continue to the next ordered stage only while the packet remains valid, the stage is allowlisted, and no stop condition has fired; otherwise stop and require fresh authority.

For the one-time provisioner-operator bootstrap transition, the saved-plan inventory must contain exactly one create—`google_service_account_iam_member.provisioner_operator_token_creator`—and every other action must be no-op. The existing bootstrap operator may execute only that exact approved bootstrap plan. Immediate post-apply verification must supply the operator-held named user through `--provisioner-operator-principal`, require exactly `roles/iam.serviceAccountTokenCreator` on only the provisioner service account, reject missing/wrong/extra/WIF/project-wide authority, and prove short-lived token mint without displaying the token. No workload plan or next gate follows implicitly.

## Reverse transitions

A reverse transition is a reviewed destruction/change event, not an implicit rollback.

Before any reverse transition:
- identify whether the target is disposable workload only or control-plane adjacent
- review state/control-plane survival explicitly
- review secret custody consequences
- review shared Basic-gate access and alert-route consequences
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
- an operation falls outside the exact approved packet allowlist, or a named stop condition has already ended that packet; internal ordered migration/service/qualification stages are not separate approvals

## Relationship to other procedures

- use `deploy/gcp/bootstrap-state-runbook.md` for bootstrap/state ceremony
- use `deploy/gcp/first-deployment-runbook.md` for first deployment operator steps
- use `deploy/gcp/private-tester-access.md` for the expiring shared browser-access boundary
- use `deploy/gcp/rollback-forward-recovery-runbook.md` for recovery-path choice
- use `deploy/gcp/teardown-rebuild-runbook.md` for disposable workload teardown/rebuild

## Current status

This procedure remains source-controlled guidance for saved-plan operations inside one future explicitly approved fictional-synthetic `develop` deployment packet. The first packet created/read back only the exact quota role and binding, then stopped before backend initialization, import, state access, or plan generation and is consumed. PR #87 merged the verifier correction at `develop@5769e0cf6af6c3f4c75fa1f7ce079ae20a96d396`; no historical plan or approval is reusable.

ADR-0016's human-visible addendum suspends separate Gate E0, signer/envelope/runner, signed FinOps receipt, and per-command approval requirements for this fictional-synthetic `develop` target. One explicit eight-hour packet may cover its ordered precheck, plans/applies, image, secrets, migration, service, access, readbacks, and qualification while retaining the runbook's stop conditions. Saved plan and backend bytes remain held through descriptors and are passed to Terraform only through `/dev/fd` with explicit inherited FDs; pathname re-open is forbidden. Live data, production, destructive recovery/state editing, and out-of-packet authority remain separate.
