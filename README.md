# Golden Rose Operations Platform

This repository contains a bounded backend tracer for the Golden Rose staff
employer-demand workflow. It is not a public portal, production deployment, or
automated hiring, matching, ranking, eligibility, or referral system.

## Current tracer boundary

- Exposes only `POST /api/staff/v1/employers`.
- Accepts only a bounded `employer_type` and normalized `display_name`.
- Uses a synthetic staff principal only in `local` and `test` environments;
  `production` with synthetic authentication fails during application creation.
- Writes a draft `Employer`, idempotency `CommandReceipt`, and append-only
  `AuditEvent` atomically in PostgreSQL.
- Uses fictional/synthetic fixtures only. Do not use client, live, or
  production data.

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
