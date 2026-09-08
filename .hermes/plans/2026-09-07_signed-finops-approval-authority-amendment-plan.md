# Signed FinOps Transaction Approval Authority Amendment Plan

> **Status:** Accepted; protected publication pending. This planning-only amendment suspends ADR-0015 Implementation PR A until protected merge, exact-tip rebaseline, and separate implementation authorization.

> **For Hermes:** After this packet merges, use merge-aware-coding-rebaseline and plan-driven TDD execution from the exact merged `develop` tip. `docs/planning/finops-signed-approval-tdd-ledger.md` is the normative node-by-node execution ledger, and `docs/planning/finops-pr-a-replay-disposition.md` is the normative path-by-path replay boundary. Do not replay the paused implementation branch wholesale.

**Goal:** Replace self-asserted local policy/approval digests with separately protected, cryptographically signed, one-use transaction authority while preserving the isolated FinOps ownership outcome and every no-cloud/state/plan/apply gate.

**Architecture:** A dedicated protected no-GCP workflow signs one exact value-safe transaction-approval envelope whose digests bind the private policy, complete transaction manifest, source, operation input or saved plan, backend configuration, private approval record, and replay root. A credential-free verifier authenticates that workflow identity, resolves and hashes all private artifacts through held descriptors, and atomically consumes the signed nonce before any of the four exact domain runners can acquire a token or execute a command. Transaction approvals and final FinOps budget receipts remain separate trust domains.

**Tech Stack:** Python 3.12, pytest, Ruff, mypy, GitHub Actions with immutable action pins, GitHub protected environments, keyless Cosign/Sigstore, semantic YAML/static policy, owner-only descriptor-relative filesystem operations, `flock`, and `O_CREAT|O_EXCL` replay claims.

**Boundary:** Planning/source work only. No workflow dispatch, GitHub environment mutation, GCP authentication, real backend initialization, state read/write, import/removal, Terraform plan/apply, resource mutation, commit, push, PR creation, migration, service activation, tester access, qualification, live data, or production action is authorized by drafting this packet.

---

## Trigger and current state

ADR-0015 and its original plan merged through PR #79. PR #80 established protected `develop@c933bfc934d2f61e4c08e077e92cc82af7e017dc`, from which Implementation PR A began. The uncommitted candidate passed the planned A1-A5 source cycles and a large local no-cloud gate, but independent architecture/security rereview found that one caller could supply both a policy or approval artifact and its matching digest. That cannot prove the artifact passed a separate protected approval ceremony.

Beatrice selected the material correction: pause PR A and amend the architecture/plan for a separately protected, cryptographically signed one-use approval envelope. The paused worktree remains preserved and must not be committed or published under the superseded execution assumption.

The same rereview identified four bounded implementation defects—ambient `PATH` collector resolution, weak saved-plan/backend argv binding, pathname-based Cosign verification, and output reopen TOCTOU. Those fixes are included in the revised PR A scope but do not independently authorize continuing the paused branch before this amendment merges.

## Definition of done

This amendment tranche is complete only when:

1. ADR-0016, this plan, and aligned status/index/security documents are independently reviewed, explicitly accepted, and merged through protected `develop`.
2. A fresh revised PR A branch starts from that exact merge and contains no unreviewed carry-over.
3. One dedicated no-GCP approval signer and one credential-free approval verifier establish exact signed authority separate from receipt signing.
4. All four named domain runners require a verified, one-use approval object before token acquisition or command execution.
5. Exact command, saved-plan/backend artifact, collector path, output descriptor, and Cosign descriptor regressions are GREEN.
6. Static policy exact-checks the approval workflow's trigger, environment, inputs, permissions, steps, action pins, run body, artifact output, and separation from the receipt signer.
7. Complete backend-free/no-cloud qualification and independent dual rereview are CLEAN on the revised uncommitted PR A surface.
8. After explicit commit approval, the complete gate passes on the exact committed HEAD, the non-empty range passes diff/Gitleaks checks, and the protected PR's required CI/review passes.
9. Revised PR A merges only under separate authority; the merge is verified and the next gate starts only after exact-tip rebaseline.
10. No operational gate is executed merely because source work merges.

## Normative executable contracts

### Exact signer workflow

`docs/planning/templates/sign-finops-approval.yml` is the complete proposed executable source for future `.github/workflows/sign-finops-approval.yml`, not illustrative pseudocode.

- Complete template SHA-256: `6b18814f94c1f3fcac3097c02cc640d610e739ccc6d86d487a9f6a0a1340e6be`.
- Canonical stripped `Validate and sign exact transaction approval envelope` run-body SHA-256: `ecb7f5e5f038c929bf6240af807e198d09daaeef91d4780806cb72758cf71344`.
- Exact workflow/job identity: `sign-finops-approval` / job ID `sign-approval` / name `Sign value-safe FinOps transaction approval`.
- Exact job contract: `ubuntu-latest`; exact `workflow_dispatch`+protected-`develop` `if`; timeout 10 minutes; non-cancelling per-ref concurrency; environment `finops-approval`; workflow `permissions: {}`; job permissions only `contents: read` and `id-token: write`.
- Exact inputs: required string `approval_envelope_base64` and required string `approval_envelope_sha256`, with no defaults and the template's exact descriptions.
- Exact ordered steps: Install Cosign; validate/sign; upload. No checkout, download, reusable workflow, network fetch command, GCP auth, secret/variable authority, Terraform, or gcloud step.
- Exact immutable actions: `sigstore/cosign-installer@ba7bc0a3fef59531c69a25acd34668d6d3fe6f22` with `cosign-release: "v3.0.6"`; `actions/upload-artifact@330a01c490aca151604b8cf639adc76d48f6c5d4`.
- Exact output: artifact `signed-finops-approval-${{ github.run_id }}`, only `build/finops-approval/approval-envelope.json` and `build/finops-approval/approval-envelope.sigstore.json`, error on missing files, seven-day retention.

Implementation copies that template byte-for-byte. Any future tool-driven formatter delta requires plan disposition and an updated reviewed template/hash before implementation. Static policy exact-checks every workflow/job/step field, the complete template hash, run hash, and manifest parity.

### Exact envelope parser contract

ADR-0016's 14-field string-only schema, strict canonical base64, JSON duplicate/constant rejection, lowercase SHA grammar, exact UTC regex plus parse/round-trip grammar and boundaries, UUIDv4 rule, four-domain operation map, and receipt-schema rejection are literal. Each individual rejection mutation has its own exact selector in `docs/planning/finops-signed-approval-negative-fixture-ledger.md`. The signer and offline verifier share one parser contract and must pass the same fixture matrix; parser divergence is a failure.

### Exact manifest and path inventory contract

The authority manifest remains an executable-authority inventory and gains exact entries for:

- workflows `sign-finops-approval.yml` and `sign-finops-receipt.yml`, with bidirectional workflow/job/ordered-step equality;
- script entrypoints `verify_finops_transaction_approval.py`, `run_finops_operator_packet.py`, `run_workload_state_packet.py`, `run_bootstrap_operator_packet.py`, and `run_workload_plan_packet.py`; and
- all pre-existing executable entries without count reduction or substitution.

Templates and tests do not become execution authority in the manifest. `scripts/validate_terraform_static.py` instead defines exact `REQUIRED_FINOPS_APPROVAL_TEMPLATE_PATHS` and `REQUIRED_FINOPS_APPROVAL_TEST_NODES` constants and compares them bidirectionally to the actual tracked template paths and AST-collected test functions. Missing, extra, duplicate, renamed, or unlisted paths/nodes fail with path-qualified diagnostics.

### Vertical TDD contract

`docs/planning/finops-signed-approval-tdd-ledger.md` supersedes the aggregate RED wording in R1-R6 below. Its 44 primary selectors execute one at a time with per-selector expected first classification and smallest GREEN checkpoint. Immediately after primary rows 1-2, the 30 exact isolated nodes in `docs/planning/finops-signed-approval-negative-fixture-ledger.md` execute one at a time before aggregate rows 3-7 and 11-12. Cycle headings group outcomes only; they never authorize horizontal test batches. The ledgers add explicit FinOps plan/import substitutions, signature-first zero-private-open ordering, held plan/backend races, bootstrap/workload-plan enforcement, individual signer/parser authority negatives, environment readback, and 41-path replay proof.

## Ordered delivery sequence

### Planning amendment PR — publish the corrected trust boundary

**Files:**

- Create: `docs/adr/ADR-0016-signed-finops-approval-authority.md`
- Create: `.hermes/plans/2026-09-07_signed-finops-approval-authority-amendment-plan.md`
- Create after review reconciliation: `docs/review-handoffs/2026-09-07-signed-finops-approval-authority-plan-review-handoff.md`
- Modify: `docs/adr/ADR-0015-finops-budget-ownership-separation.md`
- Modify: `.hermes/plans/2026-09-07_finops-budget-ownership-separation-plan.md`
- Modify: `docs/adr/README.md`
- Modify: `README.md`
- Modify: `infra/gcp/README.md`
- Modify: `deploy/gcp/bootstrap-state-runbook.md`
- Modify: `deploy/gcp/staged-plan-approval.md`
- Modify: `TECHNOLOGY_DECISIONS.md`
- Modify: `CURRENT_WORK.md`
- Modify: `ROADMAP.md`
- Modify: `NOTES.md`
- Modify: `SECURITY.md`
- Modify: `ARCHITECTURE.md`
- Modify: `TECHNICAL_REQUIREMENTS.md`
- Modify: `AGENTS.md`

Planning support files added by this amendment:

- Create: `docs/planning/templates/sign-finops-approval.yml`
- Create: `docs/planning/finops-signed-approval-tdd-ledger.md`
- Create: `docs/planning/finops-signed-approval-negative-fixture-ledger.md`
- Create: `docs/planning/finops-pr-a-replay-disposition.md`
- Create: `deploy/github/finops-approval-environment-runbook.md`

**Required content:**

- preserve PR #79/PR #80 and original A1-A5 evidence as history;
- mark original PR A execution authority suspended because a material trust assumption failed review;
- define the signed envelope, exact signer/verifier/claim ownership, sole-maintainer residual, and revised PR A sequence;
- state that the paused dirty branch is evidence only and is not publication authority;
- preserve every cloud, state, plan/apply, import/removal, migration, service, tester, live-data, and production gate.

**Planning verification:**

- verify all referenced paths exist or are explicitly proposed;
- compute hashes for ADR-0016 and this plan after the substantive review candidate freezes;
- mechanically inventory every tracked/untracked planning file;
- run documentation-governing Terraform hygiene/static tests, Ruff if Python is untouched only as required by existing CI, and `git diff --check`;
- run changed-surface Gitleaks without preserving private output; and
- obtain independent architecture/security, workflow/static-policy, and plan-executability reviews before requesting acceptance/publication authority.

**Hard stop:** No implementation file from the paused PR A worktree enters the planning PR.

### Revised Implementation PR A — signed approval foundation plus original source outcome

Create a fresh valid implementation branch only after the planning amendment merges. Base it on the exact protected merge tip. Reconstruct the reviewed PR A surface; do not merge or commit the paused dirty branch as-is.

**Original PR A files retained:**

- `infra/gcp/finops/{backend.tf,versions.tf,providers.tf,variables.tf,budget.tf,outputs.tf,.terraform.lock.hcl}`
- bootstrap FinOps bucket/IAM variables, resources, outputs, and verifier/static changes
- FinOps/workload runners, collector, receipt writer/verifier, templates, signer, CI, manifest, runbook, living docs, and tests already listed by the original plan

**Amendment files:**

- Create: `.github/workflows/sign-finops-approval.yml`
- Create: `scripts/verify_finops_transaction_approval.py`
- Create: `scripts/run_bootstrap_operator_packet.py`
- Create: `scripts/run_workload_plan_packet.py`
- Create: `deploy/gcp/receipts/templates/finops-transaction-approval-envelope.example.json`
- Modify: `deploy/github/finops-approval-environment-runbook.md`
- Modify: `scripts/run_finops_operator_packet.py`
- Modify: `scripts/run_workload_state_packet.py`
- Modify: `scripts/verify_finops_budget_receipt.py`
- Modify: `scripts/validate_terraform_static.py`
- Modify: `tests/unit/test_finops_budget_receipt.py`
- Modify: `tests/unit/test_terraform_hygiene.py`
- Modify: `.github/workflows/infrastructure-quality.yml`
- Modify: `infra/policy/predeployment-authority-manifest.json`
- Modify: `deploy/gcp/receipts/README.md`
- Modify: `deploy/gcp/finops-state-transfer-runbook.md`
- Modify: review-facing architecture/security/technical/living docs named by the original plan

#### TDD cycle R1 — exact signed approval envelope and protected signer

**Exact nodes to add before implementation:**

- `tests/unit/test_finops_budget_receipt.py::test_transaction_approval_envelope_is_value_safe_exact_and_domain_bound`
- `tests/unit/test_finops_budget_receipt.py::test_transaction_approval_rejects_unsigned_wrong_signer_wrong_issuer_stale_source_and_cross_domain_substitution`
- `tests/unit/test_terraform_hygiene.py::test_finops_approval_signer_is_separate_environment_protected_value_safe_and_no_gcp`
- `tests/unit/test_terraform_hygiene.py::test_finops_approval_signer_static_contract_rejects_trigger_input_environment_permission_step_and_run_drift`

**Execution:** Use primary TDD-ledger rows 1-2, then isolated-negative rows N1-N30, then primary rows 3-12. Each node runs vertically and separately. The aggregate list below is an outcome index only.

**Expected first RED:** approval envelope schema, signer workflow, verifier, workflow manifest/static contracts, and template are absent.

**Minimal GREEN:**

- exact schema fields from ADR-0016 only;
- separate workflow identity and `finops-approval` environment;
- direct base64 envelope plus exact SHA-256 input, no arbitrary artifact/run download;
- protected `develop` ref and `source_sha == GITHUB_SHA`;
- maximum 30-minute validity and domain/operation allowlists;
- immutable Cosign/upload action pins;
- only `contents: read` and `id-token: write`; and
- no GCP auth, secrets, private values, state, Terraform, or receipt-signing interchangeability.

#### TDD cycle R2 — credential-free verification and one-use claim

**Exact nodes:**

- `tests/unit/test_finops_budget_receipt.py::test_approval_verifier_binds_signed_policy_manifest_source_input_backend_private_approval_and_claim_root`
- `tests/unit/test_finops_budget_receipt.py::test_approval_verifier_reads_bundle_and_artifacts_once_through_held_no_follow_descriptors`
- `tests/unit/test_finops_budget_receipt.py::test_approval_verifier_owns_flock_o_excl_claim_and_keeps_nonce_consumed_after_failure`
- `tests/unit/test_finops_budget_receipt.py::test_approval_verifier_rejects_caller_supplied_matching_policy_and_digest_without_valid_bundle`
- `tests/unit/test_finops_budget_receipt.py::test_approval_verifier_rejects_claim_root_copy_symlink_rename_hardlink_and_cross_root_replay`

**Execution:** Use TDD-ledger rows 13-18 sequentially. Signature and fixed signer identity must succeed before any private root, policy, manifest, or artifact is opened or parsed.

**Expected first RED:** no approval verifier or signed replay ledger exists; current raw policy/digest APIs can be called without cryptographic authority.

**Minimal GREEN:** open only the value-safe envelope/bundle first and verify the fixed approval-workflow identity/issuer through descriptor-backed Cosign. After signature/schema success, open the private root and bound artifacts through held no-follow descriptors, validate the exact digest graph and claim-root fingerprint, then claim under verifier-owned `flock` plus `O_CREAT|O_EXCL` and fsync. The typed verified authority result has no ordinary public constructor, contains no token/private evidence, and owns operation-input/backend descriptors until child completion.

#### TDD cycle R3 — require verified authority in all four runners

**Exact nodes:**

- `tests/unit/test_finops_budget_receipt.py::test_finops_runner_requires_verified_one_use_finops_approval_before_account_or_token_access`
- `tests/unit/test_finops_budget_receipt.py::test_workload_runner_requires_verified_one_use_workload_approval_before_token_access`
- `tests/unit/test_finops_budget_receipt.py::test_runner_rejects_approval_for_other_domain_operation_manifest_policy_source_or_nonce`
- `tests/unit/test_finops_budget_receipt.py::test_consumed_approval_cannot_retry_after_command_or_finally_failure`
- `tests/unit/test_finops_budget_receipt.py::test_receipt_signature_cannot_substitute_for_transaction_approval_signature`

**Execution:** Use TDD-ledger rows 19-25 sequentially across four enforcing runners/domains.

**Expected first RED:** runners still accept raw policy/digest inputs, bootstrap/workload-plan runners are absent, and claim roots are caller-selected execution parameters.

**Minimal GREEN:** remove raw caller policy/digest admission from executable CLI paths. FinOps, workload-state, bootstrap, and workload-plan runners receive only verifier-produced authority after durable claim, recheck domain/operation/manifest identity, then perform their reviewed credential ceremony. B1 plan/apply/readback are separate signed bootstrap operations. M1 is exact `workload-plan/migration_plan` and consumes the final FinOps receipt after approval claim but before token acquisition. Any failure consumes the approval.

#### TDD cycle R4 — exact command and immutable artifact execution

**Exact nodes:**

- `tests/unit/test_finops_budget_receipt.py::test_finops_collector_executes_only_repo_bound_script_without_path_lookup`
- `tests/unit/test_finops_budget_receipt.py::test_finops_init_argv_binds_only_exact_backend_artifact`
- `tests/unit/test_finops_budget_receipt.py::test_finops_import_argv_rejects_extra_flags_state_workspace_and_resource_substitution`
- `tests/unit/test_finops_budget_receipt.py::test_finops_plan_argv_rejects_destroy_target_refresh_workspace_and_output_substitution`
- `tests/unit/test_finops_budget_receipt.py::test_finops_apply_consumes_only_exact_signed_saved_plan_bytes`
- `tests/unit/test_finops_budget_receipt.py::test_finops_and_workload_readbacks_reject_all_extra_state_arguments`
- `tests/unit/test_finops_budget_receipt.py::test_domain_runners_attempt_every_mandatory_finally_step_and_preserve_first_failure`

**Expected classification:** the fresh merged-tip branch should reproduce genuine REDs for any hardening not present in protected source. If selective replay of reviewed code makes a node pass before implementation, record it as a GREEN regression rather than manufacturing a failure.

**Execution:** Use TDD-ledger rows 26-32 sequentially.

**Minimal GREEN:** resolve the collector from the reviewed repository script path, exact-match collect/readback/init/import/plan/apply shapes, bind backend init and saved-plan apply to held signed descriptors, reject alternate flags/paths/workspaces/state/target/refresh/destroy forms, and attempt all mandatory finally readbacks.

#### TDD cycle R5 — descriptor-stable output and signature verification

**Exact nodes:**

- `tests/unit/test_finops_budget_receipt.py::test_domain_runner_output_is_opened_once_and_parsed_hashed_from_held_descriptor`
- `tests/unit/test_finops_budget_receipt.py::test_domain_runner_output_rejects_symlink_hardlink_owner_mode_size_and_replacement_races`
- `tests/unit/test_finops_budget_receipt.py::test_receipt_verifier_passes_held_envelope_and_bundle_descriptors_to_cosign`
- `tests/unit/test_finops_budget_receipt.py::test_receipt_writer_and_both_verifiers_revalidate_root_transaction_and_component_inodes_at_each_boundary`

**Execution:** Use TDD-ledger rows 33-38 sequentially, including races that replace the saved plan and backend artifact after verification but before subprocess launch.

**Expected first RED:** protected source still reopens at least some Terraform inputs, outputs, or signature components by pathname.

**Minimal GREEN:** keep signed plan/backend/operation-input FDs alive in typed authority; immediately prelaunch-revalidate and pass only `/dev/fd/<n>` through explicit `pass_fds`; close after child exit. Use one `O_NOFOLLOW` open per output/component, parse/hash the same held bytes, use descriptor-backed Cosign, and revalidate root/transaction/component identities. Preserve race evidence.

#### TDD cycle R6 — CI/static/living-doc closeout

**Exact nodes:**

- `tests/unit/test_terraform_hygiene.py::test_authority_manifest_lists_separate_approval_signer_verifier_and_exact_steps`
- `tests/unit/test_terraform_hygiene.py::test_infrastructure_quality_covers_approval_workflow_verifier_and_regressions_without_cloud_authority`
- `tests/unit/test_terraform_hygiene.py::test_static_policy_rejects_cross_signer_schema_identity_environment_and_artifact_substitution`
- `tests/unit/test_terraform_hygiene.py::test_finops_transfer_runbook_requires_signed_one_use_approval_for_every_domain_transaction`

**Execution:** Use TDD-ledger rows 39-44 sequentially, including exact environment runbook/readback and paused-path replay selectors.

**Minimal GREEN:** exact path/job/step/trigger/input/environment/permission/action/run allowlists, immutable hashes, bidirectional workflow/manifest equality, separate exact test/template inventories, no-cloud PR behavior, Gate E0 runbook, updated operational docs, replay disposition proof, and honest status docs. Do not widen Terraform resource counts or operational authority.

## Revised operational sequence

### Gate E0 — configure and verify approval environment

After revised PR A merges, but before any approval-signer dispatch, separately approve creation/configuration of exact environment `finops-approval` through `deploy/github/finops-approval-environment-runbook.md`. Require protected branches only, no custom branch/tag patterns, no secrets, no variables, no admin bypass where supported, one exact privately held owner reviewer, and truthful `prevent_self_review = false` under the accepted sole-maintainer High. Read back the complete environment and protection rules through GitHub API; any mismatch, missing field, unavailable readback, or unreviewed principal stops. Configuration and readback use a one-use approval whose scope ends at E0; they grant no signing or cloud transaction authority.

Every B1/F0/F1/F2/F3/M1 transaction then requires a fresh signed approval envelope created only after the exact private packet is reviewed. Each domain transaction has its own envelope, Sigstore bundle, approval nonce, transaction nonce, and replay claim. A gate containing multiple transactions lists each separately; no signature or nonce crosses domain or operation.

- B1 uses `bootstrap/plan`, `bootstrap/apply`, and `bootstrap/readback` as three separately signed transactions through `run_bootstrap_operator_packet.py`.
- F0/F1/F2/F3 use only the exact `finops` and `workload-state` operations already assigned to their separate runners; every operation receives its own signed approval.
- M1 uses one `workload-plan/migration_plan` approval through `run_workload_plan_packet.py`. After that approval is verified and durably claimed, the runner verifies and consumes one independently signed fresh FinOps budget receipt before loading a workload token.

The signing ceremony itself is a separate explicit action. Configuring or changing the `finops-approval` environment, dispatching the approval signer, downloading a bundle, starting any runner, authenticating, and performing any backend/state/plan/apply operation each remain within the exact later gate authorization. Planning or source merge never authorizes them.

The final FinOps budget receipt remains a different signed artifact produced after F3 evidence. Downstream M1 must consume both a fresh signed transaction approval and the separately signed, fresh, one-use FinOps budget receipt before workload authentication.

## Verification for revised PR A

The exact closeout order is mandatory:

1. Finish all source, tests, runbooks, living docs, replay ledger disposition, and the mechanically generated fresh implementation handoff.
2. Run all 44 normative ledger selectors one at a time as specified, all original A1-A5 nodes, and every retained paused-candidate remediation selector.
3. Run the complete uncommitted no-cloud gate below.
4. Freeze and inventory the exact tracked/untracked surface; obtain independent architecture/security and Terraform/workflow-static review.
5. Remediate every Blocker/High/Medium finding under new RED→GREEN nodes, rerun the complete gate, and obtain focused rereview. Repeat until CLEAN.
6. Request explicit commit approval. Stage only the mechanically reviewed inventory and run cached diff hygiene.
7. Commit once approved, then rerun the **complete** gate on exact final HEAD; a later code, test, workflow, manifest, runbook, living-doc, or handoff change invalidates that evidence and requires a full rerun.
8. Prove `origin/develop..HEAD` is non-empty; run exact-range diff hygiene and Gitleaks over that complete range.
9. Request explicit push/PR authority, push, open/read back the PR, and require all protected checks and required review evidence on the exact remote head.
10. Merge only under separate authority. Verify the merge commit/protected tip and retired branch, then exact-tip rebaseline before Gate E0 or any successor work.

The complete gate is:

- all 44 amended selectors, all original A1-A5 exact nodes, and every retained replay-ledger selector;
- `env -u PYTHONPATH uv run pytest tests/unit/test_finops_budget_receipt.py tests/unit/test_terraform_hygiene.py tests/unit/test_verify_gcp_foundation.py -q`;
- `env -u PYTHONPATH uv run python scripts/validate_terraform_static.py`;
- Terraform 1.15.8 `fmt -check -recursive infra/gcp`;
- backend-free, readonly-lock init/validate for workload, bootstrap, and FinOps roots;
- `env -u PYTHONPATH uv run ruff format --check .`;
- `env -u PYTHONPATH uv run ruff check .`;
- repository-configured `env -u PYTHONPATH uv run mypy src tests` plus explicit touched-script checking;
- `git diff --check`;
- mechanical proof that workload budget/dependency/billing-input files remain byte-identical to the amended protected base;
- changed-surface Gitleaks before commit;
- mechanical comparison of the actual diff to the accepted path/replay inventories; and
- independent architecture/security plus Terraform/workflow-static review of the exact uncommitted candidate.

Watch local disk before full Terraform-hygiene runs. Remove only explicitly approved run-owned pytest temporary directories if ENOSPC recurs.

## Review focus

Architecture/security review must determine whether:

- a local caller can forge approval by supplying matching artifacts/digests;
- signature verification occurs before private artifact parsing, token acquisition, or command execution;
- signed digests bind the complete private graph and exact claim root;
- replay remains consumed across every failure;
- approval/receipt and FinOps/workload domains are non-interchangeable;
- saved-plan/backend/collector/output/Cosign descriptors remain exact; and
- the sole-maintainer High is stated truthfully rather than presented as closed.

Workflow/static review must probe:

- alternate triggers, refs, source SHAs, environment removal/substitution, permissions, inputs/defaults, duplicate/reordered steps, mutable actions, changed run body, arbitrary artifact downloads, secret/GCP authority, and cross-workflow identity;
- malformed, duplicate-key, or oversized envelopes;
- unknown schema fields and cross-domain operation values; and
- manifest/static drift for every new workflow, script, template, and test path.

Plan-executability review must verify that the amended sequence can be implemented without any operational action and that every later signing/cloud/state gate remains explicit.

## Material replanning triggers

Return to planning if:

- the approval signer needs GCP credentials, private inputs, or repository write authority;
- GitHub environment protection cannot represent the selected ceremony;
- Sigstore cannot verify held descriptors portably on the approved runners;
- the signed envelope cannot bind the exact private graph without disclosing private values;
- one replay root cannot be stable, owner-only, and uniquely fingerprinted;
- a non-human or second-human authority becomes required;
- the revised runner cannot preserve all mandatory outcome readbacks after one-use claim; or
- any state transfer requires state push, manual editing, backend migration, replacement, or unreviewed apply.

## Explicit non-authority

Drafting, reviewing, accepting, or merging this amendment does not itself authorize implementation publication, GitHub environment configuration, signer dispatch, GCP authentication, IAM, bucket creation, backend/state access, plan/apply, import/removal, budget mutation, PR B, migration, service activation, tester access, qualification, live data, or production.
