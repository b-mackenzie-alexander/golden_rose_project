# Golden Rose Operations Platform

This repository contains bounded synthetic/local tracers for the Golden Rose
staff employer-demand workflow. The first staff Employer browser workspace,
its closeout, bounded draft-Employer revision, and backend EmployerContact
authority foundation are merged into `develop`.
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
- PR #20 merged the independently reviewed ADR-0008 EmployerContact authority
  implementation into `develop` at `6eb05d5`: nested create, bounded parent
  collection-query, exact read, and typed receipt/audit authority.
- PR #22 merged the local-only runtime/container contract into `develop` at
  `f3cac4d`: explicit private-synthetic `develop` posture, value-safe marker,
  `/health`, bounded `/readiness`, same-origin static serving, entrypoint/runtime
  behavior, and non-root local image build/inspection evidence.
- Accepted ADR-0009 targets one private, fictional-synthetic-only Cloud Run +
  Cloud SQL testing environment. PR #24 merged the local validate-without-apply
  Terraform scaffold into `develop` at `50451b3`; no cloud resource or running
  shared system exists. No public access, real identity, live/client data, or
  production claim is currently authorized or present.
- Terraform/IaC planning now uses the accepted 14-decision private synthetic-only
  GCP `develop` posture: `us-east4` for Cloud Run, Cloud SQL, and Artifact
  Registry; Terraform-managed APIs; split bootstrap/WIF provisioning identity;
  separate runtime/migration identities; private Artifact Registry digest
  deployment; Terraform-managed $50/$75/$100 budget alerts; Secret Manager
  metadata/IAM only; private Cloud SQL and VPC access; private Cloud Run
  invoker IAM; protected GitHub WIF gates; value-safe observability; standard
  labels; intentional teardown runbook support; and local state only until remote
  state is approved. Beatrice accepted a durable bootstrap/state control plane
  separate from disposable workload teardown; the existing non-workload project
  is the candidate boundary pending read-only qualification. A separate reviewed
  plan is required before implementing that contract. Terraform plan/apply,
  backend migration, cloud authentication/API calls, resource/service-identity
  provisioning, image push, deployment, real identity, live/client data, and
  production remain separately gated.
- Independent post-merge review found the merged scaffold is not yet a safe
  provisioning/deployment baseline. Required CI governance, semantic static
  policy, deterministic `uv`, Cloud Run/private-SQL connectivity, API ordering,
  Cloud SQL backup configuration, and managed-registry image binding require a
  separately reviewed validate-without-apply remediation before bootstrap work.
  PR #25 merged the documentation-only disposition at `8dc1198`, and PR #26
  merged the original remediation planning packet at `c5a1380`. Because this is
  a single-maintainer repository with no independent reviewer/CODEOWNER,
  PR #27 merged accepted ADR-0011 and its paired plan at `23f97cc7`: the
  self-authorizing-CI High remains open while only six static
  validate-without-apply tasks may begin from a fresh merged-tip branch.
  Bootstrap and cloud/deployment work remain blocked.
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
authentication. The approved cloud implementation/testing lane must use the
dedicated GCP deployment/testing project with wholly fictional synthetic data;
project IDs, billing IDs, domains, user emails, credentials, and secret payloads
must stay out of tracked source and ordinary docs. Public access, real identity
integration, live-data use, and production remain separately gated.
