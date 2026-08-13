# Slice B Runtime/Container Contract — Pre-PR Review Handoff

**Date:** 2026-08-13
**Branch:** `feat/gcp-develop-runtime-container`
**Intended base:** `origin/develop`
**Approved base SHA:** `9e27f8036184c885fcaff8a4949770a70d0c77fe`
**Review surface:** uncommitted local working tree after first review-remediation round
**Ahead commits vs base:** 0

## Rereview status

Independent review returned changes requested: one High and two Medium boundary findings; rereview confirmed those functional defects resolved and left one Medium stale-test blocker. Round 2 rereview then confirmed the stale integration assertions resolved and cleared the working tree for PR preparation, not merge. Closeout still requires a commit plus final-head committed-range verification before push/PR.

### Findings remediated

1. **High — API method semantics with static serving active.** Removed the broad multi-method `/api/{path}` static reservation so the static router no longer owns API dispatch or replaces FastAPI method-aware 405 handling. Added a no-store Starlette HTTP exception handler that preserves `Allow` headers for 405 responses. Regression: `tests/unit/test_static_app.py::test_static_router_does_not_replace_api_method_semantics` now proves `POST /api/staff/v1/employers/not-a-uuid` returns `405`, `Allow: GET`, `Cache-Control: no-store`, and no SPA shell with static serving active.
2. **Medium — bare `/api` served as SPA shell.** Changed the static fallback to reserve `api` and `api/...` path prefixes before fallback. Regression: `tests/unit/test_static_app.py::test_bare_api_paths_are_reserved_from_spa_fallback` now covers bare `/api`, query-bearing `/api?client=misconfigured`, and `/api/`.
3. **Medium — environment marker falsely emitted outside develop.** `create_app()` now registers the environment marker router only after validated `develop` posture. Regression: `tests/unit/test_main.py::test_environment_marker_is_not_registered_outside_develop` covers valid `local` and `test` settings returning no marker and no false develop/synthetic body.
4. **Medium — stale in-scope integration assertions.** Updated `tests/integration/api/test_staff_employer_reads.py` method-not-allowed and unmatched-route assertions to require `Cache-Control: no-store` on native 405/404 responses, aligning the integration suite with the intentional Starlette HTTP exception remediation.

## Review-surface caveat

This is a pre-PR review handoff for an uncommitted working tree. Local verification below proves the current files on disk, not a committed PR range. Exact committed-range checks, including `git diff --check origin/develop...HEAD` and `gitleaks git --log-opts origin/develop..HEAD`, must be rerun after the review/remediation commit exists and before push/PR.

## Scope implemented

Local-only Slice B from `.hermes/plans/2026-08-13_160852-slice-b-runtime-container-contract-plan.md`:

- develop deployment-posture settings require explicit private fictional-synthetic posture
- value-safe environment marker at `GET /api/staff/v1/environment`
- cheap no-store `/health`
- bounded no-store `/readiness` against `alembic_version.version_num`
- health/readiness isolation from Employer/EmployerContact command and query workflows
- same-origin static asset serving from configured Vite `dist` directory
- SPA fallback for non-API extensionless paths while preserving `/api` error boundary
- runtime entrypoint `golden-rose-run` that validates `PORT`/settings and binds `0.0.0.0:$PORT`
- FastAPI lifespan shutdown characterization for container termination
- local-only Docker image contract and local image build/inspection/probe evidence

## Explicit non-scope preserved

No image push, registry action, GCP API call, Terraform apply, billing linkage, service identity, Secret Manager, Artifact Registry, Cloud Run deployment, Cloud SQL use, public access, real identity, live/client data, or production work occurred.

## Key production files changed

- `src/golden_rose/config.py`
- `src/golden_rose/main.py`
- `src/golden_rose/api/environment.py`
- `src/golden_rose/api/health.py`
- `src/golden_rose/static_app.py`
- `src/golden_rose/runtime.py`
- `pyproject.toml`
- `Dockerfile`
- `.dockerignore`
- `deploy/container/README.md`

## Key tests added/updated

- `tests/unit/test_config.py`
- `tests/unit/test_main.py`
- `tests/unit/api/test_health.py`
- `tests/unit/test_static_app.py`
- `tests/unit/test_runtime.py`
- `tests/unit/test_container_contract.py`
- OpenAPI route guards in:
  - `tests/integration/api/test_staff_employers.py`
  - `tests/integration/api/test_staff_employer_reads.py`

## Local verification evidence

### Post-remediation focused rereview evidence

- Reviewer repro regressions first failed as expected: bare `/api` returned `200`, static-enabled unsupported API method returned `404`, and local/test environment marker returned `200` with false develop metadata.
- After remediation, the direct reviewer regressions passed: `5 passed, 1 warning` for the new static/environment selectors plus the existing develop marker selector.
- Focused rereview bundle passed: `16 passed, 1 warning` for `tests/unit/test_static_app.py`, `tests/unit/test_main.py`, and the local OpenAPI guards.
- Broader focused backend/static/runtime bundle passed: `31 passed, 1 warning`.
- `ruff format --check .`: `144 files already formatted`.
- `ruff check .`: passed.
- `mypy src tests`: `Success: no issues found in 69 source files`.
- `bandit -q -r src`: passed with only the already-reviewed `# nosec B104` notice for the container-required `0.0.0.0` bind.
- `pip-audit --skip-editable`: no known vulnerabilities.
- `gitleaks dir --no-banner --redact .`: no leaks found.
- `git diff --check`: passed.

### Post-rereview stale-test blocker evidence

- Patched stale assertions at `tests/integration/api/test_staff_employer_reads.py` to require `Cache-Control: no-store` for 405 and 404 native responses.
- Brought local `postgres-test` up with ignored `.env.test`, waited for health, and ran `alembic upgrade head` before the DB-backed integration file.
- Complete modified integration file passed: `tests/integration/api/test_staff_employer_reads.py` — `26 passed, 1 warning`.
- Focused rereview bundle passed: `41 passed, 1 warning` across `tests/unit/test_static_app.py`, `tests/unit/test_main.py`, the complete modified integration file, and the local OpenAPI guards.
- `ruff format --check .`: `144 files already formatted`.
- `ruff check .`: passed.
- `mypy src tests`: `Success: no issues found in 69 source files`.
- `gitleaks dir --no-banner --redact .`: no leaks found.
- `git diff --check origin/develop` and `git diff --check`: passed.
- The local PostgreSQL test container was terminated and removed; the temporary ignored `.env.test` file was cleared after use.

### Original pre-review evidence

Frontend application gate:

- `npm --prefix apps/web run verify`
- Result: lock validation passed, lockfile tests `24 passed`, ESLint passed, TypeScript passed, Vitest coverage passed with 8 files / 116 tests, build passed.
- Coverage summary: statements 94.78%, branches 93.12%, functions 98.7%, lines 95.31%.
- Known jsdom canvas warnings appeared during frontend coverage; they were already non-fatal in the successful verify run.

Backend/static/runtime focused gate:

- `env -u PYTHONPATH uv run ruff format --check .`
  - Result: `143 files already formatted`
- `env -u PYTHONPATH uv run ruff check .`
  - Result: `All checks passed!`
- `env -u PYTHONPATH uv run mypy src tests`
  - Result: `Success: no issues found in 69 source files`
- `env -u PYTHONPATH uv run bandit -q -r src`
  - Result: exit 0; one expected nosec notice for B104 on container-required `0.0.0.0` bind, with no failed Bandit finding.
- Focused pytest bundle:
  - `27 passed, 1 warning`
  - warning: pre-existing Starlette/TestClient deprecation warning.
- `env -u PYTHONPATH uv run pip-audit --skip-editable`
  - Result: `No known vulnerabilities found`; editable `golden-rose` skipped.
- `gitleaks dir --no-banner --redact .`
  - Result: no leaks found over working tree.
- `git diff --check`
  - Result: passed.

Container evidence:

- Docker Desktop initially unavailable; started locally and Docker server reached `29.5.3`.
- Built local image `golden-rose:slice-b-local`.
- First build surfaced Node engine warnings from `node:24.12.0-bookworm-slim`; Dockerfile was corrected to `node:22.22.3-bookworm-slim`, matching `apps/web/package.json`.
- Rebuild passed without engine mismatch warnings.
- Final local image ID: `sha256:ad8a8ed70236194375a0d61b26c53e6e13e0c9632c8a7eb7e01250a3ecc99da6`.
- Image inspection:
  - user: `goldenrose`
  - entrypoint: `["golden-rose-run"]`
  - static env: `GOLDEN_ROSE_STATIC_ASSETS_PATH=/app/static`
  - rootfs layers: 12
- Ephemeral inspection proved UID `10001`, no `/app/.env`, no `/app/tests`, no `/app/.hermes`, built `/app/static/index.html`, and executable `/usr/local/bin/golden-rose-run`.
- Bounded loopback run on `127.0.0.1:18080` with fictional synthetic settings:
  - `/health` returned `{"status":"ok"}`
  - `/index.html` returned 200 and contained the SPA root shell
  - `/readiness` returned expected static 503 `database_schema_unavailable` because no local database was wired for the image-only probe
  - SIGTERM to PID 1 exited with code 0
  - probe container was removed
- `docker ps -a --filter name=golden-rose-slice-b` returned no remaining containers.

## Reviewer focus areas

1. Runtime boundary: confirm `develop` settings cannot silently run without explicit private fictional-synthetic posture.
2. Health/readiness boundary: confirm `/health` remains cheap and `/readiness` only checks bounded schema state without business data mutation or synthetic workflow execution.
3. Static serving: check traversal/dotfile/source blocking and `/api` boundary preservation.
4. Entrypoint/container: verify the explicit `0.0.0.0:$PORT` bind is justified for container runtime and remains bounded by platform/network policy; no local command starts cloud services.
5. Docker contract: confirm `.dockerignore` and Dockerfile copy surfaces exclude secrets, tests, local evidence, and `.hermes` state.
6. Evidence posture: ensure Task 11 readiness 503 is not misread as deployed database readiness; it is image-only evidence without a wired local database.

## Stop boundary before PR

Independent review/remediation should happen before push/PR. After remediation, create the closeout commit, then rerun final-head checks on the committed range before opening the PR:

- `git diff --check origin/develop...HEAD`
- exact-range `gitleaks git --no-banner --redact --log-opts 'origin/develop..HEAD'`
- focused quality/security commands covering remediated files
- final status/ahead-count check
