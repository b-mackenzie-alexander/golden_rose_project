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
  Cloud SQL testing environment. State establishment, ownership reconciliation,
  exact foundation apply, and workload-free post-apply verification are complete.
  PR #74 merged canonical Cosign v3 signature admission at `develop@92b104e`.
  Approved run `33882394981` completed immutable build/push/scan, keyless signing,
  all three attestations, certificate/transparency verification, final repository
  semantic admission, and verifier-approved immutable-reference emission.
  Gate P is complete; its one-use approval is consumed. V28 later completed
  real Secret versions, private SQL/database authority, restricted migration,
  service activation, expiring Basic access, automated qualification, and browser
  handoff at protected `develop@3414818b44d5e790f2d11c7fe4d7a48ebeb6241e`.
  The service is not production and the formal qualification status remains
  `not_qualified` because the Spanish toggle failed and required manual rows remain open.
- Terraform/IaC follows the accepted fictional-synthetic GCP `develop`
  posture: `us-east4`; split bootstrap, publication, deployment, runtime, and
  migration identities; durable remote state; immutable digest promotion;
  Secret Manager metadata/IAM only; staged private Cloud SQL/VPC; temporary exact
  `allUsers` Cloud Run invocation behind the expiring application Basic gate;
  value-safe observability; and intentional teardown. Gate F, Gate P, bounded
  Secret preparation, private database authority, migration, service activation,
  automated qualification, and browser handoff are complete through v28. The
  historical PR #83-#89 source/remediation and stopped-packet sequence remains
  preserved in `NOTES.md`; those predecessor approvals and the completed v28 packet
  are consumed. Ordinary product feedback/source work uses the running service.
  Any future backend/state, plan/apply, image, Secret, database, migration, service,
  access, or qualification mutation requires fresh scoped approval; real identity,
  live data, and production remain separate. Private identifiers and secret payloads
  stay outside tracked source and ordinary documentation.
- Source-controlled Gate 2 read-only verification tooling now exists: `scripts/verify_gcp_foundation.py`
  evaluates live foundation/effective-authority posture against the reviewed
  contract without adding any mutation mode, and `deploy/gcp/evidence-template.md`
  defines the minimized redacted evidence shape for approved verification runs.
- Source-controlled fictional-synthetic qualification tooling now also exists:
  `scripts/qualify_develop_deployment.py` keeps health/readiness separate from
  bounded workflow qualification, requires the expiring application Basic
  credential through a non-argv handoff, uses newly generated fictional values
  only, and emits minimized evidence without leaking submitted identifiers,
  cursors, credentials, DSNs, or raw bodies.
- PR #29 merged the six authorized static remediations at `08fe305`: semantic
  policy, deterministic `uv`, Direct VPC/private-SQL declaration, API ordering,
  Cloud SQL backup enablement, and managed-registry digest authority. The
  self-authorizing same-repository-CI High remains open accepted residual risk.
  Accepted ADR-0012 reflects the permanent single-maintainer reality: no
  unavailable second human is required, and agent/CI review is quality evidence
  rather than independent authorization. PR #33 merged its consolidated
  source-controlled pre-deployment work. Its older separate-gate sequence is
  historical for this target; ADR-0016 permitted the now-consumed v28 packet,
  which completed fictional-synthetic deployment and qualification.
- Accepted ADR-0013 defines staged `foundation → migration → service` Terraform
  authority, Terraform-only configuration ownership, exact viewer/job-executor and
  direct-workflow WIF authority, digest-bound Cosign/SLSA/SBOM verification, and
  readiness monitoring. Its former named-IAM-only tester boundary is superseded for
  this fictional-synthetic target by ADR-0016's exact temporary `allUsers` service
  invoker behind the expiring application Basic gate.
  PR #37/PR #42/PR #46/PR #48 closed the source and verifier blockers; PR #57
  closed A1; PR #62/PR #63/PR #64 closed the later state/evaluation source
  corrections. E2/E3 state establishment/readback, A5, ownership alignment, the
  replacement-free foundation plan/apply, and post-apply verification are now
  complete. PR #74 merged at `92b104e`; successful run `33882394981` completed
  publication, signing, all attestations, transparency verification, final semantic
  admission, and verifier-approved immutable-reference emission. Gate P is complete.
- Merged source also carries a reviewed local clean-room qualification
  harness that exercises the approved pre-deployment bundle against a disposable
  repo copy plus Docker-backed synthetic PostgreSQL, including Terraform/static
  checks, service-backed tests, provenance/SBOM checks, and source-repo Git/Gitleaks
  hygiene. That evidence is local-only and does not imply cloud qualification.
- ADR-0014 now governs delivery granularity: one accepted outcome-scale plan may
  span several roadmap items and implementation PRs, while TDD stays small and
  hazardous authority remains explicit. ADR-0016's newer addendum permitted the
  consumed v28 packet to bundle precheck, plans/applies, image, secrets, migration,
  service, access, readbacks, and qualification. The private synthetic service is
  now running; live data, production, destructive recovery/state editing, future
  cloud mutation, and out-of-packet authority remain separate.
- Automated frontend parity/accessibility evidence exists, and the v28 browser
  handoff exposed a production Spanish-toggle defect plus severe workspace UX
  deficiencies. Manual accessibility/fluent-language qualification remains open;
  the accepted Wave 1 plan repairs the complete frontend surface in one later PR.

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
