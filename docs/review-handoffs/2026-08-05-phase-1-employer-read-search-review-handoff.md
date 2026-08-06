# Review Handoff — Phase 1 employer read/search tracer

**Date:** 2026-08-05
**Branch:** `feat/staff-employer-read-search`
**Target PR base:** `develop`
**Planning base:** `origin/develop` at merged planning tip `bde9143` (`docs: plan employer detail and bounded search (#10)`)
**Review surface:** historical independent-review handoff for the branch that was remediated, reviewed, and merged by PR #11
**Ahead commits vs `origin/develop` at handoff creation:** `0` (`git rev-list --count origin/develop..HEAD`)
**PR status:** historical closeout; PR #11 merged to `develop` at `b9eaee6` on 2026-08-06. Do not execute this handoff or use its branch as the base for later work.

All present-tense reviewer instructions below are preserved only as evidence of the pre-PR review state. They were completed/superseded by remediation, final verification, protected PR #11, and merge commit `b9eaee6`; no step in this historical packet remains actionable.

## Review round 1 outcome and remediation status

Independent review returned **Changes requested / not PR-ready yet** on the uncommitted working tree.

### Reported blockers
- **High:** create command did not normalize display names before request fingerprinting and insertion, allowing composed/decomposed replay conflicts.
- **High:** detail-route problem responses did not consistently emit `Cache-Control: no-store` for denied / validation / safe-persistence paths.
- **Medium:** authorized missing-detail response used generic problem type `.../not-found` instead of the approved employer-specific type.
- **Medium:** read-side detail/search paths still carried extra fields (`created_by`, plus extra create-only metadata in search) behind the application boundary.

### Remediation now applied locally
- `src/golden_rose/application/create_draft_employer.py`
  - normalizes `display_name` with `normalize_employer_text(...)` before both fingerprinting and insertion
  - replay path now preserves authoritative create semantics while read-side minimization remains separate
- `src/golden_rose/api/errors.py`
  - all installed problem handlers now return `no_store_problem_response(...)`
- `src/golden_rose/api/staff/employers.py`
  - absent-detail 404 now returns `https://golden-rose.local/problems/employer-not-found`
- `src/golden_rose/persistence/employers.py`
  - split authoritative create record from minimized read-side records:
    - `EmployerRecord` for create/replay authority
    - `EmployerDetailRecord` for exact detail reads
    - `EmployerSearchRecord` for bounded search items
- `src/golden_rose/application/get_employer.py`
  - now returns the minimized `EmployerDetailRecord`
- `src/golden_rose/application/search_employers.py`
  - now selects/builds minimized `EmployerSearchRecord` rows only

### Focused remediation verification

Commands run after remediation:

```bash
set -a && source .env.test && set +a && \
  env -u PYTHONPATH uv run pytest \
    tests/integration/application/test_create_draft_employer.py::test_create_normalizes_display_name_before_fingerprint_and_insert \
    tests/integration/application/test_create_draft_employer.py::test_replay_treats_composed_and_decomposed_names_as_same_payload \
    tests/integration/application/test_get_employer.py::test_permitted_get_returns_current_minimized_employer \
    tests/integration/application/test_search_employers.py::test_permitted_search_returns_page_and_next_cursor \
    tests/integration/api/test_staff_employer_reads.py::test_get_absent_returns_nonreflective_no_store_404 \
    tests/integration/api/test_staff_employer_reads.py::test_denied_get_runs_no_sql_and_headers_cannot_elevate \
    tests/integration/api/test_staff_employer_reads.py::test_detail_validation_and_failures_map_to_safe_no_store_problems -v
```

Observed result:
- `7 passed, 1 warning in 0.68s`

Broader rereview subset run after remediation:

```bash
set -a && source .env.test && set +a && \
  env -u PYTHONPATH uv run ruff check \
    src/golden_rose/application/create_draft_employer.py \
    src/golden_rose/application/get_employer.py \
    src/golden_rose/application/search_employers.py \
    src/golden_rose/api/errors.py \
    src/golden_rose/api/staff/employers.py \
    src/golden_rose/persistence/employers.py \
    tests/integration/application/test_create_draft_employer.py \
    tests/integration/application/test_get_employer.py \
    tests/integration/application/test_search_employers.py \
    tests/integration/api/test_staff_employer_reads.py && \
  env -u PYTHONPATH uv run mypy src tests && \
  env -u PYTHONPATH uv run pytest \
    tests/integration/application/test_create_draft_employer.py \
    tests/integration/application/test_get_employer.py \
    tests/integration/application/test_search_employers.py \
    tests/integration/api/test_staff_employer_reads.py -v
```

Observed result:
- `ruff check`: all checks passed
- `mypy src tests`: success, no issues in 44 source files
- targeted rereview suite: `32 passed, 1 warning in 1.08s`

At the time of this handoff, round 2 was asked to verify that the reported blockers were closed rather than merely covered by tests. That review/remediation cycle is complete and historical.

## 1. What changed

This slice implements the approved ADR-0004 employer read/search boundary for the synthetic/local staff plane:

- one new named permission: `employer:read` (`src/golden_rose/auth/permissions.py:3-12`)
- synthetic local principal now carries both create and read permissions (`src/golden_rose/api/dependencies.py:41-43`)
- shared application errors for absent read and safe persistence (`src/golden_rose/application/errors.py:1-6`)
- authorization-first exact employer detail query (`src/golden_rose/application/get_employer.py:12-25`)
- authorization-first bounded search query with literal `ILIKE`, optional type filter, descending keyset ordering, cursor binding, and rollback-on-DB-failure redaction (`src/golden_rose/application/search_employers.py:32-121`)
- canonical opaque cursor codec and filter fingerprinting (`src/golden_rose/application/search_cursor.py:10-105`)
- new staff routes:
  - `POST /api/staff/v1/employers/search` (`src/golden_rose/api/staff/employers.py:58-104`)
  - `GET /api/staff/v1/employers/{employer_id}` (`src/golden_rose/api/staff/employers.py:106-129`)
- exact no-store problem mapping for denied search and absent detail via the shared API error boundary (`src/golden_rose/api/errors.py:15-97`, `src/golden_rose/api/staff/employers.py:85-126`)

## 2. Explicit non-scope still preserved

Reviewer should confirm the slice did **not** add:

- migrations, schema changes, dependencies, lockfile changes, Compose changes, CI/policy changes, or frontend work
- any public route, export, list-all route, count endpoint, fuzzy/relevance search, or mutation/audit-on-read behavior
- any real identity/auth provider work, cloud changes, or live/client data handling

## 3. Primary files for review

### Production
- `src/golden_rose/api/dependencies.py`
- `src/golden_rose/api/errors.py`
- `src/golden_rose/api/staff/employers.py`
- `src/golden_rose/api/staff/schemas.py`
- `src/golden_rose/application/create_draft_employer.py`
- `src/golden_rose/application/employer_text.py`
- `src/golden_rose/application/errors.py`
- `src/golden_rose/application/get_employer.py`
- `src/golden_rose/application/search_cursor.py`
- `src/golden_rose/application/search_employers.py`
- `src/golden_rose/auth/permissions.py`

### Test coverage added/updated
- `tests/integration/api/test_staff_employer_reads.py`
- `tests/integration/api/test_staff_employers.py`
- `tests/integration/application/test_create_draft_employer.py`
- `tests/integration/application/test_get_employer.py`
- `tests/integration/application/test_search_employers.py`
- `tests/unit/api/test_dependencies.py`
- `tests/unit/api/test_employer_schemas.py`
- `tests/unit/application/test_employer_search_cursor.py`
- `tests/unit/application/test_employer_text.py`
- `tests/unit/auth/test_permissions.py`

### Living docs / evidence
- `CURRENT_WORK.md`
- `ROADMAP.md`
- `NOTES.md`
- `.hermes/plans/2026-08-04_phase-1-employer-read-search-plan.md`
- `docs/adr/ADR-0004-phase-1-employer-read-search-boundary.md`

## 4. Review focus from the approved plan

Prioritize these trust-boundary questions:

1. authorization before query / before cursor decode
2. role-label or request-header privilege elevation
3. URL/log/error reflection of names, cursors, SQL, actor details, or exception text
4. wildcard handling for `%`, `_`, and escape character in search
5. deterministic descending ordering and keyset continuation correctness
6. route-surface drift (`/search` vs `/{employer_id}` and OpenAPI exposure)
7. read-side writes: no `Employer`, `CommandReceipt`, or `AuditEvent` creation on detail/search
8. no total counts, exports, unfiltered browsing, or hidden ranking behavior
9. preserved create-route behavior and existing safe problem mappings
10. scope drift into dependency/migration/CI/policy/frontend/public surfaces

Any **High** or **Blocker** finding should block PR readiness.

## 5. Observed implementation evidence

### Focused Task 5 API regression pass
Command run:

```bash
set -a && source .env.test && set +a && \
  env -u PYTHONPATH uv run pytest \
  tests/integration/api/test_staff_employer_reads.py \
  tests/integration/api/test_staff_employers.py -v
```

Observed result:
- `24 passed, 1 warning in 1.23s`
- only warning: existing upstream `StarletteDeprecationWarning` from `fastapi.testclient`

Notable regressions covered:
- denied detail/search execute before SQL or cursor decode
- forged `X-Actor-Id` / `X-Role-Name` / `X-Permissions` headers cannot elevate access
- detail/search leave authoritative row counts unchanged
- OpenAPI exposes only approved create/detail/search routes
- search logs do not reflect body/cursor/filter/SQL/URL/actor/exception markers
- create-route exact body and OpenAPI expectations remain preserved

### Task 6 quality/security verification pass
Runtime prerequisite observed:

```bash
docker compose --env-file .env.test ps postgres-test
```

Observed status:
- `postgres-test` healthy on `127.0.0.1:55432`

Workflow-order gate run and final outcome:

```bash
set -a && source .env.test && set +a && \
  env -u PYTHONPATH uv lock --check && \
  env -u PYTHONPATH uv sync --locked --all-groups && \
  env -u PYTHONPATH uv run ruff format --check . && \
  env -u PYTHONPATH uv run ruff check . && \
  env -u PYTHONPATH uv run mypy src tests && \
  env -u PYTHONPATH uv run bandit -q -r src && \
  env -u PYTHONPATH uv run alembic upgrade head && \
  env -u PYTHONPATH uv run pytest --cov=golden_rose --cov-report=term-missing --cov-fail-under=95 && \
  env -u PYTHONPATH uv run alembic downgrade base && \
  env -u PYTHONPATH uv run alembic upgrade head && \
  env -u PYTHONPATH uv run pip-audit --skip-editable && \
  mkdir -p build && \
  env -u PYTHONPATH uv run cyclonedx-py environment --pyproject pyproject.toml \
    --output-reproducible --of JSON -o build/backend-sbom.cdx.json
```

Observed remediation during the pass:
- `ruff format --check` first failed; fixed by running `uv run ruff format .`
- `ruff check .` then found 8 import-order findings; fixed by `uv run ruff check . --fix`
- `mypy src tests` then found 3 stale imports of `SafePersistenceError`; fixed by moving those imports to `golden_rose.application.errors`

Observed green outcome after those narrow fixes:
- `97 passed, 1 warning in 3.45s`
- total coverage: `96.67%`
- `pip-audit --skip-editable`: no known vulnerabilities
- SBOM generated and validated:
  - path: `build/backend-sbom.cdx.json`
  - `bomFormat: CycloneDX`
  - `specVersion: 1.6`

### Range and hygiene evidence
Commands run:

```bash
git diff --check origin/develop...HEAD
git diff --name-status origin/develop...HEAD
git rev-list --count origin/develop..HEAD
/opt/homebrew/bin/gitleaks git --log-opts='origin/develop..HEAD' --redact
```

Observed results:
- `git diff --check origin/develop...HEAD`: clean
- `git diff --name-status origin/develop...HEAD`: no committed range delta
- `git rev-list --count origin/develop..HEAD`: `0`
- Gitleaks scanned `0 commits` / `0 bytes` and reported no leaks

Historical interpretation at handoff creation:
- the surface was **not yet a committed PR candidate**; this state was superseded when the remediated branch was committed, pushed, reviewed in PR #11, and merged at `b9eaee6`.

## 6. Historical reviewer-facing caveats — resolved

- At handoff creation, `HEAD` was not ahead of `origin/develop`, so exact-range PR-style hygiene was limited until commit.
- At handoff creation, `git status --short` showed the local slice and review used the working tree directly.
- These caveats no longer describe an active lane; PR #11 merged and later work must re-baseline from current `origin/develop`.

## 7. Archived reviewer procedure — completed; do not execute

The following records the procedure requested at the time; it is not a current instruction:

1. Inspect the local diff on `feat/staff-employer-read-search` against `origin/develop`.
2. Re-run the focused API pass first if a quick regression sanity check is needed.
3. Re-run targeted review commands as needed around:
   - `tests/integration/api/test_staff_employer_reads.py`
   - `tests/integration/application/test_search_employers.py`
   - `tests/unit/application/test_employer_search_cursor.py`
4. Verify the scope boundary remains aligned with ADR-0004 and the merged plan.
5. If findings are clear or only non-blocking, return a PR-ready review verdict for a follow-up commit/push/PR step.
6. If High/Blocker findings exist, return them with exact file/line references and blast radius before any PR is opened.

## 8. Historical stop boundary — completed

At creation, this handoff did **not** authorize opening the PR. The subsequent session completed the following steps, opened PR #11, and merged it; do not repeat them from this packet:

- review the local working tree
- remediate in-scope findings only
- rerun final-head verification after the eventual closeout commit
- push the branch
- only then open the PR to `develop`
