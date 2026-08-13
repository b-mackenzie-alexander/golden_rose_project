# Slice B Runtime and Container Contract Implementation Plan

> **For Hermes:** Execute this plan with strict RED -> GREEN TDD from `feat/gcp-develop-runtime-container`, which was created from protected `develop` commit `9e27f8036184c885fcaff8a4949770a70d0c77fe` after PR #21 merged.

**Goal:** Make the existing Golden Rose staff tracer locally packageable and observable for a future private GCP `develop` deployment without creating cloud resources or starting cloud services as part of the code slice.

**Architecture:** Add a narrow deployment posture seam to configuration, separate cheap liveness from database/schema readiness, keep full synthetic workflow qualification outside health probes, package the existing React/Vite staff UI and FastAPI API as one same-origin service, and define a local container contract that can be built and inspected before any cloud push/deploy. Runtime/service-start evidence remains local-only and must not imply GCP provisioning or production readiness.

**Tech Stack:** Python 3.12, FastAPI, Pydantic Settings, SQLAlchemy, Alembic, React/TypeScript/Vite, Docker/OCI, pytest, npm/Vitest, shell contract checks.

---

## Authority and hard stops

- Controlling boundary: ADR-0009 and `.hermes/plans/2026-08-13_145234-gcp-develop-deployment-foundation-plan.md`, Slice B.
- This branch may edit source, tests, docs, Docker/container files, and local verification scripts.
- This branch may run local unit/type/lint/build checks and local image build/inspection.
- This branch must not run Terraform, call GCP APIs, create resources, link billing, configure secrets, push images, deploy, start cloud services, use Cloud SQL, expose a public listener, or admit live/client-derived data.
- Local container/service startup is allowed only for the bounded Slice B verification described here and must use fictional/synthetic local settings only. No cloud connection strings or secrets may be used.

## Exact TDD nodes

### Task 1: Develop deployment posture settings

**Objective:** Accept explicit `develop` configuration only when it is labeled as the private fictional-synthetic posture, while retaining the existing production/synthetic fail-closed guard.

**Files:**
- Modify: `tests/unit/test_config.py`
- Modify: `src/golden_rose/config.py`

**RED command:**
`env -u PYTHONPATH uv run pytest tests/unit/test_config.py::test_develop_requires_explicit_private_synthetic_cloud_posture -q`

**Expected RED:** validation/import failure because `develop`, deployment target, and public synthetic label are not yet modeled.

**Minimal GREEN:** add `develop` as an accepted environment plus a narrowly validated deployment target and public environment label contract. `develop` must require the exact private synthetic deployment target and non-empty synthetic/non-production label. `production` must still reject synthetic auth.

### Task 2: Non-production marker contract

**Objective:** Expose a value-safe environment marker that the same-origin UI can use to avoid unlabeled shared-develop operation.

**Files:**
- Modify: `tests/unit/test_main.py` or a new focused marker test
- Modify: `src/golden_rose/main.py` and/or a narrow metadata route/module
- Modify frontend only if the marker is rendered immediately in this slice

**RED command:**
`env -u PYTHONPATH uv run pytest tests/unit/test_main.py::test_develop_app_exposes_value_safe_non_production_marker -q`

**Expected RED:** no marker route or app state exists.

**Minimal GREEN:** add only value-safe marker metadata for the configured environment label. Do not expose database URLs, staff UUIDs, command IDs, or record values.

### Task 3: Cheap database-independent liveness

**Objective:** Add `/health` as a cheap process-level probe that never creates the database engine and never touches business state.

**Files:**
- Create: `src/golden_rose/api/health.py`
- Modify: `src/golden_rose/main.py`
- Test: `tests/unit/api/test_health.py`

**RED command:**
`env -u PYTHONPATH uv run pytest tests/unit/api/test_health.py::test_health_is_database_independent_and_value_safe -q`

**Expected RED:** health route absent.

**Minimal GREEN:** return a static `200` value-safe body from `/health`; prove engine factory is not called by the probe.

### Task 4: Bounded readiness

**Objective:** Add `/readiness` that checks configuration plus bounded database/schema availability without mutating business records.

**Files:**
- Modify: `src/golden_rose/api/health.py`
- Test: `tests/unit/api/test_health.py`

**RED command:**
`env -u PYTHONPATH uv run pytest tests/unit/api/test_health.py::test_readiness_checks_database_schema_without_business_mutation -q`

**Expected RED:** readiness route absent or not checking schema.

**Minimal GREEN:** inspect only authoritative database/schema metadata through the existing engine, return value-safe failure bodies, and avoid domain writes/command replay.

### Task 5: Qualification remains separate

**Objective:** Ensure health/readiness never run synthetic Employer/EmployerContact qualification flows.

**Files:**
- Test: `tests/unit/api/test_health.py`
- Modify: `src/golden_rose/api/health.py` only if needed

**RED command:**
`env -u PYTHONPATH uv run pytest tests/unit/api/test_health.py::test_health_and_readiness_do_not_run_synthetic_qualification -q`

**Expected RED:** missing explicit guard/characterization.

**Minimal GREEN:** prove probes do not call application command modules or idempotent mutation paths.

### Task 6: Same-origin static asset serving

**Objective:** Serve built Vite assets from one approved directory without turning arbitrary filesystem paths into public content.

**Files:**
- Create: `src/golden_rose/static_app.py`
- Modify: `src/golden_rose/main.py`
- Test: `tests/unit/test_static_app.py`

**RED command:**
`env -u PYTHONPATH uv run pytest tests/unit/test_static_app.py::test_static_app_serves_only_configured_vite_dist_directory -q`

**Expected RED:** static app seam absent.

**Minimal GREEN:** mount only an explicitly configured build directory when present; no directory listing, no arbitrary root exposure, no `.env`/source file serving.

### Task 7: API and frontend route boundary

**Objective:** Preserve API 404/405 behavior and route unknown frontend paths to the SPA shell only outside `/api`.

**Files:**
- Test: `tests/unit/test_static_app.py`
- Modify: `src/golden_rose/static_app.py`

**RED command:**
`env -u PYTHONPATH uv run pytest tests/unit/test_static_app.py::test_api_paths_are_not_swallowed_by_frontend_fallback -q`

**Expected RED:** fallback route absent or swallows API paths.

**Minimal GREEN:** add a fallback that serves `index.html` for non-API browser paths while preserving `/api` route/error semantics.

### Task 8: Entrypoint port and process contract

**Objective:** Provide an executable entrypoint that binds to `0.0.0.0:$PORT`, rejects invalid ports/configuration deterministically, forwards signals, and returns the application process exit status.

**Files:**
- Create: `scripts/container-entrypoint.sh`
- Test: `tests/unit/test_container_entrypoint.py`

**RED command:**
`env -u PYTHONPATH uv run pytest tests/unit/test_container_entrypoint.py::test_entrypoint_requires_valid_port_and_execs_uvicorn_on_all_interfaces -q`

**Expected RED:** entrypoint absent.

**Minimal GREEN:** add a shell entrypoint with strict mode, numeric port validation, no secret printing, and `exec uvicorn golden_rose.main:app --host 0.0.0.0 --port "$PORT"`.

### Task 9: Graceful shutdown ownership

**Objective:** Prove FastAPI lifespan disposes the database engine on shutdown and document SIGTERM expectations without relying only on shell behavior.

**Files:**
- Modify: `tests/unit/test_main.py`
- Modify: `src/golden_rose/main.py` only if needed

**RED command:**
`env -u PYTHONPATH uv run pytest tests/unit/test_main.py::test_lifespan_shutdown_disposes_engine_for_container_termination -q`

**Expected RED:** missing exact container-termination characterization, or immediate pass if existing lifespan ownership is sufficient.

**Minimal GREEN:** retain or tighten lifespan disposal; do not add business shutdown mutations.

### Task 10: Docker image contract

**Objective:** Define a local image build that runs as non-root, includes only required runtime artifacts, and excludes secrets/tests/coverage/local evidence.

**Files:**
- Create: `Dockerfile`
- Create: `.dockerignore`
- Create: `deploy/container/README.md`
- Test: `tests/unit/test_container_contract.py`

**RED command:**
`env -u PYTHONPATH uv run pytest tests/unit/test_container_contract.py::test_docker_contract_uses_non_root_runtime_and_excludes_secret_surfaces -q`

**Expected RED:** Dockerfile/ignore absent.

**Minimal GREEN:** add a multi-stage or narrow single-stage Dockerfile with fixed non-root user, runtime-only copy surface, no `.env`/tests/build evidence, runtime config through environment variables only, and no cloud-specific credentials.

### Task 11: Local build and inspection verification

**Objective:** Build and inspect the image locally, then optionally run bounded local startup probes if still in approved local-only scope.

**Commands:**
- `docker build -t golden-rose:slice-b-local .`
- inspect image user, entrypoint, exposed env assumptions, and digest/id
- run local container only with fictional synthetic settings and a non-default valid `PORT`
- probe `/health` and `/readiness`
- send SIGTERM and verify deterministic graceful exit

**Hard stop:** no image push and no cloud deployment.

## Final verification target

Before review handoff, run the focused Slice B tests plus the existing application-quality-equivalent gates that are practical locally:

- `env -u PYTHONPATH uv run ruff format --check .`
- `env -u PYTHONPATH uv run ruff check .`
- `env -u PYTHONPATH uv run mypy src tests`
- focused Slice B pytest selectors
- existing backend test suite with approved local database override where integration tests require PostgreSQL
- `npm run verify` in `apps/web` if frontend/static-serving behavior changed
- `git diff --check`
- exact-range Gitleaks only after commit and before push/PR
