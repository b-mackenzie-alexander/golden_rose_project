# ADR-0015: Separate Billing Budget ownership from workload provisioning

- **Status:** Accepted and merged by PR #79
- **Date:** 2026-09-07
- **Owner:** Beatrice Alexander (engagement owner and sole repository maintainer)
- **Amends:** ADR-0013 for cost-guardrail ownership, Terraform state topology, and migration-plan identity
- **Related:** ADR-0012, ADR-0014, accepted ADR-0016 awaiting protected publication, `.hermes/plans/2026-09-07_finops-budget-ownership-separation-plan.md`

## Context and evidence posture

The protected source remains `develop@f41e2756c820abc736c52739c6a67390107afb7f`. The PR #78 bootstrap bucket-authority plan applied successfully, exact state/IAM/foundation readback passed, and the separately reviewed provisioner-owned workload-backend proof passed. Those approvals are consumed.

A fresh migration saved-plan packet then proved the selected named-human identity and non-echoing provisioner token path, but Terraform initialization stopped before state read or plan generation. The explicit quota-project binding requires the impersonated provisioner to hold `serviceusage.services.use` on that project. Granting that permission—whether through the predefined Service Usage Consumer role or a custom role—would introduce project-level provisioner authority that the accepted boundary prohibits.

Independent architecture and security disposition reviews found no packet-only retry that preserves all current constraints. Scoping quota attribution only to planning moves the same permission boundary. The current workload root refreshes an existing Billing Budget during normal plans, so simply omitting quota attribution is not an admitted fix.

Evidence is classified as follows:

- **Observed:** operator identity and provisioner token mint passed; initialization failed on quota-project service-use authority; no state read, plan, apply, or mutation occurred.
- **Validated:** provisioner-owned workload-backend access works without the process-wide quota override; explicit quota-project use requires the authenticated principal to hold `serviceusage.services.use`; the current workload root owns the Billing Budget and directly depends on it from migration/service resources.
- **Accepted owner direction:** separate Billing Budget ownership into a billing-authorized control-plane/FinOps Terraform root rather than granting project-level authority to the workload provisioner.
- **Not yet validated:** exact FinOps backend identity, imported budget state, provider behavior after the split, workload plan behavior without a quota override, and cross-root operational receipt/readback.

### Post-merge implementation finding

Implementation PR A review later proved that this ADR's local approval-digest contract is incomplete: a caller able to supply both a policy or approval artifact and its matching digest can create a self-consistent packet without proving a separate protected approval ceremony occurred. Beatrice therefore paused the uncommitted PR A candidate and selected a separately protected, cryptographically signed, one-use approval envelope. Accepted ADR-0016 and `.hermes/plans/2026-09-07_signed-finops-approval-authority-amendment-plan.md` define that material correction and await protected publication.

Until that amendment merges through protected `develop`, is used as the exact rebaseline, and receives separate implementation authorization, ADR-0015's Implementation PR A authority is suspended. The original ownership-separation decision remains accepted; no current source branch, unsigned policy/digest pair, or local test result authorizes implementation publication or an operational action.

## Decision

### 1. Add one IAM-isolated FinOps Terraform root

Create `infra/gcp/finops/` as a third Terraform root with a backend/state object and lock scope distinct from both bootstrap and workload roots. Its backend uses a separately created durable bucket whose resource-level IAM policy excludes the workload provisioner. It owns only the existing develop Billing Budget and the minimum value-safe outputs needed to verify its cost-guardrail contract.

The initial private-target identity contract is exact even though principal values remain operator-held:

- **FinOps operator:** one privately bound named human whose exact billing-account binding is the pre-existing `roles/billing.admin` on the exact billing account. That role is admitted only for this human and must provide `billing.accounts.get` plus `billing.budgets.get`, `billing.budgets.list`, `billing.budgets.create`, and `billing.budgets.update`; no alternate/additional operator billing role or new billing-account IAM mutation is allowed. Every packet binds the complete private billing-account policy/etag and approval digest and fails on drift.
- **Quota consumer:** one privately bound project on which that same named human already has `serviceusage.services.use`; the FinOps provider sets `billing_project` to that project and `user_project_override = true`.
- **FinOps state authority:** the bucket-level IAM policy contains exactly one `roles/storage.objectAdmin` binding with exactly two distinct privately bound `user:` members: the FinOps operator and accountable recovery owner. No service account, group, domain, public principal, condition, legacy bucket role, or second bucket-level role is permitted. The private control-project IAM baseline must separately prove that its exact inherited principals/roles add no unreviewed FinOps-state reader/writer; every workload identity, including the provisioner, must fail object read/write permission probes.
- **Credential ceremony:** every FinOps read/plan/import/apply packet selects one active owner-held `authorized_user` credential, binds the emitted short-lived token to the exact named human without identity output, passes it only through process memory, rejects ambient ADC and persistent impersonation/token-file/credential-file/login-config overrides, and expires the packet after one attempt.
- **Effective-IAM denial:** readback rejects any unreviewed billing-account role, quota-project role newly introduced by this tranche, state-bucket principal, condition, key, WIF path, or service-account impersonation path.

Two source-controlled domain runners enforce—not share—operational authority:

- `run_finops_operator_packet.py` admits only billing-human transactions for `collect`, FinOps `readback`, `init_import`, `plan`, or exact-plan `apply`.
- `run_workload_state_packet.py` admits only provisioner transactions for workload `readback` or exact-address `state_remove`; it has no FinOps backend, Billing Budget API, plan, import, apply, or quota-project path.

B1 continues through the existing named-human bootstrap packet boundary, not either new runner. M1 consumes the receipt in the credential-free offline verifier, then uses a fresh provisioner migration-plan packet; it cannot invoke the FinOps runner. Each gate packet binds the exact runner/trust domain and an immutable transaction manifest containing operation enum, exact ordered primary steps, pre-authorized success/failure `finally` readbacks, working directories, complete argv, minimal environment-key schema, source/input/backend digests, output destinations/type/schema/size/redaction/permission requirements, expected preconditions, wall-clock expiry, exact approval-record digest, and one-use transaction nonce. Output content digests are deliberately absent before execution: each destination must be absent, and the runner atomically seals return codes plus computed output digests afterward. A gate controller invokes only the bound domain transaction(s), and any interruption before mandatory dual-backend readback leaves both roots frozen until a separately reviewed recovery-readback packet completes.

Each domain runner validates and atomically consumes its own approval/transaction claim before executing only the bound graph; a read/collect/import/plan approval cannot admit apply, state removal, another identity, another working directory, or altered arguments. The FinOps runner constructs its environment; rejects inherited `GOOGLE_*`, `CLOUDSDK_*`, ADC, impersonation, access-token-file, credential-file, login-config, service-account-key, and WIF paths; confirms one active `authorized_user`; binds the selected access token to that human through a non-echoing stdin helper; and passes it only in child process memory. The workload runner permits only the separately proven non-echoing named-human-to-provisioner token path and rejects ambient user, quota override, WIF, keys, and every other credential source. Provider HCL contains no credentials. Adversarial tests cover credential-path and cross-domain/cross-operation/cwd/argv/expiry/approval/nonce/output-destination substitution.

The FinOps collector does not call the Monitoring API and receives no workload-project Monitoring role. It reads the exact Billing Budget under the FinOps identity, while a separately authorized workload-state read supplies the notification-channel resource ID/address. The offline receipt builder joins those independently acquired facts and requires the budget's routing ID to equal the exact workload-state channel ID; any live Monitoring qualification remains in the separately approved foundation verifier.

The accountable owner may already retain separately approved recovery access to the workload state bucket. That pre-existing custody is not inherited from FinOps and must be recorded explicitly; the FinOps root grants no workload-state access.

The FinOps root:

- uses its own checked-in dependency lock generated under the repository's pinned CI Terraform version and the locked Google provider selected by that lock;
- receives billing account, exact budget resource name, filtered workload project, notification-channel resource name, and quota project only through operator-held private inputs;
- does not accept labels or another filter input and must preserve the complete imported budget filter unchanged;
- does not own workload networking, Cloud SQL, Cloud Run, identities, IAM, Secret versions, monitoring channels/policies, or application data;
- does not create a second budget or alter the accepted display name, USD 100 amount, currency, three thresholds, `CURRENT_SPEND` bases, exact single-project filter, notification channel, default-recipient suppression, or updates-rule schema during transfer;
- does not grant the workload provisioner any project-level role.

A later automated FinOps identity, additional budget, billing transfer, or production cost policy requires a separate amendment.

### 2. Transfer existing budget state without live replacement

Source delivery and state transfer are deliberately interleaved so no merged configuration can silently propose budget destruction:

1. **Implementation PR A** adds the dedicated FinOps state-bucket resources to bootstrap source, the FinOps root, its lockfile, receipt tooling, CI/static contracts, and transfer runbook while leaving the workload budget resource and its dependencies unchanged. From PR A merge until transfer closeout, all FinOps plan/apply is frozen except the exact state-bucket and import gates.
2. A separately approved bootstrap plan/apply creates only the reviewed FinOps state bucket and exact resource-level custody bindings, then proves the workload provisioner and all unrelated identities cannot access it.
3. Read-only preflight binds the exact current workload state address, full live budget resource name/configuration, absent FinOps lineage, private inputs, recovery evidence, and all three backend identities.
4. Initialize the FinOps backend and import the exact existing budget through the FinOps `init_import` transaction under one reviewed approval. Its manifest pre-authorizes FinOps success/failure readback; the same gate binds a separate workload `readback` transaction/nonce. Every success, failure, timeout, or interruption must end in both exact backends being read; if that cannot complete or FinOps presence cannot be disproved, freeze both roots and require a recovery-readback packet.
5. Only after reviewed import/readback success, use the provisioner-only workload runner's exact `state_remove` transaction to remove the sole old budget address under another approval; the same gate binds FinOps/workload readback transactions. Prove exactly one Terraform owner. The no-plan/no-apply freeze remains active throughout temporary dual ownership and after old-state removal.
6. **Implementation PR B**, prepared from the exact then-current protected tip, removes the workload budget resource, direct dependencies, and unused input plumbing; updates verifier/receipt admission and living docs; and restores source/state alignment. The freeze ends only after PR B merges and independent readback proves the FinOps root is the sole owner and workload source/state both omit the budget.

If FinOps import fails before any state write, the still-merged workload configuration and state remain aligned. If outcome is unknown, both states are read before any retry. If old-state removal fails after import, both roots remain frozen. If PR B cannot merge after successful state removal, restore only through a separately reviewed state/source recovery packet—never an improvised apply.

No `state push`, manual state editing, destroy/recreate, budget mutation, provider upgrade, backend migration/reconfiguration shortcut, or simultaneous apply is permitted.

### 3. Replace same-root dependency with a signed executable receipt gate

Remove direct `depends_on = [google_billing_budget.develop]` edges from the migration job and staff service only in Implementation PR B, after the state transfer. Terraform cannot express a dependency across separately owned states.

The cost guardrail remains a mandatory operational prerequisite. A dedicated billing-side collector runs only under the exact FinOps human credential ceremony and reads only the exact privately bound budget resource, quota/API posture, and referenced notification channel. It must reject display-name search, duplicate candidates, broad listing as authority, and any resource-name mismatch. The general workload foundation verifier no longer performs billing API collection under the provisioner.

The collector produces:

1. a private canonical FinOps receipt containing schema version, unique nonce, issue/expiry timestamps, protected source SHA, exact full budget resource name, FinOps backend fingerprint/lineage/serial/address set, workload lineage/serial and budget-address absence, complete live budget posture, notification-channel resource binding, API posture, and raw-evidence digests;
2. a value-safe signing envelope containing only receipt/evidence digests, source SHA, nonce, issue/expiry timestamps, and schema version;
3. a detached keyless Sigstore bundle produced by a dedicated protected no-GCP signing workflow whose exact `workflow_ref`, OIDC issuer, certificate identity, action pins, and no-secret/no-cloud permissions are source-controlled.

`verify_finops_budget_receipt.py` verifies the bundle before parsing the private receipt; requires digest agreement, exact signer identity/issuer/transparency proof, nonce uniqueness, a maximum 30-minute validity window, unexpired use, exact source/backend/state/live bindings, and one explicit plan-approval reference; and records consumption so the receipt cannot authorize another plan. Failure, stale evidence, duplicate/display-name substitution, altered state/live evidence, or unavailable verification stops before workload authentication or Terraform.

All private receipt artifacts and replay state live under one absolute, pre-existing owner-selected evidence root outside Git. The writer/verifier walks and opens the requested root/ancestors with `O_DIRECTORY|O_NOFOLLOW`, holds directory descriptors, records device/inode identity, and rejects symlinks, non-owned paths, group/world access, hard-link surprises, path escape, and unsafe ancestors; directories are `0700` and files `0600`. Immediately before receipt publication, bundle publication, ready-marker publication, and nonce claiming, it reopens the original absolute parent without following symlinks and compares device/inode identity with the held descriptor; mismatch stops and preserves—not deletes—the temporary artifact for classified recovery. All mutations are descriptor-relative. Receipt plus envelope are written and `fsync`ed in a fresh nonce-scoped staging directory and published together by one atomic directory rename. A verified Sigstore bundle is added through an exclusive temp-file write/rename and a final `ready` marker is published only after every digest is recomputed. The verifier is the sole lock owner during consumption: it acquires the exclusive cross-process `flock` itself, repeats parent identity admission, verifies the ready transaction and approval binding, atomically claims the nonce with `O_CREAT|O_EXCL` plus file/directory `fsync`, and releases the lock only after the final claim is durable. Callers never pre-acquire or hand off that lock. Incomplete staging directories and partial bundle transactions are non-authoritative and require classified cleanup; a final claim can never be overwritten or reused.

The complete budget posture is literal: exact display identity; USD 100 amount/currency; 50%, 75%, and 100% `CURRENT_SPEND` thresholds; one exact workload-project filter and no label/credit/service filters unless already proven unchanged; exact notification channel; `disable_default_iam_recipients = true`; updates-rule schema `1.0`; and non-hard-cap posture.

Every later migration/service saved-plan request binds a fresh verified receipt and its one-use consumption record. A workflow success flag, caller-supplied boolean, unsigned JSON, display-name match, or stale signed receipt is not sufficient. Private values remain outside Git, logs, and ordinary chat.

### 4. Keep workload migration authority quota-free and provisioner-scoped

After state transfer, PR B, and FinOps readback, prepare a fresh workload migration saved-plan packet using the proven provisioner token and workload backend path without a process-wide quota-project override. It must verify and consume the fresh signed FinOps receipt before workload authentication, then use normal refresh and locking and mechanically admit only the reviewed migration-stage actions.

The workload root continues to manage the workload project's Billing Budgets API enablement with `disable_on_destroy = false`; the FinOps operator's explicitly configured quota project is a separate private binding. Removing budget ownership does not authorize API disablement. FinOps provider tests must require `billing_project = var.quota_project_id`, `user_project_override = true`, and explicit selected-token execution; provider configuration must contain no credential, impersonation, or key field.

If normal workload planning still requires project-level provisioner quota-use authority after the budget resource is absent, stop and replan. Do not restore ambient named-human credentials, grant a project role, target around the failing resource, suppress refresh, substitute WIF/keys, or change quota attribution in place.

### 5. Preserve the existing staged deployment sequence

After the split is implemented, transferred, and independently verified, ADR-0013's normal gates resume:

1. reviewed workload `migration` plan;
2. separately approved exact-plan apply and infrastructure readback;
3. separately approved database role and database-URL Secret-version preparation;
4. separately approved migration-job execution and schema/authority evidence;
5. reviewed `service` plan/apply;
6. named tester access and private fictional-synthetic qualification.

Each remains a distinct approval. This ADR does not authorize any of them.

## Consequences and constraints

### Positive

- Preserves the prohibition on project-level workload-provisioner authority.
- Places billing-account resources under an identity that already has explicit billing custody.
- Keeps workload provisioning and cost-governance ownership independently reviewable.
- Avoids using ambient user fallback merely to refresh one billing resource.

### Costs and risks

- Adds a third backend, lock scope, state lineage, recovery record, and operator procedure.
- Introduces a controlled cross-root operational dependency that Terraform cannot encode directly.
- Requires a carefully ordered temporary dual-state-ownership interval during import-before-remove transfer.
- Billing handoff must later transfer FinOps operating authority without widening workload authority.

### Hard constraints

- No project-level role may be granted to the workload provisioner as part of this amendment.
- No budget replacement, second budget, threshold/routing change, or live mutation is authorized by planning acceptance.
- Private identifiers, backend values, state, plan files, receipts, principals, and raw provider output remain outside tracked source and ordinary discussion.
- Planning merge does not authorize backend initialization, import, state removal, Terraform plan/apply, migration, service activation, tester access, live data, or production.

## Alternatives considered

### Grant only `serviceusage.services.use` to the provisioner

Rejected for this direction. A custom role containing one permission is narrower than the predefined role but remains project-level provisioner authority and changes the accepted trust boundary.

### Use a dual-identity provider configuration in one workload state

Rejected for the first correction. It mixes billing-human and workload-provisioner credentials inside one plan, complicates token custody, provider aliasing, state ownership, and anti-fallback verification.

### Omit or substitute the quota project

Rejected. It changes reviewed billing/quota custody without proving a valid consumer project and does not remove the provider refresh requirement.

### Pause migration indefinitely

Rejected as the selected delivery direction. Preserving the current contracts remains safer than an unreviewed retry, but it does not produce the accepted private feedback target.

## Approval and revisit triggers

This ADR and its outcome-scale plan merged through protected `develop` in PR #79 at `e7bab14795a24ff69fcc3cd7f8bd28f2cbb9cd73`. That original source authorization is now historical and suspended by the implementation-review finding recorded above. Revised PR A may begin only after ADR-0016 is accepted, merged through protected `develop`, rebaselined from the exact tip, and separately authorized. Every bootstrap, IAM, backend, state-transfer, plan/apply, migration, and downstream operation remains separately reviewed and approved.

Revisit if the provider cannot preserve the existing budget through import-before-remove transfer, workload planning still requires project-level provisioner quota authority after extraction, a billing-authorized non-human identity becomes required, cross-root receipt verification is infeasible, billing custody changes, or production/multi-environment FinOps becomes active.
