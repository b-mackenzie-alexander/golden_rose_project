# Teardown and rebuild runbook

This runbook defines the controlled disposal and reconstruction of the human-visible fictional-synthetic `develop` workload environment while preserving the lifecycle-independent control plane and remote state. Before human handoff, only the non-mutating readiness inspection in this document runs. An actual destructive drill occurs only after the browser walkthrough and requires separate destructive approval.

Current source status: PR #37 merged the teardown/rebuild source contracts at `caf96a7`, PR #42 made tester verification service-stage-only at `b2d79b5`, and PR #48 completed the separate foundation-stage verifier alignment at `5f265d8`. Private records show separately approved partial foundation work; this runbook remains future operator guidance until the later explicitly approved operational gates.

## Scope

- disposable workload teardown and rebuild only
- control-plane/state survival across workload teardown
- deletion protection and explicit break-glass steps
- inventory, cost, secret, evidence, and orphan-resource checks
- no automatic scheduled destroy

## Core rule

The workload environment is disposable; the control plane is not. Teardown must preserve bootstrap/state survival and must not destroy the lifecycle-independent state bucket, WIF trust baseline, or operator-held recovery records.

## Mandatory pre-handoff non-mutating readiness inspection

Without running Terraform destroy/plan/apply or changing cloud resources, verify and record:

1. the reviewed deletion order is service, migration job, database consumers/login material, private Cloud SQL workload, workload networking/monitoring, and only then other disposable workload resources;
2. the state bucket, backend configuration, state-generation references, recovery bindings, workload-provisioner identity, WIF baseline, and operator-held recovery records are explicitly excluded;
3. deletion protection and any break-glass step are identified but not changed;
4. rebuild prerequisites include exact protected source/image, provider locks, state generations, quota bootstrap/import state, private database prerequisites, four secret payload classes, synthetic labels, budget alerts, Basic gate, expiry, and one-instance cap;
5. post-rebuild verification requires exact IAM/resource readback, public minimized probes, fixed Basic denials, synthetic workflow qualification, log scan, and browser walkthrough.

Any actual destroy, deletion-protection change, state removal, or rebuild command is forbidden during this inspection.

## Preconditions

1. Teardown or rebuild is explicitly approved for the reviewed target.
2. Current inventory and value-safe evidence have been collected.
3. Secret custody owners know whether values will be retained, rotated, or replaced.
4. The temporary shared-access window is closed or intentionally re-opened later.
5. The operator understands which resources are protected by deletion protection or require break-glass handling.

## Control-plane/state survival

- Preserve the durable state bucket and its recovery controls.
- Preserve operator-held backend configuration and bootstrap handoff records.
- Preserve reviewed WIF trust and identity-separation contracts unless a separate reviewed change says otherwise.
- Verify the workload teardown path cannot target bootstrap resources.

## Inventory before teardown

Capture a private or value-safe inventory of at least:

- exact workload resources intended for teardown
- current image digest and migration state reference
- current secret version references without payloads
- shared browser-access expiry and public-invoker state
- latest foundation verification and qualification evidence
- current cost/budget/alert posture
- any known orphan-resource suspicion

## Deletion protection and break-glass

- Respect deletion protection on reviewed resources by default.
- If a resource cannot be removed without disabling deletion protection, require an explicit break-glass step and record who approved and executed it in the operator-held record.
- Break-glass must stay narrow to the reviewed disposable workload resource; it must not widen to state or broad IAM.

## Teardown sequence

1. Remove the temporary public invoker and expire/rotate shared browser access if needed.
2. Preserve or export value-safe evidence needed for later comparison.
3. Confirm secrets that should not survive are scheduled for rotation or replacement.
4. Remove only reviewed disposable workload resources through the later approved operational path.
5. Verify control-plane/state survival immediately after teardown.
6. Check for orphan-resource residue, unexpected costs, lingering invoker grants, lingering secret references, or stale alert routes.

## Rebuild sequence

1. Reconfirm the reviewed Terraform/state/foundation baseline.
2. Recreate workload resources only from the reviewed contract.
3. Re-inject secrets out of band using the secret-custody runbook.
4. Reapply the exact temporary shared browser boundary only through the shared-access procedure.
5. Re-run foundation verification, health/readiness, and bounded qualification.
6. Record the rebuilt environment as fictional-synthetic-only and separately gated from production.

## Orphan-resource and cost checks

After teardown or rebuild, verify:

- no unexpected workload resources remain
- no unexpected invoker remains; an intentionally retained service must have only the exact reviewed temporary `allUsers` binding behind the Basic gate
- no stale secret versions or secret consumers are left without an owner decision
- no unexpected alerting, logging, or storage cost drivers remain
- no orphan-resource suspicion remains unresolved

## Evidence boundary

Tracked evidence may say that teardown/rebuild occurred, that control-plane/state survival held, and that orphan-resource/cost checks passed or failed. Do not place private endpoints, payloads, tester identities, or plan output into tracked source.

## Forbidden automation

- No automatic scheduled destroy.
- No cron-driven teardown.
- No convenience wildcard delete of the control plane.
- No rebuild that bypasses the reviewed secret-injection or tester-access ceremonies.
- No destructive drill before the mandatory human browser walkthrough or without separate destructive approval.
