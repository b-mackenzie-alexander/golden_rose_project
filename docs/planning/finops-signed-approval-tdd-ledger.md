# Signed FinOps Approval TDD Execution Ledger

**Status:** Historical superseded supporting contract. Its protected publication completed, but ADR-0016's merged 2026-09-09 human-visible addendum suspends this signer/TDD path for fictional-synthetic `develop`; PR #83 merged the replacement source contract. Retain as evidence only.

## Execution rule

Cycle headings are organizational only. Execute each row vertically and in table order, except for the explicit isolated-negative insertion below: add only that exact selector, run it, record the observed RED or honest immediate-pass GREEN classification, make only the named smallest production checkpoint when RED, rerun the exact selector, then run the stated sibling bundle before moving to the next row. After rows 1-2, execute N1-N30 from `docs/planning/finops-signed-approval-negative-fixture-ledger.md` in order before returning to row 3. Do not install a horizontal batch of tests before implementation. A harness/import/setup failure is not a product RED.

The fresh post-amendment base controls classification. Selectively replayed paused-candidate behavior that already satisfies a row is recorded as a GREEN regression; do not weaken source to manufacture RED. The 41-path replay ledger in `docs/planning/finops-pr-a-replay-disposition.md` mechanically controls which later remediation selectors must be recreated.

## R1 — envelope and signer

| Order | Exact selector | Expected first classification | Smallest GREEN checkpoint |
|---:|---|---|---|
| 1 | `tests/unit/test_finops_budget_receipt.py::test_transaction_approval_envelope_is_value_safe_exact_and_domain_bound` | RED: schema/parser absent | Exact 14-string-field schema and value-safe field allowlist only. |
| 2 | `tests/unit/test_finops_budget_receipt.py::test_transaction_approval_rejects_unsigned_wrong_signer_wrong_issuer_and_wrong_source` | RED: signature verifier absent | Fixed approval workflow identity/issuer and exact source SHA comparison. |
| 3 | `tests/unit/test_finops_budget_receipt.py::test_transaction_approval_rejects_malformed_non_object_duplicate_key_and_json_constant` | GREEN aggregate regression after isolated N1-N4 | Preserve UTF-8 object parser with duplicate-key and constant rejection. |
| 4 | `tests/unit/test_finops_budget_receipt.py::test_transaction_approval_rejects_noncanonical_base64_encoded_and_decoded_size_boundaries` | GREEN aggregate regression after isolated N5-N8 | Preserve canonical ASCII base64, 10,924 encoded-byte and 1..8,192 decoded-byte bounds. |
| 5 | `tests/unit/test_finops_budget_receipt.py::test_transaction_approval_rejects_digest_mismatch_missing_extra_and_wrong_type_fields` | GREEN aggregate regression after isolated N9-N14 | Preserve exact field equality, all values exact strings, lowercase SHA/UUID grammar, and envelope byte digest. |
| 6 | `tests/unit/test_finops_budget_receipt.py::test_transaction_approval_timestamp_boundaries_are_exact` | GREEN aggregate regression after isolated N15-N17 | Preserve exact UTC regex/round-trip grammar and accepted +60s/-5m/30m edges; reject adjacent values, expiry, and inversion. |
| 7 | `tests/unit/test_finops_budget_receipt.py::test_transaction_approval_rejects_wrong_domain_operation_unknown_and_receipt_schema_substitution` | GREEN aggregate regression after isolated N18-N20 | Preserve exact four-domain operation map and approval schema; no receipt schema. |
| 8 | `tests/unit/test_terraform_hygiene.py::test_finops_approval_signer_matches_normative_template_and_run_hash` | RED: workflow absent | Byte-copy normative template; bind workflow SHA `6b18814f94c1f3fcac3097c02cc640d610e739ccc6d86d487a9f6a0a1340e6be` and run SHA `ecb7f5e5f038c929bf6240af807e198d09daaeef91d4780806cb72758cf71344`. |
| 9 | `tests/unit/test_terraform_hygiene.py::test_finops_approval_signer_rejects_trigger_input_default_duplicate_and_malformed_yaml_drift` | RED: signer-specific static contract absent | Duplicate-detecting YAML plus exact `workflow_dispatch.inputs`; no defaults/other triggers. |
| 10 | `tests/unit/test_terraform_hygiene.py::test_finops_approval_signer_rejects_environment_if_runner_timeout_concurrency_and_permission_drift` | RED: exact job contract absent | Exact job ID/name/environment/if/runner/timeout/concurrency/permissions. |
| 11 | `tests/unit/test_terraform_hygiene.py::test_finops_approval_signer_rejects_secret_gcp_var_auth_download_reusable_network_terraform_and_gcloud_authority` | GREEN aggregate regression after isolated N21-N29 | Preserve isolated diagnostics for added permissions, `secrets.*`, GCP `vars.*`, auth, download/reusable/network, Terraform, and gcloud. |
| 12 | `tests/unit/test_terraform_hygiene.py::test_finops_approval_signer_rejects_step_inventory_field_action_run_and_artifact_drift` | RED for remaining step fields; extra-output case is GREEN after N30 | Exact ordered three-step inventory, pins, all step fields, run hash, and exact two-file artifact/name/path/retention/failure contract. |

Run the complete R1 selector bundle before R2.

## R2 — signature-first private graph and replay

| Order | Exact selector | Expected first classification | Smallest GREEN checkpoint |
|---:|---|---|---|
| 13 | `tests/unit/test_finops_budget_receipt.py::test_approval_verifier_invalid_bundle_opens_no_private_root_policy_manifest_or_artifact` | RED: verifier absent | Open only value-safe envelope/bundle, verify signature first, and record zero private opens on failure. |
| 14 | `tests/unit/test_finops_budget_receipt.py::test_approval_verifier_binds_signed_policy_manifest_source_input_backend_private_approval_and_claim_root` | RED: private graph resolver absent | After signature/schema success, descriptor-open and compare every signed digest and root fingerprint. |
| 15 | `tests/unit/test_finops_budget_receipt.py::test_approval_verifier_reads_each_private_artifact_once_through_held_no_follow_descriptor` | RED: descriptor ownership absent | One held `O_NOFOLLOW` FD per artifact; hash/parse only held bytes. |
| 16 | `tests/unit/test_finops_budget_receipt.py::test_approval_verifier_owns_flock_o_excl_claim_and_keeps_nonce_consumed_after_failure` | RED: approval replay ledger absent | Verifier-only lock, durable exclusive claim, no removal/overwrite. |
| 17 | `tests/unit/test_finops_budget_receipt.py::test_approval_verifier_rejects_matching_caller_policy_and_digest_without_valid_signature` | RED: raw caller policy remains admissible | No public executable constructor/path from unsigned policy/digest to typed authority. |
| 18 | `tests/unit/test_finops_budget_receipt.py::test_approval_verifier_rejects_claim_root_copy_symlink_rename_hardlink_and_cross_root_replay` | RED: root fingerprint/race coverage absent | Canonical path/device/inode/owner fingerprint, root revalidation, one ledger. |

Run R1+R2 before runner integration.

## R3 — four enforcing domains

| Order | Exact selector | Expected first classification | Smallest GREEN checkpoint |
|---:|---|---|---|
| 19 | `tests/unit/test_finops_budget_receipt.py::test_finops_runner_requires_verified_one_use_finops_approval_before_account_or_token_access` | RED: raw policy path still executable | FinOps runner accepts only claimed typed `finops` authority before account/token loaders. |
| 20 | `tests/unit/test_finops_budget_receipt.py::test_workload_state_runner_requires_verified_one_use_approval_before_token_access` | RED: raw policy path still executable | Workload-state runner accepts only claimed typed authority before token loader. |
| 21 | `tests/unit/test_finops_budget_receipt.py::test_bootstrap_runner_requires_signed_plan_apply_and_readback_approvals` | RED: bootstrap runner absent | New bootstrap runner with only `plan`, `apply`, `readback`; each separate signed claim. |
| 22 | `tests/unit/test_finops_budget_receipt.py::test_workload_plan_runner_requires_signed_migration_plan_approval_and_fresh_finops_receipt_before_token` | RED: workload-plan runner absent | New `workload-plan/migration_plan` runner; approval claim then receipt claim then token. |
| 23 | `tests/unit/test_finops_budget_receipt.py::test_all_runners_reject_other_domain_operation_manifest_policy_source_and_nonce` | RED: four-domain matrix absent | Exact runner/domain/operation/graph equality and cross-product rejections. |
| 24 | `tests/unit/test_finops_budget_receipt.py::test_consumed_transaction_approval_cannot_retry_after_primary_or_finally_failure` | RED: failure ownership incomplete | Keep approval consumed and require fresh signature/nonce after every failure. |
| 25 | `tests/unit/test_finops_budget_receipt.py::test_receipt_signature_and_approval_signature_are_non_interchangeable` | RED: cross-signer matrix absent | Distinct schemas, certificate identities, artifact names and replay ledgers. |

Run R1-R3 before command execution hardening.

## R4 — exact commands and inputs

| Order | Exact selector | Expected first classification | Smallest GREEN checkpoint |
|---:|---|---|---|
| 26 | `tests/unit/test_finops_budget_receipt.py::test_finops_collector_executes_only_repo_bound_script_without_path_lookup` | RED or replayed GREEN regression | Resolve exact repository script; never ambient `PATH`. |
| 27 | `tests/unit/test_finops_budget_receipt.py::test_finops_init_argv_binds_only_exact_backend_descriptor` | RED | Exact init flags and `-backend-config=/dev/fd/<held-fd>` only. |
| 28 | `tests/unit/test_finops_budget_receipt.py::test_finops_import_argv_rejects_extra_flags_state_workspace_and_resource_substitution` | RED | Exact address and full resource ID from signed policy; no trailing args. |
| 29 | `tests/unit/test_finops_budget_receipt.py::test_finops_plan_argv_rejects_destroy_target_refresh_workspace_and_output_substitution` | RED | Exact normal-refresh plan argv and signed output destination only. |
| 30 | `tests/unit/test_finops_budget_receipt.py::test_finops_apply_consumes_only_exact_signed_saved_plan_descriptor` | RED | Exact apply with `/dev/fd/<held-plan-fd>` and signed bytes. |
| 31 | `tests/unit/test_finops_budget_receipt.py::test_finops_and_workload_readbacks_reject_all_extra_state_arguments` | RED or replayed GREEN regression | Exact `terraform state list` only. |
| 32 | `tests/unit/test_finops_budget_receipt.py::test_domain_runners_attempt_every_mandatory_finally_step_and_preserve_first_failure` | RED or replayed GREEN regression | Attempt all pre-authorized finally nodes; retain first error. |

Run R1-R4 before descriptor-race work.

## R5 — held Terraform inputs, outputs and signature components

| Order | Exact selector | Expected first classification | Smallest GREEN checkpoint |
|---:|---|---|---|
| 33 | `tests/unit/test_finops_budget_receipt.py::test_saved_plan_replacement_after_verification_cannot_change_apply_bytes` | RED | Typed authority keeps plan FD open; prelaunch recheck; `/dev/fd`; `pass_fds`; close after child. |
| 34 | `tests/unit/test_finops_budget_receipt.py::test_backend_replacement_after_verification_cannot_change_init_bytes` | RED | Same held-FD custody for backend configuration. |
| 35 | `tests/unit/test_finops_budget_receipt.py::test_domain_runner_output_is_opened_once_and_parsed_hashed_from_held_descriptor` | RED or replayed GREEN regression | One no-follow output FD; parse/hash identical bytes. |
| 36 | `tests/unit/test_finops_budget_receipt.py::test_domain_runner_output_rejects_symlink_hardlink_owner_mode_size_and_replacement_races` | RED | Exact file metadata and replacement race matrix. |
| 37 | `tests/unit/test_finops_budget_receipt.py::test_receipt_and_approval_verifiers_pass_held_envelope_and_bundle_descriptors_to_cosign` | RED or partial GREEN | `/dev/fd` plus explicit `pass_fds` in both verifiers. |
| 38 | `tests/unit/test_finops_budget_receipt.py::test_writers_and_verifiers_revalidate_root_transaction_and_component_inodes_at_each_boundary` | RED or replayed GREEN regression | Reopen requested path/no-follow; compare held identities; preserve race artifacts. |

Run R1-R5 before static/docs closeout.

## R6 — manifest, path, environment and closeout

| Order | Exact selector | Expected first classification | Smallest GREEN checkpoint |
|---:|---|---|---|
| 39 | `tests/unit/test_terraform_hygiene.py::test_authority_manifest_bidirectionally_matches_four_runners_two_signers_and_exact_workflow_steps` | RED | Exact workflow/job/step and script entrypoint equality; missing/extra/duplicate/rename negatives. |
| 40 | `tests/unit/test_terraform_hygiene.py::test_finops_approval_template_and_test_node_inventory_is_exact` | RED | Validator constants exact-check template paths and AST-collected selector set bidirectionally. |
| 41 | `tests/unit/test_terraform_hygiene.py::test_infrastructure_quality_covers_approval_workflow_verifier_runners_and_regressions_without_cloud_authority` | RED | Exact CI paths/commands and no cloud authority. |
| 42 | `tests/unit/test_terraform_hygiene.py::test_finops_transfer_and_staged_runbooks_require_signed_authority_for_all_four_domains` | RED | Gate E0 and B1/F0/F1/F2/F3/M1 signed-domain contracts. |
| 43 | `tests/unit/test_terraform_hygiene.py::test_finops_approval_environment_runbook_defines_exact_configuration_approval_and_readback_gate` | RED: runbook absent | Exact environment name, branch policy, no secrets/vars, reviewer/self-review/admin-bypass posture, stop/readback. |
| 44 | `tests/unit/test_terraform_hygiene.py::test_revised_pr_a_replay_disposition_covers_every_paused_and_new_path` | RED until fresh candidate is assembled | Mechanically compare all 41 rows, additional paths, fresh base and successor handoff; old handoff absent. |

Run all 44 primary selectors plus all 30 isolated negative-fixture selectors, all original A1-A5 selectors, every retained paused-remediation selector named by the replay ledger, and then the complete final verification sequence in the amendment plan.
