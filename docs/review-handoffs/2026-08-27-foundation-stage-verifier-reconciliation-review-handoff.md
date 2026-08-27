# Focused rereview handoff — foundation-stage verifier reconciliation

**Date:** 2026-08-27
**Branch:** `fix/foundation-stage-verifier-reconciliation`
**PR base:** `develop`
**Exact base:** `origin/develop@d7952b4c362beff5e88f6ec09f2f9a90a1fb3495` (PR #47 merge)
**Review surface:** refreshed uncommitted working-tree slice on a fresh implementation branch from current protected `develop`, after prior rereviews found and this branch remediated the last evidence and verifier-surface mismatches
**Cloud status:** no GCP authentication/inspection, backend/state action, Terraform plan/apply, import, or runtime action

## Purpose
Review the source-only reconciliation that makes `scripts/verify_gcp_foundation.py` match the reviewed post-PR #46 stage contract: `foundation` must prove no executable workload and no Cloud SQL requirement, while later verifier stages remain responsible for fail-closed private Cloud SQL posture checks.

## Scope actually changed

### Production code
- `scripts/verify_gcp_foundation.py`

### Tests
- `tests/unit/test_verify_gcp_foundation.py`

### Living docs / contract summaries
- `CURRENT_WORK.md`
- `ROADMAP.md`
- `NOTES.md`
- `TECHNOLOGY_DECISIONS.md`
- `infra/gcp/README.md`
- `deploy/gcp/staged-plan-approval.md`
- `deploy/gcp/evidence-template.md`

## Prior rereview and remediation
The immediately preceding rereview returned **CHANGES REQUIRED** with three findings that are now remediated:
1. `main()` still aborted collection on missing Cloud SQL in `foundation`; `collect_foundation_snapshot(..., mode=...)` is now stage-aware and treats `NOT_FOUND` / `not found` Cloud SQL reads as `{}` only for `foundation`, while later modes still fail closed.
2. `deploy/gcp/evidence-template.md` still asserted Cloud SQL at every stage; it now records Cloud SQL as absent/out of scope in `foundation` and required/private-path-only in `migration` and `service`.
3. The changed verifier surface failed Ruff because of a line-length regression; that formatting/lint issue is now closed.

An earlier rereview also found one Medium stale-summary issue in `CURRENT_WORK.md`; that historical summary has already been corrected so Task 11 no longer claims foundation-stage private Cloud SQL verification.

No production change broadened gate ordering or cloud/state authority.

## Intended contract of this slice
1. `foundation` mode must not require Cloud SQL inventory or configuration.
2. `foundation` mode must still reject any present Cloud Run job or service workload.
3. `foundation` mode must reject unexpected Cloud SQL presence/configuration as a stage mismatch, not accept it as required success evidence.
4. `migration` and `service` modes must still fail closed on missing or drifted private Cloud SQL posture.
5. Contract-summary docs must stop claiming foundation-mode verification proves a private database path before that lower-layer resource family is in scope.
6. The slice remains source-only and grants no cloud or state authority.

## TDD and verification evidence

### RED
```text
env -u PYTHONPATH uv run pytest tests/unit/test_verify_gcp_foundation.py::test_foundation_mode_treats_cloud_sql_as_deferred_but_later_modes_still_require_it -q
```
Observed: FAIL — foundation mode still emitted `cloud sql inventory drifted from develop-postgres` when Cloud SQL was absent.

### GREEN
Minimal implementation in `scripts/verify_gcp_foundation.py`:
- foundation mode now rejects only unexpected Cloud SQL inventory/configuration presence;
- migration/service modes still require reviewed Cloud SQL inventory and posture;
- collection is now stage-aware, so a missing Cloud SQL read no longer aborts `foundation` mode before evaluation.

Added regression for the collection path:
```text
env -u PYTHONPATH uv run pytest tests/unit/test_verify_gcp_foundation.py::test_foundation_mode_main_allows_absent_cloud_sql_during_collection -q
```
Observed: PASS — `1 passed in 0.04s`

Re-run exact node:
```text
env -u PYTHONPATH uv run pytest tests/unit/test_verify_gcp_foundation.py::test_foundation_mode_treats_cloud_sql_as_deferred_but_later_modes_still_require_it -q
```
Observed: PASS — `1 passed in 0.04s`

### Full in-scope verification
```text
env -u PYTHONPATH uv run ruff check scripts/verify_gcp_foundation.py tests/unit/test_verify_gcp_foundation.py
env -u PYTHONPATH uv run ruff format --check scripts/verify_gcp_foundation.py tests/unit/test_verify_gcp_foundation.py
env -u PYTHONPATH uv run pytest tests/unit/test_verify_gcp_foundation.py -q
env -u PYTHONPATH uv run pytest tests/unit/test_terraform_hygiene.py -q
env -u PYTHONPATH uv run python scripts/validate_terraform_static.py
terraform fmt -check -recursive infra/gcp
terraform -chdir=infra/gcp init -backend=false -input=false -lockfile=readonly
terraform -chdir=infra/gcp validate
terraform -chdir=infra/gcp/bootstrap init -backend=false -input=false -lockfile=readonly
terraform -chdir=infra/gcp/bootstrap validate
git diff --check
```
Observed:
- Ruff lint/format checks: passed
- verifier suite: `40 passed`
- terraform hygiene: `235 passed`
- static validation: `Terraform static validation passed`
- backend-free workload and bootstrap validation: passed
- diff hygiene: passed

## Reviewer focus
1. Confirm foundation-mode Cloud SQL absence is now intentional and exact, not a weakened later-stage verifier boundary.
2. Confirm migration/service modes still fail closed on missing `develop-postgres` inventory and private Cloud SQL posture.
3. Confirm foundation mode still rejects workload inventory/configuration.
4. Confirm `CURRENT_WORK.md:17` is aligned with the corrected verifier contract and no longer claims foundation-stage private Cloud SQL verification.
5. Confirm the doc updates in `TECHNOLOGY_DECISIONS.md`, `infra/gcp/README.md`, `deploy/gcp/staged-plan-approval.md`, and `deploy/gcp/evidence-template.md` match the implemented verifier semantics.
6. Confirm no tracked text implies this slice authorizes source/live inventory, backend/state action, Terraform plan/apply, or cloud mutation.

## Review-surface caveats
- There is no committed branch range yet; review is against the live working-tree diff.
- Exact-range Gitleaks over `origin/develop..HEAD` is not yet meaningful final-head evidence until a commit exists.
- After rereview clears this surface, the next steps are: closeout commit, exact-head verification, exact-range Gitleaks, then push/PR.

## Requested verdict
Return **PASS** or **CHANGES REQUIRED** with severity, exact path/line, reproduction, and minimum remediation. Treat this packet as the refreshed exact-surface handoff after the prior findings were remediated. Do not treat this rereview as approval to commit, push, perform cloud work, or proceed to any later gate.
