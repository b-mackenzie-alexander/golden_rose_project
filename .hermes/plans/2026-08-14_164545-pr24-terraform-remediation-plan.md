# PR #24 Terraform remediation implementation plan

> Planning packet only. Do not implement from this branch. The later implementation requires a fresh branch from the exact merged `develop` tip, explicit authorization, strict RED → GREEN execution, independent review, and protected promotion.

**Status:** Accepted planning boundary; implementation not authorized
**Date:** 2026-08-14
**Planning base:** `origin/develop` at `8dc1198c0eb571ca39e9f4814bb3af5e33079890` (PR #25 merge)
**Planning branch:** `docs/pr24-remediation-plan`
**Controlling decision:** `docs/adr/ADR-0010-pr24-terraform-remediation-boundary.md`
**Review handoff:** `docs/review-handoffs/2026-08-14-pr24-remediation-plan-review-handoff.md`

## Goal

Remediate all seven findings from the independent final-head review of PR #24 without authenticating to GCP or granting provisioning/deployment authority. The resulting implementation must remain a backend-free, validate-without-apply scaffold that produces trustworthy static evidence.

The remediation order is mandatory because the first two findings govern whether later CI evidence can be trusted:

1. required-CI authority — High;
2. semantic static-policy enforcement — High;
3. deterministic `uv` selection — Medium;
4. private Cloud Run → Cloud SQL path — Medium;
5. API activation ordering — Medium;
6. Cloud SQL automated-backup baseline — Medium;
7. managed Artifact Registry image authority — Medium.

## Hard boundaries

The planning and later implementation slices do not authorize:

- GCP login, credential discovery, project/API inspection, or any cloud API call;
- Terraform backend configuration or migration, `terraform plan`, or `terraform apply`;
- API enablement, provisioning, IAM mutation, service-account creation, or GitHub policy mutation from the planning branch;
- image build/push, database migration, Cloud SQL use, Cloud Run deployment, service start, public ingress, real identity, live/client data, or production work;
- bootstrap/state/WIF implementation; that remains a separate packet after this remediation merges and is independently cleared;
- invented project IDs, billing IDs, account names, reviewer identities, user emails, domains, credentials, secret payloads, RTO/RPO, backup retention, or production policy.

Only fictional synthetic fixtures may be added. Terraform checks remain `fmt`, backend-disabled `init`, `validate`, `graph`, semantic policy validation, and tests.

## Mandatory governance prerequisite

This repository is currently a private personal repository with one administrator, classic branch protection, no rulesets, no GitHub environments, and no independent collaborator or external status producer. A same-repository GitHub Actions job cannot become non-self-authorizing merely by changing its status name: a PR can edit the workflow that emits that status.

The selected authority model is therefore a real non-author reviewer:

- Beatrice must nominate an independently controlled GitHub account belonging to another accountable person, grant it repository write access, and approve its CODEOWNER responsibility before the implementation branch starts.
- The reviewer must not be the PR author, the last pusher, an alternate account controlled by the author, an agent acting with the author's credentials, or an optional bot whose check can be skipped.
- With one independent reviewer, the author—not the reviewer—must push requested corrections. If the reviewer becomes the latest pusher, a second eligible non-last-pusher approver is required; the last-push control must not be bypassed to avoid that consequence.
- Protected `develop` and `main` will require one approving review, stale-review dismissal, CODEOWNER review, and approval after the latest push.
- `.github/CODEOWNERS` will assign the independent reviewer to `.github/workflows/**`, `.github/CODEOWNERS`, `infra/github/**`, `infra/policy/**`, `scripts/validate_terraform_static.py`, `tests/unit/test_terraform_hygiene.py`, `pyproject.toml`, and `uv.lock`.
- Required checks will include `enforce`, `check`, `application`, and `Terraform static validation`.
- The remediation PR that introduces this bootstrap control must itself receive the named independent review before merge. After merge, repository policy is applied from the protected `develop` version under separate explicit authorization and read back with `verify-repo-policy.sh`.

If an eligible reviewer is not nominated and verified, Task 1 remains RED, the High remains open, and Tasks 2–7 must not begin. An independently controlled GitHub App that produces a required check bound to that App may replace the human model only through a separately reviewed amendment to this plan.

## Implementation strategy

Use one later implementation branch, suggested name `security/pr24-terraform-remediation`, from the then-current exact `origin/develop` tip. Execute one finding at a time. Preserve the first failing assertion for each RED in `NOTES.md`, make only the minimum GREEN change, run the focused node, then run the accumulated Terraform hygiene suite. Do not batch-write seven implementations before testing.

## Task 1 — Make required CI non-self-authorizing (High)

### Files

- Create: `.github/CODEOWNERS`
- Modify: `infra/github/repo-policy.json`
- Modify: `.github/workflows/infrastructure-quality.yml`
- Modify: `infra/github/apply-repo-policy.sh` only if exact payload tests expose a missing field
- Modify: `infra/github/verify-repo-policy.sh` only if read-back tests expose a missing field
- Modify: `tests/unit/test_repo_policy_apply_script.py`
- Create or modify: `tests/unit/test_repo_policy_verify_script.py`
- Modify: `GIT_WORKFLOW.md`
- Modify: `SECURITY.md`
- Modify: `TECHNOLOGY_DECISIONS.md`

### RED nodes

Add exact tests that fail against the current solo-maintainer policy:

- `test_repo_policy_requires_independent_review_authority`
- `test_repo_policy_requires_terraform_static_validation`
- `test_infrastructure_quality_required_context_runs_for_every_protected_branch_pr`
- `test_codeowners_protects_ci_policy_and_validator_authority`
- `test_apply_script_emits_independent_review_policy`
- `test_verify_script_rejects_missing_independent_review_controls`
- `test_verify_script_rejects_missing_required_terraform_context`

The CODEOWNERS unit test must reject placeholders, the repository owner as the sole critical-path owner, and an empty/missing independent owner without making network calls. A separate read-only preflight must query the supplied login's current repository permission and require `write`, `maintain`, or `admin` before the implementation branch starts and again before policy activation. Do not invent the final login.

### GREEN contract

For both protected branches, set:

- `required_approving_review_count: 1`;
- `dismiss_stale_reviews: true`;
- `require_code_owner_reviews: true`;
- `require_last_push_approval: true`;
- required status contexts: `enforce`, `check`, `application`, `Terraform static validation`;
- existing administrator enforcement, strict update-before-merge, conversation-resolution, no-force-push, and no-deletion controls remain enabled.

Because `Terraform static validation` becomes required, its producer must run on every pull request to `develop` and `main`. Remove the current path filter and use an unconditional protected-branch `pull_request` trigger. Do not create an always-waiting required context. The exact regression must prove a documentation-only or application-only PR still schedules the named job; qualify that exact context on the implementation PR before post-merge policy activation.

Keep apply and verify payloads derived from `repo-policy.json`; do not duplicate mutable policy literals in shell logic. The independent reviewer approves the exact final implementation head. Only after merge and separate authorization may the protected `develop` policy be applied and verified live. Do not claim the High closed from repository files alone.

### Verification

```text
env -u PYTHONPATH uv run pytest \
  tests/unit/test_repo_policy_apply_script.py \
  tests/unit/test_repo_policy_verify_script.py -q
env -u PYTHONPATH uv run pytest tests/unit/test_terraform_hygiene.py -q
```

Stop if the independent reviewer cannot be verified, the bootstrap review is missing, or live read-back later differs from committed policy.

The reviewer-permission preflight is read-only GitHub evidence. It does not authorize collaborator invitations, role changes, or repository-policy mutation; those require Beatrice's separate explicit action/approval.

### Staged bootstrap evidence gate

The CODEOWNERS file does not exist on the current base and cannot be treated as live before the bootstrap implementation PR merges. Preserve redacted outputs from exact read-only GitHub queries in this order:

**Stage A — before creating the implementation branch**

1. prove the nominated login's collaborator permission is `write`, `maintain`, or `admin`;
2. prove the nominated login and intended PR author differ.

**Stage B — before merging the bootstrap implementation PR**

3. prove the nominated reviewer submitted `APPROVED` on the exact final head SHA after the latest author push, using the review object's `commit_id` and the PR's current `headRefOid`;
4. prove the reviewer differs from the recorded latest pusher; inspect available PR timeline/push evidence and do not infer this from commit authorship alone;
5. prove all configured checks, including the now-unconditional `Terraform static validation`, passed on the exact head and that GitHub reports the PR eligible to merge under the then-live policy. This independent bootstrap review is evidence, but current zero-approval branch policy means the High is not yet operationally closed.

**Stage C — after merge to `develop`, before policy mutation**

6. prove the exact reviewed head merged into `develop` and preserve the merge event/metadata needed to show no administrator bypass was used; this assertion is post-merge by definition and must not be required in Stage B;
7. prove protected `develop` now contains `.github/CODEOWNERS`, GitHub reports no CODEOWNERS parse errors, and every listed authority path resolves only to the nominated independent owner rather than the repository author as an alternative owner;
8. record whether protected `main` contains that CODEOWNERS revision. It normally will not until a later `develop` → `main` promotion; do not claim code-owner enforcement on `main` while its base lacks the file.

**Stage D — after separately authorized policy application**

9. prove branch-protection read-back on both `develop` and `main` requires one approval, stale-review dismissal, approval after the latest push, strict checks, and all named contexts;
10. prove `develop` additionally has effective CODEOWNER resolution. On `main`, the one non-author approval plus last-push approval is the immediate non-self-authorizing control until the reviewed CODEOWNERS file reaches `main`; `require_code_owner_reviews` must not be described as effective there before that promotion;
11. after the later reviewed `develop` → `main` promotion, verify CODEOWNERS resolution on `main` and record that stronger path-specific control separately.

Use `gh api`/GraphQL read-only queries and record query shapes plus minimized assertions in the implementation handoff; do not print tokens or broad account data. `verify-repo-policy.sh` covers branch-policy fields but does not by itself prove collaborator permission, CODEOWNERS resolution, review/head binding, actor separation, or no-bypass merge. Task 1 remains High/open if any assertion required for the affected branch/stage is unavailable, ambiguous, stale, or relies on self-attestation.

## Task 2 — Replace lexical policy authority with semantic parsing (High)

### Files

- Modify: `pyproject.toml`
- Modify: `uv.lock`
- Modify: `.github/workflows/infrastructure-quality.yml`
- Create: `infra/policy/static-validation-manifest.json`
- Rewrite narrowly: `scripts/validate_terraform_static.py`
- Modify: `tests/unit/test_terraform_hygiene.py`
- Add only if fixtures materially improve readability: `tests/fixtures/terraform_policy/**`

### Dependency decision

Add exact reviewed development dependencies and lock them:

- `python-hcl2==8.1.2` for HCL2 parsing;
- `ruamel.yaml==0.19.1` using YAML 1.2 safe parsing with duplicate-key rejection.

Continue using the standard library `json` parser for `.tf.json`, with a duplicate-rejecting `object_pairs_hook`; decoding must occur before policy inspection so Unicode-escaped keys cannot hide privileged blocks and duplicate names cannot use last-key-wins behavior.

### RED nodes

Add parameterized adversarial tests with stable case IDs. At minimum:

- `test_semantic_policy_rejects_unicode_escaped_tf_json_keys`
- `test_semantic_policy_rejects_yaml_flow_and_quoted_push_triggers`
- `test_semantic_policy_scans_renamed_workflow_files`
- `test_semantic_policy_rejects_mutable_actions_and_reusable_workflows`
- `test_semantic_policy_rejects_mutable_job_and_service_containers`
- `test_semantic_policy_rejects_workflow_and_job_write_permissions`
- `test_semantic_policy_rejects_destructive_commands_in_folded_and_sequence_forms`
- `test_semantic_policy_rejects_unknown_workflows_jobs_steps_and_commands`
- `test_semantic_policy_rejects_duplicate_yaml_and_json_keys`
- `test_semantic_policy_rejects_malformed_hcl_json_and_yaml_fail_closed`
- `test_semantic_policy_redacts_parser_and_policy_violation_values`
- `test_semantic_policy_rejects_extra_instances_of_allowed_resource_types`
- `test_semantic_policy_rejects_unapproved_project_service_instances`
- `test_semantic_policy_rejects_dynamic_values_at_guarded_paths`
- `test_semantic_policy_rejects_execution_field_mutations`
- `test_semantic_policy_rejects_unknown_manifest_and_workflow_fields`
- `test_semantic_policy_preserves_current_scaffold_allowlist`
- `test_infrastructure_quality_runs_semantic_validator_in_locked_environment`

Fixtures must include, not merely mention:

- `"\u0062ackend"`, `"\u0063redentials"`, and Unicode-escaped forbidden resource names in `.tf.json`;
- YAML `on: [push]`, quoted `"on"`, flow mappings, anchors/aliases, folded and literal command scalars, and `.yaml` plus renamed `.yml` files;
- `uses: owner/action@main`, tag refs, branch refs, non-40-hex refs, local actions, and reusable workflow calls;
- mutable `container:` and `services.*.image` tags without `@sha256:`;
- top-level and job-level `permissions: write-all`, `id-token: write`, `contents: write`, `packages: write`, and equivalent map forms;
- `terraform plan`, `terraform apply`, destroy, cloud auth/CLI, credential-bearing API mutations, and deployment commands represented through alternate scalar forms;
- a workflow retaining a required job name while removing/replacing its required validation steps.
- an otherwise syntactically safe new workflow, job, step, local action, reusable workflow, or shell command that is absent from the reviewed structural allowlist.
- duplicate `.tf.json` object names that attempt last-key-wins replacement of privileged or ordinary keys;
- an extra instance of an otherwise allowed resource type, an unapproved service in `google_project_service`, and a guarded unsafe value assembled through an expression;
- malformed and valid-but-forbidden HCL/JSON/YAML containing distinctive secret canaries, with assertions that paths/reasons are reported but canaries never appear in stdout or stderr.
- approved actions whose `with.repository`, `with.ref`, other action inputs, environment values, `shell`, `working-directory`, `if`, `runs-on`, permissions, or unknown fields are mutated while action references and command text remain unchanged.

### GREEN contract

The validator must:

1. discover every `.tf`, `.tf.json`, `.github/workflows/*.yml`, and `.github/workflows/*.yaml` file under the supplied `--root`;
2. parse each file into a semantic representation and fail closed on parse errors or duplicate keys; standard JSON decoding must use a duplicate-rejecting `object_pairs_hook` rather than Python's default last-key-wins behavior;
3. load `infra/policy/static-validation-manifest.json` with duplicate-name rejection and fail-closed schema validation; Task 2's manifest describes only structures present at that exact node and must not pre-authorize Task 3–7 additions;
4. enforce the reviewed Terraform manifest by expected file, block kind, type, labels, instance cardinality, permitted attribute paths, and exact literals or explicit semantic predicates for security-relevant values; reject unknown instances, duplicate labels, and unevaluable/dynamically constructed values at guarded paths;
5. permit only the local `./develop` module and approved Google provider configuration, reject all backend blocks and data sources, and add `google_compute_subnetwork.cloud_run` only during Task 4's own RED → GREEN manifest update;
6. bind the complete accepted semantic object for every workflow, job, service, container, and step: filenames, names, triggers, concurrency/defaults, runner, timeout, needs/strategy/outputs, permissions, conditions, environments, exact environment names and values, action references, exact or explicitly constrained `with` inputs, normalized command blocks, shell, working directory, and every other accepted execution-affecting field; reject unknown fields and dynamic values except explicitly enumerated safe predicates;
7. reject unknown workflows, jobs, steps, local actions, reusable workflows, and commands, and require remote actions to use their reviewed 40-hex commits and job/service containers to use reviewed immutable digests;
8. prohibit push/schedule/manual/repository-dispatch authority, write permissions, cloud credentials/authentication, Terraform plan/apply/destroy, deployment, and other currently forbidden capabilities as defense-in-depth in addition to the structural manifests;
9. preserve the current private/no-secret/no-backend/no-public-edge Terraform contract while authorizing later planned additions only in their own node;
10. catch parser/decode exceptions and produce deterministic path-qualified, redacted violations without echoing source lines, credentials, secret canaries, or offending values to stdout or stderr.

Parsing plus a destructive-command denylist is insufficient because shell construction can evade lexical matching. Raw or normalized string checks may remain only as defense-in-depth; exact allowlisted workflow structure and command blocks are the workflow policy boundary. Any legitimate workflow change must update the protected manifest/tests and receive CODEOWNER review in the same pull request.

### Verification

```text
env -u PYTHONPATH uv lock --check
env -u PYTHONPATH uv run pytest tests/unit/test_terraform_hygiene.py -q
env -u PYTHONPATH uv run --locked python scripts/validate_terraform_static.py
```

The infrastructure workflow must set up the pinned `uv`, report its version, and invoke the validator through `env -u PYTHONPATH uv run --locked python ...`; plain system-Python invocation is prohibited once parser dependencies are introduced. Update the protected workflow manifest accordingly.

Stop if any supported syntax is silently skipped, aliases/duplicate keys weaken evaluation, parse errors pass, or current forbidden fixtures regress.

## Task 3 — Pin deterministic `uv` selection (Medium)

### Files

- Modify: `.github/workflows/application-quality.yml`
- Modify: `.github/workflows/infrastructure-quality.yml`
- Modify: `infra/policy/static-validation-manifest.json`
- Modify: `tests/unit/test_terraform_hygiene.py`

### RED nodes

- `test_application_quality_workflow_pins_reviewed_uv_artifact`
- `test_infrastructure_quality_workflow_pins_reviewed_uv_artifact`
- `test_required_workflows_use_identical_uv_version_and_checksum`
- `test_required_workflows_emit_pinned_uv_version_before_dependency_use`
- `test_semantic_manifest_rejects_unapproved_uv_steps_and_inputs`

### GREEN contract

Keep `astral-sh/setup-uv` pinned to reviewed action commit `d0cc045d04ccac9d8b7881df0226f9e82c39688e` and configure both required workflows with:

```text
version: "0.12.5"
checksum: "68a509da24b06b4223a1c0175fb5eb5bc79342b76cbeff0cfe51ac3f5b17b6b2"
```

The checksum is for `uv-x86_64-unknown-linux-gnu.tar.gz` from the official `0.12.5` release. Add exact `uv --version` commands after setup and before the first `uv lock`, `uv sync`, or `uv run` operation in both workflows. Semantically parse and assert that ordering; checking version/checksum YAML inputs alone is insufficient. Any future version change must update both workflows, checksum evidence, tests, and lock qualification in one reviewed change.

First prove the Task 2 manifest rejects the new setup inputs and version-reporting steps. Then update both workflows and only their exact manifest objects together; do not weaken unknown-field rejection.

### Verification

```text
env -u PYTHONPATH uv run pytest \
  tests/unit/test_terraform_hygiene.py::test_application_quality_workflow_pins_reviewed_uv_artifact \
  tests/unit/test_terraform_hygiene.py::test_infrastructure_quality_workflow_pins_reviewed_uv_artifact \
  tests/unit/test_terraform_hygiene.py::test_required_workflows_use_identical_uv_version_and_checksum \
  tests/unit/test_terraform_hygiene.py::test_required_workflows_emit_pinned_uv_version_before_dependency_use -q
```

## Task 4 — Declare private Cloud Run → Cloud SQL connectivity (Medium)

### Architecture decision

Use Cloud Run v2 Direct VPC egress, not a Serverless VPC Access connector. Add one explicit regional `/26` subnet in the dedicated workload VPC and set `PRIVATE_RANGES_ONLY`. This supplies a path to Cloud SQL's private address without creating public database ingress or routing all application egress through the VPC. The CIDR remains a required non-secret input until later read-only cloud qualification can prove it is non-overlapping; do not invent a tracked environment value.

### Files

- Modify: `infra/gcp/variables.tf`
- Modify: `infra/gcp/develop.tf`
- Modify: `infra/gcp/develop/variables.tf`
- Modify: `infra/gcp/develop/network.tf`
- Modify: `infra/gcp/develop/cloud_run.tf`
- Modify: `infra/policy/static-validation-manifest.json`
- Modify: `tests/unit/test_terraform_hygiene.py`
- Modify: `infra/gcp/README.md`

### RED nodes

- `test_cloud_run_uses_direct_vpc_egress_to_explicit_private_subnet`
- `test_cloud_run_subnet_cidr_is_required_private_and_at_least_slash_26`
- `test_private_cloud_sql_remains_without_public_addressing`
- `test_semantic_manifest_rejects_unapproved_direct_vpc_structure`
- extend `test_gcp_terraform_root_loads_develop_resource_module` to require `google_compute_subnetwork.cloud_run` and graph edges to Cloud Run.

### GREEN contract

- Add a required root and child `cloud_run_subnet_cidr` string variable with validation limited to RFC1918 IPv4 CIDRs whose prefix is `/26` or broader; no default.
- Add `google_compute_subnetwork.cloud_run` in `var.region`, attached to `google_compute_network.develop`, with `private_ip_google_access = true` and `stack_type = "IPV4_ONLY"`.
- Add Cloud Run v2 `template.vpc_access.network_interfaces` referencing the managed network and subnet and set `egress = "PRIVATE_RANGES_ONLY"`.
- Keep Cloud SQL `ipv4_enabled = false`, keep the service private, and add no Cloud Run public invoker IAM.
- Do not add a VPC connector, NAT gateway, external address, public route, firewall opening, proxy sidecar, or secret injection.
- First prove the Task 3 manifest rejects the new variable, subnet, and Cloud Run VPC blocks; then update only those exact source/manifest objects together.

### Verification

```text
terraform fmt -check -recursive infra/gcp
terraform -chdir=infra/gcp init -backend=false -input=false
terraform -chdir=infra/gcp validate
terraform -chdir=infra/gcp graph
env -u PYTHONPATH uv run --locked python scripts/validate_terraform_static.py
env -u PYTHONPATH uv run pytest tests/unit/test_terraform_hygiene.py -q
```

## Task 5 — Order API activation before dependent resources (Medium)

### Files

- Modify: `infra/gcp/develop/artifact_registry.tf`
- Modify: `infra/gcp/develop/cloud_run.tf`
- Modify: `infra/gcp/develop/cloud_sql.tf`
- Modify: `infra/gcp/develop/identities.tf`
- Modify: `infra/gcp/develop/network.tf`
- Modify: `infra/gcp/develop/secrets.tf`
- Modify: `infra/policy/static-validation-manifest.json`
- Modify: `tests/unit/test_terraform_hygiene.py`

### RED nodes

- `test_artifact_registry_depends_on_artifact_registry_api`
- `test_cloud_run_depends_on_run_and_compute_apis`
- `test_cloud_sql_depends_on_sqladmin_and_service_networking_apis`
- `test_networking_depends_on_compute_and_service_networking_apis`
- `test_identities_depend_on_iam_api`
- `test_secret_metadata_depends_on_secret_manager_api`
- `test_semantic_manifest_rejects_unapproved_api_dependencies`

### GREEN contract

Use explicit `depends_on` references to exact `google_project_service.approved["<service>"]` instances. Do not use blanket timing sleeps, provisioners, `null_resource`, local-exec, or a dependency on every API when a smaller exact set is known. Preserve `disable_on_destroy = false` and `check_if_service_has_usage_on_destroy = true`.

Expected minimum mapping:

- Artifact Registry repository → `artifactregistry.googleapis.com`;
- Cloud Run service → `run.googleapis.com` and `compute.googleapis.com` for Direct VPC egress;
- Cloud SQL → `sqladmin.googleapis.com` plus the private-service connection;
- VPC/subnet/address → `compute.googleapis.com`;
- service-networking connection → `servicenetworking.googleapis.com` and the managed network/address;
- service accounts → `iam.googleapis.com`;
- Secret Manager metadata → `secretmanager.googleapis.com`.

Terraform references continue to provide resource-to-resource ordering; API dependencies supplement rather than replace them.

First prove the Task 4 manifest rejects each new `depends_on`; then update the exact source and manifest entries together.

## Task 6 — Encode the accepted Cloud SQL automated-backup baseline (Medium)

### Files

- Modify: `infra/gcp/develop/cloud_sql.tf`
- Modify: `tests/unit/test_terraform_hygiene.py`
- Modify: `infra/gcp/README.md`
- Modify: `SECURITY.md`
- Modify: `infra/policy/static-validation-manifest.json`

### RED nodes

- `test_cloud_sql_enables_automated_backups`
- `test_cloud_sql_backup_baseline_does_not_claim_unapproved_retention_or_recovery_targets`
- `test_semantic_manifest_rejects_unapproved_backup_configuration`

### GREEN contract

Add `settings.backup_configuration { enabled = true }` to the PostgreSQL instance. Do not invent `start_time`, location, retained-backup count, transaction-log retention, point-in-time recovery, RTO/RPO, restore cadence, or production durability claims. Those remain open controls for the subsequent bootstrap/state/recovery packet. Static validation proves configuration shape only; no backup or restore has occurred.

First prove the Task 5 manifest rejects the new backup block; then update only the exact Cloud SQL source/manifest object together.

## Task 7 — Bind the deployed image to the managed regional Artifact Registry (Medium)

### Files

- Modify: `infra/gcp/variables.tf`
- Modify: `infra/gcp/locals.tf`
- Modify: `infra/gcp/develop.tf`
- Modify: `infra/gcp/develop/variables.tf`
- Modify: `infra/gcp/develop/locals.tf`
- Modify: `infra/gcp/develop/cloud_run.tf`
- Modify: `tests/unit/test_terraform_hygiene.py`
- Modify: `infra/gcp/README.md`
- Modify: `infra/policy/static-validation-manifest.json`

### RED nodes

- `test_container_input_accepts_digest_only_not_arbitrary_registry_reference`
- `test_cloud_run_image_is_derived_from_managed_regional_repository`
- `test_container_digest_rejects_tags_malformed_and_non_sha256_values`
- `test_semantic_manifest_rejects_unapproved_digest_authority_structure`

### GREEN contract

Change `container_image_digest` to accept only `sha256:` plus exactly 64 lowercase hexadecimal characters. Construct the full Cloud Run image reference inside the develop module from:

```text
${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.application_images.repository_id}/staff-tracer@${var.container_image_digest}
```

Cloud Run consumes only that derived reference. Callers cannot supply another project, region, registry host, repository, image name, tag, or mutable reference. Preserve the Artifact Registry repository's regional location, cleanup policy, and no image-push authority. Do not claim immutable tags: the current repository does not configure `docker_config.immutable_tags`, and digest-only deployment—not tag immutability—is the authority required by this slice.

First prove the Task 6 manifest rejects the changed variable validation, derived local, and Cloud Run image expression; then update only those exact source/manifest objects together.

## Task 8 — Accumulated qualification and independent rereview

### Living documents

After implementation, update only evidence/status affected by the work:

- `CURRENT_WORK.md`
- `ROADMAP.md`
- `NOTES.md` (append at bottom in ascending date order)
- `AGENTS.md`
- `README.md`
- `ARCHITECTURE.md`
- `SECURITY.md`
- `TECHNICAL_REQUIREMENTS.md`
- `TECHNOLOGY_DECISIONS.md`
- `GIT_WORKFLOW.md`
- `docs/adr/ADR-0010-pr24-terraform-remediation-boundary.md`
- `infra/gcp/README.md`
- implementation review handoff created from the exact branch base/head.

Do not mark live branch policy validated until post-merge apply/read-back evidence exists. Do not mark cloud connectivity, backup, deployment, or recovery validated from static Terraform.

### Required local qualification

Run from a clean checkout with no cloud credentials required:

```text
env -u PYTHONPATH uv sync --locked --all-groups
env -u PYTHONPATH uv run ruff format --check .
env -u PYTHONPATH uv run ruff check .
env -u PYTHONPATH uv run mypy src tests
env -u PYTHONPATH uv run bandit -q -r src
env -u PYTHONPATH uv run pip-audit --skip-editable
terraform fmt -check -recursive infra/gcp
terraform -chdir=infra/gcp init -backend=false -input=false
terraform -chdir=infra/gcp validate
terraform -chdir=infra/gcp graph
env -u PYTHONPATH uv run --locked python scripts/validate_terraform_static.py
env -u PYTHONPATH uv run pytest tests/unit/test_repo_policy_apply_script.py tests/unit/test_repo_policy_verify_script.py -q
env -u PYTHONPATH uv run pytest tests/unit/test_terraform_hygiene.py -q
git diff --check
gitleaks git --redact --log-opts="<exact-base>..<exact-head>"
```

Run the full repository `pytest` gate only with the already approved disposable local PostgreSQL harness; do not start a service implicitly. Record any harness-only blocker honestly.

### Independent review focus

Use independent reviewers for:

1. governance and CI authority, including bootstrap and live-application sequencing;
2. parser bypass/adversarial coverage and secret-safe failures;
3. Terraform graph, Direct VPC/private SQL, API ordering, backup claim limits, and image provenance;
4. exact-range evidence, documentation truthfulness, and no-cloud/no-side-effect scope.

Any Blocker, High, or Medium finding blocks publication. After remediation, rereview the exact final head, rerun exact-range Gitleaks, then request explicit authorization before commit/push/PR unless that authorization is already current for the implementation lane.

## Post-merge sequence

After the implementation PR merges:

1. rebaseline exact `origin/develop`;
2. complete Stage C CODEOWNERS evidence on protected `develop`;
3. under separate explicit authorization, apply repository policy from protected `develop` and read back both branches under Stage D;
4. record `develop` CODEOWNER enforcement and `main`'s non-author/last-push approval control separately; do not claim `main` CODEOWNER enforcement until the file reaches that base branch;
5. record whether Task 1 is operationally validated for each branch; if not, keep the High open for that branch;
6. do not authenticate to GCP or run Terraform plan/apply;
7. only after the remediation is independently cleared and governance is operational, create the separate bootstrap/state/WIF planning packet.

## Completion criteria

This remediation is complete only when:

- all seven findings have focused RED → GREEN evidence and accumulated tests;
- an eligible independent reviewer owns and approves the protected authority paths;
- staged live bootstrap evidence proves collaborator/reviewer/latest-pusher/no-bypass separation, effective `develop` CODEOWNERS, honest `main` CODEOWNERS status, and both-branch policy read-back;
- every protected-branch PR receives the required `Terraform static validation` context;
- semantic parsing rejects the specified bypass classes and fails closed;
- the semantic validator executes through the locked project environment;
- both required workflows select the same pinned `uv` artifact/checksum and emit `uv --version` before dependency use;
- Terraform graph shows the explicit Direct VPC path and API dependencies;
- Cloud SQL automated backups are configured without false recovery claims;
- Cloud Run image authority is derived only from the managed regional repository and digest-only input;
- no backend, cloud credential, plan/apply, provisioning, image push, deployment, service start, real identity, or live/client data is introduced;
- exact final-head independent rereview returns no Blocker, High, or Medium finding;
- post-merge repository-policy read-back—not source alone—validates the governance control.
