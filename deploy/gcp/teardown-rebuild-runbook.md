# Teardown and rebuild runbook

This runbook defines the controlled disposal and reconstruction of the private fictional-synthetic `develop` workload environment while preserving the lifecycle-independent control plane and remote state. It does not authorize any automatic scheduled destroy or unreviewed cloud mutation from this source-controlled branch.

Current source status: PR #37 merged the teardown/rebuild source contracts at `caf96a7`, PR #42 made tester verification service-stage-only at `b2d79b5`, and PR #48 completed the separate foundation-stage verifier alignment at `5f265d8`. Private records show separately approved partial foundation work; this runbook remains future operator guidance until the later explicitly approved operational gates.

## Scope

- disposable workload teardown and rebuild only
- control-plane/state survival across workload teardown
- deletion protection and explicit break-glass steps
- inventory, cost, secret, evidence, and orphan-resource checks
- no automatic scheduled destroy

## Core rule

The workload environment is disposable; the control plane is not. Teardown must preserve bootstrap/state survival and must not destroy the lifecycle-independent state bucket, WIF trust baseline, or operator-held recovery records.

## Preconditions

1. Teardown or rebuild is explicitly approved for the reviewed target.
2. Current inventory and value-safe evidence have been collected.
3. Secret custody owners know whether values will be retained, rotated, or replaced.
4. Any named tester window is closed or intentionally re-opened later.
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
- named tester access state
- latest foundation verification and qualification evidence
- current cost/budget/alert posture
- any known orphan-resource suspicion

## Deletion protection and break-glass

- Respect deletion protection on reviewed resources by default.
- If a resource cannot be removed without disabling deletion protection, require an explicit break-glass step and record who approved and executed it in the operator-held record.
- Break-glass must stay narrow to the reviewed disposable workload resource; it must not widen to state or broad IAM.

## Teardown sequence

1. Close tester access and rotate any suspect access material if needed.
2. Preserve or export value-safe evidence needed for later comparison.
3. Confirm secrets that should not survive are scheduled for rotation or replacement.
4. Remove only reviewed disposable workload resources through the later approved operational path.
5. Verify control-plane/state survival immediately after teardown.
6. Check for orphan-resource residue, unexpected costs, lingering invoker grants, lingering secret references, or stale alert routes.

## Rebuild sequence

1. Reconfirm the reviewed Terraform/state/foundation baseline.
2. Recreate workload resources only from the reviewed contract.
3. Re-inject secrets out of band using the secret-custody runbook.
4. Reapply named tester access only through the private tester procedure.
5. Re-run foundation verification, health/readiness, and bounded qualification.
6. Record the rebuilt environment as fictional-synthetic-only and separately gated from production.

## Orphan-resource and cost checks

After teardown or rebuild, verify:

- no unexpected workload resources remain
- no public or broad invoker binding remains
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
