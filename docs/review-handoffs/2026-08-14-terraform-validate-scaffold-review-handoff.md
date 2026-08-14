# Terraform Validate-Without-Apply Scaffold — Historical Pre-PR Handoff and Post-Merge Disposition

**Date:** 2026-08-14
**Historical status:** PR #24 merged into protected `develop`; the pre-PR surface below is retained as chronological evidence and is superseded for current status by the post-merge disposition at the end of this document.
**Branch:** `feat/gcp-terraform-validate-scaffold`
**Intended base:** `origin/develop`
**Approved base SHA:** `c27e1eeafab4bd18e697b43abc63744673a2b536`
**Current HEAD:** `c27e1eeafab4bd18e697b43abc63744673a2b536`
**Review surface:** remediated uncommitted local working tree against PR #23's merged `develop` tip
**Ahead commits vs base:** 0

## Review status

This is a focused re-review handoff for a repeatedly remediated uncommitted local working tree. The first review verdict was **NOT ready to commit or open a PR** because one Blocker and two Medium findings required remediation. Focused rereview cleared those named fixes, then returned three additional Medium findings in the remediation itself. Final rereview cleared those paths but returned two Medium bypass findings around workflow filenames and JSON provider credentials. The implementation surface is still not a committed branch range and no PR has been opened. Review should inspect the live working tree, including untracked files, before any staging/commit/push/PR.

The branch implements the reviewed Terraform validate-without-apply scaffold and static/policy harness from `.hermes/plans/2026-08-13_181005-terraform-preparation-plan.md`. Local Terraform execution is now approved for this branch only in the bounded form recorded here: `terraform fmt`, `terraform init -backend=false`, and `terraform validate`. Terraform `plan`/`apply`, cloud authentication, API enablement, provisioning, image push, service start, deployment, public access, real identity, live/client data, and production remain outside this branch.

## Remediation summary for focused re-review

Initial review findings and current working-tree remediation:

1. Blocker — Terraform ignored the intended resource scaffold because `infra/gcp/develop/*.tf` was not connected to the root module.
   - Remediation: added `infra/gcp/develop.tf` with an explicit `module "develop"` block and added child-module `variables.tf` and `locals.tf` under `infra/gcp/develop/`.
   - Regression: `tests/unit/test_terraform_hygiene.py::test_gcp_terraform_root_loads_develop_resource_module` runs `terraform -chdir=infra/gcp graph` and asserts the graph contains expected `module.develop.google_*` resource nodes and does not report an empty configuration.
2. Medium — static scanner missed Terraform JSON configuration.
   - Remediation: `scripts/validate_terraform_static.py` now scans both `*.tf` and `*.tf.json`.
   - Regression: `tests/unit/test_terraform_hygiene.py::test_terraform_static_validation_harness_rejects_tf_json_forbidden_patterns` proves a forbidden `google_service_account_key` in `bypass.tf.json` is rejected.
3. Medium — infrastructure workflow used mutable action tags.
   - Remediation: `.github/workflows/infrastructure-quality.yml` now SHA-pins `actions/checkout`, `actions/setup-python`, `astral-sh/setup-uv`, and `hashicorp/setup-terraform`.
   - Regression: `tests/unit/test_terraform_hygiene.py::test_infrastructure_quality_workflow_runs_static_validation_without_apply_or_auth` asserts the reviewed SHA pins and rejects mutable `@v` action references for this workflow.

The remediation itself still requires independent rereview.

Focused rereview follow-up findings and current working-tree remediation:

1. Medium — clean CI checkout would fail before the graph regression because Terraform plugins were not initialized before pytest.
   - Remediation: `.github/workflows/infrastructure-quality.yml` now runs `terraform fmt -check -recursive infra/gcp`, `terraform -chdir=infra/gcp init -backend=false -input=false`, and `terraform -chdir=infra/gcp validate` before static validation and pytest.
   - Regression: `tests/unit/test_terraform_hygiene.py::test_infrastructure_quality_workflow_runs_static_validation_without_apply_or_auth` now asserts these workflow commands.
2. Medium — `.tf.json` policy coverage was incomplete for JSON-form backend and Cloud Run environment/secret-injection shapes.
   - Remediation: `scripts/validate_terraform_static.py` now includes JSON-equivalent deny substrings for `"backend"`, `"env"`, `"value_source"`, and `"secret_key_ref"` while continuing to scan `*.tf.json`.
   - Regressions: `tests/unit/test_terraform_hygiene.py::test_terraform_static_validation_harness_rejects_tf_json_backend_configuration` and `tests/unit/test_terraform_hygiene.py::test_terraform_static_validation_harness_rejects_tf_json_cloud_run_env_injection` prove the two cited JSON bypass shapes are rejected.
3. Medium — immutable action pinning was not an ongoing invariant.
   - Remediation: `scripts/validate_terraform_static.py` now enumerates every `uses:` reference in infrastructure workflows and rejects any reference that is not pinned to a full 40-hex commit SHA.
   - Regression: `tests/unit/test_terraform_hygiene.py::test_terraform_static_validation_harness_rejects_unpinned_infrastructure_actions` proves `third-party/action@main` is rejected; the current workflow test also enumerates all current `uses:` refs and asserts full-SHA pins.

This second remediation also still requires independent rereview before staging, commit, push, or PR.

Final rereview follow-up findings and current working-tree remediation:

1. Medium — action-pin enforcement was bypassable by non-`infrastructure*` workflow filenames.
   - Remediation: `scripts/validate_terraform_static.py` now scans every `.github/workflows/*.yml` and `.github/workflows/*.yaml` file for forbidden cloud/deployment authority and unpinned `uses:` references. `.github/workflows/infrastructure-quality.yml` now triggers on `.github/workflows/**` changes.
   - Regression: `tests/unit/test_terraform_hygiene.py::test_terraform_static_validation_harness_rejects_unpinned_workflow_actions` uses `terraform-quality.yml` with `third-party/action@main` and proves the scanner rejects it; the workflow test asserts the `.github/workflows/**` path trigger.
2. Medium — JSON-form provider credentials bypassed the scanner.
   - Remediation: `scripts/validate_terraform_static.py` now rejects the JSON key `"credentials"` in Terraform configuration.
   - Regression: `tests/unit/test_terraform_hygiene.py::test_terraform_static_validation_harness_rejects_tf_json_provider_credentials` proves a `providers.tf.json` Google provider credentials entry is rejected.

The final focused independent rereview cleared this exact uncommitted working tree with no remaining Blocker, High, or Medium finding. It independently reproduced all-workflow filename/action-pin enforcement and JSON provider-credential rejection, confirmed clean-checkout Terraform init/fmt/validate/graph behavior, and reran the local Terraform/static/test/security gate. The next step is the closeout commit, exact-final-head verification, push, and PR creation; committed-range evidence remains pending until that commit exists.

## Review-surface caveat

Local verification below proves the files currently on disk. Because `origin/develop..HEAD` has zero commits, committed-range evidence such as exact-range Gitleaks and `git diff --check origin/develop...HEAD` is not yet meaningful as final PR evidence. After review/remediation and commit, rerun committed-range checks before push/PR.

`git diff --check` does not inspect untracked files. This review surface includes substantial untracked source under `infra/gcp/`, `.github/workflows/`, `scripts/`, and `tests/`; reviewers should inspect untracked files directly or stage the exact reviewed file list and run `git diff --cached --check` before final commit.

## Scope implemented

Repo-local Terraform and policy/static validation only:

- Terraform scaffold under `infra/gcp/` for private fictional-synthetic-only `develop` posture.
- Root module `infra/gcp/develop.tf` explicitly loads the `infra/gcp/develop/` child module so Terraform validates and graphs the intended resource declarations.
- Provider/version scaffold with local backend-free initialization and tracked provider lockfile.
- Required variables without defaults for cloud/project/image inputs.
- Value-safe outputs and standard non-sensitive labels.
- Develop API allowlist declarations with destructive-disable safeguards.
- Private regional Artifact Registry repository with cleanup policy.
- Secret Manager metadata-only resources without secret payload/version resources.
- Dedicated VPC/private-service-access scaffold.
- Private Cloud SQL PostgreSQL 16 baseline: `db-f1-micro`, 10 GiB SSD, no public IPv4, deletion protection.
- Private Cloud Run service scaffold using a required immutable image digest variable and runtime service account.
- Distinct runtime and migration service-account declarations without keys.
- Static validation harness that fails closed on forbidden Terraform/source/workflow patterns.
- Pull-request-only infrastructure-quality workflow with read-only repository permission and clean-checkout Terraform init/fmt/validate before pytest.
- SHA-pinned third-party actions in the infrastructure-quality workflow.
- Living-document rebaseline for the new local Terraform validation approval and next development/testing cloud implementation lane.

## Explicit non-scope preserved

For this branch:

- No Terraform plan.
- No Terraform apply.
- No GCP authentication or API calls.
- No API enablement.
- No resource provisioning.
- No service identity creation in cloud.
- No secrets, secret payloads, credentials, project IDs, billing IDs, domains, or user emails in tracked source.
- No image push or registry action.
- No Cloud SQL use.
- No service start or deployment.
- No public access.
- No real identity/provider integration.
- No live/client-derived data.
- No production work or production-readiness claim.

Beatrice has approved moving into the dedicated GCP development/testing project after this scaffold branch is review-qualified, but that is a later lane and should not be treated as evidence produced by this branch.

## Changed tracked files

Modified tracked files currently shown by `git status --short --untracked-files=all`:

- `.gitignore`
- `AGENTS.md`
- `ARCHITECTURE.md`
- `CURRENT_WORK.md`
- `NOTES.md`
- `README.md`
- `ROADMAP.md`
- `SECURITY.md`
- `TECHNICAL_REQUIREMENTS.md`
- `TECHNOLOGY_DECISIONS.md`
- `docs/adr/ADR-0009-gcp-develop-deployment-boundary.md`
- `docs/adr/README.md`

## Untracked implementation files in review surface

- `.github/workflows/infrastructure-quality.yml`
- `infra/gcp/.terraform.lock.hcl`
- `infra/gcp/README.md`
- `infra/gcp/versions.tf`
- `infra/gcp/providers.tf`
- `infra/gcp/variables.tf`
- `infra/gcp/locals.tf`
- `infra/gcp/outputs.tf`
- `infra/gcp/develop.tf`
- `infra/gcp/develop/apis.tf`
- `infra/gcp/develop/artifact_registry.tf`
- `infra/gcp/develop/secrets.tf`
- `infra/gcp/develop/network.tf`
- `infra/gcp/develop/cloud_sql.tf`
- `infra/gcp/develop/cloud_run.tf`
- `infra/gcp/develop/identities.tf`
- `infra/gcp/develop/locals.tf`
- `infra/gcp/develop/variables.tf`
- `scripts/validate_terraform_static.py`
- `tests/unit/test_terraform_hygiene.py`

Ignored local Terraform working directory remains untracked/ignored:

- `infra/gcp/.terraform/`

## Test/static coverage added

`tests/unit/test_terraform_hygiene.py` currently contains 99 tests. Coverage includes:

- `.gitignore` protection for Terraform state, plans, tfvars, auto-tfvars, and local `.terraform/` while preserving `.terraform.lock.hcl` as trackable.
- Terraform README boundary and no-apply/no-auth/no-secret/no-workflow-secret claims.
- Terraform version/provider/variables/outputs/labels scaffold requirements.
- Terraform graph regression proving the root module loads expected `module.develop.google_*` resource nodes.
- Develop API enablement allowlist with disable safeguards.
- Artifact Registry privacy/region/cleanup posture.
- Secret Manager metadata-only posture.
- Dedicated VPC/private-service-access posture.
- Private Cloud SQL baseline.
- Private digest-only Cloud Run baseline.
- Distinct service-account declarations and Cloud Run runtime service-account use.
- Static scanner execution without cloud access, including `*.tf` and `*.tf.json` forbidden-pattern coverage for service-account keys, JSON-form backend configuration, JSON-form provider credentials, and JSON-form Cloud Run env/secret injection.
- Pull-request infrastructure workflow without auth/apply/secret authority, with clean-checkout Terraform fmt/init-without-backend/validate before pytest, `.github/workflows/**` trigger coverage, and invariant immutable SHA-pinned actions across all workflow filenames.
- Negative fixtures for forbidden Terraform artifacts, backend blocks, workflow auth/push/apply, service-account keys, secret payloads/IAM, public ingress/IP/authorized networks, SQL users, project IAM, env/secret injection, Cloud Run jobs, billing budgets, logging sinks, monitoring alerts/channels, scheduler jobs, storage buckets, load-balancer/CDN/TLS/public-edge resources, default VPC/default routes/custom routes, VPN/Interconnect/peering/Private Service Connect, packet mirroring, firewall/security policy resources, network attachments, service connection policies, and Network Connectivity hubs.

## Static scanner behavior to review

`scripts/validate_terraform_static.py`:

- Scans required Terraform scaffold files under `infra/gcp/`.
- Accepts `--root` so negative fixtures can be scanned without cloud access.
- Reports forbidden artifacts/patterns before missing scaffold files.
- Rejects local state/plan/tfvars artifacts under scanned Terraform root.
- Rejects forbidden Terraform substrings in both `*.tf` and `*.tf.json`, including HCL and JSON-form backend config, JSON-form credentials, impersonation, public IAM, broad IAM, service-account keys, secret payload/version/IAM, public networking and public-edge resources, Cloud Run jobs/env/secret injection/public ingress, Cloud SQL public/user/password patterns, and mutable `:latest` image references.
- Scans all `.yml` and `.yaml` files under `.github/workflows/` for forbidden auth/apply/push/non-GITHUB_TOKEN secret/WIF authority.
- Enumerates every scanned workflow `uses:` reference and rejects any action reference that is not pinned to a full 40-hex commit SHA.

## Local verification evidence

### Terraform CLI evidence

- `terraform version`
  - Result: Terraform v1.15.8 on `darwin_arm64`.
- First `terraform fmt -check -recursive infra/gcp`
  - Result: failed with exit 3 and identified `infra/gcp/develop/cloud_sql.tf`.
- `terraform fmt -recursive infra/gcp`
  - Result: formatted `infra/gcp/develop/cloud_sql.tf`.
- `terraform -chdir=infra/gcp init -backend=false`
  - Result: initialized successfully, installed/generated lock entry for `hashicorp/google` v6.50.0, no backend configured.
- `terraform -chdir=infra/gcp validate`
  - Result: `Success! The configuration is valid.`
- Final rerun:
  - `terraform fmt -check -recursive infra/gcp && terraform -chdir=infra/gcp init -backend=false -input=false && terraform -chdir=infra/gcp validate && terraform -chdir=infra/gcp graph | grep -E 'module\.develop\.google_(cloud_run_v2_service|sql_database_instance|compute_network|project_service|artifact_registry_repository|service_account)'`
  - Result: init reused `hashicorp/google` v6.50.0 from lockfile, validate returned `Success! The configuration is valid.`, and graph output included expected `module.develop.google_*` resource nodes for Cloud Run, Cloud SQL, VPC, API services, Artifact Registry, and service accounts.

No Terraform plan/apply was run.

### Static/test evidence

- `python scripts/validate_terraform_static.py`
  - Result: `Terraform static validation passed`.
- `env -u PYTHONPATH uv run pytest tests/unit/test_terraform_hygiene.py -q`
  - Result before remediation: `93 passed in 3.40s`.
- Combined final rerun:
  - `python scripts/validate_terraform_static.py && env -u PYTHONPATH uv run pytest tests/unit/test_terraform_hygiene.py -q`
  - Result after first remediation docs/handoff update: static validation passed and `95 passed in 4.74s`.
  - Result after second remediation: static validation passed and `98 passed in 5.09s`.
  - Result after latest remediation: static validation passed and `99 passed in 3.93s`.

### Diff/security evidence

- `git diff --check`
  - Result: passed with exit 0.
- `gitleaks dir --no-banner --redact .`
  - Result after first remediation docs/handoff update: scanned ~7.33 MB in 3.04s and reported `no leaks found`.
  - Result after second remediation: scanned ~7.35 MB in 3.61s and reported `no leaks found`; paired `git diff --check` passed with exit 0.
  - Result after latest remediation: scanned ~7.36 MB in 2.58s and reported `no leaks found`; paired `git diff --check` passed with exit 0.
- Stale-doc search for prior planning-only/no-implementation-authority wording:
  - Result: no current matches for the targeted stale phrases.

## Reviewer focus areas

1. Terraform source boundary: confirm scaffold remains reviewable and local-validation-only for this branch, with no backend, no plan/apply artifact, no real tfvars, no project/billing/user/domain identifiers, and no secret payloads.
2. Terraform module loading: confirm `infra/gcp/develop.tf` loads the `develop` child module, variables are passed correctly, and `terraform -chdir=infra/gcp graph` includes expected `module.develop.google_*` resource nodes.
3. Provider lockfile: confirm `infra/gcp/.terraform.lock.hcl` is appropriate to track and that `.gitignore` ignores `.terraform/`, state, plans, and variable-input artifacts without ignoring the lockfile.
4. API enablement declarations: confirm the accepted API allowlist is narrow, uses `disable_on_destroy = false`, and does not imply current cloud API calls by itself.
5. Cloud Run/SQL/Artifact Registry/secrets/network scaffold: confirm it matches ADR-0009's private fictional-synthetic-only posture and does not introduce public invoker, public DB, secret versions, IAM grants, SQL users/passwords, mutable image tags, or deployment authority.
6. Static scanner ordering and false positives/false negatives: confirm forbidden-pattern detection happens before missing-file checks for negative fixtures, scans `*.tf.json`, rejects JSON-form backend/env/secret-injection bypass shapes, and required scaffold files still pass.
7. Workflow authority and CI parity: confirm `.github/workflows/infrastructure-quality.yml` is pull-request-only with `contents: read`, immutable action SHA pins for every `uses:` reference, clean-checkout Terraform fmt/init-without-backend/validate before pytest, no `id-token: write`, no secrets, no GCP auth, no Terraform plan/apply, no image push, and no deployment authority.
8. Living-document truth: confirm updated docs correctly distinguish current local scaffold evidence from the newly approved future development/testing cloud lane and from this second remediation's rereview requirement.
9. Untracked-file hygiene: because this is an uncommitted working tree, verify untracked files directly or stage reviewed files before relying on cached/range hygiene.

## Suggested review commands

Start with live working-tree inspection:

```text
git status --short --untracked-files=all
git diff --stat
git diff --name-only
git diff --check
```

Then inspect and run the focused verification:

```text
terraform fmt -check -recursive infra/gcp
terraform -chdir=infra/gcp init -backend=false -input=false
terraform -chdir=infra/gcp validate
terraform -chdir=infra/gcp graph
python scripts/validate_terraform_static.py
env -u PYTHONPATH uv run pytest tests/unit/test_terraform_hygiene.py -q
gitleaks dir --no-banner --redact .
```

Before commit/PR, either stage the exact reviewed file list and run cached hygiene or otherwise directly inspect untracked files:

```text
git diff --cached --check
```

After commit and before push/PR, rerun committed-range evidence:

```text
git diff --check origin/develop...HEAD
gitleaks git --no-banner --redact --log-opts 'origin/develop..HEAD'
git rev-list --count origin/develop..HEAD
git status --short
```

## Stop boundary before PR

Independent rereview of this remediation should happen before staging/commit/push/PR. After rereview clears the remediated working tree:

1. stage the exact reviewed files, including untracked Terraform/workflow/test/script files and the provider lockfile;
2. run cached/range hygiene as appropriate;
3. commit;
4. rerun final-head Terraform/static/test/security checks on the committed surface;
5. push and open PR only after final committed evidence is clean.

Do not run Terraform plan/apply, authenticate to GCP, enable APIs, provision resources, push images, configure secrets, start services, deploy, admit real identity, admit live/client data, or claim production readiness as part of this review branch.

## PR #24 CI remediation addendum

PR #24's first `application` run failed at `uv run ruff format --check .`. The failure identified only `scripts/validate_terraform_static.py` and `tests/unit/test_terraform_hygiene.py` as unformatted; the job had already completed the frontend dependency, audit, and frontend-SBOM stages. The missing backend-SBOM artifact was a downstream fail-fast consequence, not an independent backend-SBOM finding. The narrow remediation applies the repository formatter to exactly those two files. Before pushing the follow-up commit, rerun formatter/lint, Terraform static validation and hygiene tests, Terraform fmt/init-without-backend/validate/graph, diff hygiene, and exact-range Gitleaks against the final head. No cloud action is authorized or required.

The formatter follow-up advanced the next `application` run to full pytest, which failed only because `test_gcp_terraform_root_loads_develop_resource_module` invokes `terraform` and the Application quality job did not install that CLI. The remediation adds the same SHA-pinned `hashicorp/setup-terraform` action and Terraform 1.15.8 version already used by infrastructure-quality before the application quality command, with a regression proving the setup precedes full pytest. This supplies a local test dependency only; it adds no Terraform plan/apply, cloud authentication, or cloud authority.

The Terraform-CLI follow-up then reached graph execution but failed because clean CI checkout has no initialized Google provider plugin. The remediation adds `terraform -chdir=infra/gcp init -backend=false -input=false` before full pytest and extends the workflow regression to require that exact backend-free initialization ordering. This downloads the locked provider required for local graph testing only; it does not configure a backend, run Terraform plan/apply, authenticate to GCP, or create cloud authority.

## Post-merge final-head disposition

PR #24 merged into protected `develop` at `50451b30d02e457f70657dd4c82d07ced5ac77eb`. Final PR head `f164815cf971077d783c7de186acc7941e930afc` and the squash merge have the same tree. Required `application`, `check`, and `enforce` checks passed, and the pull-request-only `Terraform static validation` check also passed. The final Application quality run installed Terraform, initialized the locked provider with `-backend=false`, and completed the full existing gate with `404 passed` at `96.23%` coverage. Infrastructure quality completed format, backend-free initialization, validate, static validation, and `100` Terraform hygiene tests. Exact merged-range Gitleaks reported no leaks.

This evidence clears only PR #24's repo-local validate-without-apply behavior. No Terraform plan/apply, GCP authentication, API enablement, provisioning, backend migration, image push, deployment, Cloud SQL use, secret configuration, public access, real identity, live/client data, or production-readiness evidence exists.

GitHub contains no approving review object for PR #24. CodeRabbit's green status represented a skipped review for the non-default target branch and is not substantive review evidence. The final two PR commits changed the required Application quality workflow after the historical uncommitted-tree rereview; independent read-only final-head review inspected those commits and found no separate Medium-or-higher defect introduced by the Terraform setup or backend-free initialization corrections.

The broader final merged surface is **not cleared as a provisioning/deployment baseline**. Independent final-head review returned:

1. **High — required CI is self-authorized.** Live branch protection requires `enforce`, `check`, and `application`, while the Terraform context is not independently required. Pull requests may modify the required workflow definitions while retaining the required job names, and the repository has no required approval, CODEOWNERS, or last-push approval control.
2. **High — the static scanner is lexically bypassable.** The raw substring/regex implementation accepted a semantically privileged workflow fixture and a Terraform JSON backend whose key used a Unicode escape even though Terraform recognized the backend. The existing `100` hygiene tests therefore do not prove the claimed fail-closed semantic policy boundary.
3. **Medium — `uv` selection is mutable.** Both workflows pin `astral-sh/setup-uv` by action commit but omit deterministic `version` and checksum inputs; the repository does not otherwise declare the installed `uv` tool version.
4. **Medium — Cloud Run lacks a declared path to private Cloud SQL.** The private-IP database and dedicated VPC exist, but the service declares neither Direct VPC egress/subnet attachment nor a connector.
5. **Medium — API enablement is unordered.** Dependent resources do not declare dependencies on their required `google_project_service` resources, allowing first-apply service-activation races.
6. **Medium — Cloud SQL omits the accepted automated-backup baseline.** The instance has no `backup_configuration` despite ADR-0009's develop-recovery requirement.
7. **Medium — image authority is not bound to the managed Artifact Registry.** The root variable proves only a digest suffix; Cloud Run can accept a digest reference from another registry/project/region/repository.

The next code-changing lane must be a separately planned, independently reviewed validate-without-apply remediation. Both High findings block promotion. The four infrastructure architecture findings block Terraform plan/apply and any deployment-baseline claim. Bootstrap/state/WIF implementation planning follows remediation; its accepted direction keeps state authority lifecycle-independent from disposable workload infrastructure, with the existing non-workload project only a candidate pending read-only qualification.

PR #25 subsequently merged this documentation-only disposition into protected `develop` at `8dc1198c0eb571ca39e9f4814bb3af5e33079890`. ADR-0010 and `.hermes/plans/2026-08-14_164545-pr24-terraform-remediation-plan.md` are the follow-on planning packet; no finding is implemented by those documents.
