# Golden Rose Operations Platform

This repository contains bounded synthetic/local backend tracers for the Golden
Rose staff employer-demand workflow. A first staff Employer browser workspace
is proposed but not yet implemented. This is not a public portal, production deployment, or
automated hiring, matching, ranking, eligibility, or referral system.

## Current tracer boundary

- Exposes `POST /api/staff/v1/employers`, `GET /api/staff/v1/employers/{employer_id}`,
  and bounded `POST /api/staff/v1/employers/search` on the staff plane.
- Create accepts only a bounded `employer_type` and normalized `display_name`;
  search requires a bounded name fragment with optional type and opaque cursor.
- Uses a synthetic staff principal only in `local` and `test` environments;
  `production` with synthetic authentication fails during application creation.
- Writes a draft `Employer`, idempotency `CommandReceipt`, and append-only
  `AuditEvent` atomically in PostgreSQL.
- Uses fictional/synthetic fixtures only. Do not use client, live, or
  production data.
- ADR-0005 accepts a standalone `apps/web/` frontend boundary over only these
  contracts; implementation remains unauthorized until the planning packet
  merges and a fresh session receives separate implementation approval.

## Local verification

Copy `.env.example` into an ignored local environment file and supply a
disposable PostgreSQL database URL plus a synthetic staff UUID. Start the
approved local test database, then run migrations before the integration suite:

```text
uv sync --locked --all-groups
uv run alembic upgrade head
uv run pytest --cov=golden_rose --cov-report=term-missing --cov-fail-under=95
uv run alembic downgrade base
uv run alembic upgrade head
uv run ruff format --check .
uv run ruff check .
uv run mypy src tests
uv run bandit -q -r src
uv run pip-audit --skip-editable
```

The application must not be started against production settings with synthetic
authentication. No infrastructure, public route, real identity integration, or
live-data use is authorized by this tracer.
