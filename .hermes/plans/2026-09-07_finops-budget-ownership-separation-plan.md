# FinOps Budget Ownership Separation and Migration Resumption Plan

> **Status:** Accepted by Beatrice on 2026-09-07; documentation-only publication pending. No implementation or operational authority is implied.

> **For Hermes:** Use plan-driven TDD execution after this accepted plan is merged into protected `develop`. Keep every cloud/state/plan/apply gate separately approved.

**Goal:** Move the existing develop Billing Budget out of the provisioner-operated workload root into a billing-authorized FinOps root without replacing the live budget, granting project-level provisioner authority, or weakening the staged deployment path; then return to a mechanically admitted migration plan.

**Architecture:** A new `infra/gcp/finops/` root owns only the existing Billing Budget in a third state lineage stored in a dedicated IAM-isolated state bucket. The workload root keeps workload resources and API enablement but no billing-account resource after an interleaved import/remove/source sequence. A canonical privately detailed receipt plus value-safe keyless-signed envelope replaces the impossible cross-root Terraform dependency and becomes a mandatory migration/service plan prerequisite.

**Tech Stack:** Repository-pinned Terraform 1.15.8 for CI, separately exact-bound compatible Terraform for approved operator packets, checked-in per-root lockfiles, Google provider selected by each lock, Python 3.12, pytest, Ruff, mypy, Cosign/Sigstore, Gitleaks, and owner-held GCP evidence.

**Boundary:** Accepted and unpublished; planning acceptance grants no implementation or cloud authority before protected merge.

---

## Outcome and definition of done

This tranche is complete only when all of the following are true:

1. The planning packet is accepted and merged through a documentation-only PR.
2. Source/tests/validators merge in two interleaved implementation PRs: PR A adds isolated FinOps state/root/receipt capability while retaining workload ownership; PR B removes workload ownership only after state transfer.
3. A dedicated FinOps state bucket is applied/read back with an exact policy that excludes the workload provisioner and unrelated identities.
4. The exact existing budget is imported into FinOps state and removed from workload state under separate approvals, with a continuous no-plan/no-apply freeze, no live replacement, and exactly one final Terraform owner.
5. A billing-authorized identity produces a no-op FinOps plan, exact live/state readback, and fresh signed receipt.
6. A fresh provisioner-owned workload migration plan succeeds without a process-wide quota override and is mechanically admitted with only the reviewed migration-stage creates, bounded data reads, and outputs.
7. No migration infrastructure apply, database role/password, Secret version, migration execution, service, tester access, live data, or production action occurs without its later gate.

The normal ADR-0013 sequence may then continue under separate approvals without another planning cycle unless a material trigger below fires.

## Included roadmap outcomes

- Preserve least-privilege human/service-account boundaries while unblocking the private synthetic deployment path.
- Establish complete state/backend/recovery posture for the new FinOps owner.
- Preserve accepted budget thresholds, routing, and non-hard-cap posture.
- Restore a reviewable `migration` saved-plan gate.
- Keep the private fictional-synthetic target production-shaped without treating it as production-ready.

## Ordered delivery sequence

### Planning PR — Publish the material decision

**Files:**
- Create: `docs/adr/ADR-0015-finops-budget-ownership-separation.md`
- Create: `.hermes/plans/2026-09-07_finops-budget-ownership-separation-plan.md`
- Create: `docs/review-handoffs/2026-09-07-finops-budget-ownership-separation-plan-review-handoff.md`
- Modify: `README.md`
- Modify: `infra/gcp/README.md`
- Modify: `deploy/gcp/bootstrap-state-runbook.md`
- Modify: `deploy/gcp/staged-plan-approval.md`
- Modify: `TECHNOLOGY_DECISIONS.md`
- Modify: `CURRENT_WORK.md`
- Modify: `ROADMAP.md`
- Modify: `NOTES.md`
- Modify: `docs/adr/README.md`
- Modify: `AGENTS.md`
- Modify: `ARCHITECTURE.md`
- Modify: `SECURITY.md`
- Modify: `TECHNICAL_REQUIREMENTS.md`

**Acceptance:** Independent architecture/security, Terraform/state-transfer, and plan-executability reviews are CLEAN; Beatrice explicitly accepted the reviewed contract on 2026-09-07. The pre-acceptance reviewed hashes and the current accepted-publication hashes, plus the status-only reason for their difference, must be recorded in the handoff and the latter explicitly confirmed before branch publication.

**Hard stop:** No Terraform source behavior, backend file, provider configuration, test behavior, cloud call, or state action in this PR.

### Implementation PR A — Add isolated FinOps capability while retaining workload ownership

**Objective:** Add the dedicated state bucket, FinOps root, receipt machinery, and CI/static contracts without removing the existing workload budget or its dependencies.

**Files:**
- Create: `infra/gcp/finops/backend.tf`
- Create: `infra/gcp/finops/versions.tf`
- Create: `infra/gcp/finops/providers.tf`
- Create: `infra/gcp/finops/variables.tf`
- Create: `infra/gcp/finops/budget.tf`
- Create: `infra/gcp/finops/outputs.tf`
- Create: `infra/gcp/finops/.terraform.lock.hcl`
- Modify: `infra/gcp/bootstrap/state.tf`
- Modify: `infra/gcp/bootstrap/iam.tf`
- Modify: `infra/gcp/bootstrap/variables.tf`
- Modify: `infra/gcp/bootstrap/outputs.tf`
- Create: `scripts/run_finops_operator_packet.py`
- Create: `scripts/run_workload_state_packet.py`
- Create: `scripts/collect_finops_budget_evidence.py`
- Create: `scripts/write_finops_budget_receipt.py`
- Create: `scripts/verify_finops_budget_receipt.py`
- Create: `tests/unit/test_finops_budget_receipt.py`
- Create: `deploy/gcp/receipts/templates/finops-budget-receipt.example.json`
- Create: `deploy/gcp/receipts/templates/finops-budget-envelope.example.json`
- Create: `.github/workflows/sign-finops-receipt.yml`
- Modify: `.github/workflows/infrastructure-quality.yml`
- Modify: `infra/policy/predeployment-authority-manifest.json`
- Modify: `scripts/validate_terraform_static.py`
- Modify: `tests/unit/test_terraform_hygiene.py`
- Modify: `tests/unit/test_verify_gcp_foundation.py`
- Modify: `deploy/gcp/staged-plan-approval.md`
- Modify: `deploy/gcp/bootstrap-state-runbook.md`
- Create: `deploy/gcp/finops-state-transfer-runbook.md`
- Modify: `deploy/gcp/receipts/README.md`
- Modify: `infra/gcp/README.md`
- Modify: `CURRENT_WORK.md`, `ROADMAP.md`, `NOTES.md`, `SECURITY.md`, `ARCHITECTURE.md`, `TECHNICAL_REQUIREMENTS.md`, `TECHNOLOGY_DECISIONS.md`, `AGENTS.md`

#### TDD cycle A1 — FinOps root and provider boundary

**Exact nodes:**
- `tests/unit/test_terraform_hygiene.py::test_finops_root_owns_only_the_existing_budget_contract`
- `tests/unit/test_terraform_hygiene.py::test_finops_provider_requires_explicit_billing_project_and_user_project_override`
- `tests/unit/test_terraform_hygiene.py::test_finops_inputs_are_private_no_default_and_outputs_are_value_safe`
- `tests/unit/test_terraform_hygiene.py::test_finops_budget_preserves_complete_existing_posture`

Write these tests first. The first run must fail because `infra/gcp/finops/` does not exist. Minimal GREEN creates only the partial backend, provider, no-default inputs, exact budget, and value-safe outputs. Inputs are billing account, exact full budget resource name for admission/import, workload project, notification-channel resource name, and quota project—no labels. Require the provider's `billing_project` and `user_project_override = true`; prohibit credential/key/impersonation fields.

#### TDD cycle A2 — IAM-isolated state bucket

**Exact nodes:**
- `tests/unit/test_terraform_hygiene.py::test_finops_state_bucket_is_distinct_and_excludes_workload_provisioner`
- `tests/unit/test_terraform_hygiene.py::test_finops_state_bucket_policy_is_exactly_one_object_admin_binding_with_two_distinct_user_members`
- `tests/unit/test_terraform_hygiene.py::test_finops_state_bucket_has_uniform_access_versioning_retention_and_public_denial`
- `tests/unit/test_verify_gcp_foundation.py::test_finops_state_policy_rejects_provisioner_unreviewed_principals_roles_conditions_and_inherited_access`

Minimal GREEN adds one durable FinOps state bucket and one authoritative bucket policy: exactly `roles/storage.objectAdmin` mapped to exactly two distinct privately supplied `user:` principals (operator and recovery), with no other bucket role, member, or condition. It must be a separate bucket—not another prefix in the provisioner-readable workload bucket. Private effective-IAM evidence also binds the complete control-project baseline and proves every prohibited workload identity fails object read/write probes.

#### TDD cycle A3 — Dedicated collector and signed receipt

**Exact nodes:**
- `tests/unit/test_finops_budget_receipt.py::test_operator_runner_rejects_ambient_adc_google_cloudsdk_overrides_impersonation_keys_wif_wrong_account_and_code_or_token_argv`
- `tests/unit/test_finops_budget_receipt.py::test_operator_runner_uses_one_active_authorized_user_and_process_memory_token_for_collection_and_terraform`
- `tests/unit/test_finops_budget_receipt.py::test_operator_runner_binds_transaction_steps_cwd_argv_expiry_approval_nonce_and_output_destinations`
- `tests/unit/test_finops_budget_receipt.py::test_operator_runner_seals_computed_output_digests_only_after_execution`
- `tests/unit/test_finops_budget_receipt.py::test_workload_runner_admits_only_provisioner_readback_and_exact_state_remove_transactions`
- `tests/unit/test_finops_budget_receipt.py::test_domain_runners_reject_cross_identity_cross_backend_and_cross_gate_substitution`
- `tests/unit/test_finops_budget_receipt.py::test_operator_runner_requires_exact_existing_billing_admin_binding_and_complete_policy_etag`
- `tests/unit/test_finops_budget_receipt.py::test_collector_requires_exact_full_budget_resource_name_and_complete_posture`
- `tests/unit/test_finops_budget_receipt.py::test_collector_never_calls_monitoring_api_and_offline_join_requires_exact_state_channel_id`
- `tests/unit/test_finops_budget_receipt.py::test_collector_rejects_display_name_or_duplicate_candidate_authority`
- `tests/unit/test_finops_budget_receipt.py::test_writer_atomically_publishes_owner_only_receipt_and_envelope_directory`
- `tests/unit/test_finops_budget_receipt.py::test_writer_rejects_symlink_hardlink_path_escape_unsafe_ancestor_and_partial_transaction`
- `tests/unit/test_finops_budget_receipt.py::test_writer_detects_parent_rename_and_symlink_replacement_before_each_publication_and_preserves_temp`
- `tests/unit/test_finops_budget_receipt.py::test_verifier_rejects_wrong_signer_issuer_digest_nonce_freshness_and_bindings`
- `tests/unit/test_finops_budget_receipt.py::test_verifier_claims_nonce_once_under_cross_process_lock_and_keeps_claim_on_later_failure`
- `tests/unit/test_finops_budget_receipt.py::test_verifier_is_sole_replay_lock_owner_and_caller_never_prelocks`
- `tests/unit/test_verify_gcp_foundation.py::test_workload_verifier_never_collects_billing_budget_under_provisioner`

Minimal GREEN adds two disjoint manifest-constrained runners. The FinOps runner handles only billing-human collection and FinOps init/import/plan/apply/readback; the workload runner handles only provisioner-owned workload readback and exact-address state removal. B1 remains on the existing bootstrap boundary, while M1 receipt consumption is credential-free and precedes a fresh provisioner migration packet. Each invocation atomically consumes one exact transaction manifest whose primary and `finally` steps bind identity, cwd, argv, environment schema, source/input/backend digests, absent output destinations and schemas, expiry, approval, and nonce; output content hashes are computed and atomically sealed only afterward. Tests reject cross-domain/cross-operation substitution. The FinOps runner requires exact `roles/billing.admin` policy/etag and an active `authorized_user`; the workload runner admits only the proven process-memory provisioner token and no quota override. Receipt persistence and signing follow ADR-0015's descriptor, parent-identity, atomic-publication, and verifier-owned replay-lock rules.

#### TDD cycle A4 — CI, lock, and static enforcement

**Exact nodes:**
- `tests/unit/test_terraform_hygiene.py::test_infrastructure_quality_validates_finops_root_with_pinned_terraform`
- `tests/unit/test_terraform_hygiene.py::test_finops_root_has_its_own_checked_in_google_provider_lock`
- `tests/unit/test_terraform_hygiene.py::test_static_policy_rejects_duplicate_budget_ownership_and_finops_expansion`
- `tests/unit/test_terraform_hygiene.py::test_finops_signer_workflow_has_no_gcp_or_secret_authority`

Extend CI to backend-free initialize/validate all three roots under its existing pinned Terraform `1.15.8`. Generate and commit the FinOps lock under that exact toolchain; do not copy or infer a provider version. Static policy permits one FinOps budget and the exact bootstrap state resources only, while PR A deliberately retains the existing workload budget until transfer.

#### TDD cycle A5 — Transfer safety and current-doc contract

**Exact nodes:**
- `tests/unit/test_terraform_hygiene.py::test_finops_transfer_runbook_enforces_continuous_two_root_freeze`
- `tests/unit/test_terraform_hygiene.py::test_finops_transfer_handles_unknown_import_outcome_by_reading_both_states`
- `tests/unit/test_terraform_hygiene.py::test_finops_transfer_prohibits_state_push_manual_edit_replacement_and_apply`

The runbook requires import-before-remove, exact full resource-name binding, separate approvals, normal locks, pre/post backups, both-state readback for every outcome, and a freeze from PR A merge through PR B closeout. PR A must not edit `infra/gcp/develop/budgets.tf`, workload budget dependencies, or workload billing inputs.

Every operational gate below requires new immutable domain-specific transaction manifest(s), exact independent review, exact approval-record digest, and an atomically consumed nonce per transaction. One gate approval may pre-authorize several explicitly listed domain transactions and their failure-finally readbacks, but no runner or nonce crosses a trust domain or operation class.

### Operational Gate B1 — Create and verify the FinOps state bucket

After PR A merges and exact-tip rebaseline, prepare one bootstrap saved plan whose only non-no-op actions are the reviewed FinOps state bucket and its single authoritative `roles/storage.objectAdmin` binding with exactly the two distinct named-human members. Under separate plan/apply approvals, apply only that binary plan and verify bucket controls, the complete bucket/control-project IAM maps, accountable recovery, and failed object read/write probes for the workload provisioner and every unrelated identity. Stop before FinOps initialization.

### Operational Gate F0/F1/F2 — Transfer state under a continuous freeze

F0 is read-only and binds the exact budget resource name—not display name—the old state, absent new state, live complete posture, all three backends, billing-human credential/permissions, quota project, notification-channel state binding, API, recovery, and freeze. One approval binds two non-interchangeable transactions: a FinOps-human `collect` transaction with a pre-authorized FinOps `readback` finally step through `run_finops_operator_packet.py`, and a provisioner workload `readback` transaction through `run_workload_state_packet.py`. Neither runner can invoke the other's API/backend/identity.

F1 separately approves one FinOps-human `init_import` transaction containing exact init/import primary steps and pre-authorized FinOps `finally` readback, plus a separate provisioner workload-readback transaction/nonce. The gate controller invokes all bound outcome readbacks after success/error; interruption leaves both roots frozen until a separately reviewed recovery-readback packet runs both domain runners. If new-state presence cannot be disproved, no retry or F2 follows.

F2, only after reviewed F1 success, approves one provisioner `state_remove` transaction whose sole mutable step is exact old-address removal and whose `finally` block reads workload state, plus one separate FinOps-human readback transaction/nonce. Both backends are read afterward to prove exactly one owner. The freeze remains through PR B merge. No plan/apply is allowed in either root during source/state skew or dual ownership.

### Implementation PR B — Remove workload ownership after successful state transfer

**Files:**
- Delete: `infra/gcp/develop/budgets.tf`
- Modify: `infra/gcp/develop/cloud_run.tf`
- Modify: `infra/gcp/develop/migration_job.tf`
- Modify: `infra/gcp/develop/variables.tf`
- Modify: `infra/gcp/develop.tf`
- Modify: `infra/gcp/variables.tf`
- Modify: `infra/gcp/develop/outputs.tf`
- Modify: `infra/gcp/outputs.tf`
- Modify: `scripts/validate_terraform_static.py`
- Modify: `scripts/verify_gcp_foundation.py`
- Modify: `tests/unit/test_terraform_hygiene.py`
- Modify: `tests/unit/test_verify_gcp_foundation.py`
- Modify: `deploy/gcp/staged-plan-approval.md`, `deploy/gcp/finops-state-transfer-runbook.md`, `infra/gcp/README.md`
- Modify: `CURRENT_WORK.md`, `ROADMAP.md`, `NOTES.md`, `SECURITY.md`, `ARCHITECTURE.md`, `TECHNICAL_REQUIREMENTS.md`, `TECHNOLOGY_DECISIONS.md`, `AGENTS.md`

**Exact nodes:**
- `tests/unit/test_terraform_hygiene.py::test_workload_root_no_longer_owns_billing_budget`
- `tests/unit/test_terraform_hygiene.py::test_workload_stage_resources_require_finops_receipt_not_budget_dependency`
- `tests/unit/test_terraform_hygiene.py::test_workload_billing_input_is_removed_but_api_enablement_remains_non_destructive`
- `tests/unit/test_verify_gcp_foundation.py::test_workload_verifier_requires_verified_fresh_finops_receipt`
- `tests/unit/test_verify_gcp_foundation.py::test_workload_verifier_rejects_unsigned_stale_or_mismatched_finops_receipt`

These are genuine REDs against PR A because workload ownership remains intentionally present. Minimal GREEN removes only the old resource/input/dependencies, changes the cost-guardrail output to a truthful external signed-gate contract, and routes budget admission through the offline receipt verifier. PR B must not mutate FinOps configuration or state.

#### Exact implementation verification

Run after each named RED→GREEN cycle, then run:

- `env -u PYTHONPATH uv run pytest tests/unit/test_finops_budget_receipt.py tests/unit/test_terraform_hygiene.py tests/unit/test_verify_gcp_foundation.py -q`
- `env -u PYTHONPATH uv run python scripts/validate_terraform_static.py`
- `terraform fmt -check -recursive infra/gcp`
- `env -u PYTHONPATH uv run ruff format --check .`
- `env -u PYTHONPATH uv run ruff check .`
- `env -u PYTHONPATH uv run mypy .`
- reproduce `.github/workflows/infrastructure-quality.yml` locally for bootstrap, workload, and FinOps backend-free init/validate under Terraform 1.15.8
- `git diff --check`
- after commit: `BASE_SHA=$(git merge-base HEAD origin/develop) && gitleaks git --redact --log-opts="$BASE_SHA..HEAD"`

No real backend initialization, state read/import/remove, plan, apply, or cloud call is allowed in either implementation PR.

### Operational Gate F3 — FinOps convergence and signed receipt

Under separate plan and readback approvals, use only gate-specific FinOps-human transactions. The plan transaction binds pre-state/readback, initialization, saved-plan creation, JSON rendering, and post-plan `finally` readback as exact ordered steps; the later collector/readback transaction has its own approval and nonce:

- require active `authorized_user` provenance, selected-token userinfo equality, the exact existing `roles/billing.admin` binding and complete billing policy/etag, exact quota-project `serviceusage.services.use`, exact FinOps bucket policy, and fail-before-call rejection of ADC, inherited `GOOGLE_*`/`CLOUDSDK_*`, impersonation, token/credential/login files, keys, WIF, and code/token argv;
- generate an exact FinOps saved plan with `billing_project` and `user_project_override = true`;
- require zero create/update/delete/replacement actions and value-safe output no-ops;
- do not apply a no-op plan; any provider/state normalization action requires a separate disposition and approval;
- collect the budget by exact full resource name and require the complete USD 100/filter/threshold/spend-basis/channel/default-recipient/schema posture; do not call Monitoring under the FinOps identity, and join the budget routing ID offline to the exact channel ID from separately authorized workload-state evidence;
- publish receipt/envelope atomically under a validated owner-only evidence root, sign only the value-safe envelope through the dedicated no-GCP workflow, verify the detached bundle, publish the ready marker, and leave the nonce unconsumed until one exact downstream plan approval claims it.

### Operational Gate M1 — Regenerate the workload migration plan

Prepare a fresh packet bound to PR B, final transfer evidence, and a newly issued unexpired FinOps receipt. Before workload authentication, the approval recorder invokes—but does not lock around—`env -u PYTHONPATH uv run python scripts/verify_finops_budget_receipt.py --evidence-root <owner-only-absolute-root> --nonce <exact-nonce> --approval-record <exact-reviewed-approval> --consume`. The verifier alone acquires/releases the replay-ledger `flock`, validates parent/ready/approval bindings, and durably creates the atomic final nonce claim. Any verification/claim failure stops before workload authentication. Once claimed, the receipt stays consumed even if M1 later fails and a fresh F3 receipt is required for any successor. The credential-free verifier then exits; a separate fresh provisioner migration-plan packet/transaction performs workload initialization/state/plan steps without process-wide quota attribution. Neither receipt consumption nor M1 uses a FinOps-human runner. Require:

- exact source/toolchain/backend/workspace/input/state bindings;
- complete pre/post-plan state continuity across normal plan locking;
- exactly the reviewed migration-stage managed creates;
- no update/delete/replacement/action invocation;
- only bounded reviewed data reads and output changes;
- absence of budget ownership and all service/tester/Secret-version actions;
- stop after binary/JSON plan admission.

A failure requiring provisioner project-level quota authority is a material stop, not permission to grant it.

### Normal downstream continuation

After M1 plan review, continue ADR-0013 only through separate approvals: exact migration infrastructure apply/readback; database role and database-URL Secret versions; migration execution/schema evidence; service plan/apply; tester access; qualification. Each packet must bind the FinOps receipt. No additional planning PR is required unless a material trigger fires.

## Security and privacy boundaries

- No project-level role for the workload provisioner.
- No ambient user fallback, WIF substitution, service-account key, targeting, refresh bypass, lock bypass, backend migration shortcut, or global quota configuration.
- No private identifiers, state, plans, receipts, credentials, payloads, or raw provider output in Git or ordinary chat.
- State transfer is ownership metadata work, not authority to mutate the budget.
- Synthetic-only deployment remains mandatory; no live/client-derived data or production claim.

## Material replanning triggers

Return to planning if any of these occur:

- the existing budget cannot be imported without replacement or mutation;
- the provider cannot represent the notification channel across roots without exposing or duplicating authority;
- workload planning still requires project-level provisioner quota permission after budget extraction;
- state transfer requires `state push`, manual edits, backend migration, or live budget recreation;
- a non-human billing identity, provider alias, additional environment, or production budget becomes required;
- source decomposition cannot preserve one workload stage root and one budget owner;
- client feedback changes the private synthetic target.

## Explicit non-authority

Acceptance of this plan authorizes planning publication only. It does not authorize implementation before merge, cloud authentication, backend/state operations, import/removal, Terraform plan/apply, budget mutation, database preparation, migration execution, service activation, tester access, qualification, live data, or production.
