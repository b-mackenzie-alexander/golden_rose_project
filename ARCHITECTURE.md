# Architecture — Golden Rose Operations Platform

**Status:** Proposed architecture baseline. It describes intended boundaries, not an approved cloud deployment or running system.

## Architectural posture
Start with one modular product and a relational operational core. Preserve explicit trust boundaries and auditability without prematurely splitting into microservices.

## Logical components
```text
Agency Staff Web App ──┐
                       ├─ Staff API / domain service ─┐
Public Worker/Employer ┤                               ├─ PostgreSQL operational records
Apps (later, separate) └─ Public API / domain service ─┤
                                                       ├─ Private document store (later, qualified)
                                                       ├─ Audit-event / reporting projections
                                                       └─ Observability, backup, secret-management services
```

## Security-plane boundary
- **Staff plane:** separate hostname/application/API route set, identity client, session/token audience, credentials, authorization policies, and deployment secrets. Staff actions are attributable and MFA is required before live use.
- **Public plane:** future worker/employer experience. It does not receive generic administrative APIs or access to staff-plane credentials/data.
- **Controlled crossing:** staff can take defined, audited actions on public-workflow records. Public identities cannot self-promote into staff roles.

The logical split does not require independent products or microservices in V1. It requires deliberate identity, endpoint, credential, deployment, and data-access separation.

## Authoritative data and derived views
PostgreSQL is the proposed transactional system of record for approved operational entities. The dashboard, calendar/month views, work queues, and metrics are derived projections/queries over authoritative records; they are not independent manual response stores.

Material operational changes preserve actor, time, reason where applicable, source/reference, and relationship to the prior record/event. Corrections, voids, cancellations, replacements, and supersessions are linked actions rather than silent overwrites of issued/audited history.

## Proposed technology direction
- React + TypeScript + Vite + Tailwind CSS for browser UIs.
- Python + FastAPI for typed domain APIs and authorization.
- PostgreSQL with SQLAlchemy and Alembic for transactional data and migration-managed changes.
- Managed cloud container/database/object-storage services are candidates only; the existing first-priced reference is Google Cloud Run + Cloud SQL, with AWS equivalents retained for comparison.
- GitHub-based CI/CD and repository governance as code; exact provider/account configuration remains unapproved.

See `TECHNOLOGY_DECISIONS.md` for rationale and `docs/adr/` for durable decisions.

## Data boundaries
- Minimize personal, household, location, document, and free-text data.
- Keep exact worksite/household address internal by default; use least-precise location outside approved workflows.
- Store documents outside database rows with private, controlled access only after document-ingestion qualification.
- Keep secrets out of Git, logs, client builds, and ordinary operational records.
- Use synthetic/de-identified data in development until an approved test-data procedure exists.

## Environment and promotion model
```text
feature/* → PR/CI → develop (isolated non-production, synthetic/approved data)
develop   → PR/release evidence → main (immutable production candidate)
main artifact → protected explicit production promotion
```

`develop` and production require isolated projects/accounts/resources, identity clients, secrets, databases, buckets, and budgets. Production is a deliberate promotion of the qualified immutable artifact, not an automatic side effect of a merge.

## Deferred architecture decisions
Identity provider; cloud provider/region; production topology; infrastructure-as-code implementation; document/malware-scanning services; background workers; messaging/signature/payment/screening integrations; RTO/RPO; WAF/CDN/network design; and exact dashboard/reporting technology.
