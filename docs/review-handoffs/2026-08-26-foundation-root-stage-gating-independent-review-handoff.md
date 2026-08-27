# Independent rereview handoff — foundation-root stage-gating source amendment

**Date:** 2026-08-26
**Branch:** `fix/foundation-root-stage-gating`
**Target base:** protected `develop`
**Exact approved base:** `origin/develop@3c897e4e83b36431b48a3536ee95021b459bf1cf` (`docs: plan source-live adoption boundary (#45)`)
**Review surface:** current uncommitted working tree above `origin/develop`; not committed, pushed, or otherwise promoted
**Ahead commits vs `origin/develop`:** `0`
**Behind commits vs `origin/develop`:** `0`
**Cloud status:** no cloud authentication, inspection, import, backend/state action, Terraform plan/apply, publication, deployment, database mutation, or live qualification

## 1. Objective

Review the first implementation slice after PR #45: a narrow source amendment that makes `deployment_stage=foundation` omit network, private-service-access, Cloud SQL, and application-database resources plus their operator-held inputs. This slice must preserve the already-accepted later adoption, Gate 3, and Gate 4 sequence and must not widen into cloud execution authority.

## 2. Status truth

- PR #45 merged the accepted source/live adoption-reconciliation planning packet into protected `develop` at `3c897e4`.
- That plan identified a hard stop: the then-current always-loaded `infra/gcp/develop` module still evaluated network, private-service-access, Cloud SQL, and application-database resources unconditionally.
- The active coding lane rebased from the exact merged planning tip `3c897e4`.
- The stale planning branch `docs/source-live-adoption-reconciliation` was retired locally after rebaseline.
- The current review surface is an **uncommitted working tree only**. `origin/develop..HEAD` contains zero commits, so this is not PR-ready committed-range evidence.
- The first independent review and three follow-up rereviews returned **CHANGES REQUIRED**; this packet now describes the latest remediated working-tree rereview surface.
- Local no-cloud verification for the remediated source amendment is complete and recorded below.
- Same-repository CI remains the accepted High/open residual risk and must not be described as independent authorization.
- No cloud/runtime side effect occurred in this lane.

## 3. Governing scope

This review surface is controlled by:
- `.hermes/plans/2026-08-26_164654-source-live-adoption-reconciliation-plan.md`
- `CURRENT_WORK.md`
- `ROADMAP.md`
- `NOTES.md`
- `infra/gcp/README.md`
- `deploy/gcp/bootstrap-state-runbook.md`
- `deploy/gcp/staged-plan-approval.md`
- `TECHNOLOGY_DECISIONS.md`

## 4. Review scope manifest

```text
CURRENT_WORK.md
NOTES.md
ROADMAP.md
infra/gcp/develop/cloud_run.tf
infra/gcp/develop/cloud_sql.tf
infra/gcp/develop/migration_job.tf
infra/gcp/develop/network.tf
infra/gcp/develop/outputs.tf
infra/gcp/develop/variables.tf
infra/gcp/variables.tf
scripts/validate_terraform_static.py
tests/unit/test_terraform_hygiene.py
docs/review-handoffs/2026-08-26-foundation-root-stage-gating-independent-review-handoff.md
```

## 5. What changed, by concern

### A. Foundation-stage resource gating
- stage-gated `google_compute_network`, `google_compute_subnetwork`, `google_compute_global_address`, and `google_service_networking_connection` so foundation does not evaluate them
- stage-gated `google_sql_database_instance` and `google_sql_database` so foundation does not evaluate them
- updated dependent references to counted resources with explicit `[0]` indexing in migration/service-only paths

### B. Foundation-stage operator-held input boundary
- made every foundation-omitted operator-held input genuinely optional with `default = null` at both the root and child module boundaries, including `container_image_digest`, Direct VPC CIDR, and every reviewed Cloud SQL input
- added validation so foundation requires `null`, while migration/service still require exact reviewed non-null inputs and still reject missing/null deferred values
- made service-only tester-authority receipt/bundle/certificate inputs genuinely optional at both boundaries with `default = null`, while preserving the child-module `deployment_stage == "service"` non-null guards
- preserved existing reviewed validation shape for migration/service values rather than broadening accepted input patterns

### C. Foundation-safe outputs and static-policy alignment
- changed database-related outputs to `null` in foundation so the source contract no longer implies foundation-stage database material
- extended `scripts/validate_terraform_static.py` so the reviewed count-expression and migration-subnetwork expectations match the new source contract
- added a focused Terraform hygiene regression proving each reviewed variable block in both modules sets `default = null`, rejects non-null deferred foundation values, and rejects missing/null deferred values in migration/service

### D. Living-doc rebaseline
- updated `CURRENT_WORK.md` from planning-publication lane to source-amendment coding lane
- updated `ROADMAP.md` so PR #45 is historical merged context and this separate amendment is the active unchecked implementation item
- appended `NOTES.md` with rebaseline, RED→GREEN, focused verification, and disposable service-backed verification evidence

## 6. Exact evidence observed on this working tree

### A. First RED → GREEN node
- `env -u PYTHONPATH uv run pytest tests/unit/test_terraform_hygiene.py -q -k foundation_stage_omits_network_and_cloud_sql_actions_and_inputs`
  - initial observed RED before implementation
  - final observed GREEN: `1 passed, 234 deselected`

### B. Focused no-cloud verification
- `env -u PYTHONPATH uv run ruff format --check scripts/validate_terraform_static.py tests/unit/test_terraform_hygiene.py`
  - observed: `2 files already formatted`
- `env -u PYTHONPATH uv run ruff check scripts/validate_terraform_static.py tests/unit/test_terraform_hygiene.py`
  - observed: `All checks passed!`
- `env -u PYTHONPATH uv run pytest tests/unit/test_terraform_hygiene.py -q -k foundation_stage_omits_deferred_network_cloud_sql_and_tester_inputs`
  - observed: `1 passed, 234 deselected in 0.56s`
- `env -u PYTHONPATH uv run pytest tests/unit/test_terraform_hygiene.py tests/unit/test_verify_gcp_foundation.py -q`
  - observed: `274 passed in 51.58s`
- `env -u PYTHONPATH uv run python scripts/validate_terraform_static.py`
  - observed: `Terraform static validation passed`
- `terraform fmt -check -recursive infra/gcp`
  - observed: success
- `terraform -chdir=infra/gcp init -backend=false -input=false -lockfile=readonly && terraform -chdir=infra/gcp validate`
  - observed: success
- `terraform -chdir=infra/gcp/bootstrap init -backend=false -input=false -lockfile=readonly && terraform -chdir=infra/gcp/bootstrap validate`
  - observed: success
- `git diff --check`
  - observed: clean

### C. Disposable service-backed regression bundle
- `GOLDEN_ROSE_TEST_DB_PASSWORD=test docker compose up -d postgres-test`
  - observed: loopback-only `postgres-test` started and became healthy on `127.0.0.1:55432`
- `GOLDEN_ROSE_DATABASE_URL='postgresql+psycopg://golden_rose_test:test@127.0.0.1:55432/golden_rose_test' env -u PYTHONPATH uv run alembic upgrade head`
  - observed: success
- `GOLDEN_ROSE_DATABASE_URL='postgresql+psycopg://golden_rose_test:test@127.0.0.1:55432/golden_rose_test' env -u PYTHONPATH uv run pytest -q`
  - observed: `662 passed, 2 warnings in 61.52s`
- `GOLDEN_ROSE_TEST_DB_PASSWORD=test docker compose down`
  - observed: disposable PostgreSQL container and network removed
- `GOLDEN_ROSE_TEST_DB_PASSWORD=test docker compose ps -a`
  - observed: empty service listing

## 7. Range-hygiene caveat

This branch still has **zero commits ahead of `origin/develop`**. Therefore:
- this packet describes a local working-tree review surface, not an exact committed head
- exact-range `gitleaks git --log-opts 'origin/develop..HEAD'` is not yet meaningful final PR evidence
- protected CI, PR review, and merge have not been exercised on this slice

Review should focus on the code/documentation surface itself. Commit-range secret scanning and final-head proof belong after review-driven remediation, closeout commit creation, and exact-head rerun.

## 8. Primary reviewer focus

1. **Foundation-stage fail-closed behavior**
   - confirm foundation no longer evaluates network/private-service-access/Cloud SQL/application-database resources
   - confirm migration/service behavior remains intact and no counted-resource dereference leaks into foundation

2. **Operator-held input discipline**
   - confirm Direct VPC and Cloud SQL inputs are truly absent/forbidden in foundation
   - confirm migration/service still require the reviewed inputs and validations

3. **Static-policy and regression integrity**
   - confirm `scripts/validate_terraform_static.py` and `tests/unit/test_terraform_hygiene.py` enforce the same contract the source now claims
   - confirm the new acceptance patterns do not accidentally widen allowed stage/cardinality behavior

4. **Living-doc truthfulness**
   - confirm docs now describe PR #45 as merged historical planning context and this branch as the active source-amendment working tree
   - confirm no doc text implies import, backend/state action, Terraform plan/apply, or cloud authority

5. **Scope control**
   - confirm the slice stays narrow and does not drift into adoption inventory collection, backend migration, saved-plan generation, or later gate execution

## 9. Explicit non-scope preserved

This packet does **not** claim that any of the following occurred:
- GCP authentication or read-only inspection
- Terraform import
- backend initialization/migration beyond local `-backend=false` validation
- Terraform plan/apply
- resource provisioning, drift repair, or deletion
- image publication
- secret payload injection
- Cloud SQL creation or use outside disposable local PostgreSQL testing
- Cloud Run job/service deployment
- tester access
- source/live inventory collection
- adoption ceremony execution
- Gate 3 or Gate 4 approval
- live/client data or production readiness

## 10. Review findings remediated for this rereview

1. **Foundation-omitted inputs were not truly optional**
   - remediated by adding `default = null` to each reviewed input in both `infra/gcp/variables.tf` and `infra/gcp/develop/variables.tf`
   - migration/service validation branches now explicitly reject missing/null deferred values while foundation still rejects non-null deferred values

2. **Formatter gate drift in `tests/unit/test_terraform_hygiene.py`**
   - remediated by formatting the file and rerunning the exact reviewer-requested Ruff commands

3. **Service-only tester-authority inputs were still required**
   - remediated by adding `default = null` to `tester_authority_receipt_path`, `tester_authority_bundle_path`, and `tester_authority_certificate_identity` in both variable files
   - preserved the child-module service-only non-null validation and extended the focused Terraform hygiene regression to cover this deferred input family

4. **Stale Cloud SQL no-default assertions contradicted the foundation contract**
   - remediated by removing obsolete assertions from `test_gcp_develop_cloud_sql_is_private_minimal_postgresql_without_public_ip`
   - retained the broader staged-input regression as the authoritative default/null and stage-validation proof

5. **Stale root-wide and Direct VPC no-default assertions contradicted the staged-input contract**
   - remediated by removing the root-wide default prohibition and narrowing the Direct VPC test to CIDR validation plus root-module forwarding
   - retained the broader staged-input regression as the authoritative deferred-default and stage-requiredness proof

## 11. Independent rereview outcome

**PASS — 2026-08-27.** The final remediated working-tree surface received independent rereview with no Blocker, High, or Medium finding. This outcome clears only the closeout commit, exact-head verification, exact-range secret scan, and separately approved push/PR sequence; it is not merge authority and does not authorize cloud, backend/state, Terraform plan/apply, or adoption work.

## 12. Requested reviewer outcome

Please return one of:
- **PASS** — no remaining Blocker/High/Medium finding on the current working-tree source-amendment surface
- **CHANGES REQUIRED** — with findings labeled by severity and exact file/line or contract reference

If findings exist, prefer this structure:
1. severity
2. exact surface
3. why it violates the accepted plan / source boundary / evidence contract
4. minimal remediation direction

## 13. Stop boundary after review

If the independent session clears this working tree, the next step is:
1. perform any minimal closeout edits required by review
2. rerun exact working-tree verification
3. create a closeout commit on `fix/foundation-root-stage-gating`
4. rerun exact-head verification and exact-range secret scanning on the committed delta
5. only then push/open PR under explicit approval

Do **not** infer authority for adoption work, backend/state actions, Terraform plan/apply, or any cloud mutation from a PASS on this packet.
