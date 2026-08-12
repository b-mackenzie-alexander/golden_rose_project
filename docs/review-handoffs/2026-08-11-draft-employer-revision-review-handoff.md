# Review Handoff — Draft Employer revision implementation slice

> **Historical handoff notice:** Sections 1-12 record the pre-PR review surface that ultimately merged through PR #17 at `1543248`. Their branch, commit-count, and stop-boundary statements are preserved as historical evidence, not current repository state. Section 13 records the separate post-merge remediation handoff that ultimately merged through PR #18 at `a4d8f90`; its pre-merge stop statements are also historical.

**Date:** 2026-08-11
**Branch:** `feat/staff-draft-employer-revision`
**Target PR base:** `develop`
**Planning base / merge tip:** `origin/develop` at `1c66eeb92cd384eb32e345a9f7c3fcb424308825` (`docs: accept draft Employer revision planning packet (#16)`)
**Controlling authorities:**
- `docs/adr/ADR-0007-phase-1-draft-employer-revision-boundary.md`
- `.hermes/plans/2026-08-08_111916-phase-1-draft-employer-revision-plan.md`
- `.hermes/plans/2026-08-11_154209-task-10-privacy-localization-accessibility-transition-plan.md`
**Review surface:** local uncommitted working tree
**Ahead commits vs `origin/develop` at handoff creation:** `0`
**Behind commits vs `origin/develop` at handoff creation:** `0`
**PR status:** no PR yet; commit/push/PR-open remain blocked on independent review and post-review closeout

## 1. Current branch truth

Observed live branch state at handoff creation:
- `git rev-parse HEAD` → `1c66eeb92cd384eb32e345a9f7c3fcb424308825`
- `git rev-parse origin/develop` → `1c66eeb92cd384eb32e345a9f7c3fcb424308825`
- `git rev-list --count origin/develop..HEAD` → `0`
- `git rev-list --count HEAD..origin/develop` → `0`

Interpretation:
- this slice is **not** a committed PR range yet
- exact-range review over `origin/develop...HEAD` is not yet meaningful
- review must target the **live working-tree diff** and real local verification evidence

## 2. Approved scope and non-scope

This handoff covers the bounded Phase 1 draft Employer revision slice only:
- draft-only revision of `display_name` and `employer_type`
- expected-version / idempotency / current-authoritative replay semantics
- strict browser contract hardening for revision/detail responses
- English/Spanish parity
- automated accessibility and focus/announcement behavior
- privacy / side-channel / diagnostic redaction evidence
- focused service-backed revision diagnostic verification under approved local PostgreSQL scope

It must confirm the lane did **not** widen into:
- public worker/employer workflows
- real auth/session/identity rollout
- additional entity surfaces beyond draft Employer name/type revision
- live/client data usage
- production/deployment/GCP work
- human browser/manual accessibility or fluent-language qualification claims
- post-Task-10 implementation beyond the approved review/handoff step

## 3. Primary files in the review surface

### Product / browser client / frontend
- `apps/web/src/api/employerClient.ts`
- `apps/web/src/api/employerContracts.ts`
- `apps/web/src/api/employerClient.test.ts`
- `apps/web/src/employers/EmployerRevisionForm.tsx`
- `apps/web/src/employers/EmployerRevisionForm.test.tsx`
- `apps/web/src/employers/EmployerWorkspace.tsx`
- `apps/web/src/employers/EmployerWorkspace.test.tsx`
- `apps/web/src/employers/EmployerCreateForm.tsx`
- `apps/web/src/employers/EmployerDetail.tsx`
- `apps/web/src/employers/EmployerSearch.tsx`
- `apps/web/src/i18n/messages.ts`
- `apps/web/src/i18n/LanguageProvider.test.tsx`
- `apps/web/src/test/valueSafeDiagnostics.ts`
- `apps/web/src/test/valueSafeDiagnostics.test.ts`
- `apps/web/src/app/App.test.tsx`

### Backend / persistence / migration / API
- `src/golden_rose/application/revise_draft_employer.py`
- `src/golden_rose/application/create_draft_employer.py`
- `src/golden_rose/application/errors.py`
- `src/golden_rose/api/staff/employers.py`
- `src/golden_rose/api/staff/schemas.py`
- `src/golden_rose/api/errors.py`
- `src/golden_rose/api/dependencies.py`
- `src/golden_rose/auth/permissions.py`
- `src/golden_rose/persistence/employers.py`
- `src/golden_rose/persistence/command_receipts.py`
- `src/golden_rose/persistence/audit_events.py`
- `src/golden_rose/persistence/models.py`
- `migrations/versions/0003_add_revision_compatibility_fields.py`

### Tests / evidence / living docs
- `tests/integration/application/test_revise_draft_employer.py`
- `tests/integration/api/test_staff_employers.py`
- `tests/integration/api/test_staff_employer_reads.py`
- `tests/integration/application/test_create_draft_employer.py`
- `tests/integration/test_initial_migration.py`
- `tests/unit/api/test_dependencies.py`
- `tests/unit/api/test_employer_schemas.py`
- `tests/unit/auth/test_permissions.py`
- `CURRENT_WORK.md`
- `ROADMAP.md`
- `NOTES.md`

## 4. What changed in this slice

### Backend command + persistence surface
- Added the draft Employer revision application path with bounded expected-version and idempotency semantics.
- Extended persistence and migration coverage for revision-compatible fields and authoritative event/receipt behavior.
- Added or updated API/schema/permission coverage for the staff revision surface.

### Frontend/browser surface
- Added the standalone draft revision form and integrated it into the staff workspace.
- Hardened browser-side revision and detail parsing so leaked actor-attribution fields like `updated_by` are rejected instead of entering routine browser state.
- Preserved accepted revision metadata (`version`, `updated_at`, result-version headers, replay semantics).
- Added localization, accessibility, focus/announcement, privacy side-channel, and value-safe diagnostic evidence through exact Task 10 nodes.

### Living docs / evidence
- Updated `CURRENT_WORK.md`, `ROADMAP.md`, and `NOTES.md` through Task 10 closeout verification.
- Recorded service-backed Task 10.6 evidence separately from the frontend/browser Task 10 closeout evidence.

## 5. Exact Task 10 evidence summary

### Task 10.1 — revision i18n parity
- Honest GREEN regression.
- Exact English/Spanish revision keys already matched; selector aligned to approved wording.

### Task 10.2 — axe parity across revision and recovery states
- Real RED → GREEN.
- Root issue: locale-frozen local validation messaging plus standalone `workspaceCommandOwner` defaulting behavior.
- Bounded fix: render-time localized error-kind mapping and `workspaceCommandOwner` default to `null`.

### Task 10.3 — transition announcements + reduced-motion-safe focus
- Real RED → GREEN.
- Root issue: focus owners existed but announcement semantics were missing.
- Bounded fix: `role="alert"` / `role="status"` on existing value-free transition surfaces.

### Task 10.4 — browser side-channel / service-worker / Cache API boundaries
- Honest GREEN regression.
- Existing instrumentation already covered history/storage/console/DOM diagnostics plus Cache API and service-worker access boundaries.

### Task 10.5 — value-independent Testing Library diagnostics
- Honest GREEN regression.
- Exact selector passed against the existing global value-safe diagnostic hook.

### Task 10.6 — service-backed revision error/exception diagnostics
- Harness/setup repair first, then honest GREEN regression.
- First focused run failed at fixture setup because the repo-default DB URL targeted stale local credentials.
- Approved service override used for real verification:
  - `GOLDEN_ROSE_DATABASE_URL='postgresql+psycopg://golden_rose_test:test@127.0.0.1:55432/golden_rose_test'`
- Exact selector then passed without backend code changes for diagnostic redaction.

### Task 10.7 — routine browser actor-attribution rejection
- Real RED → GREEN.
- Root issue: browser client accepted `updated_by` in detail/revision success payloads.
- Bounded fix: strict allowlists for routine detail/revision response keys while preserving approved revision metadata.

## 6. Real verification evidence already observed

### Post-review remediation round (2026-08-11)
- Independent review reported a blocker/high rereview round before PR readiness.
- Remediated findings:
  - shared create/revise `display_name` validation parity now rejects blank, >200-char, and control-character revision names in schema and direct application entry points
  - the initial existing-receipt replay branch in `src/golden_rose/application/revise_draft_employer.py` now safe-fails malformed receipt result-version / result-event authority instead of downgrading integrity failures into idempotency conflicts
  - revision-era migration/metadata/live-schema expectations were reconciled, including additional database check-constraint coverage and deferrable-FK timing expectations
  - the remaining OpenAPI route-surface guard in `tests/integration/api/test_staff_employer_reads.py` now includes the approved `/api/staff/v1/employers/{employer_id}/revisions` route while still rejecting adjacent unapproved routes by exact path-set assertion
- Rereview verification:
  - `env -u PYTHONPATH GOLDEN_ROSE_DATABASE_URL='postgresql+psycopg://golden_rose_test:test@127.0.0.1:55432/golden_rose_test' uv run pytest tests/integration/api/test_staff_employer_reads.py -q`
    - result: `16 passed`
  - `env -u PYTHONPATH GOLDEN_ROSE_DATABASE_URL='postgresql+psycopg://golden_rose_test:test@127.0.0.1:55432/golden_rose_test' uv run pytest tests/unit/application/test_employer_text.py tests/unit/api/test_employer_schemas.py tests/integration/application/test_revise_draft_employer.py tests/integration/api/test_staff_employers.py -q`
    - result: `110 passed`
  - `env -u PYTHONPATH GOLDEN_ROSE_DATABASE_URL='postgresql+psycopg://golden_rose_test:test@127.0.0.1:55432/golden_rose_test' uv run pytest tests/integration/test_initial_migration.py -q`
    - result: `27 passed`
  - `env -u PYTHONPATH GOLDEN_ROSE_DATABASE_URL='postgresql+psycopg://golden_rose_test:test@127.0.0.1:55432/golden_rose_test' uv run pytest tests/integration/test_initial_migration.py tests/integration/application/test_revise_draft_employer.py tests/integration/api/test_staff_employers.py tests/unit/api/test_employer_schemas.py -q`
    - result: `134 passed`
  - `env -u PYTHONPATH GOLDEN_ROSE_DATABASE_URL='postgresql+psycopg://golden_rose_test:test@127.0.0.1:55432/golden_rose_test' uv run pytest tests/integration/application/test_revise_draft_employer.py::test_concurrent_same_key_changed_actor_or_payload_has_one_success_and_one_conflict -q`
    - result: `1 passed`

### Focused service-backed API evidence
- `env -u PYTHONPATH GOLDEN_ROSE_DATABASE_URL='postgresql+psycopg://golden_rose_test:test@127.0.0.1:55432/golden_rose_test' uv run pytest tests/integration/api/test_staff_employers.py::test_revision_error_and_exception_diagnostics_are_value_safe -q`
  - result: `1 passed`
- `env -u PYTHONPATH GOLDEN_ROSE_DATABASE_URL='postgresql+psycopg://golden_rose_test:test@127.0.0.1:55432/golden_rose_test' uv run pytest tests/integration/api/test_staff_employers.py -q`
  - result: `31 passed`

### Task 10 closeout verification
- `npm --prefix apps/web run test -- --run src/employers/EmployerRevisionForm.test.tsx src/employers/EmployerWorkspace.test.tsx src/test/valueSafeDiagnostics.test.ts`
  - result: `84 passed`
- `npm --prefix apps/web run test -- --run src/i18n/LanguageProvider.test.tsx src/api/employerClient.test.ts`
  - result: `25 passed`
- `npm --prefix apps/web run typecheck`
  - result: passed
- `git diff --check`
  - result: passed

### Honest warnings preserved
- jsdom/axe still emits `Not implemented: HTMLCanvasElement's getContext() method` during automated axe coverage.
- These warnings are non-failing harness noise, not a failing accessibility gate.

## 7. Known caveats the reviewer should treat carefully

- The review surface is an **uncommitted working tree**, not a PR range.
- `origin/develop..HEAD` currently contains `0` commits, so exact-range PR hygiene and exact-range Gitleaks are **not yet meaningful**.
- The Task 10.6 database override was required only because the repo-default local test URL was stale for the currently running approved local PostgreSQL service.

## 8. Reviewer focus areas

The independent review should explicitly verify:
1. draft Employer revision command/persistence boundaries remain limited to `display_name` and `employer_type`
2. expected-version / idempotency / current-authoritative replay semantics are enforced consistently across backend and browser surfaces
3. routine browser detail/revision parsing rejects unauthorized extra fields, especially actor-attribution leakage, without weakening the accepted revision metadata contract
4. localization parity remains exact across revision and recovery states
5. focus ownership and announcement semantics remain value-free and reduced-motion-safe
6. revision values do not leak into browser side channels, caches, service workers, console output, or Testing Library diagnostics
7. living docs describe the lane honestly: Task 10 is closeout-verified, but human browser/manual accessibility/fluent-language qualification is still deferred
8. no adjacent unauthorized scope entered this slice (GCP, live data, auth rollout, public surfaces, broader entities)

## 9. Secret-scan / range-hygiene posture at handoff

- `git diff --check` passed on the live working tree.
- Exact committed-range secret scanning has **not** been rerun for this slice because there are still `0` commits ahead of `origin/develop`.
- Per the handoff workflow, exact-range secret scanning should happen only after the reviewed slice is committed and the verification target becomes a real `origin/develop..HEAD` range.

## 10. Final local review-surface verification at handoff creation

Observed commands:

```bash
git status --short --branch
git diff --stat
git diff --name-only
git diff --check
git rev-list --count origin/develop..HEAD
git rev-list --count HEAD..origin/develop
```

Observed truth:
- branch: `feat/staff-draft-employer-revision`
- review surface: **uncommitted working tree**
- ahead commits: `0`
- behind commits: `0`
- `git diff --check`: passed
- diff summary at handoff creation: `34 files changed, 8575 insertions(+), 130 deletions(-)`

## 11. Stop boundary before PR open

This slice is being handed off for **independent rereview after remediation**, not declared PR-ready.

Required next sequence:
1. independent rereview of the live working-tree diff and this remediation round
2. if cleared, create the closeout commit for the exact reviewed surface
3. rerun final-head focused verification on the committed head
4. run exact-range secret scanning on `origin/develop..HEAD`
5. only then push and open/update the PR

## 12. Handoff disposition

This part of the Phase 1 implementation appears complete enough to hand off for rereview.

The correct current disposition is:
- **cleared for independent rereview handoff after remediation**
- **not yet cleared for push/PR/merge**
- **final-head closeout evidence still belongs after review and commit**

## 13. Post-merge remediation handoff — 2026-08-11

### Current branch truth

- Base: exact merged `origin/develop` at `1543248` (`feat: implement draft employer revision slice (#17)`)
- Branch: `fix/draft-employer-revision-post-merge`
- Review surface: local uncommitted working tree
- Publication status: commit/push/PR remain blocked on complete local gates and fresh independent rereview

### Findings being remediated

1. **Medium — browser target binding:** `reviseEmployer()` accepted a valid-shaped success whose `employer_id` differed from the requested path Employer. The parser now validates the response against `input.employerId`; focused coverage proves a cross-target success becomes `unknown_outcome` rather than browser authority.
2. **Medium — concurrent no-op/audit authority:** fresh-command no-op and `changed_fields` were calculated before receipt reservation/compare-and-swap. The use case now reserves first, performs a locked exact current-row read at `expected_version`, derives semantic change authority from that row, and rolls back the reserved receipt on no-op. Deterministic unit coverage recorded the original RED; a PostgreSQL interleaving regression proves a future-version catch-up remains at version 2 with no spurious receipt or audit event.
3. **Low hardening closed in the same application boundary:** known SQLAlchemy receipt/read/write/audit failures now roll back and raise `SafePersistenceError`, preserving the existing value-safe API 503 contract rather than leaking raw persistence exceptions.

### Scope and review focus

Review the exact browser target-binding change, receipt-reservation/row-lock ordering, no-op rollback, changed-field derivation, replay preservation, persistence exception classification, new focused tests, and documentation reconciliation. Confirm no endpoint, field, lifecycle, permission, replay, audit-payload, deployment, live-data, or adjacent-entity expansion.

### Required disposition

Focused and complete local application-quality/security verification now pass: locked toolchain/package checks, frontend verification/audit/SBOM, Ruff, mypy, Bandit, Alembic upgrade→downgrade→upgrade, `238 passed` backend tests at `96.14%` coverage, pip-audit, backend SBOM validation, and `git diff --check`. The remediation remains not PR-ready until a fresh independent rereview reports no unresolved Blocker/High/Medium finding.

The exact changed tracked/untracked working-tree source set was additionally scanned with `gitleaks detect --no-git` after a rejected zero-byte Git-mode attempt; the content scan covered `678,465` bytes and found no leaks. This does not replace required exact-range scanning after a reviewed commit exists.

### Independent rereview disposition

Fresh independent rereview of the exact uncommitted surface returned **PASS** with no Blocker, High, or Medium finding. It verified requested-target response binding, receipt-reservation/locked-row no-op and changed-field ordering, atomic CAS/audit behavior, safe SQLAlchemy failure classification, historical-versus-current documentation truth, preserved deferred gates, and no unauthorized scope expansion. The reviewer found the surface ready for the closeout commit after the completed full gate; it remains not PR-ready until final-head verification and exact-range scanning run after that commit.

### Historical merge disposition — 2026-08-12

The closeout commit completed final-head verification and exact-range secret scanning, all protected checks passed, and PR #18 merged the remediation into protected `develop` at `a4d8f90`. Section 13 is retained as review history and no longer represents an active branch or gate.
