# ADR-0003: Phase 1 Backend Toolchain and Synchronous Transaction Boundary

**Status:** Accepted
**Date:** 2026-08-04

## Context and evidence posture

The first Phase 1 tracer must establish a reproducible backend environment and prove one atomic domain-row plus audit-event command. The repository has no application manifest or test environment. The development host currently provides Python 3.12 and `uv`; the accepted product direction already proposes FastAPI, PostgreSQL, SQLAlchemy, and Alembic.

The workload is a small staff-facing transactional application. No measured need currently justifies asynchronous database/application complexity.

## Decision

Use this backend baseline for the first slice:

- Python 3.12;
- `uv` for dependency resolution, lockfile generation, environments, and command execution, with Hatchling as the pinned package build backend;
- FastAPI with Pydantic v2 for the staff API and typed boundary validation, served locally by Uvicorn;
- synchronous SQLAlchemy 2 sessions and psycopg 3 with the reviewed binary distribution;
- PostgreSQL 16 as the only integration database;
- Alembic as the only schema-creation/evolution path;
- pytest and HTTPX for unit/API/integration tests;
- Ruff for formatting and linting;
- mypy for static type checks;
- pytest-cov for coverage evidence;
- Bandit for focused Python static security analysis;
- pip-audit for Python dependency vulnerability scanning; and
- cyclonedx-bom for reproducible CI SBOM evidence.

Direct top-level dependencies are pinned in `pyproject.toml` for the first approved implementation packet and all transitive versions are locked in `uv.lock`. Dependency updates remain reviewed changes with tests and vulnerability evidence.

Use one repository-root Python package under `src/golden_rose/`. A future frontend may use its own manifest under `apps/web/`; it does not require a premature Python workspace or JavaScript scaffold in this slice.

Use one synchronous SQLAlchemy session/transaction per command. The application authority performs authorization before write, then creates the `Employer` and `AuditEvent` within one explicit transaction. No ORM auto-table creation, background worker, queue, cache, event bus, or asynchronous database path is introduced.

## Consequences and constraints

- The first slice favors reviewable transaction semantics over speculative concurrency optimization.
- FastAPI request handlers may be normal synchronous functions; the framework may execute them in its worker threadpool.
- Database tests must run against PostgreSQL 16. Unit tests that do not exercise persistence may remain database-free.
- Local database startup is a separately approved coding-session action. The committed Compose definition is loopback-only and synthetic/test-only.
- GitHub Actions may run an ephemeral PostgreSQL 16 service and must execute locked dependency sync, formatting/lint, types, Bandit, tests/coverage, Alembic upgrade→downgrade→upgrade, dependency audit, and SBOM generation.
- Application CI is introduced before it is added to protected-branch required checks. The reviewed repository policy can require it after the check has completed successfully on a real PR.
- This ADR selects a development/runtime toolchain, not a cloud region, production account, identity provider, data-admission posture, or public trust plane.

## Alternatives considered

- **Asynchronous SQLAlchemy/psycopg:** deferred until measured concurrency or latency demonstrates a need; it would enlarge transaction, testing, and failure-state complexity now.
- **SQLite for local/integration tests:** rejected because it cannot prove selected PostgreSQL constraints, JSONB, concurrency, and transaction behavior.
- **Poetry, pip-tools, or ad hoc virtualenv requirements files:** rejected in favor of the already available, lockfile-oriented `uv` workflow.
- **Premature monorepo workspace tooling:** deferred until a second application manifest exists.
- **Microservices/event sourcing:** rejected for this slice; authoritative current state remains in PostgreSQL domain rows with append-only material audit history.

## Approval and revisit trigger

Beatrice accepted this stack on 2026-08-04 for the first Phase 1 slice. Revisit only when a concrete requirement demonstrates that Python 3.12, synchronous request/database handling, PostgreSQL 16, or the root package layout creates a material security, supportability, deployment, or performance constraint.