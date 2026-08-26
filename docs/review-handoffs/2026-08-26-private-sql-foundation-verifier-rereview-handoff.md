# Focused rereview handoff — private-SQL foundation verifier reconciliation

**Date:** 2026-08-26
**Historical branch:** `fix/foundation-verifier-stage-authority` (retired after merge)
**PR outcome:** PR #42 merged to protected `develop` at `b2d79b54d38dd24819509271646d0c71b593d92e` on 2026-08-26.
**Planning authority merge:** `origin/develop@1c1a7b6782c263b9fdb3ea67fd524328bc537f38` (PR #39 plan publication)
**Historical review base:** `origin/develop@6ef2452d7db812a9c644f328005d5230c8611c39` (PR #41 merge tip)
**Merged implementation tip:** `develop@b2d79b54d38dd24819509271646d0c71b593d92e`
**Review surface:** historical pre-commit working-tree handoff; its evidence was subsequently committed, reviewed, and merged as PR #42
**Post-merge status:** the implementation branch and stale worktree records were retired; initial Gate 2 and partial foundation work are privately recorded, while remaining decision freezes stay separately unapproved
**Cloud status:** no GCP authentication/inspection, Terraform plan/apply, private-network or Cloud SQL provisioning, secret/database action, service start, deployment, tester access, or qualification

## Purpose

Review the bounded implementation of `.hermes/plans/2026-08-25_195726-private-sql-foundation-verifier-reconciliation-plan.md` Tasks 1–2 on the live working tree before any commit, push, or PR action.

## Scope actually changed

### Production code
- `scripts/verify_gcp_foundation.py`

### Tests
- `tests/unit/test_verify_gcp_foundation.py`

### Living docs / evidence
- `CURRENT_WORK.md`
- `ROADMAP.md`
- `NOTES.md`

## Intended contract of this slice

1. `foundation` and `migration` verifier modes must not require later service-stage tester receipt inputs.
2. `service` mode must still require tester receipt/bundle/certificate inputs and still derive authority through `derive_tester_authority_contract(...)`.
3. Decoupling tester authority must **not** weaken the lower-layer Cloud SQL requirement.
4. `foundation` must continue to reject present Cloud Run service/job workload inventory.
5. The slice remains source-only and no-cloud.

## Explicit non-scope

- no Terraform `plan`, `apply`, import, state, or backend migration
- no GCP auth or live inspection
- no private VPC, private-service-access, or Cloud SQL resource creation
- no secret versions/payloads, database users/passwords, or database login
- no migration job execution, Cloud Run service activation, tester grant, or qualification
- no receipt payloads, real principals, project IDs, billing IDs, or live operator-held values in tracked source

## TDD results recorded for this slice

### Task 1 — stage-aware tester authority boundary

Added exact tests:
- `tests/unit/test_verify_gcp_foundation.py::test_foundation_and_migration_modes_accept_absent_tester_inputs`
- `tests/unit/test_verify_gcp_foundation.py::test_service_mode_rejects_absent_tester_inputs_before_live_reads`
- `tests/unit/test_verify_gcp_foundation.py::test_service_mode_derives_tester_authority_contract_before_evaluation`

Observed RED:
```bash
env -u PYTHONPATH uv run pytest \
  tests/unit/test_verify_gcp_foundation.py::test_foundation_and_migration_modes_accept_absent_tester_inputs \
  tests/unit/test_verify_gcp_foundation.py::test_service_mode_rejects_absent_tester_inputs_before_live_reads -q
```
Result: `2 failed`

Observed cause:
- `_parse_args()` still required `--tester-authority-receipt`, `--tester-authority-bundle`, and `--tester-authority-certificate-identity` in every mode.

Minimal GREEN implemented:
- tester receipt/bundle/certificate arguments are optional at parse time;
- `_derive_service_tester_authority(args)` rejects missing tester inputs only for `--mode service`;
- `main()` injects `private_invoker_principal` and `tester_authority_receipt_sha256` into the contract only in service mode.

Observed GREEN:
- reran the same focused command → `2 passed`
- `env -u PYTHONPATH uv run pytest tests/unit/test_verify_gcp_foundation.py::test_service_mode_derives_tester_authority_contract_before_evaluation -q` → `1 passed`

### Task 2 — preserve Cloud SQL as an explicit lower-layer requirement

Added exact regression:
- `tests/unit/test_verify_gcp_foundation.py::test_foundation_mode_still_requires_private_cloud_sql_after_tester_decoupling`

Observed result:
```bash
env -u PYTHONPATH uv run pytest \
  tests/unit/test_verify_gcp_foundation.py::test_foundation_mode_still_requires_private_cloud_sql_after_tester_decoupling -q
```
Result: `1 passed`

Classification:
- honest GREEN regression; current behavior already still rejects absent `develop-postgres`, public/wrong-version Cloud SQL posture, and present Cloud Run service/job workloads in foundation mode.

## Verified local evidence

- `env -u PYTHONPATH uv run pytest tests/unit/test_verify_gcp_foundation.py -q` → `39 passed`
- `env -u PYTHONPATH uv run pytest tests/unit/test_terraform_hygiene.py -q` → `234 passed`
- `env -u PYTHONPATH uv run python scripts/validate_terraform_static.py` → `Terraform static validation passed`
- Focused rereview remediation: `env -u PYTHONPATH uv run ruff check scripts/verify_gcp_foundation.py tests/unit/test_verify_gcp_foundation.py` → passed after replacing B010-triggering `setattr()` calls with direct module-attribute assignment through `cast(Any, module)`.
- Focused formatting verification: `env -u PYTHONPATH uv run ruff format --check scripts/verify_gcp_foundation.py tests/unit/test_verify_gcp_foundation.py` → passed.
- `git diff --check` → passed
- `git status --short --branch` currently shows only the intended working-tree surface plus this handoff packet

## Review-surface caveats

- `git rev-list --count origin/develop..HEAD` is `0`, so there is no committed branch range yet.
- Exact-range `git diff --check origin/develop...HEAD` and exact-range `gitleaks git --log-opts 'origin/develop..HEAD'` are **not yet meaningful final-head evidence** for this slice.
- Review must be grounded in the live working-tree diff, not a committed PR range.

## Reviewer focus

1. Confirm `scripts/verify_gcp_foundation.py` does not derive or require tester authority outside service mode.
2. Confirm service mode still fails closed on missing tester receipt inputs before any live-read path.
3. Confirm service mode still derives tester authority via `derive_tester_authority_contract(...)` rather than accepting caller-supplied principal/digest values.
4. Confirm foundation/migration modes do not accidentally read `private_invoker_principal` or `tester_authority_receipt_sha256`.
5. Confirm Cloud SQL remains required in foundation mode and Cloud Run service/job presence still fails foundation mode.
6. Confirm living docs now describe the exact merged base (`6ef2452`), current branch, no-cloud boundary, and review-before-commit posture truthfully.

## Requested verdict

Return **PASS** or **CHANGES REQUIRED** with severity, exact path/line, reproduction, and minimum remediation. Do not treat this working-tree review surface as approval to commit, push, open a PR, perform cloud work, or proceed to any later gate.

## Stop boundary after rereview

Review/remediate this exact working-tree slice first. Only after rereview clears the surface should the next steps be:
1. closeout commit under explicit approval,
2. exact-head verification,
3. exact-range Gitleaks on the committed range,
4. push,
5. PR open/update,
6. protected CI observation.
