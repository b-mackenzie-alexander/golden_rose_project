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
- Terraform/IaC implementation now follows the accepted 14-decision private synthetic-only
  GCP `develop` posture: `us-east4` for Cloud Run, Cloud SQL, and Artifact
  Registry; Terraform-managed APIs; split bootstrap/WIF provisioning identity;
  separate runtime/migration identities; private Artifact Registry digest
  deployment; Terraform-managed $50/$75/$100 budget alerts; Secret Manager
  metadata/IAM only; private Cloud SQL and VPC access; private Cloud Run
  invoker IAM; protected GitHub WIF gates; value-safe observability; standard
  labels; intentional teardown runbook support; and local state only until remote
  state is approved. Beatrice accepted a durable bootstrap/state control plane
  separate from disposable workload teardown; the existing non-workload project
  is the candidate boundary pending read-only qualification. The source-controlled
  implementation lane merged through PR #33 at `3c0118a`. A post-merge audit
  found F1-F17 deployment-path defects, including four Blockers; accepted
  ADR-0013 and its paired plan now govern a documentation-gated no-cloud
  remediation before any read-only qualification or Terraform progression. Terraform plan/apply,
  backend migration, cloud authentication/API calls, resource/service-identity
  provisioning, image push, deployment, real identity, live/client data, and
  production remain separately gated.
- Source-controlled Gate 2 read-only verification tooling now exists: `scripts/verify_gcp_foundation.py`
  evaluates live foundation/effective-authority posture against the reviewed
  contract without adding any mutation mode, and `deploy/gcp/evidence-template.md`
  defines the minimized redacted evidence shape for that later qualification step.
- Source-controlled private-synthetic qualification tooling now also exists:
  `scripts/qualify_develop_deployment.py` keeps health/readiness separate from
  bounded workflow qualification, requires authenticated private access, uses
  newly generated fictional values only, and emits minimized evidence without
  leaking submitted identifiers, cursors, tokens, DSNs, or raw bodies.
- PR #29 merged the six authorized static remediations at `08fe305`: semantic
  policy, deterministic `uv`, Direct VPC/private-SQL declaration, API ordering,
  Cloud SQL backup enablement, and managed-registry digest authority. The
  self-authorizing same-repository-CI High remains open accepted residual risk.
  Accepted ADR-0012 reflects the permanent single-maintainer reality: no
  unavailable second human is required, and agent/CI review is quality evidence
  rather than independent authorization. Its consolidated plan covers all
  remaining source-controlled pre-deployment work in one later PR while keeping
  read-only GCP qualification, Terraform plan, foundation apply, first private
  synthetic deployment, and qualification as separate explicit owner gates.
- Accepted ADR-0013 adds the required post-PR33 boundary: staged
  `foundation → migration → service` Terraform authority; Terraform-only
  configuration ownership; IAM-private internet-reachable named testers;
  exact viewer/job-executor and direct-workflow WIF authority; keyless
  digest-bound Cosign/SLSA/SBOM verification; and authenticated `/readiness`
  availability monitoring. PR #35 merged the amended planning packet at
  `db1f293`; PR #37 then merged the no-cloud remediation into protected
  `develop` at `caf96a7`. PR #42 subsequently merged the bounded source-only
  verifier reconciliation at `b2d79b5`: tester authority is required only at
  service stage, while private Cloud SQL remains a required lower-layer
  foundation contract. The next step is to freeze the remaining Gate 2
  decisions and reconcile the partial live foundation before distinct Terraform
  plan/apply gates. Separately approved operator work has established a partial
  non-executable foundation; private records hold its identifiers and raw
  evidence. No image publication, executable deployment, or qualification has
  occurred.
- The current branch also carries a reviewed local clean-room qualification
  harness that exercises the approved pre-deployment bundle against a disposable
  repo copy plus Docker-backed synthetic PostgreSQL, including Terraform/static
  checks, service-backed tests, provenance/SBOM checks, and source-repo Git/Gitleaks
  hygiene. That evidence is local-only and does not imply cloud qualification.
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
