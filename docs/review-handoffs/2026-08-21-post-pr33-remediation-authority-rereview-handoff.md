# Independent re-review handoff — post-PR33 authority-boundary remediation working tree

**Date:** 2026-08-21
**Branch:** `fix/post-pr33-deployment-path-remediation`
**Target base:** protected `develop`
**Exact approved base:** `develop@fd7b89dd848a1eb12e2eb6ba082d2dcb3d3b8ea0` (`docs: close post-pr35 planning packet route (#36)`)
**Committed branch head:** `6e11635b4168ee7827462a4a28ad85b509024890` (`fix: close out post-pr33 remediation qualification`)
**Re-review surface:** current uncommitted local working tree above `6e11635`, not yet committed or pushed
**Cloud status:** no cloud authentication, Terraform plan/apply, publication, deployment, or live qualification performed

## 1. Objective

Review the current uncommitted remediation surface that closes the post-PR33 deployment-path authority findings left open after the earlier exact-head packet for `6e11635`. This packet is for an independent review session of the **working tree**, not the older committed head.

## 2. Status truth

- PR #33 merged into protected `develop` at `3c0118abb8b84472141992d2238033b1312d5af2`; its branch is retired.
- A post-merge audit found F1–F17 deployment-path defects, including four Blockers.
- The earlier exact-head packet for `6e11635` drew CHANGES REQUIRED, including:
  - missing reviewed stage-receipt producer/transport authority;
  - collapsed migration/service execution path;
  - project-scoped deployer Run authority;
  - caller-supplied tester authority;
  - deploy-time provenance/SBOM trust of workflow-authored JSON.
- ADR-0013 Amendment A and the amended remediation plan now govern this narrower authority-boundary round.
- The current working tree is no-cloud qualified locally but remains uncommitted and still requires independent re-review before any closeout commit, push, or PR creation.
- Same-repository CI remains High/open accepted residual risk and must not be described as independent authorization.

## 3. Governing scope

This re-review surface is controlled by:
- `docs/adr/ADR-0013-post-pr33-deployment-path-remediation.md`
- `.hermes/plans/2026-08-20_002931-post-pr33-deployment-path-remediation-plan.md`
- `CURRENT_WORK.md`
- `ROADMAP.md`
- `NOTES.md`
- `infra/policy/predeployment-authority-manifest.json`
- `.github/workflows/deploy-develop.yml`
- `scripts/validate_terraform_static.py`
- `scripts/verify_stage_receipt.py`
- `scripts/verify_deploy_image_authority.py`
- `scripts/verify_gcp_foundation.py`

## 4. Review target files

### Modified tracked files
```text
.github/workflows/deploy-develop.yml
.hermes/plans/2026-08-20_002931-post-pr33-deployment-path-remediation-plan.md
CURRENT_WORK.md
NOTES.md
deploy/gcp/private-tester-access.md
docs/adr/ADR-0013-post-pr33-deployment-path-remediation.md
infra/gcp/develop.tf
infra/gcp/develop/iam.tf
infra/gcp/develop/observability.tf
infra/gcp/develop/variables.tf
infra/gcp/variables.tf
infra/policy/predeployment-authority-manifest.json
scripts/validate_terraform_static.py
tests/unit/test_terraform_hygiene.py
```

### New untracked files in review surface
```text
docs/review-handoffs/2026-08-21-post-pr33-remediation-independent-review-handoff.md
scripts/verify_deploy_image_authority.py
scripts/verify_stage_receipt.py
tests/unit/test_deploy_image_authority.py
tests/unit/test_stage_receipt.py
```

## 5. What changed in this round

### A. Stage and receipt authority
- foundation image input now fail-closes to `null` only; migration/service require immutable `sha256:<64 hex>` digests.
- deploy workflow now exposes stage-selectable `migration` / `service` inputs plus operator-held base64 receipt inputs.
- `scripts/verify_stage_receipt.py` adds a dedicated reviewed boundary for stage receipt validation, including stage, source SHA, plan/lock/non-secret-input digests, reviewed inventory, immutable workload digest, and service-only migration-success receipt binding.
- static policy and tests now pin the receipt-verification sequence before cloud auth.

### B. Exact-resource deploy authority
- project-scoped deployer Run grants were replaced with exact Cloud Run job/service IAM members.
- Terraform static policy and tests were updated to require the narrowed resources and reject the old project-scoped grants.

### C. Direct deploy-time image authority
- local isolated OCI compatibility spike proved the intended final-image SBOM contract for Cosign v3.0.6 + Syft v1.20.0: deploy-time attestation parsing must use DSSE payload subject binding, not workflow-authored JSON claims.
- `scripts/verify_deploy_image_authority.py` was added to validate raw direct Cosign OCI verification output against the immutable image subject and reviewed predicate types.
- tests were added for direct deploy-image authority parsing.

### D. Tester-authority and live verifier/runbook updates
- Terraform variables/root pass-through and private-tester runbook were updated toward the review-bound tester authority contract.
- observability and verifier surfaces were updated enough for the no-cloud gate, including request method + readiness check contract alignment.

## 6. Exact local verification observed on this working tree

### Authority / static / Terraform bundle
- `env -u PYTHONPATH uv run python scripts/validate_terraform_static.py`
  - observed: `Terraform static validation passed`
- `terraform fmt -check -recursive infra/gcp`
  - observed: success
- `terraform -chdir=infra/gcp validate`
  - observed: `Success! The configuration is valid.`
- `terraform -chdir=infra/gcp/bootstrap validate`
  - observed: `Success! The configuration is valid.`

### Focused authority suites
- `env -u PYTHONPATH uv run pytest tests/unit/test_terraform_hygiene.py tests/unit/test_stage_receipt.py tests/unit/test_deploy_image_authority.py tests/unit/test_image_provenance.py tests/unit/test_verify_gcp_foundation.py tests/unit/test_qualify_develop_deployment.py -q`
  - observed: `295 passed in 52.21s`

### Repo quality gates
- `env -u PYTHONPATH uv run ruff format --check .`
  - observed: pass
- `env -u PYTHONPATH uv run ruff check .`
  - observed: `All checks passed!`
- `env -u PYTHONPATH uv run mypy src tests`
  - observed: `Success: no issues found in 79 source files`
- `env -u PYTHONPATH uv run bandit -q -r src`
  - observed: pass (one existing `# nosec` warning only)

### Full no-cloud pytest gate
- Started disposable local PostgreSQL only after the initial no-service failure proved the service-backed suite still needed the approved local runtime.
- `GOLDEN_ROSE_TEST_DB_PASSWORD=test docker compose up -d postgres-test`
  - observed: loopback-only `postgres-test` healthy on `127.0.0.1:55432`
- `GOLDEN_ROSE_DATABASE_URL='postgresql+psycopg://golden_rose_test:test@127.0.0.1:55432/golden_rose_test' env -u PYTHONPATH uv run alembic upgrade head`
  - observed: success
- `GOLDEN_ROSE_DATABASE_URL='postgresql+psycopg://golden_rose_test:test@127.0.0.1:55432/golden_rose_test' env -u PYTHONPATH uv run pytest -q`
  - observed: `622 passed, 2 warnings in 62.26s`
- `GOLDEN_ROSE_TEST_DB_PASSWORD=test docker compose down`
  - observed: disposable PostgreSQL container and network removed
- `GOLDEN_ROSE_TEST_DB_PASSWORD=test docker compose ps -a`
  - observed: empty service listing

### Hygiene / secret scan
- `git diff --check`
  - observed: pass
- `/opt/homebrew/bin/gitleaks dir . --redact --no-banner`
  - observed: `no leaks found`

## 7. Reviewer focus

1. **Receipt authority boundary**
   - confirm the deploy path no longer depends on a publish-produced stage receipt authority;
   - confirm service stage requires a separately signed migration-success receipt binding;
   - confirm reviewed inventory/digest/source constraints are enforced at the script boundary rather than only implied by docs.

2. **Migration/service separation**
   - confirm workflow and tests no longer collapse migration execution and service readiness into one unreviewed path;
   - confirm step inventory/ordering and static policy actually lock the intended sequence.

3. **Deployer authority scoping**
   - confirm exact job/service IAM member resources replaced project-wide Run grants and that static tests reject regressions.

4. **Direct OCI evidence trust**
   - confirm deploy-time image authority parsing consumes actual Cosign OCI output and signed DSSE subjects/predicates rather than workflow-authored JSON assertions.

5. **Tester authority and verifier completeness**
   - confirm the tester-authority contract and readiness/monitoring verifier changes are sufficient for this no-cloud slice and identify any remaining gaps before closeout commit.

6. **Living-doc honesty**
   - confirm current docs describe an uncommitted working-tree rereview surface, not the prior exact committed head.

## 8. Non-scope

- no commit, push, PR creation, or merge
- no GCP authentication or inspection
- no Terraform plan/apply
- no image publication
- no secret injection or database login creation
- no Cloud Run deployment or live qualification

## 9. Requested reviewer output

Please return one of:
- **PASS** — ready for closeout commit + exact-head rerun packet creation; or
- **CHANGES REQUIRED** — severity-labeled findings against this exact working tree, with concrete file/contract references.

If findings remain, treat this packet as the authoritative rereview surface rather than the earlier `6e11635` exact-head handoff.
