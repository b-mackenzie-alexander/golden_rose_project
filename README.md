# Golden Rose Operations Platform

This repository contains bounded synthetic/local tracers for the Golden Rose
staff employer-demand workflow. The first staff Employer browser workspace,
its closeout, and the bounded draft-Employer revision slice are merged into
`develop`.
This is not a public portal, production deployment, or
automated hiring, matching, ranking, eligibility, or referral system.

## Current tracer boundary

- Exposes `POST /api/staff/v1/employers`, `GET /api/staff/v1/employers/{employer_id}`,
  bounded `POST /api/staff/v1/employers/search`, and bounded
  `POST /api/staff/v1/employers/{employer_id}/revisions` on the staff plane.
- Create accepts only a bounded `employer_type` and normalized `display_name`;
  search requires a bounded name fragment with optional type and opaque cursor.
- Uses a synthetic staff principal only in `local` and `test` environments;
  `production` with synthetic authentication fails during application creation.
- Writes draft Employer creation/revision changes, idempotency `CommandReceipt`
  authority, and append-only `AuditEvent` evidence atomically in PostgreSQL.
- Uses fictional/synthetic fixtures only. Do not use client, live, or
  production data.
- ADR-0005 accepted a standalone `apps/web/` frontend boundary over only these
  contracts, and PR #13 merged the initial local/synthetic Employer workspace.
- ADR-0006 governs the closeout merged by PR #15. ADR-0007 and its paired plan
  govern the draft-revision implementation merged by PR #17 at `1543248`;
  PR #18 merged its bounded remediation at `a4d8f90`.
- The active lane is planning publication. Accepted ADR-0008 and its paired plan
  define a backend EmployerContact create, bounded parent collection-query,
  exact-read, and authority foundation. Exact-artifact review passed, but no
  adjacent implementation is authorized until the planning packet merges through
  protected `develop` and a fresh coding lane receives separate approval.
- Automated frontend parity/accessibility evidence exists locally, but human
  browser/manual accessibility/fluent-language qualification remains deferred
  until a shared deployed `develop` target exists.

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
mkdir -p build
npm --userconfig apps/web/.npmrc --prefix apps/web sbom --sbom-format cyclonedx --sbom-type application > build/frontend-sbom.cdx.json
uv run python scripts/validate_sbom.py build/frontend-sbom.cdx.json --spec 1.5 --name web --version 0.0.0 --purl 'pkg:npm/%40golden-rose/web@0.0.0'
uv run cyclonedx-py environment --pyproject pyproject.toml --output-reproducible --of JSON -o build/backend-sbom.cdx.json
uv run python scripts/validate_sbom.py build/backend-sbom.cdx.json --spec 1.6 --name golden-rose --version 0.1.0
```

The application must not be started against production settings with synthetic
authentication. No infrastructure, public route, real identity integration, or
live-data use is authorized by this tracer.
