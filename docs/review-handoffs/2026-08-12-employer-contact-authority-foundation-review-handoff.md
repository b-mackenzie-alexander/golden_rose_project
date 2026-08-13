# Review Handoff — EmployerContact authority foundation implementation slice

**Date:** 2026-08-12
**Branch:** `feat/employer-contact-authority-foundation`
**Target PR base:** `develop`
**Planning base / merge tip:** `origin/develop` at `745f9e88a23bea57c70a2e0fee7541c6984c65f7` (`docs: accept EmployerContact authority planning packet (#19)`)
**Controlling authorities:**
- `docs/adr/ADR-0008-phase-1-employer-contact-authority-foundation.md`
- `.hermes/plans/2026-08-12_111500-phase-1-employer-contact-authority-foundation-plan.md`
- `GIT_WORKFLOW.md`
**Review surface:** local uncommitted working tree
**Ahead commits vs `origin/develop` at handoff creation:** `0`
**Behind commits vs `origin/develop` at handoff creation:** `0`
**PR status:** no PR yet; commit/push/PR-open remain blocked on independent review, post-review closeout, final-head verification, and exact-range secret scanning

## 1. Current branch truth

Observed live branch state at handoff creation:
- `git rev-parse HEAD` → `745f9e88a23bea57c70a2e0fee7541c6984c65f7`
- `git rev-parse origin/develop` → `745f9e88a23bea57c70a2e0fee7541c6984c65f7`
- `git rev-list --count origin/develop..HEAD` → `0`
- `git rev-list --count HEAD..origin/develop` → `0`

Interpretation:
- this slice is **not** a committed PR range yet
- exact-range review over `origin/develop...HEAD` is not yet meaningful
- exact-range Gitleaks is still pending by design
- review must target the **live working-tree diff** and the real local verification evidence already recorded in the repo

## 2. Approved scope and explicit non-scope

This handoff covers only the bounded ADR-0008 implementation slice:
- backend-only EmployerContact create beneath an existing draft Employer
- bounded parent-scoped collection query for authoritative rediscovery
- exact parent-scoped read
- generalized type-bound entity-authority registry for receipt/audit correspondence
- strict contact transport/response schema and permission boundaries
- focused living-doc alignment and independent-review handoff preparation

It must confirm the lane did **not** widen into:
- browser/UI work
- phone, email, relationship/title, preferred language/contact method, status, consent, outreach, correction, update, delete, or global/name search
- Worksite, StaffingRequest, ShiftNeed, queue, calendar, map, worker, or dashboard work
- real identity/session/MFA/provider rollout
- deployment/GCP/runtime expansion
- client/live data, migration/import, or production activation
- broader roadmap completion claims for employer/contact/worksite/request/shift persistence

## 3. Primary files in the review surface

### Product / migration / persistence / API
- `migrations/versions/0003_add_revision_compatibility_fields.py`
- `migrations/versions/0004_employer_contact_authority.py`
- `src/golden_rose/api/dependencies.py`
- `src/golden_rose/api/staff/employers.py`
- `src/golden_rose/api/staff/schemas.py`
- `src/golden_rose/application/contact_cursor.py`
- `src/golden_rose/application/contact_text.py`
- `src/golden_rose/application/create_draft_employer.py`
- `src/golden_rose/application/create_employer_contact.py`
- `src/golden_rose/application/get_employer_contact.py`
- `src/golden_rose/application/query_employer_contacts.py`
- `src/golden_rose/auth/permissions.py`
- `src/golden_rose/persistence/audit_events.py`
- `src/golden_rose/persistence/command_receipts.py`
- `src/golden_rose/persistence/employer_contacts.py`
- `src/golden_rose/persistence/entity_authorities.py`
- `src/golden_rose/persistence/models.py`

### Tests
- `tests/integration/application/test_create_draft_employer.py`
- `tests/integration/application/test_create_employer_contact.py`
- `tests/integration/api/test_staff_employer_reads.py`
- `tests/integration/api/test_staff_employers.py`
- `tests/integration/test_initial_migration.py`
- `tests/unit/api/test_dependencies.py`
- `tests/unit/api/test_employer_contact_schemas.py`
- `tests/unit/application/test_contact_cursor.py`
- `tests/unit/application/test_contact_text.py`
- `tests/unit/auth/test_permissions.py`

### Living docs / evidence / review state
- `AGENTS.md`
- `ARCHITECTURE.md`
- `CURRENT_WORK.md`
- `NOTES.md`
- `README.md`
- `ROADMAP.md`
- `SECURITY.md`
- `TECHNICAL_REQUIREMENTS.md`
- `TECHNOLOGY_DECISIONS.md`
- `docs/adr/ADR-0008-phase-1-employer-contact-authority-foundation.md`
- `docs/adr/README.md`
- `docs/review-handoffs/2026-08-12-employer-contact-authority-foundation-review-handoff.md`

## 4. What changed in this slice

### Migration and authority foundation
- Added `employer_contacts` and `entity_authorities` to generalize the prior Employer-only receipt/event integrity model.
- Added migration `0004_employer_contact_authority.py` plus supporting metadata and persistence helpers.
- Adapted the existing Employer create path so Employer authority rows are inserted atomically under the upgraded schema.
- Extended receipt and audit authority checks to include exact type-bound command/result/event relationships for Employer and EmployerContact.

### Application layer
- Added shared contact-name normalization and validation helpers.
- Added EmployerContact create command logic with atomic authority/contact/receipt/event writes, replay handling, bounded conflict behavior, audit minimization, concurrency coverage, and safe persistence translation.
- Added parent/page-size-bound opaque contact cursor helpers.
- Added parent-scoped query and exact-read application commands with authorization-first ordering, minimized read models, no-write behavior, and value-safe persistence handling.

### API and permission surface
- Added exact EmployerContact request/response/query schemas.
- Added synthetic/local principal support for `employer_contact:draft:create` and `employer_contact:read`.
- Added staff-plane routes for:
  - `POST /api/staff/v1/employers/{employer_id}/contacts`
  - `POST /api/staff/v1/employers/{employer_id}/contacts/query`
  - `GET /api/staff/v1/employers/{employer_id}/contacts/{employer_contact_id}`
- Completed the bounded API failure matrices, OpenAPI route guards, unsupported-path/method behavior, and application/access-log privacy assertions through the approved Task 7 exact-node list.

### Living docs and handoff state
- Updated status surfaces so the repo now says the exact-node implementation list is exhausted and the next real step is independent review.
- Added this durable review packet for the local working-tree surface.

## 5. Exact-node completion summary

The approved ADR-0008 execution lane is locally complete through its currently authorized exact nodes:
- **Task 2:** GREEN through the coupled migration/writer checkpoint and the authority-table/update-delete/downgrade safety nodes.
- **Task 3:** GREEN through all three contact-name normalization/validation nodes.
- **Task 5:** fully GREEN through EmployerContact create, replay/conflict, concurrency, rollback, audit minimization, and safe-persistence coverage.
- **Task 6:** GREEN through the full cursor/query/get application lane.
- **Task 7:** GREEN through cycle 17 across schema/permission/dependency/API/OpenAPI/unsupported-path/logging/privacy boundaries.

Task 7’s approved exact-node list is exhausted. No further implementation was performed after that boundary.

## 6. Real verification evidence already observed

For the full node-by-node ledger, commands, and honest RED/GREEN classifications, see `NOTES.md` entries covering the EmployerContact coding lane (`NOTES.md` around lines 1388-1528 at handoff creation).

Key observed evidence already in the repo includes:

### Migration and writer compatibility
- Coupled migration/writer checkpoint:
  - `env -u PYTHONPATH GOLDEN_ROSE_DATABASE_URL='[REDACTED]' uv run pytest tests/integration/test_initial_migration.py::test_employer_contact_migration_upgrades_populated_employer_authority_without_rewriting_history tests/integration/application/test_create_draft_employer.py::test_existing_employer_create_remains_atomic_and_replay_safe_on_employer_contact_schema -q`
  - result: `2 passed in 0.50s`

### Contact API/OpenAPI/read-route proof points
- Route-set guard bundle:
  - `env -u PYTHONPATH GOLDEN_ROSE_ENVIRONMENT=local GOLDEN_ROSE_AUTH_MODE=[REDACTED] GOLDEN_ROSE_DATABASE_URL='[REDACTED]' GOLDEN_ROSE_SYNTHETIC_STAFF_ID='[REDACTED]' uv run pytest tests/integration/api/test_staff_employer_reads.py::test_openapi_exposes_only_approved_staff_employer_routes tests/integration/api/test_staff_employers.py::test_openapi_exposes_only_intended_staff_route tests/integration/api/test_staff_employers.py::test_openapi_exposes_only_create_search_detail_and_revision_routes tests/integration/api/test_staff_employers.py::test_staff_employer_revision_openapi_exposes_only_approved_contract tests/integration/api/test_staff_employer_reads.py::test_staff_employer_contact_openapi_exposes_only_approved_contract -q`
  - result: `5 passed, 1 warning in 0.91s`
- Unsupported-path/method exact node:
  - `env -u PYTHONPATH GOLDEN_ROSE_ENVIRONMENT=local GOLDEN_ROSE_AUTH_MODE=[REDACTED] GOLDEN_ROSE_DATABASE_URL='[REDACTED]' GOLDEN_ROSE_SYNTHETIC_STAFF_ID='[REDACTED]' uv run pytest tests/integration/api/test_staff_employer_reads.py::test_staff_employer_contact_unmatched_and_method_not_allowed_routes_do_not_execute_or_reflect_contact_markers -q`
  - result: `1 passed, 1 warning in 0.89s`
- Logging/privacy exact node after test-only adjustment:
  - `env -u PYTHONPATH GOLDEN_ROSE_ENVIRONMENT=local GOLDEN_ROSE_AUTH_MODE=[REDACTED] GOLDEN_ROSE_DATABASE_URL='[REDACTED]' GOLDEN_ROSE_SYNTHETIC_STAFF_ID='[REDACTED]' uv run pytest tests/integration/api/test_staff_employer_reads.py::test_staff_employer_contact_routes_do_not_log_contact_or_authority_markers -q`
  - result: `1 passed, 1 warning in 0.95s`
- Focused final follow-up for the last two Task 7 nodes:
  - `env -u PYTHONPATH GOLDEN_ROSE_ENVIRONMENT=local GOLDEN_ROSE_AUTH_MODE=[REDACTED] GOLDEN_ROSE_DATABASE_URL='[REDACTED]' GOLDEN_ROSE_SYNTHETIC_STAFF_ID='[REDACTED]' uv run pytest tests/integration/api/test_staff_employer_reads.py::test_staff_employer_contact_unmatched_and_method_not_allowed_routes_do_not_execute_or_reflect_contact_markers tests/integration/api/test_staff_employer_reads.py::test_staff_employer_contact_routes_do_not_log_contact_or_authority_markers -q`
  - result: `2 passed, 1 warning in 0.78s`

### Hygiene
- `git diff --check`
  - result: passed repeatedly during the lane, including after the cycle-17 closeout and again during handoff preparation

## 7. Honest caveats the reviewer should treat carefully

- The review surface is an **uncommitted local working tree**, not a PR diff.
- `origin/develop..HEAD` contains `0` commits, so committed-range review and committed-range secret scanning are still pending.
- Some service-backed selectors required an explicit disposable PostgreSQL URL override (`[REDACTED]`) because the repo-default integration DSN was stale during those focused runs. That setup repair is recorded in `NOTES.md` and should not be mistaken for product evidence.
- The remaining warning in current focused pytest runs is the pre-existing `StarletteDeprecationWarning` emitted by `fastapi.testclient`/`httpx`, not a known product defect.
- Task 7 cycle 17 was a **test-only** RED→GREEN: the first draft of the new node over-claimed against third-party `httpx` request logs captured by `caplog`; the bounded fix was to constrain the forbidden log surface to the relevant `golden_rose*` and `uvicorn*` logger families.

## 8. Reviewer focus areas

The independent review should explicitly verify:
1. migration `0004` lock ordering, backfill, typed authority constraints, downgrade refusal logic, and ordinary-row mutation-guard truthfulness
2. the existing Employer create path remains atomic and replay-safe on the upgraded authority schema
3. EmployerContact create preserves exact permission ordering, draft-parent gating, normalized fingerprinting, replay/conflict semantics, concurrency behavior, rollback, and audit minimization
4. query and exact-read routes remain parent-scoped, minimized, no-store, write-free, and nondisclosing across denied, validation, not-found, persistence, and unexpected-failure paths
5. OpenAPI and route inventory stay exactly within the approved nested contact surface and do not leak adjacent unapproved routes
6. unsupported methods/unmatched subpaths do not execute contact logic, do not reflect contact/authority markers, and do not claim operation-level cache/idempotency headers
7. application/access-log and audit surfaces do not disclose contact PII or authority markers beyond the approved changed-field naming contract
8. the review packet and living docs now describe the slice honestly as a **review handoff on a local working tree**, not as a PR-ready committed range
9. no adjacent scope entered the branch: browser, Worksite/Request/Shift, deployment, real identity, or live/client data

## 9. Secret-scan / range-hygiene posture at handoff

- `git diff --check` passes on the live working tree.
- Exact committed-range secret scanning has **not** been rerun for this slice because there are still `0` commits ahead of `origin/develop`.
- Per the handoff workflow, exact-range Gitleaks should run only after the reviewed slice is committed and the verification target becomes a real `origin/develop..HEAD` range.

## 10. Final local review-surface verification at handoff creation

Observed commands:

```bash
git status --short && printf '\n---BRANCH---\n' && git branch --show-current
git rev-parse HEAD
git rev-parse origin/develop
git rev-list --count origin/develop..HEAD
git rev-list --count HEAD..origin/develop
git diff --name-only
git diff --stat
git diff --check
```

Observed truth:
- branch: `feat/employer-contact-authority-foundation`
- review surface: **local uncommitted working tree**
- ahead commits: `0`
- behind commits: `0`
- base `HEAD == origin/develop == 745f9e88a23bea57c70a2e0fee7541c6984c65f7`
- `git diff --check`: passed
- primary changed surface includes product code, tests, living docs, and this review packet; there is no committed PR range yet

## 11. Stop boundary before PR open

This slice is being handed off for **independent review**, not declared PR-ready.

Required next sequence:
1. independent review of the live working-tree diff and this handoff packet
2. remediate any findings on the same local branch without widening scope
3. create the closeout commit for the exact reviewed surface
4. rerun final-head focused and broader verification on the committed head
5. run exact-range secret scanning on `origin/develop..HEAD`
6. only then push and open/update the PR

## 12. Handoff disposition

This bounded EmployerContact authority foundation slice appears complete enough to hand off for independent review.

The correct current disposition is:
- **cleared for independent review handoff on the local working tree**
- **not yet cleared for commit/push/PR/merge**
- **final-head verification and exact-range secret scanning still belong after review and commit**

## 13. 2026-08-13 remediation addendum after independent review blockers

An independent review of the same local working-tree surface returned a **not PR-ready yet** verdict because three required local quality gates were failing on the uncommitted rereview surface:

1. `env -u PYTHONPATH uv run ruff format --check .` reported formatter drift.
2. `env -u PYTHONPATH uv run pytest tests/unit/application/test_contact_text.py tests/unit/application/test_contact_cursor.py tests/unit/api/test_employer_contact_schemas.py tests/unit/auth/test_permissions.py tests/unit/api/test_dependencies.py -q` failed with three stale permission expectations in `tests/unit/api/test_dependencies.py`.
3. `env -u PYTHONPATH uv run mypy src tests` failed in `tests/integration/api/test_staff_employer_reads.py` because the test referenced implicitly exported names from module imports rather than explicit application modules.

### Narrow remediation applied on the same local branch
- Updated the three stale synthetic/local permission expectations in `tests/unit/api/test_dependencies.py` so they include the approved `employer_contact:draft:create` and `employer_contact:read` permissions.
- Adjusted `tests/integration/api/test_staff_employer_reads.py` so the mypy-sensitive saved references come from the explicit application modules while route monkeypatches still exercise `golden_rose.api.staff.employers`.
- Ran Ruff formatting on the exact reviewer-identified files and then completed the narrowly adjacent Ruff cleanup required for the full repo-local quality gate to pass on the current working tree.

### Exact rerun commands and observed results after remediation
- `env -u PYTHONPATH uv run ruff format --check .`
  - result: `131 files already formatted`
- `env -u PYTHONPATH uv run ruff check .`
  - result: `All checks passed!`
- `env -u PYTHONPATH uv run mypy src tests`
  - result: `Success: no issues found in 61 source files`
- `env -u PYTHONPATH uv run pytest tests/unit/application/test_contact_text.py tests/unit/application/test_contact_cursor.py tests/unit/api/test_employer_contact_schemas.py tests/unit/auth/test_permissions.py tests/unit/api/test_dependencies.py -q`
  - result: `29 passed, 1 warning in 0.92s`
- `env -u PYTHONPATH uv run pytest tests/integration/test_initial_migration.py::test_employer_contact_migration_upgrades_populated_employer_authority_without_rewriting_history tests/integration/application/test_create_draft_employer.py::test_existing_employer_create_remains_atomic_and_replay_safe_on_employer_contact_schema tests/integration/api/test_staff_employer_reads.py::test_post_staff_employer_contact_returns_exact_201_contract_and_replay_headers tests/integration/api/test_staff_employer_reads.py::test_post_staff_employer_contact_failure_matrix_is_exact_no_store_value_safe_and_write_free tests/integration/api/test_staff_employer_reads.py::test_staff_employer_contact_openapi_exposes_only_approved_contract tests/integration/api/test_staff_employer_reads.py::test_staff_employer_contact_unmatched_and_method_not_allowed_routes_do_not_execute_or_reflect_contact_markers tests/integration/api/test_staff_employer_reads.py::test_staff_employer_contact_routes_do_not_log_contact_or_authority_markers -q`
  - result: `7 passed, 1 warning in 3.33s`
- `git diff --check`
  - result: passed

### Updated rereview surface statement
- The rereview surface is still the **local uncommitted working tree** on `feat/employer-contact-authority-foundation` above `origin/develop` at `745f9e88a23bea57c70a2e0fee7541c6984c65f7`.
- This remediation is **not committed yet**, so it still is not a PR-ready committed range.

## 14. 2026-08-13 migration-contract remediation addendum after follow-up rereview

The next independent rereview of the same local uncommitted surface proved that the prior remediation addendum had closed only the lint/unit/mypy layer, not the migration-contract findings. The reviewer directly confirmed four remaining blockers on the live filesystem:

1. `migrations/versions/0003_add_revision_compatibility_fields.py` was still retroactively widened to include `create_employer_contact` and `employer_contact.created`, violating the requirement that all EmployerContact widening live in `0004` rather than rewriting revision-0003 history.
2. `migrations/versions/0004_employer_contact_authority.py` still lacked the reviewed upgrade/downgrade lock-order and fail-closed successor-data refusal behavior.
3. `tests/integration/test_initial_migration.py::test_initial_metadata_exposes_authority_relationships` still targeted the predecessor Employer-only authority FK surface and failed with `KeyError: 'fk_command_receipts_result_employer'`.
4. `env -u PYTHONPATH uv run ruff format --check .` still reported one remaining formatter drift line in `tests/integration/api/test_staff_employer_reads.py`.

### Narrow remediation applied for those follow-up blockers
- Restored `migrations/versions/0003_add_revision_compatibility_fields.py` to the exact historical revision-only contract so it once again permits only `create_draft_employer` and `revise_draft_employer` plus the corresponding Employer-only audit schema/event values.
- Reworked `migrations/versions/0004_employer_contact_authority.py` so `0004` now solely owns the EmployerContact widening and explicitly enforces the approved lock/refusal contract:
  - upgrade takes `SHARE ROW EXCLUSIVE` locks on `command_receipts`, `employers`, then `audit_events`
  - downgrade takes `SHARE ROW EXCLUSIVE` locks on `command_receipts`, `employers`, `employer_contacts`, `entity_authorities`, then `audit_events`
  - downgrade executes a `SELECT EXISTS` successor-data preflight and raises `RuntimeError("successor employer-contact authority data blocks downgrade")` before destructive DDL when any EmployerContact/contact-authority/contact-receipt/contact-event state exists
- Updated `tests/integration/test_initial_migration.py::test_initial_metadata_exposes_authority_relationships` to assert the typed `entity_authorities` FK/unique surface rather than the predecessor Employer-only FK shape.
- Seeded the required Employer authority row in the populated head-schema downgrade tests so those fixtures remain valid under the typed authority spine before downgrade is exercised.
- Collapsed the remaining wrapped assignment in `tests/integration/api/test_staff_employer_reads.py` so the formatter gate is truly clean on the live tree.

### Exact rerun commands and observed results after migration-contract remediation
- `env -u PYTHONPATH uv run ruff format --check .`
  - result: `131 files already formatted`
- `env -u PYTHONPATH uv run pytest tests/integration/test_initial_migration.py::test_initial_metadata_exposes_authority_relationships -q`
  - result: `1 passed in 0.15s`
- `env -u PYTHONPATH uv run pytest tests/integration/test_initial_migration.py::test_initial_metadata_exposes_authority_relationships tests/integration/test_initial_migration.py::test_employer_contact_migration_upgrades_populated_employer_authority_without_rewriting_history tests/integration/test_initial_migration.py::test_revision_empty_downgrade_restores_closeout_schema_and_guards tests/integration/test_initial_migration.py::test_revision_populated_create_only_downgrade_preserves_rows_correspondence_constraints_and_guards tests/integration/test_initial_migration.py::test_revision_populated_downgrade_fails_closed_and_preserves_schema_data_guards -q`
  - result: `5 passed in 0.80s`
- `env -u PYTHONPATH uv run ruff check .`
  - result: `All checks passed!`
- `env -u PYTHONPATH uv run mypy src tests`
  - result: `Success: no issues found in 61 source files`
- `env -u PYTHONPATH uv run pytest tests/unit/application/test_contact_text.py tests/unit/application/test_contact_cursor.py tests/unit/api/test_employer_contact_schemas.py tests/unit/auth/test_permissions.py tests/unit/api/test_dependencies.py -q`
  - result: `29 passed, 1 warning in 0.46s`
- `env -u PYTHONPATH uv run pytest tests/integration/test_initial_migration.py::test_employer_contact_migration_upgrades_populated_employer_authority_without_rewriting_history tests/integration/application/test_create_draft_employer.py::test_existing_employer_create_remains_atomic_and_replay_safe_on_employer_contact_schema tests/integration/api/test_staff_employer_reads.py::test_post_staff_employer_contact_returns_exact_201_contract_and_replay_headers tests/integration/api/test_staff_employer_reads.py::test_post_staff_employer_contact_failure_matrix_is_exact_no_store_value_safe_and_write_free tests/integration/api/test_staff_employer_reads.py::test_staff_employer_contact_openapi_exposes_only_approved_contract tests/integration/api/test_staff_employer_reads.py::test_staff_employer_contact_unmatched_and_method_not_allowed_routes_do_not_execute_or_reflect_contact_markers tests/integration/api/test_staff_employer_reads.py::test_staff_employer_contact_routes_do_not_log_contact_or_authority_markers -q`
  - result: `7 passed, 1 warning in 1.02s`
- `git diff --check`
  - result: passed

### Updated rereview disposition after migration-contract remediation
- The review surface is still the **local uncommitted working tree** on `feat/employer-contact-authority-foundation` above `origin/develop`.
- The migration-contract blockers identified by the follow-up rereview are now remediated and locally reverified.
- This slice is still **not** commit/push/PR-ready yet, because the remediation itself remains uncommitted and still requires one more independent rereview of the exact live working-tree surface.
- The remediation itself now requires **independent re-review** before closeout commit, final-head verification, exact-range secret scanning, push, or PR.

## 15. 2026-08-13 broader migration/application authority-harness remediation addendum

The next independent rereview confirmed the named blockers from addendum 14 were closed, but it correctly rejected PR preparation because adjacent in-scope full-file suites still contained stale predecessor-authority assumptions:

1. `tests/integration/test_initial_migration.py -q` still had stale FK assertions in broader revision/live-schema authority tests and manual head-schema Employer seeds without matching `entity_authorities` rows.
2. `tests/integration/application/test_create_draft_employer.py -q` still had a manual replay seed that inserted Employer/current-audit/receipt rows without the required typed authority row.
3. The append-only and duplicate-event migration guards were failing before their intended assertions because their manual Employer receipt/event fixtures did not seed the typed authority row required by the current schema.

### Narrow remediation applied for those broader authority-harness blockers
- Updated the remaining in-scope migration FK assertions to the typed authority surface:
  - `fk_command_receipts_result_entity_authority`
  - `fk_command_receipts_creation_event`
  - `fk_audit_events_entity_authority`
  - `fk_audit_events_command_result`
  - `uq_command_receipts_command_result_entity`
- Added a small local `_insert_employer_authority` helper to `tests/integration/test_initial_migration.py` and used it only where a head-schema manual Employer seed is intended to proceed to receipt/event/append-only assertions.
- Added the same narrow helper to `tests/integration/application/test_create_draft_employer.py` for the manually corrupted replay fixtures so those tests exercise replay/authority validation rather than failing on the new typed FK prerequisite.

### Exact rerun commands and observed results after broader authority-harness remediation
- `env -u PYTHONPATH GOLDEN_ROSE_DATABASE_URL='[REDACTED]' uv run pytest tests/integration/test_initial_migration.py -q`
  - result: `30 passed in 2.63s`
- `env -u PYTHONPATH GOLDEN_ROSE_DATABASE_URL='[REDACTED]' uv run pytest tests/integration/application/test_create_draft_employer.py -q`
  - result: `17 passed in 0.59s`
- `env -u PYTHONPATH uv run ruff format --check .`
  - result: `131 files already formatted`
- `env -u PYTHONPATH uv run ruff check .`
  - result: `All checks passed!`
- `env -u PYTHONPATH uv run mypy src tests`
  - result: `Success: no issues found in 61 source files`
- `git diff --check`
  - result: passed

### Updated rereview disposition after broader authority-harness remediation
- The review surface is still the **local uncommitted working tree** on `feat/employer-contact-authority-foundation` above `origin/develop`.
- The broader migration/application authority-harness blockers identified by the latest rereview are now remediated and locally reverified.
- This slice remains **not** commit/push/PR-ready yet, because the remediation itself is uncommitted and still requires independent rereview of the exact live working-tree surface.

## 16. 2026-08-13 PR #20 application-check remediation addendum

After independent rereview accepted the local surface, the slice was committed as `42363c1` and opened as PR #20. The required `application` check failed during the full CI command:

- `uv run pytest --cov=golden_rose --cov-report=term-missing --cov-fail-under=95`

### Observed CI failure class
- The failing tests were in `tests/integration/application/test_revise_draft_employer.py` and `tests/integration/application/test_revise_draft_employer_post_merge.py`.
- The common failure was stale full-suite revision harness data: manual Employer fixtures inserted `employers`, and sometimes matching receipt/event rows, without the typed `entity_authorities` row now required by the generalized authority spine.
- The failures surfaced as `fk_command_receipts_result_entity_authority` and `fk_audit_events_entity_authority` violations before the tests reached their intended revision receipt/event/replay/concurrency assertions.
- The below-threshold coverage line in CI was a consequence of the aborted failing pytest run, not the primary defect.

### Narrow remediation applied locally
- Added a local `_insert_employer_authority(...)` helper to `tests/integration/application/test_revise_draft_employer.py`.
- Added a local `_insert_employer_authority(...)` helper to `tests/integration/application/test_revise_draft_employer_post_merge.py`.
- Seeded typed Employer authority rows for manual Employer fixtures intended to proceed to revision command/audit/replay/concurrency assertions.
- In the inconsistent-target replay regression, seeded authority for both the requested employer and the replay-target employer so the test reaches the intended malformed-authority replay boundary rather than failing early on the registry FK.

### Exact local repro after remediation
- `env -u PYTHONPATH GOLDEN_ROSE_DATABASE_URL='[REDACTED]' uv run pytest tests/integration/application/test_revise_draft_employer.py tests/integration/application/test_revise_draft_employer_post_merge.py -q`
  - result: `29 passed in 0.85s`
- The first full local rerun of CI's pytest command then reached completion but still failed the coverage threshold at `94.45%`, so a bounded contact-cursor unit regression was added to cover approved malformed payload-shape rejection branches.
- `env -u PYTHONPATH uv run pytest tests/unit/application/test_contact_cursor.py -q`
  - result: `3 passed in 0.28s`
- `env -u PYTHONPATH GOLDEN_ROSE_ENVIRONMENT=test GOLDEN_ROSE_AUTH_MODE=synthetic GOLDEN_ROSE_SYNTHETIC_STAFF_ID='[REDACTED]' GOLDEN_ROSE_DATABASE_URL='[REDACTED]' uv run pytest --cov=golden_rose --cov-report=term-missing --cov-fail-under=95`
  - result: `284 passed, 1 warning` with total coverage `96.22%`

### Current disposition
- The PR #20 remediation was committed as `f00de15` and pushed.
- Exact-range Gitleaks across `745f9e88a23bea57c70a2e0fee7541c6984c65f7..f00de15af518e555a66c5ee354c85a634c5b3704` scanned `2 commits` and found no leaks.
- PR #20 was monitored after the push until `application`, `check`, `enforce`, and CodeRabbit all reported success for `f00de15`.
