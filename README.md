# Golden Rose Operations Platform

This repository contains the Golden Rose staff operations platform source. It
supports staff-facing worker/employer intake, staff account administration,
dashboard operations, deployable-package guardrails and controlled live-data
staff pilot readiness.

This is not a public portal, automatic hiring/matching/ranking/eligibility/
referral system, or self-service worker/employer application. Human staff
decision boundaries, named staff accountability, bilingual/accessibility parity,
auth-sensitive no-store handling and separate public/staff identity planes remain
core product constraints.

## 2026-10-01 — Current status after PR #156

PR #156, `feat: add live-data staff pilot readiness`, is merged into protected
`develop` at `985a8d1ac8630310ea58c0bca809665612c5ddbc`. The source now
contains the controlled live-data staff pilot readiness runbook/template/
validator, package-index wiring and production-mode environment marker for a
staff-only working environment where real worker and employer records may be
entered only after a separate operator-held cloud packet validates staff OIDC,
named accounts, disabled demo/presentation/static-example posture, live-data
scope, backup/restore, data governance, support/training/manual acceptance,
rollback/closeout and migration-disposition boundaries.

No current cloud deployment, service mutation, migration execution, production
completion, live identity-provider activation, credential rotation, data
export/import or client-owned transition is implied by this repository status.
Older fictional/synthetic and private-demo references below are historical
evidence or local/test guidance unless a current section explicitly says
otherwise.

## 2026-09-14 — Staff intake planning boundary

The proposed outcome spans PRs A–D, including bounded canonical correction and current-facts re-review (contract §9), not read-only-after-finalization maintenance. Original intake/review/output links remain immutable; corrections use separate reasoned, permission/version-checked, audited commands. Saves are section-local with independent keys/status and aggregate unsaved indication. Docs-only publication is independent of UI merge; both accepted planning and preserved UI merges gate coding. These are proposed contracts, not implemented or verified functionality.

Accepted conversational direction is durable shared worker/employer intake with explicit save/resume, version-bound review and follow-up, restricted addresses, deliberate existing-party links without overwrite, and atomic finalization only after complete current review. Technical details remain proposed source contracts, not deployed functionality or new client/counsel policy. See [Staff intake contract](docs/planning/staff-intake-contract.md), [outcome-scale plan](.hermes/plans/2026-09-14-staff-intake-workflows-plan.md), and proposed [ADR-0017](docs/adr/ADR-0017-staff-intake-workflows.md).

The improved Wave 1 UI is the preserved uncommitted predecessor in `/Users/genie/Desktop/golden_rose_project` on `feat/staff-intake-workflows`; do not reset, stash, copy over, or mix it into this docs-only planning worktree. Complete and merge that predecessor and the accepted planning packet before intake coding. V28 deployment/browser evidence is historical and its packet consumed; this audit did not recheck runtime availability or access expiry. The last recorded formal status remains `not_qualified`. No cloud, live-data, public-plane, implementation, or service-start authority is granted here.

## Current tracer boundary (implemented predecessor, not intake scope)

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
  the Wave 1 improved-UI candidate must finish review/qualification and merge
  as the separate predecessor before staff-intake implementation begins.

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
authentication. Local and automated tests use disposable or fictional fixtures.
The next controlled staff pilot may contain real worker and employer records
only after a separate operator-held cloud packet validates the live-data scope,
named staff access, staff OIDC, disabled demo/static-example posture, backup/
restore, data governance, support/training/manual acceptance, rollback/closeout
and migration-disposition boundaries. Project IDs, billing IDs, domains, user
emails, credentials, service URLs and secret payloads must stay out of tracked
source and ordinary docs.
