# Signed FinOps Approval Isolated Negative-Fixture Ledger

**Status:** Historical superseded supporting contract. Its protected publication completed, but ADR-0016's merged 2026-09-09 human-visible addendum suspends this signer/fixture path for fictional-synthetic `develop`; PR #83 merged the replacement source contract. Retain as evidence only.

## Execution rule

These 30 isolated negative nodes remove wrong-reason ambiguity from the aggregate R1 rows in `docs/planning/finops-signed-approval-tdd-ledger.md`. Execute N1-N30 vertically, in order, immediately after main-ledger row 2 and before main-ledger row 3. For each node: add only the named selector and its single mutation, run it and observe the stated RED, make only the named smallest GREEN checkpoint, rerun the selector, then rerun the already-GREEN positive signer/envelope selectors. Main-ledger rows 3-7 and 11-12 run afterward as aggregate regression bundles, not as substitutes for these isolated nodes.

A parser/setup/import error, rejection for a different mutation, or a test that combines two listed mutations is not the required RED. All signer and offline-verifier parser nodes use the same fixture against both entrypoints and must assert the same rejection class without logging or reflecting input values.

## Parser/schema isolation

| ID | Exact selector | Sole first mutation and expected RED | Smallest GREEN checkpoint |
|---:|---|---|---|
| N1 | `tests/unit/test_finops_budget_receipt.py::test_transaction_approval_rejects_malformed_json_alone` | Truncate otherwise-valid JSON; RED because malformed JSON is not rejected deterministically by the shared parser. | Reject malformed UTF-8 JSON with one constant value-safe diagnostic. |
| N2 | `tests/unit/test_finops_budget_receipt.py::test_transaction_approval_rejects_non_object_json_alone` | Replace the valid object with `[]`; RED because a non-object reaches field validation. | Require the decoded top level to be exactly a JSON object. |
| N3 | `tests/unit/test_finops_budget_receipt.py::test_transaction_approval_rejects_duplicate_key_alone` | Duplicate only `approval_nonce`; RED because last-key-wins parsing accepts it. | Duplicate-detecting object-pairs hook shared by signer and verifier. |
| N4 | `tests/unit/test_finops_budget_receipt.py::test_transaction_approval_rejects_json_constant_alone` | Replace one otherwise-valid string with `NaN`; RED because a JSON constant is admitted or fails for the wrong reason. | Reject `NaN`, `Infinity`, and `-Infinity` at JSON parse time. |
| N5 | `tests/unit/test_finops_budget_receipt.py::test_transaction_approval_rejects_noncanonical_base64_alone` | Add valid-but-noncanonical padding/whitespace to an otherwise-valid encoding; RED because permissive decoding accepts it. | ASCII-only strict decode plus canonical re-encode equality. |
| N6 | `tests/unit/test_finops_budget_receipt.py::test_transaction_approval_rejects_encoded_size_limit_plus_one_alone` | Supply exactly 10,925 encoded bytes; RED because the encoded input bound is absent. | Reject encoded input above 10,924 bytes before decoding. |
| N7 | `tests/unit/test_finops_budget_receipt.py::test_transaction_approval_rejects_empty_decoded_envelope_alone` | Canonically encode zero bytes; RED because an empty decoded envelope is admitted to parsing. | Require decoded length at least one byte before JSON parsing. |
| N8 | `tests/unit/test_finops_budget_receipt.py::test_transaction_approval_rejects_decoded_size_limit_plus_one_alone` | Canonically encode 8,193 decoded bytes; RED because the decoded bound is absent. | Reject decoded input above 8,192 bytes. |
| N9 | `tests/unit/test_finops_budget_receipt.py::test_transaction_approval_rejects_envelope_digest_mismatch_alone` | Change only the expected envelope SHA-256; RED because caller-matched digest metadata is trusted. | Recompute exact decoded-envelope bytes and compare one lowercase SHA-256. |
| N10 | `tests/unit/test_finops_budget_receipt.py::test_transaction_approval_rejects_missing_field_alone` | Remove only `policy_sha256`; RED because missing fields are tolerated or fail non-deterministically. | Require exact equality with the 14-field schema. |
| N11 | `tests/unit/test_finops_budget_receipt.py::test_transaction_approval_rejects_extra_field_alone` | Add only `project_id`; RED because extra fields are tolerated. | Reject any key outside the exact 14-field schema before value use. |
| N12 | `tests/unit/test_finops_budget_receipt.py::test_transaction_approval_rejects_wrong_field_type_alone` | Change only `domain` from string to integer; RED because coercion or later logic accepts it. | Require every one of the 14 values to be an exact JSON string. |
| N13 | `tests/unit/test_finops_budget_receipt.py::test_transaction_approval_rejects_noncanonical_sha256_alone` | Uppercase only one valid digest; RED because noncanonical SHA grammar is accepted. | Require exactly 64 lowercase hexadecimal characters for every SHA field. |
| N14 | `tests/unit/test_finops_budget_receipt.py::test_transaction_approval_rejects_noncanonical_uuidv4_alone` | Uppercase only an otherwise-valid UUIDv4 nonce; RED because UUID normalization is implicit. | Parse UUIDv4 and require exact lowercase-hyphenated round-trip equality. |
| N15 | `tests/unit/test_finops_budget_receipt.py::test_transaction_approval_rejects_noncanonical_timestamp_alone` | Remove zero padding from one UTC timestamp component; RED because `%Y-%m-%dT%H:%M:%SZ` parsing alone accepts it. | Exact regex plus parse and exact UTC `strftime` round-trip equality. |
| N16 | `tests/unit/test_finops_budget_receipt.py::test_transaction_approval_rejects_timestamp_boundary_plus_one_alone` | Move only `issued_at` one second beyond an accepted future/age boundary; RED because the adjacent rejection is absent. | Enforce exact +60-second and -5-minute issuance bounds and reject boundary+1. |
| N17 | `tests/unit/test_finops_budget_receipt.py::test_transaction_approval_rejects_expiry_window_boundary_plus_one_alone` | Set only the validity window to 30 minutes plus one second; RED because the maximum window is not exact. | Require `0 < expires_at - issued_at <= 30 minutes` and current time before expiry. |
| N18 | `tests/unit/test_finops_budget_receipt.py::test_transaction_approval_rejects_wrong_domain_operation_pair_alone` | Pair `bootstrap` with `migration_plan`; RED because domain and operation are validated independently. | Enforce the exact four-domain operation map. |
| N19 | `tests/unit/test_finops_budget_receipt.py::test_transaction_approval_rejects_unknown_domain_alone` | Replace only `domain` with `unknown`; RED because unknown domains are not fail-closed. | Allow exactly `finops`, `workload-state`, `bootstrap`, and `workload-plan`. |
| N20 | `tests/unit/test_finops_budget_receipt.py::test_transaction_approval_rejects_receipt_schema_substitution_alone` | Supply a valid receipt envelope in place of approval schema; RED because trust-domain schema identity is not enforced. | Require exact approval schema and reject receipt fields before signature authority construction. |

## Workflow-authority isolation

| ID | Exact selector | Sole first mutation and expected RED | Smallest GREEN checkpoint |
|---:|---|---|---|
| N21 | `tests/unit/test_terraform_hygiene.py::test_finops_approval_signer_rejects_added_permission_alone` | Add only `actions: read`; RED because the permission map is not exact. | Exact workflow `{}` and exact job `{contents: read, id-token: write}` permissions. |
| N22 | `tests/unit/test_terraform_hygiene.py::test_finops_approval_signer_rejects_secret_reference_alone` | Add only one `secrets.*` reference; RED because secret expression use is not rejected independently. | Reject any secret expression anywhere in the workflow tree. |
| N23 | `tests/unit/test_terraform_hygiene.py::test_finops_approval_signer_rejects_gcp_variable_reference_alone` | Add only one GCP authority-bearing `vars.*` reference; RED because environment authority can be caller-selected. | Reject the exact forbidden GCP variable namespaces anywhere in the workflow tree. |
| N24 | `tests/unit/test_terraform_hygiene.py::test_finops_approval_signer_rejects_gcp_auth_action_alone` | Add only one GCP-auth action; RED because an extra pinned action can gain cloud authority. | Exact allowed action identities plus explicit GCP-auth rejection. |
| N25 | `tests/unit/test_terraform_hygiene.py::test_finops_approval_signer_rejects_artifact_download_action_alone` | Add only one artifact-download action; RED because caller-selected prior-run input can re-enter. | Exact three-step inventory and explicit artifact-download rejection. |
| N26 | `tests/unit/test_terraform_hygiene.py::test_finops_approval_signer_rejects_reusable_workflow_alone` | Add only job-level reusable-workflow `uses`; RED because job shape is not exact. | Forbid job-level `uses` and require the exact ordinary job fields. |
| N27 | `tests/unit/test_terraform_hygiene.py::test_finops_approval_signer_rejects_network_fetch_command_alone` | Append only one `curl` command to the canonical run body; RED because exact-body or network-command policy is absent. | Require canonical run hash and explicit network-fetch command rejection. |
| N28 | `tests/unit/test_terraform_hygiene.py::test_finops_approval_signer_rejects_terraform_command_alone` | Append only one `terraform` command to the canonical run body; RED because Terraform execution can enter the signer. | Require canonical run hash and explicit Terraform command rejection. |
| N29 | `tests/unit/test_terraform_hygiene.py::test_finops_approval_signer_rejects_gcloud_command_alone` | Append only one `gcloud` command to the canonical run body; RED because GCP CLI authority can enter the signer. | Require canonical run hash and explicit gcloud command rejection. |
| N30 | `tests/unit/test_terraform_hygiene.py::test_finops_approval_signer_rejects_extra_output_file_alone` | Add one third artifact output path while retaining both approved files; RED because subset checking accepts it. | Exact two-file artifact path set, order, name, retention, and missing-file behavior. |

## Completion

R1 is incomplete unless all 30 isolated nodes and main-ledger rows 1-12 have each been run separately under the stated sequence. Static inventory must compare this exact selector set bidirectionally with `REQUIRED_FINOPS_APPROVAL_TEST_NODES`; missing, extra, duplicate, renamed, or unlisted nodes fail closed. The aggregate selectors remain useful regression matrices but cannot supply RED evidence for any isolated node above.
