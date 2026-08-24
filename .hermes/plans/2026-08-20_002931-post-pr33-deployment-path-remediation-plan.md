# Post-PR33 Deployment-Path Remediation Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task only after the planning packet is explicitly accepted and merged. Component reviewers are agent/separate-session quality evidence, not independent human authorization.

**Goal:** Remediate the source-level deployment blockers and material verification gaps found after PR #33 so Golden Rose can truthfully proceed from merged source contracts to separately approved read-only GCP qualification, reviewed staged Terraform plans, foundation apply, first private fictional-synthetic deployment, and post-deployment qualification.

**Architecture:** Keep the lifecycle-independent bootstrap/state root and one disposable workload root, but replace the current all-at-once workload assumption with an explicit staged contract: `foundation` creates no executable Cloud Run workload, `migration` adds the configured migration job only after an immutable image and secret references exist, and `service` adds the configured staff service only after migration evidence passes. Terraform remains desired-state authority; workflow commands may execute or roll forward reviewed resources but must not become an untracked configuration authority. Runtime configuration uses exact non-secret environment values plus exact Secret Manager references; payloads remain out of Terraform source/state, GitHub inputs, logs, chat, and ordinary evidence.

**Tech Stack:** Terraform 1.15.8, Google provider 6.50.0, GCP Cloud Run v2/Jobs, Cloud SQL PostgreSQL 16, Secret Manager, Artifact Registry, Billing Budgets, Cloud Logging/Monitoring, GitHub Actions OIDC/WIF, Python 3.12, uv 0.12.5, pytest, semantic HCL/YAML/JSON policy validation, Gitleaks, CycloneDX, Docker Buildx.

---

## Status, authority, and activation boundary

- **Audit base:** protected `develop@3c0118abb8b84472141992d2238033b1312d5af2`, the PR #33 squash merge.
- **Repository state at plan drafting:** local `develop`, `origin/develop`, and the live remote `develop` ref matched; the worktree was clean.
- **Planning status:** the initial packet was accepted by Beatrice on 2026-08-20 and merged as PR #34 at `develop@63caa4088da44d5f98663bfc2578a0f93444a0fc`. This post-PR34 amendment remains documentation-only; implementation stays blocked until the amended ADR/plan packet passes fresh independent review, publishes through the protected planning workflow, and merges.
- **Required decision amendment:** merged ADR-0013 superseded ADR-0012 for the changed Gate 4/5 staging, Terraform-only configuration ownership, IAM-private tester ingress, narrowed deploy-executor role, direct-workflow WIF separation, mandatory Sigstore provenance/SBOM, and authenticated availability evidence. The unmerged amendment adds exact planning-review remediation nodes; it grants no implementation or cloud authority until it merges.
- **Implementation branch after activation:** fresh `fix/post-pr33-deployment-path-remediation` from the exact planning-packet merge tip.
- **Review truth:** the same-repository-CI High remains open accepted residual risk. Agent and CI evidence do not become independent authorization.
- **Cloud truth:** no GCP authentication or inspection, backend migration, Terraform plan/apply, API enablement, provisioning, image push, secret action, Cloud SQL use, service start, deployment, or live qualification is authorized by this plan or its implementation PR.

## Accepted owner decisions

Beatrice explicitly accepted the following decisions on 2026-08-20. PR #34 merged the initial planning authority; this amendment preserves the decisions while adding required proof nodes and is not implementation authority until it merges:

1. **Staged Terraform authority:** use one workload root with a required no-default `deployment_stage` enum (`foundation`, `migration`, `service`). Gate 4 applies only `foundation`; Gate 5 separately reviews/applies `migration`, executes the configured job, then separately reviews/applies `service`. No broad `workload_enabled` boolean and no imperative resource creation.
2. **First-deployment execution:** Terraform is the sole resource/configuration authority. The build workflow publishes and attests the immutable artifact. The deploy workflow verifies existing Terraform-managed configuration, executes the already configured migration job without overrides, inspects typed readiness, and emits evidence; it does not create resources, mutate configuration, or repair drift.
3. **Tester ingress:** use an IAM-private Cloud Run service with `INGRESS_TRAFFIC_ALL`, mandatory exact service-level named invocation, no `allUsers`/`allAuthenticatedUsers`, and a reviewed loopback proxy/token procedure. Describe this honestly as IAM-private and internet-reachable, not internal-network-only or production staff authentication.
4. **Deploy-executor authority:** grant only `roles/run.jobsExecutor` on the exact migration job and `roles/run.viewer` on the exact migration job and staff service. Forbid `roles/run.developer`, `roles/run.admin`, execution overrides, service-account impersonation, IAM mutation, secret access, provisioning, registry publication, and application invocation.
5. **WIF identity separation:** map and enforce the signed direct-workflow `workflow_ref`. Bind the publisher only to exact `build-image.yml@refs/heads/develop`, the deploy executor only to exact `deploy-develop.yml@refs/heads/develop`, and leave the provisioner without GitHub WIF authority until a separate Terraform-apply workflow is accepted. Remove shared repository-level impersonation and unnecessary Token Creator bindings.
6. **Provenance strength:** require keyless Cosign signatures and signed in-toto attestations bound to the exact image digest, exact build-workflow identity, GitHub OIDC issuer, transparency-log inclusion, SLSA v1 provenance, image-level SBOM, and checksum-bound validated backend/frontend CycloneDX SBOMs. Publication and deployment verify independently; no Medium deferral path remains.
7. **Availability evidence:** add an authenticated Cloud Monitoring HTTPS uptime check against the exact IAM-private service `/readiness` endpoint using the Monitoring service agent with exact service-level invocation. Repeated-failure routing is a provisional develop trigger, not an SLA; request-derived 5xx alerts remain complementary.

## Confirmed finding ledger

| ID | Severity | Finding | Required disposition |
| --- | --- | --- | --- |
| F1 | Blocker | Runtime and migration `GOLDEN_ROSE_*` configuration and secret references are absent from every executable deployment path. | Remediate in Tasks 2–3. |
| F2 | Blocker | Gate 4 says foundation-only/no workload, but the root unconditionally creates the Cloud Run service/job with a required image. | Remediate through staged authority in Tasks 1–2. |
| F3 | Blocker | The current WIF deployer authority does not match a safe executable contract: it lacks existing-job execution/view authority while the workflow imperatively mutates job/service configuration. | Remediate in Tasks 4 and 8 under the accepted non-mutating deploy-executor model. |
| F4 | Blocker | Internal-only ingress has no viable named-human tester or local qualification path. | Implement the accepted IAM-private internet-reachable model in Task 7. |
| F5 | High | Billing budget exists without managed `billingbudgets.googleapis.com` enablement/dependency; the verifier also excludes that API. | Remediate in Task 5. |
| F6 | High/open accepted | Same-repository CI can alter workflows/policy that mint required statuses and cloud credentials. | Preserve as accepted residual risk; do not claim fixed. |
| F7 | High | Repository/ref/environment WIF condition does not enforce provisioner/publisher/deployer workflow separation; the same principal set reaches all three identities. | Remediate in Task 4. |
| F8 | Medium | Foundation verifier compares budget channel resource names to a display name and can reject a correct deployment. | Remediate in Task 6. |
| F9 | Medium | Bootstrap root is not provider-schema validated in CI. | Remediate in Task 9. |
| F10 | Medium | Cloud SQL recovery inputs lack provider-valid upper bounds. | Remediate in Task 5. |
| F11 | Medium | Request-log posture is documentary rather than enforced. | Remediate or narrowly disposition in Task 11. |
| F12 | Medium | Alerts see observed 5xx responses but not an unreachable/silent service; deploy checks `conditions[0]` instead of the typed Ready condition. | Remediate in Tasks 8 and 11. |
| F13 | Medium | Static manifest cardinality counts HCL blocks, not `count`/`for_each` expansion. | Remediate in Task 9. |
| F14 | Medium | Failure evidence files are created only on success; `if: always()` uploads can mask the primary failure with missing-artifact errors. | Remediate in Task 8. |
| F15 | Medium | Current SBOM/provenance evidence is not cryptographically bound to the published image digest. | Implement the accepted mandatory Sigstore remediation in Task 10. |
| F16 | Medium | Direct workflow mutation can leave migration job/schema/service state partially advanced without structured recovery evidence. | Remediate in Tasks 2 and 8; preserve forward-recovery semantics. |
| F17 | Documentation integrity | Living docs still describe the retired branch, PR #33 as open, and ADR-0012/source closeout as pending. | Reconcile in Task 12. |

### Audit-finding classification note

The independent claim that a deploy workflow must itself execute full foundation verification and bounded application qualification is **not adopted as stated**. ADR-0012 deliberately separates deployment (Gate 5) from qualification (Gate 6). The remediation must instead:

- label deployment evidence as deployment-only;
- select and validate the typed Cloud Run Ready condition and reviewed revision/digest;
- never set `qualification_executed: true` during deployment;
- require Gate 6 foundation/database/application qualification before the target is described as qualified.

## Explicit non-goals and hard stops

This remediation does not authorize or implement:

- GCP authentication, read-only inspection, plan/apply, backend migration, provisioning, image push, secret-version creation, migration execution, service start, or tester access;
- project, billing-account, domain, user-email, principal, backend, plan, state, endpoint, or credential values in tracked source;
- secret payloads in Terraform source/state/plans, GitHub variables, workflow inputs/artifacts, chat, screenshots, logs, or ordinary documentation;
- public unauthenticated invocation, real staff identity, live/client-derived data, production resources, production promotion, or legal/compliance claims;
- automatic rollback across an unproven schema compatibility boundary;
- a second-human/CODEOWNER prerequisite or a claim that agent/CI review is independent authorization;
- unrelated product work, staff authentication, OCR/uploads, maps, dashboards, worker records, matching/ranking, or production operations.

## Revised gate model accepted by this plan

1. **Planning acceptance:** accept ADR-0013 plus this plan and merge the documentation-only packet.
2. **Remediation implementation:** complete Tasks 1–13 on one fresh fix branch with no cloud access or service start; merge only after exact-head evidence and owner disposition of Blocker/High findings.
3. **Gate 2 — read-only GCP qualification:** separately approve named projects and read-only commands; gather project/IAM/API/quota/CIDR/collision facts.
4. **Gate 3 — bootstrap/backend and staged plan preparation:** approve bootstrap/backend ceremony and exact non-secret inputs. Produce a reviewed `foundation` plan; no workload resources may appear.
5. **Gate 4 — foundation apply:** apply only the exact `foundation` plan, then run foundation-mode verification. No image, secret payload, job, service, migration, or tester access.
6. **Gate 5A — immutable publication and secret/database preparation:** approve exact image publication; create payload-bearing secret versions and database login roles out of band; verify value-safe references/authority.
7. **Gate 5B — migration activation:** review/apply exact `migration` plan; verify configured job identity/image/secret references; execute once under advisory-lock authority; capture schema/compatibility evidence.
8. **Gate 5C — service activation:** only after successful migration evidence, review/apply exact `service` plan; verify named invoker, runtime configuration, revision/digest, and typed Ready status.
9. **Gate 6 — qualification:** run foundation/database/application qualification, access/log/alert/cost/recovery checks, and browser/accessibility/English/Spanish walkthroughs. Only this gate may establish “private GCP develop target qualified with fictional synthetic data.”

Passing one gate never grants the next.

---

### Task 0: Publish and accept the planning amendment

**Objective:** Establish explicit planning authority for the changed staged deployment, runtime configuration, IAM, and tester-access contracts before code changes.

**Files:**
- Create: `docs/adr/ADR-0013-post-pr33-deployment-path-remediation.md`
- Modify: `docs/adr/README.md`
- Modify: `CURRENT_WORK.md`
- Modify: `ROADMAP.md`
- Modify: `NOTES.md` by appending a new 2026-08-20 entry at the bottom of the dated evidence run
- Modify: `SECURITY.md`
- Modify: `TECHNOLOGY_DECISIONS.md`
- Modify: `ARCHITECTURE.md`
- Modify: `README.md`
- Modify: `GIT_WORKFLOW.md`
- Modify separately after explicit protected-file approval: `AGENTS.md`
- Review: `.hermes/plans/2026-08-20_002931-post-pr33-deployment-path-remediation-plan.md`

**Steps:**

1. Create accepted ADR-0013 with the seven owner decisions above, rejected alternatives, gate changes, consequences, and explicit no-cloud authority.
2. Reconcile living docs to observed PR #33 merge truth while marking remediation implementation blocked on planning acceptance.
3. Preserve the PR #33 review handoff as historical evidence; add a merged/superseded notice rather than rewriting its observed commands.
4. Run independent architecture/Terraform, IAM/WIF, workflow/supply-chain, and documentation consistency reviews of the planning packet.
5. Record every finding and Beatrice disposition; revise the packet until no undispositioned Blocker/High remains.
6. Record Beatrice’s 2026-08-20 explicit acceptance of ADR-0013 and this plan.
7. Publish and merge the documentation-only planning PR through protected `develop`.
8. Stop. Re-fetch/prune and rebaseline before implementation; planning merge grants no cloud authority.

**Verification:**

- `git diff --check origin/develop...HEAD`
- exact-range Gitleaks over the planning commit range
- repository Markdown/path-reference checks
- protected `enforce`, `check`, and `application` statuses

**Expected result:** accepted merged planning authority with truthful post-PR33 status; no product/Terraform/workflow implementation and no cloud action.

---

### Task 1: Freeze the staged authority model in tests and policy

**Objective:** Make `foundation → migration → service` resource authority fail closed before changing Terraform behavior.

**Files:**
- Modify: `infra/policy/predeployment-authority-manifest.json`
- Modify: `scripts/validate_terraform_static.py`
- Modify: `tests/unit/test_terraform_hygiene.py`
- Modify: `infra/gcp/variables.tf`
- Modify: `infra/gcp/develop/variables.tf`

**RED tests to add:**

- `test_deployment_stage_accepts_only_foundation_migration_or_service`
- `test_foundation_stage_contract_forbids_cloud_run_service_and_job`
- `test_migration_stage_contract_allows_job_but_forbids_service`
- `test_service_stage_contract_requires_job_and_service`
- `test_static_validator_rejects_unconditional_executable_workload_resources`
- `test_static_validator_rejects_boolean_workload_shortcut`
- `test_foundation_stage_does_not_require_or_resolve_container_image_digest`
- `test_local_stage_inventory_evaluator_rejects_job_or_service_in_foundation`

**Steps:**

1. Add failing source-contract tests for the exact enum and monotonic stage order.
2. Run each exact node and confirm a behavioral RED against the unconditional current resources—not an import/setup failure.
3. Add root/module `deployment_stage` variables with one exact allowlist and no default. Make the image digest nullable only for `foundation`, require it for `migration` and `service`, and ensure the foundation path never resolves the managed image local.
4. Extend semantic policy so reviewed stage expressions are allowlisted exactly and arbitrary `count`/`for_each` expansion remains rejected.
5. Require the manifest to declare stage ownership for executable resources instead of relying only on block count.
6. Add a narrow local evaluator for the only reviewed stage expressions and make it prove the evaluated foundation/migration/service inventories; do not call a configuration graph an inventory proof.
7. Run focused tests and the complete Terraform hygiene suite.

**Commands:**

```text
env -u PYTHONPATH uv run pytest tests/unit/test_terraform_hygiene.py::<exact-node> -q
env -u PYTHONPATH uv run pytest tests/unit/test_terraform_hygiene.py -q
env -u PYTHONPATH uv run --locked python scripts/validate_terraform_static.py
terraform fmt -check -recursive infra/gcp
```

**Expected GREEN:** invalid/ambiguous stage authority fails closed; no cloud command is run.

---

### Task 2: Stage Cloud Run job/service creation without losing Terraform authority

**Objective:** Ensure foundation apply contains no executable workload, migration job creation precedes service creation, and Terraform remains the source of desired configuration.

**Files:**
- Modify: `infra/gcp/develop.tf`
- Modify: `infra/gcp/develop/cloud_run.tf`
- Modify: `infra/gcp/develop/migration_job.tf`
- Modify: `infra/gcp/develop/iam.tf`
- Modify: `infra/gcp/develop/outputs.tf`
- Modify: `infra/gcp/outputs.tf`
- Modify: `tests/unit/test_terraform_hygiene.py`
- Modify: `scripts/verify_gcp_foundation.py`
- Modify: `tests/unit/test_verify_gcp_foundation.py`

**RED tests to add:**

- `test_foundation_graph_contains_no_cloud_run_job_or_service`
- `test_migration_graph_contains_job_without_service_or_invoker_binding`
- `test_service_graph_contains_job_service_and_named_invoker_binding`
- `test_stage_outputs_do_not_reference_absent_resources_unsafely`
- `test_foundation_verifier_mode_rejects_present_workload`
- `test_deployment_verifier_mode_requires_expected_job_and_service`
- `test_stage_plan_receipt_rejects_wrong_stage_source_lock_or_image_digest`

**Steps:**

1. Build graph probes from clean copied roots with partial backend omitted exactly as existing graph tests do; treat them as structural evidence only, not evaluated inventory evidence.
2. Confirm RED because current Terraform always includes both resources.
3. Gate migration job creation on `migration` or `service`; gate service and service-level invoker IAM on `service` only.
4. Make outputs stage-safe without leaking endpoints, project IDs, principals, or secret references.
5. Add explicit verifier modes (`foundation`, `migration`, `service`) so Gate 4 expects no executable workload and Gate 5 expects only the stage-authorized inventory.
6. Ensure teardown/rebuild semantics cover monotonic promotion and an explicitly reviewed reverse transition; do not automate schema rollback.
7. Define the Gate 3+ saved-plan receipt contract: stage, source SHA, plan hash, provider-lock digest, non-secret-input digest, evaluated inventory, approval reference, and workload image digest where applicable. A later separately approved saved plan must be inspected through `terraform show -json` before approval/apply; this remediation task only tests/parses the value-safe receipt shape and does not run `terraform plan`.
8. Run clean-copy init/validate/graph for every stage with fictional shape-valid non-secret inputs.

**Expected GREEN:** Gate 4’s plan can be proven free of job/service resources; later stages add only their reviewed resource set.

---

### Task 3: Wire exact runtime and migration configuration safely

**Objective:** Make the migration job and service capable of starting from reviewed Terraform configuration while keeping payloads out of source/state.

**Files:**
- Modify: `infra/gcp/develop/secrets.tf`
- Modify: `infra/gcp/develop/iam.tf`
- Modify: `infra/gcp/develop/cloud_run.tf`
- Modify: `infra/gcp/develop/migration_job.tf`
- Modify: `infra/gcp/develop/variables.tf`
- Modify: `infra/gcp/variables.tf`
- Modify: `infra/gcp/develop.tf`
- Modify: `infra/gcp/develop/outputs.tf`
- Modify: `infra/gcp/outputs.tf`
- Modify: `scripts/validate_terraform_static.py`
- Modify: `tests/unit/test_terraform_hygiene.py`
- Modify: `deploy/gcp/first-deployment-runbook.md`

**Required configuration contract:**

- Service secret reference: `GOLDEN_ROSE_DATABASE_URL` → runtime-only database URL secret.
- Migration secret reference: `GOLDEN_ROSE_DATABASE_URL` → migration-only database URL secret.
- Shared or separately justified secret reference: `GOLDEN_ROSE_SYNTHETIC_STAFF_ID`.
- Exact non-secret values: `GOLDEN_ROSE_ENVIRONMENT=develop`, `GOLDEN_ROSE_AUTH_MODE=synthetic`, `GOLDEN_ROSE_DEPLOYMENT_TARGET=gcp-develop-private-synthetic`.
- Operator-held, reviewed non-secret label: `GOLDEN_ROSE_PUBLIC_ENVIRONMENT_LABEL` containing “non-production” and “synthetic”.
- Exact digest marker: `GOLDEN_ROSE_DEPLOYED_IMAGE_DIGEST` must equal the image digest in the same reviewed stage plan.
- Migration-only non-secret role marker: `GOLDEN_ROSE_MIGRATION_ASSUMED_ROLE=golden_rose_schema_owner` unless ADR-0013 accepts a different exact reviewed identifier.

**RED tests to add:**

- `test_service_has_complete_exact_develop_configuration_contract`
- `test_migration_job_has_complete_exact_develop_configuration_contract`
- `test_runtime_and_migration_use_distinct_database_secret_ids`
- `test_digest_environment_marker_is_bound_to_container_image_digest`
- `test_static_validator_allows_only_reviewed_secret_reference_shapes`
- `test_static_validator_rejects_literal_secret_values_and_unlisted_env_names`
- `test_static_validator_rejects_cross_wired_runtime_and_migration_database_secrets`
- `test_runtime_and_migration_secret_iam_is_per_secret_and_rejects_collection_wide_access`

**Steps:**

1. Replace the broad prohibition on any Cloud Run env/secret reference with an exact allowlist; retain rejection of literal payloads, unknown secret IDs, unknown env names, `value` for payload-bearing settings, and arbitrary version selectors.
2. Split runtime and migration database secret metadata so each identity can receive only its own login material, and replace collection-wide secret IAM with explicit or narrowly keyed per-secret bindings. Shared synthetic-staff identity access requires an exact separately justified binding.
3. Add exact secret-reference blocks and exact non-secret env blocks to the stage-authorized resources.
4. Bind image and `GOLDEN_ROSE_DEPLOYED_IMAGE_DIGEST` to the same Terraform input.
5. Update the runbook with a non-echoing, source-controlled reference-binding ceremony and exact value-safe verification. Do not include payload commands or identifiers.
6. Prove plan/state documentation still warns that Secret Manager references are safe metadata but payloads must never enter Terraform.

**Expected GREEN:** a configured migration job/service can satisfy `Settings`; no payload exists in source, Terraform variables, outputs, or ordinary evidence.

---

### Task 4: Enforce deployer and WIF authority separation

**Objective:** Give each automation identity only the authority its reviewed workflow needs and enforce workflow identity at the cloud trust boundary.

**Files:**
- Modify: `infra/gcp/bootstrap/wif.tf`
- Modify: `infra/gcp/bootstrap/iam.tf`
- Modify: `infra/gcp/bootstrap/outputs.tf`
- Modify: `infra/gcp/develop/iam.tf`
- Modify: `infra/gcp/develop/variables.tf`
- Modify: `infra/gcp/variables.tf`
- Modify: `infra/gcp/develop.tf`
- Modify: `infra/policy/predeployment-authority-manifest.json`
- Modify: `scripts/validate_terraform_static.py`
- Modify: `scripts/verify_gcp_foundation.py`
- Modify: `tests/unit/test_terraform_hygiene.py`
- Modify: `tests/unit/test_verify_gcp_foundation.py`
- Modify: `deploy/gcp/bootstrap-state-runbook.md`

**RED tests to add:**

- `test_wif_service_accounts_cannot_share_repository_only_impersonation_authority`
- `test_publisher_trust_requires_exact_build_image_workflow_ref`
- `test_deployer_trust_requires_exact_deploy_develop_workflow_ref`
- `test_provisioner_trust_is_disabled_or_bound_to_an_accepted_exact_workflow_ref`
- `test_deploy_executor_has_exact_job_execution_and_job_service_viewer_roles`
- `test_deploy_executor_cannot_update_resources_override_jobs_impersonate_service_accounts_publish_images_manage_iam_read_secrets_or_provision_foundation`
- `test_foundation_verifier_rejects_substituted_wif_pool_or_provider`
- `test_foundation_verifier_requires_exact_authority_specific_workflow_claims`
- `test_wif_provider_requires_workflow_dispatch_event`

**Steps:**

1. Confirm current official OIDC claims and pinned-provider IAM behavior before implementation; record version-sensitive facts in ADR-0013/handoff, not as assumptions.
2. Map `attribute.workflow_ref = assertion.workflow_ref` and enforce the exact direct publisher/deploy workflow references plus repository/owner/ref/environment/event conditions.
3. Bind image-publisher and deploy-executor service-account impersonation to their different exact `workflow_ref` principal sets; remove repository-only shared impersonation.
4. Remove `roles/iam.serviceAccountTokenCreator` from the ordinary WIF paths unless an exact separately reviewed operation proves it necessary.
5. Remove GitHub WIF impersonation from the provisioner until a separately accepted Terraform-apply workflow exists.
6. Grant the deploy executor only exact-job `roles/run.jobsExecutor` and exact job/service `roles/run.viewer`; reject `roles/run.developer`, `roles/run.admin`, `roles/run.jobsExecutorWithOverrides`, and service-account-user/token-creator authority.
7. Derive expected deploy-executor/publisher principals from `control_plane_project_id` plus reviewed account names rather than accepting arbitrary caller strings as authority.
8. Extend foundation verification to validate exact pool/provider/workflow/ref/environment conditions and all effective bindings.
9. Add literal negative fixtures for `push`, `schedule`, `pull_request`, and missing event claims; only `workflow_dispatch` is accepted.

**Expected GREEN:** a qualifying publisher workflow cannot impersonate deploy executor/provisioner, the provisioner has no dormant GitHub WIF path, and the deploy executor can inspect the exact resources and execute only the configured migration job without overrides or configuration mutation.

---

### Task 5: Close API and provider-input plan failures

**Objective:** Make accepted non-secret inputs survive source validation and ensure every Terraform-managed API dependency is explicit.

**Files:**
- Modify: `infra/gcp/develop/apis.tf`
- Modify: `infra/gcp/develop/budgets.tf`
- Modify: `infra/gcp/variables.tf`
- Modify: `infra/gcp/develop/variables.tf`
- Modify: `scripts/validate_terraform_static.py`
- Modify: `scripts/verify_gcp_foundation.py`
- Modify: `tests/unit/test_terraform_hygiene.py`
- Modify: `tests/unit/test_verify_gcp_foundation.py`

**RED tests to add:**

- `test_budget_api_is_managed_and_budget_depends_on_it`
- `test_approved_api_inventory_includes_billing_budgets`
- `test_transaction_log_retention_rejects_zero_and_values_above_seven`
- `test_retained_backups_rejects_zero_and_values_above_365`
- `test_root_and_module_recovery_validations_are_identical`

**Steps:**

1. Add `billingbudgets.googleapis.com` to the reviewed API set and explicit budget dependency ordering.
2. Update the static manifest/verifier exact API inventories in the same node.
3. Constrain standard Cloud SQL PostgreSQL transaction-log retention to the current provider/API-supported 1–7 range and retained backups to 1–365, verifying current official docs at implementation time.
4. Add boundary tests at 1, 7, 8, 365, and 366.
5. Keep final operator selections Gate 2/3 inputs; do not invent RTO/RPO.

**Expected GREEN:** invalid recovery values fail during source validation and budget creation no longer depends on ambient API state.

---

### Task 6: Correct live foundation verifier representations and staged evidence

**Objective:** Ensure the read-only verifier accepts correct live GCP response shapes and rejects actual drift for each stage.

**Files:**
- Modify: `scripts/verify_gcp_foundation.py`
- Modify: `tests/unit/test_verify_gcp_foundation.py`
- Modify: `deploy/gcp/evidence-template.md`
- Modify: `scripts/validate_terraform_static.py`
- Modify: `infra/policy/predeployment-authority-manifest.json`

**RED tests to add:**

- `test_budget_channel_resource_name_is_resolved_to_expected_channel_identity`
- `test_display_name_cannot_substitute_for_budget_channel_resource_name`
- `test_foundation_mode_rejects_job_or_service_inventory`
- `test_migration_mode_requires_configured_job_and_no_service`
- `test_service_mode_requires_reviewed_revision_digest_configuration_and_iam`
- `test_verifier_rejects_missing_or_extra_required_api_by_stage`
- `test_verifier_rejects_arbitrary_deployer_principal_not_derived_from_control_plane_project`

**Steps:**

1. Preserve raw notification-channel resource names from the Budget API.
2. Resolve/compare stable channel resource identity and separately compare display name; do not compare unlike fields.
3. Replace synthetic fixtures that model the wrong live response shape with captured value-safe schema fixtures or official API-shape fixtures.
4. Add stage-aware inventory/IAM/configuration checks from Tasks 2–5.
5. Ensure evidence remains redacted and descriptor-safe.

**Expected GREEN:** a correct fixture modeled after live API responses passes; mismatched channel/resource/principal/stage fixtures fail closed.

---

### Task 7: Implement the accepted named-tester access boundary

**Objective:** Make the chosen ingress model actually reachable by approved testers without making the service publicly invokable.

**Files:**
- Modify: `infra/gcp/develop/cloud_run.tf`
- Modify: `infra/gcp/develop/iam.tf`
- Modify: `infra/gcp/develop/variables.tf`
- Modify: `infra/gcp/variables.tf`
- Modify: `scripts/validate_terraform_static.py`
- Modify: `scripts/verify_gcp_foundation.py`
- Modify: `scripts/qualify_develop_deployment.py`
- Modify: `tests/unit/test_terraform_hygiene.py`
- Modify: `tests/unit/test_verify_gcp_foundation.py`
- Modify: `tests/unit/test_qualify_develop_deployment.py`
- Modify: `deploy/gcp/private-tester-access.md`
- Modify: `deploy/gcp/first-deployment-runbook.md`

**RED tests for the recommended IAM-private decision:**

- `test_service_uses_accepted_iam_private_ingress_not_unreachable_internal_only_posture`
- `test_named_invoker_is_required_and_public_invokers_remain_forbidden`
- `test_qualification_contract_requires_reviewed_authenticated_proxy_or_token_path`
- `test_foundation_verifier_distinguishes_network_reachability_from_iam_privacy`
- `test_private_tester_runbook_does_not_claim_internal_network_privacy`
- `test_tester_authority_rejects_substituted_extra_empty_group_domain_principal_set_and_public_invokers`
- `test_qualification_failure_writes_minimized_atomic_failure_evidence`

**Steps:**

1. Implement only the ingress model accepted in ADR-0013.
2. For IAM-private ingress, retain Cloud Run IAM authentication and only exact review-bound individual tester identities; reject group, domain, principal-set, broad, and public invokers. Document network reachability honestly.
3. Define an operator-held, review-bound tester-authority artifact/fingerprint and authenticated tester/proxy procedure without endpoints, emails, or token values in tracked source. Terraform and the verifier must compare the effective binding to that reviewed authority rather than an arbitrary caller-provided principal.
4. Keep bearer tokens off command lines and out of evidence.
5. Initialize a minimized failure qualification result before the first request, atomically update the failed boundary and teardown/rebuild disposition on handled failure, then exit nonzero without raw transport/error values.
6. Add live Gate 6 checks for both network reachability and IAM denial/allow behavior.
7. If internal-only is selected instead, replace these paths/tests with the accepted in-project runner/load-balancer/VPN/IAP resources and recalculate cost/authority before implementation.

**Expected GREEN:** the documented qualification path is viable under the exact Terraform ingress/IAM contract and remains non-public at the authorization layer.

---

### Task 8: Make deploy workflow evidence failure-safe and stage-aware

**Objective:** Prevent workflow-driven configuration drift, preserve partial-failure evidence, and distinguish deployment completion from qualification.

**Files:**
- Modify: `.github/workflows/deploy-develop.yml`
- Modify: `infra/policy/predeployment-authority-manifest.json`
- Modify: `scripts/validate_terraform_static.py`
- Modify: `tests/unit/test_terraform_hygiene.py`
- Modify: `deploy/gcp/rollback-forward-recovery-runbook.md`
- Modify: `deploy/gcp/first-deployment-runbook.md`

**RED tests to add:**

- `test_deploy_workflow_refuses_resources_not_already_at_reviewed_terraform_configuration`
- `test_deploy_workflow_selects_ready_condition_by_type`
- `test_deploy_workflow_binds_ready_revision_to_reviewed_digest`
- `test_deploy_workflow_initializes_failed_result_before_cloud_mutation`
- `test_deploy_workflow_updates_failed_stage_and_recovery_disposition_on_error`
- `test_always_uploads_do_not_fail_when_early_stage_evidence_is_absent`
- `test_deploy_evidence_never_claims_gate6_qualification`
- `test_privileged_jobs_have_bounded_timeouts`
- `test_deploy_rejects_missing_or_mismatched_reviewed_stage_plan_receipt`

**Steps:**

1. Write the failure-result skeleton before the first cloud mutation, with `result=failed`, current stage, `qualification_executed=false`, and no sensitive values.
2. Use trap/finalization behavior that preserves the primary failure and uploads whatever bounded evidence exists without a second missing-file failure.
3. Verify a value-safe reviewed-stage-plan receipt before execution: exact stage, source SHA, plan hash, provider-lock digest, approval reference, evaluated inventory, and authorized image digest. Reject a missing, wrong-stage, wrong-source, wrong-plan-hash, wrong-lock, or wrong-digest receipt; publication evidence alone is insufficient.
4. Verify the migration job/service are already Terraform-created and configured for the reviewed digest before execution/readiness inspection; do not let gcloud introduce unmodeled image, env, secret-reference, IAM, ingress, scaling, or network drift.
5. Select Cloud Run condition `type=Ready`, bind the ready revision/image digest to reviewed evidence, and keep `/readiness` plus bounded workflow qualification in Gate 6.
6. Capture pre-migration job/service digest and schema-compatibility posture as recovery evidence; do not automate unsafe rollback.
7. Add bounded job timeout and command-level timeouts where current CLIs support them.
8. Preserve serialization and publish-run head-SHA binding.

**Expected GREEN:** every failure stage yields a value-safe primary result, deployment success means only deployment readiness, and qualification remains explicitly false/pending.

---

### Task 9: Harden static cardinality and exact CI parity

**Objective:** Make policy cardinality reflect expanded Terraform behavior and validate both roots in required CI.

**Files:**
- Modify: `scripts/validate_terraform_static.py`
- Modify: `tests/unit/test_terraform_hygiene.py`
- Modify: `infra/policy/predeployment-authority-manifest.json`
- Modify: `.github/workflows/infrastructure-quality.yml`
- Modify: `.github/workflows/application-quality.yml` if needed to keep one required exact gate

**RED tests to add:**

- `test_manifest_rejects_unbounded_count_on_allowed_resource_type`
- `test_manifest_rejects_unbounded_for_each_on_allowed_resource_type`
- `test_manifest_accepts_only_reviewed_stage_expansion_expressions`
- `test_infrastructure_workflow_initializes_and_validates_workload_and_bootstrap_roots`
- `test_bootstrap_validation_failure_blocks_the_required_quality_path`

**Steps:**

1. Parse and evaluate only the narrow reviewed static expansion forms; reject arbitrary expressions rather than pretending block count equals resource count.
2. Represent stage-specific maximum expanded counts in the manifest.
3. Add bootstrap `init -backend=false -input=false -lockfile=readonly` and `validate` to CI beside workload validation.
4. Preserve exact Terraform 1.15.8 and Google provider 6.50.0 lockfile checks.
5. Ensure one protected required path exercises the complete static/bootstrap/workload contract; do not rely solely on an optional path-filtered check.

**Expected GREEN:** bootstrap provider-schema drift and resource-expansion policy drift fail before merge.

---

### Task 10: Strengthen or explicitly disposition image/SBOM provenance

**Objective:** Bind deploy evidence to the exact image and accurately state the supply-chain assurance level.

**Files:**
- Modify: `.github/workflows/build-image.yml`
- Modify: `.github/workflows/deploy-develop.yml`
- Modify: `scripts/verify_image_provenance.py`
- Modify: `tests/unit/test_image_provenance.py`
- Modify: `scripts/validate_terraform_static.py`
- Modify: `tests/unit/test_terraform_hygiene.py`
- Modify: `infra/policy/predeployment-authority-manifest.json`
- Modify: `deploy/gcp/evidence-template.md`
- Modify: `docs/security/dependency-purpose-license-review.md` if assurance claims change

**RED tests required for the accepted cryptographic/OCI binding:**

- `test_publish_evidence_binds_source_commit_builder_and_subject_digest`
- `test_backend_and_frontend_sboms_are_attached_or_attested_to_exact_digest`
- `test_deploy_rejects_valid_sbom_from_different_digest`
- `test_deploy_rejects_unsigned_or_untrusted_provenance`
- `test_local_pr_mode_does_not_overclaim_publish_attestation`
- `test_deploy_rejects_unsigned_or_untrusted_image_sbom_attestation`
- `test_deploy_rejects_unsigned_or_untrusted_application_sbom_checksum_attestation`
- `test_deploy_rejects_wrong_attestation_subject_predicate_identity_issuer_or_transparency_proof`
- `test_image_sbom_is_schema_valid_linux_amd64_digest_bound_and_nonempty`

**Steps:**

1. Confirm current Cosign/Sigstore and Artifact Registry behavior against the exact private-repository boundary before implementation; do not substitute an unverified registry attachment shape.
2. Pin the Cosign installer/action and Cosign version immutably.
3. Sign the exact pushed digest keylessly and require the exact protected build-workflow certificate identity, GitHub Actions OIDC issuer, and transparency-log inclusion.
4. Generate and sign SLSA v1 provenance bound to the exact repository commit and reviewed builder.
5. Generate and validate an image-level SBOM with a dedicated validator mode or verifier: schema-valid, `linux/amd64`, root identity equal to the immutable digest, and nonempty final-image component inventory. Reject application-only, wrong-platform, or wrong-digest documents before signing.
6. Bind validated backend/frontend CycloneDX SBOM checksums to a signed in-toto attestation on the same digest.
7. Verify signature, subject, identity, issuer, transparency inclusion, provenance, image SBOM, and application SBOM checksums immediately after publication and independently before migration execution. Require the same trust checks for every attestation class.
8. Keep signing/provenance output value-safe and prevent secret-bearing build arguments or application content from entering attestations.
9. Make `linux/amd64` target explicit in build commands and tests so local ARM and CI builds share one intended deployment architecture.

**Expected GREEN:** exact-digest signature and attestation verification passes at publication and deployment; no checksum-only or workflow-success fallback is accepted.

---

### Task 11: Enforce log minimization and no-traffic availability evidence

**Objective:** Turn observability posture markers into behavior and detect an unreachable/silent service.

**Files:**
- Modify: `infra/gcp/develop/observability.tf`
- Modify: `infra/gcp/develop/variables.tf`
- Modify: `infra/gcp/variables.tf`
- Modify: `infra/gcp/develop.tf`
- Modify: `scripts/verify_gcp_foundation.py`
- Modify: `tests/unit/test_verify_gcp_foundation.py`
- Modify: `scripts/validate_terraform_static.py`
- Modify: `tests/unit/test_terraform_hygiene.py`
- Modify: `deploy/gcp/evidence-template.md`

**RED tests to add:**

- `test_stronger_request_log_posture_has_enforceable_exclusion_or_is_rejected`
- `test_uuid_bearing_staff_paths_are_not_retained_in_routine_request_logs`
- `test_authenticated_readiness_uptime_check_targets_exact_cloud_run_service`
- `test_monitoring_service_agent_has_only_exact_service_invocation`
- `test_availability_alert_detects_repeated_authenticated_readiness_failure`
- `test_foundation_verifier_requires_authenticated_readiness_uptime_check`
- `test_alert_evidence_does_not_claim_approved_slo_or_rto`
- `test_uptime_check_and_monitoring_invoker_are_absent_before_service_stage`
- `test_service_stage_has_exactly_one_uptime_check_and_monitoring_invoker`

**Steps:**

1. Confirm what Cloud Run request-log fields can be excluded or routed under the chosen ingress/access model.
2. Implement an exact exclusion/minimization control or remove the unsupported stronger marker; never leave a documentary value that implies behavior.
3. Add an HTTPS Cloud Monitoring uptime check targeting the exact Cloud Run service `/readiness` endpoint with Service Agent Authentication only in `service`; foundation and migration must contain neither the check nor its alert/invoker dependencies.
4. Grant the Monitoring service agent only exact service-level `roles/run.servicesInvoker` or the current narrow equivalent containing `run.routes.invoke`, only in `service`; continue to reject public/broad invokers.
5. Send no business/synthetic-user payload, query data, request body, or application secret; validate only stable readiness status/content and latency.
6. Alert on repeated check failure through the operator-held route. Keep thresholds as provisional develop review triggers, not SLOs or client commitments.
7. Retain request-derived 5xx alerts as complementary evidence and reject an unnecessary Service Directory private check, synthetic-monitor function, or unauthenticated health path for this target.
8. Extend foundation/qualification verification to prove the configured check, exact monitoring invoker, recent observation, and alert route.

**Expected GREEN:** the selected log posture changes actual logging behavior, and a silent/unreachable target has a reviewable alert path.

---

### Task 12: Reconcile all living docs and produce a fresh remediation handoff

**Objective:** Replace stale PR #33/feature-branch status with truthful merged-but-remediation-blocked posture and prepare exact review evidence.

**Files:**
- Modify: `CURRENT_WORK.md`
- Modify: `ROADMAP.md`
- Modify: `NOTES.md` by appending at the bottom of the dated evidence run
- Modify: `SECURITY.md`
- Modify: `TECHNICAL_REQUIREMENTS.md`
- Modify: `TECHNOLOGY_DECISIONS.md`
- Modify: `ARCHITECTURE.md`
- Modify: `README.md`
- Modify: `GIT_WORKFLOW.md`
- Modify: `docs/adr/README.md`
- Modify separately with explicit protected-file approval: `AGENTS.md`
- Modify: `infra/gcp/README.md`
- Modify: `deploy/gcp/bootstrap-state-runbook.md`
- Modify: `deploy/gcp/first-deployment-runbook.md`
- Modify: `deploy/gcp/private-tester-access.md`
- Modify: `deploy/gcp/rollback-forward-recovery-runbook.md`
- Modify: `deploy/gcp/teardown-rebuild-runbook.md`
- Create: `deploy/gcp/staged-plan-approval.md`
- Add completion/supersession notice: `docs/review-handoffs/2026-08-16-consolidated-predeployment-closeout-review-handoff.md`
- Create: `docs/review-handoffs/2026-08-20-post-pr33-deployment-path-remediation-review-handoff.md`

**Required status truth:**

- PR #33 merged at `3c0118a`; its branch is retired.
- PR #33 completed its source-controlled implementation lane but post-merge audit found substantiated deployment-path Blocker/High findings.
- ADR-0013 and this plan govern the bounded remediation after acceptance.
- Same-repository CI remains High/open accepted residual risk.
- No cloud action occurred during remediation.
- Gate 2 remains separately owner-approved; Gate 3+ remain blocked until remediation merges and exact findings are closed/dispositioned.
- Historical plans/handoffs retain their observed evidence and are marked historical/superseded rather than silently rewritten.

**Steps:**

1. Search authoritative Markdown for stale feature branch, open PR #33, “awaiting review,” “local closeout pending,” “proposed ADR-0012,” and pre-remediation Gate 4/5 language.
2. Update current/living surfaces; add notices to historical surfaces.
3. Append observed test/review evidence only after all commands finish; do not edit while final-head gates run.
4. Create `deploy/gcp/staged-plan-approval.md` as the value-safe procedure for every future stage transition: saved binary plan custody, JSON inventory, source/lock/non-secret-input/plan digests, stage and workload digest binding, explicit approval record, post-apply verifier, and reverse-transition destruction review. It must preserve the separate approval boundary and contain no live values.
5. Create a handoff with exact base/head, changed-path manifest, finding ledger/dispositions, component reviews, test evidence, deferred Gate 2+ facts, and explicit no-cloud statement.
6. Run path-reference and diff hygiene.

**Expected GREEN:** no authoritative living surface presents PR #33 as open or the deployment path as ready for plan/apply.

---

### Task 13: Full no-cloud qualification, independent rereview, and closeout

**Objective:** Prove the complete remediation at an immutable committed head before PR merge.

**Files:**
- Verification only after Task 12; modify only if a surfaced defect requires a new TDD remediation cycle.

**Verification order:**

1. Focused exact-node RED/GREEN evidence for every finding.
2. Full Terraform hygiene suite.
3. Locked static validator.
4. Terraform formatting.
5. Clean-checkout workload root `init -backend=false -input=false -lockfile=readonly` and `validate`.
6. Clean-checkout bootstrap root `init -backend=false -input=false -lockfile=readonly` and `validate`.
7. Clean-copy graph probes plus local evaluated-inventory checks for `foundation`, `migration`, and `service` stages.
8. Focused verifier/provenance/qualification/workflow tests, including stage-plan-receipt, per-secret IAM, tester-authority, qualification-failure-evidence, monitoring-stage, and every-attestation trust-boundary matrices.
9. Full Python format/lint/mypy/Bandit/application suite with disposable PostgreSQL and expected fail-closed downgrade proof.
10. Frontend lock validation, verify/build, audit, and schema-validated SBOM.
11. Backend dependency audit and schema-validated SBOM.
12. Local `linux/amd64` image build plus reviewed provenance mode.
13. `git diff --check` and working-tree Gitleaks before closeout commit.
14. Commit the reviewed scope; freeze the surface.
15. Exact-head rerun of the complete mandatory gate and exact-range Gitleaks.
16. Independent component reviews:
    - staged Terraform graph/gate authority;
    - IAM/WIF/deployer/ingress security;
    - runtime secret-reference/database authority;
    - workflow/provenance/failure recovery;
    - API/budget/logging/monitoring/verifier live-shape behavior;
    - documentation/residual-risk/gate consistency.
17. Beatrice dispositions every substantiated Blocker/High finding.
18. Fresh cross-lane rereview verifies every original F1–F17 disposition against current source.
19. Push exact reviewed head, open PR, monitor only latest-head required checks, resolve conversations, and merge only after explicit Beatrice approval.

**Minimum expected evidence:**

- zero undispositioned Blocker/High findings;
- all Medium findings remediated or explicitly accepted with scope/mitigation;
- both Terraform roots provider-schema valid;
- stage graphs and evaluated inventories match the revised gate model;
- future Gate 3+ transition records require the reviewed stage-plan receipt and explicit approval before apply or deploy execution;
- no environment identifier, principal, backend value, plan, state, endpoint, credential, or payload in the committed range;
- clean exact-range secret scan and diff hygiene;
- no cloud authentication, plan/apply, provisioning, image push, secret action, service start, deployment, or live data;
- living docs state that merge grants only a request for separately approved Gate 2 read-only qualification.

---

## 2026-08-21 amendment A — review-confirmed transition authority repairs

**Authority:** Beatrice accepted this amendment after the independent review of `6e11635` confirmed that the initial F1–F17 implementation left receipt production/transport, exact-resource deploy IAM, tester-authority anchoring, direct OCI evidence verification, stage separation, full drift checks, and uptime live-shape verification incomplete.

**Scope:** This remains a no-cloud remediation. It authorizes only tracked source/docs/tests for the following exact contracts; receipt signing, protected environment configuration, all Terraform plan/apply work, publication, deployment, and live verification stay separate gates.

1. Add a signed operator-held stage-plan receipt transport: manual deploy dispatch supplies receipt and detached Sigstore bundle; the workflow performs fresh `cosign verify-blob` against an operator-held protected certificate identity before parsing it. The publication workflow must not create or upload a plan-approval receipt.
2. Split deploy selection into exactly `migration` and `service`. Migration validates only its own receipt and Terraform-owned job projection then executes the job. Service validates its own receipt plus a separately signed migration-success receipt bound to the migration receipt hash and image digest, then validates only the Terraform-owned service projection and readiness.
3. Replace project-scoped deployer grants with Cloud Run v2 job/service IAM-member resources: executor on only `run-migrations`; viewer on that job and `staff-tracer`; reject project-level deployer `run` grants in the static validator and live verifier.
4. Introduce the review-bound named-tester receipt interface. Terraform inputs require a derived exact user principal and immutable authority SHA-256; verifier inputs include the operator-held receipt/bundle and independently verify/derive the principal before accepting live IAM. Add substitute-principal negatives.
5. Replace self-authored provenance/SBOM claim files with fresh Cosign signature and attestation verification against the digest. Preserve and parse raw verified output; obtain the final-image SBOM only from its OCI attestation and reject self-authored JSON or wrong signed subject/predicate.
6. Add normalized Terraform configuration projections for migration job and service to signed stage receipts, and compare every reviewed execution-affecting field before job execution/readiness.
7. Expand the foundation verifier snapshot from uptime display names to complete uptime configuration and exact project-number-derived Monitoring service agent. Reject wrong host/path/TLS/auth/project-agent fixtures.
8. Correct committed living docs and replace stale exact-head claims with a new final-head handoff only after the remediation commit and final verification are complete.

**Required regression evidence:** fixture-driven workflow producer/consumer interoperability; digest-free foundation variable admission and migration/service digest rejection; signed-receipt and tester-authority substitute negatives; deployer resource-IAM scope negatives; direct-Cosign output/self-authored-JSON negatives; migration/service separation and projection-drift negatives; authenticated uptime full-shape negatives; and a full no-cloud rerun on the new committed head.

---

## Likely changed-path surface

The implementation plan is intentionally bounded to these families:

```text
docs/adr/ADR-0013-post-pr33-deployment-path-remediation.md
docs/adr/README.md
.hermes/plans/2026-08-20_002931-post-pr33-deployment-path-remediation-plan.md
infra/gcp/backend.tf                         # inspect only unless staged backend contract requires a reviewed change
infra/gcp/variables.tf
infra/gcp/develop.tf
infra/gcp/develop/variables.tf
infra/gcp/develop/cloud_run.tf
infra/gcp/develop/migration_job.tf
infra/gcp/develop/secrets.tf
infra/gcp/develop/iam.tf
infra/gcp/develop/apis.tf
infra/gcp/develop/budgets.tf
infra/gcp/develop/observability.tf
infra/gcp/develop/outputs.tf
infra/gcp/outputs.tf
infra/gcp/bootstrap/wif.tf
infra/gcp/bootstrap/iam.tf
infra/gcp/bootstrap/outputs.tf
infra/policy/predeployment-authority-manifest.json
.github/workflows/application-quality.yml
.github/workflows/infrastructure-quality.yml
.github/workflows/build-image.yml
.github/workflows/deploy-develop.yml
scripts/validate_terraform_static.py
scripts/verify_gcp_foundation.py
scripts/verify_image_provenance.py
scripts/qualify_develop_deployment.py
tests/unit/test_terraform_hygiene.py
tests/unit/test_verify_gcp_foundation.py
tests/unit/test_image_provenance.py
tests/unit/test_qualify_develop_deployment.py
deploy/gcp/*.md
CURRENT_WORK.md
ROADMAP.md
NOTES.md
SECURITY.md
TECHNICAL_REQUIREMENTS.md
TECHNOLOGY_DECISIONS.md
ARCHITECTURE.md
README.md
GIT_WORKFLOW.md
AGENTS.md
docs/review-handoffs/*.md
```

No file outside this surface may be added merely for convenience. Any required new workflow, Terraform root, provider dependency, custom role, executable script, or product-code change requires a plan amendment and fresh owner acceptance before implementation.

## Risks and tradeoffs

- **Staged-root complexity:** one stage enum is less structurally isolated than three independent roots, but avoids cross-state duplication and keeps one workload state authority. Exact graph/policy tests are mandatory.
- **Multiple Gate 5 plans:** migration-before-service requires separate reviewed state transitions. This adds operator ceremony but prevents service startup against unknown schema state.
- **IAM-private ingress:** internet network reachability with mandatory IAM is simpler and cheaper than a load balancer/VPN, but it is not internal-network privacy. Wording, threat model, tester instructions, and owner acceptance must be explicit.
- **Narrow deploy-executor roles:** exact-job execution plus exact-resource viewing should satisfy the accepted non-mutating workflow; any unexpected permission denial is a stop-and-review event rather than grounds for `roles/run.developer`.
- **WIF claim coupling:** exact direct-workflow `workflow_ref` bindings add provider/verifier complexity and must be updated deliberately if workflows become reusable or paths change.
- **Provenance tooling:** mandatory cryptographic OCI/Sigstore evidence improves binding but adds action/tool, registry, transparency-log, and verification dependencies; no checksum-only fallback is accepted.
- **Authenticated monitoring invoker:** the Monitoring service agent becomes an additional exact service invoker that must be derived, inventoried, and verified without broadening human/application access.
- **Logging exclusions:** aggressive URL-log exclusion can reduce incident evidence. Minimize UUID-bearing paths while preserving value-safe status/latency/error telemetry.
- **No automated schema rollback:** forward recovery or synthetic teardown/rebuild remains safer when compatibility is unknown; the plan must not manufacture downgrade authority.
- **Solo-maintainer concentration:** all compensating controls remain defense in depth; none converts Beatrice’s own repository/cloud authority into independent approval.

## Planning-packet completion criteria

This accepted plan is ready for implementation activation only when:

- ADR-0013 exists and is internally consistent with ADR-0009/ADR-0012;
- Beatrice explicitly accepted all seven owner decisions on 2026-08-20;
- every F1–F17 finding has a planned remediation or explicit proposed residual-risk disposition;
- staged Gate 4/5 authority is unambiguous and migration precedes service activation;
- Terraform remains desired-state authority for executable resource configuration;
- tester ingress wording matches real network and IAM behavior;
- no unavailable second-human prerequisite is introduced;
- no project/user/billing/principal/backend/plan/state/endpoint/credential/payload value is committed;
- independent planning reviews find no undispositioned Blocker/High issue;
- the planning-only PR merges through protected `develop`;
- implementation starts only from the exact resulting merge tip.

## Stop boundary after remediation merge

A successful remediation merge authorizes only a request for separately approved Gate 2 read-only GCP qualification. It does not authorize backend initialization/migration, Terraform plan/apply, API enablement, provisioning, image publication, secret injection, database login creation, migration execution, Cloud Run activation, tester access, qualification, real identity, live/client data, public unauthenticated access, or production.
