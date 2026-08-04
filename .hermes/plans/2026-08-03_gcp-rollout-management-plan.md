# Golden Rose GCP Rollout and Service Management Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task after explicit approval.

**Goal:** Roll out and operate a narrowly scoped, staff-only employer-demand workflow on GCP without prematurely enabling public access, live-data collection, uploads, automated matching, or unnecessary infrastructure.

**Architecture:** Preserve one modular product with materially separate staff and future public trust planes. Develop and qualify locally first, promote immutable containers through an isolated GCP non-production environment, and permit production only after data, identity, recovery, security, client-ownership, and support gates pass.

**Tech Stack:** React/TypeScript/Vite, FastAPI/Python, PostgreSQL/SQLAlchemy/Alembic, Docker, Cloud Run, Cloud SQL for PostgreSQL, Artifact Registry, Secret Manager, Cloud Logging/Monitoring, GitHub Actions with Workload Identity Federation; Cloud Storage, Cloud Tasks, Cloud Scheduler, Identity Platform, and Maps only when their workflow need is approved.

---

## 1. Scope and operating objective

The first rollout serves authorized agency staff performing this workflow:

`employer → contact → worksite → staffing request → shift need → review/correction → demand queue → derived calendar/coverage view`

The service must reduce duplicate paper/form handling while preserving human agency review, attributable corrections, and authoritative operational history.

### Included in the first rollout

- Staff authentication and server-enforced authorization.
- Employer-demand entry, retrieval, review, correction, and queue management.
- Derived calendar/shift-coverage views from authoritative records.
- Audit events, safe operational logging, monitoring, backup, restore, rollback, support, and training evidence.
- Synthetic/de-identified data until a separate production-data gate is approved.

### Explicitly excluded

- Public employer or worker portals.
- Document uploads, payments, signatures, screening, messaging, and Maps/geocoding.
- Legacy-data migration or unrestricted live-data import.
- Automated matching, ranking, eligibility, hiring, or referral decisions.
- Kubernetes, self-managed VMs, and premature service decomposition.

## 2. Proposed GCP ownership boundaries

| Concern | Proposed service | Initial boundary |
|---|---|---|
| Staff web/API | Cloud Run | Separate staff hostname, endpoints, runtime identity, secrets, and authorization policy |
| Operational records | Cloud SQL for PostgreSQL | Authoritative employer-demand records; migration-managed schema; least-privilege application role |
| Container images | Artifact Registry | Immutable, vulnerability-reviewed images promoted by digest |
| Application secrets | Secret Manager | Environment-specific access granted only to the relevant runtime/deployment identity |
| Authentication | Identity Platform, subject to identity design approval | Staff-only client/audience, MFA, recovery, deprovisioning, and no public-to-staff role promotion |
| Logs and alerts | Cloud Logging and Monitoring | Structured operational logs with personal-data redaction; audit events remain distinct |
| CI/CD | GitHub Actions + Workload Identity Federation | No long-lived GCP service-account keys; environment-specific deployment identities |
| Documents | Private Cloud Storage, deferred | No bucket or ingestion path until upload purpose, scanning, retention, and authorization are approved |
| Scheduled/async work | Cloud Scheduler and Cloud Tasks, deferred | Add only for an approved expiration/notification workflow; no hidden business decisions |
| Mapping | Google Maps Platform, deferred | Broad service zones remain the baseline; no exact-location transfer without separate approval |

## 3. Rollout sequence

### Stage 0 — Confirm workflow and cloud decisions

**Exit criteria**

- The accepted canonical inventory, state model, queue model, calendar semantics, adaptive CDTA-composed zone taxonomy, NYC job-demand map contract, staff permission matrix, and MFA/recovery/support contract remain authoritative. The client validates terminology, provisional queue policy, zone/map usability/delegation/out-of-area policy, exact-address recipients, live renderer/tile/geocoder provider posture, staged requiredness, named staff roles, and support contacts; exact zone names are not an implementation gate.
- Staff role/permission and production MFA, account-recovery, session, access-review, support-ownership, and Platform Administrator boundaries are accepted. Production activation still requires named personnel, identity-provider/configuration qualification, initial cohort/data classification, and rehearsed procedures.
- GCP is recorded as the selected platform with a validated region and documented alternatives/revisit triggers.
- Development and production ownership, budgets, domain/DNS, incident contacts, and production promotion authority are named. The signed contractual constraint is recorded: Beatrice pays approved infrastructure charges until final payment for the engagement, after which billing responsibility transfers to the client through a documented handoff.
- Cloud SQL HA, backup/PITR, RTO/RPO, retention, and restore-test expectations are decided.

**Documentation follow-up after approval**

- Update `TECHNOLOGY_DECISIONS.md` and create a GCP ADR under `docs/adr/`.
- Align `ARCHITECTURE.md`, `SECURITY.md`, `CURRENT_WORK.md`, `ROADMAP.md`, and `NOTES.md`.

### Stage 1 — Build and qualify locally

- Implement the approved staff workflow with tests first and synthetic/de-identified fixtures.
- Use local containers and PostgreSQL-compatible behavior to prove schema migrations, authorization, audit events, queue/calendar derivation, backup/restore procedure, and upgrade/rollback behavior.
- Keep cloud provisioning, public routes, integrations, uploads, and production data disabled.

**Promotion evidence**

- Unit, integration, authorization, migration, accessibility, English/Spanish parity, audit/log-redaction, backup/restore, and security checks pass.
- A staff workflow demonstration confirms entry, retrieval, correction, queue use, and derived calendar behavior.

### Stage 2 — Establish the isolated GCP non-production foundation

- Create a dedicated non-production GCP project with billing budget alerts and named owners.
- Configure least-privilege human groups and service accounts; prohibit routine owner/editor use.
- Establish Artifact Registry, Secret Manager, Cloud Run, Cloud SQL, Logging/Monitoring, and GitHub Workload Identity Federation.
- Use synthetic/approved test data only.
- Restrict ingress and administrative access according to the approved staff-plane design.
- Capture infrastructure as reviewed code before treating the environment as reproducible.

**Exit criteria**

- Deployment uses an immutable image digest and no stored GCP service-account key.
- Cloud Run cannot read unrelated secrets or administer Cloud SQL.
- Database access, migrations, backups, logs, alerts, budgets, rollback, and environment teardown/rebuild are verified.
- No public workflow, upload path, Maps integration, or production dataset is present.

### Stage 3 — Deploy and qualify the staff pilot in non-production

- Deploy the same application artifact intended for production qualification.
- Run end-to-end tests for staff identity, role enforcement, demand entry/search/correction, audit history, queue/calendar derivation, logging, alerting, concurrency, and failure states.
- Exercise restore into an isolated target and document measured recovery behavior.
- Conduct independent security and privacy review, resolve all High/Blocker findings, and record residual risks.
- Obtain agency acceptance using synthetic or separately approved test records.

**Exit criteria**

- Acceptance owner signs off on workflow behavior and manual fallback.
- Monitoring, incident triage, account recovery, staff offboarding, rollback/forward recovery, and support procedures are rehearsed.
- Production-data classification, minimization, retention, access, export, and deletion rules are approved.

### Stage 4 — Controlled production pilot

- Create a separate production GCP project, database, secrets, identity client, budgets, and deployment identity.
- Promote the qualified immutable artifact; do not rebuild it for production.
- Start with a named, limited staff cohort and the minimum approved data scope.
- Keep legacy/manual fallback available during the observation window.
- Hold a recorded go/no-go review before expansion.
- Maintain Beatrice's interim billing responsibility until final contract payment is confirmed; do not prematurely transfer billing liability or remove the continuity controls needed for the staff pilot.

**Pilot success measures**

- Authorized staff can reliably create and retrieve demand records.
- Corrections and state changes are attributable and recoverable.
- Queue aging and calendar/coverage views agree with authoritative records.
- No cross-role access, secret leakage, material personal-data logging, or unapproved integrations occur.
- Support burden, incident frequency, latency, error rate, database capacity, and monthly cost remain within approved thresholds.

### Stage 5 — Stabilize, then expand deliberately

- Resolve pilot findings before adding users, data classes, or workflows.
- Add worker profiles, uploads, public access, asynchronous notifications, or Maps only through separate field-purpose, privacy, security, accessibility, operational, and client-approval gates.
- Promote each expansion as its own qualified increment; rollout is not blanket permission for future features.

## 4. Ongoing service management

### Daily/continuous

- Monitor availability, application errors, failed authentication, authorization denials, Cloud SQL health/connections, task failures if enabled, and budget anomalies.
- Keep operational logs free of secrets and unnecessary personal/location data.
- Route alerts to a named human owner; avoid alerts with no response procedure.

### Weekly during the pilot

- Review incidents, error trends, support requests, audit anomalies, database/storage growth, backup status, identity changes, and spend against budget.
- Reconcile workflow metrics to authoritative records rather than a parallel spreadsheet.
- Record client feedback as Observed or Reported evidence, not automatic requirements.

### Per release

- Require protected PR/CI checks, dependency and secret scanning, authorization and migration tests, immutable image identification, independent review, release notes, rollback/forward-recovery instructions, and explicit promotion approval.
- Use expand → migrate/backfill → switch → contract for database changes.
- Verify monitoring and support documentation before promotion.

### Monthly/quarterly, with cadence approved before production

- Review IAM membership, service-account permissions, staff accounts, recovery/break-glass access, secrets, dependencies, retention, costs, quotas, capacity, and incident trends.
- Perform scheduled restore tests and record measured results against RTO/RPO.
- Review whether Cloud SQL sizing/HA, Cloud Run minimum instances/concurrency, and log retention still match actual use.
- Revisit vendor services only when workflow evidence justifies their cost and data-processing impact.

## 5. Management roles

| Role | Responsibility |
|---|---|
| Client/agency owner | Business workflow, production-data, user-cohort, policy, and rollout acceptance |
| Owner/delegated Manager | Agency account lifecycle and approved operational permissions |
| Operations Staff | Employer-demand workflow within assigned permissions; no cloud administration |
| Platform Administrator | Deployment health and approved technical support; no standing access to operational personal data or business-role administration |
| Beatrice/project technical lead | Architecture, delivery evidence, cost/security posture, and promotion recommendation |
| Independent reviewer | Security, privacy, authorization, migration, recovery, and release-evidence review |

Production access must not rely on one person without documented recovery and transfer procedures. Under the reported signed contractual term, Beatrice pays approved infrastructure charges until the final engagement payment has been rendered. At that point, a documented client handoff transfers billing responsibility along with the agreed account/project, budget-alert, domain/DNS, data, support, recovery, and long-term operational-access ownership. Record final-payment confirmation, the effective transfer date, responsible contacts, and a continuity check; do not transfer secrets through chat or source control.

## 6. Cost controls

- Estimate non-production and production separately.
- Treat Cloud SQL as the likely fixed baseline cost; Cloud Run scale-to-zero does not eliminate database cost.
- Set budgets and alerts before workload deployment, but do not describe budget alerts as hard spending caps.
- Track database compute/storage/backups/HA, Cloud Run minimum instances and egress, logging retention, Artifact Registry, secrets/KMS, identity/MFA, network/edge, support, and post-credit cost.
- Review actual cost during the pilot before enabling HA increases, minimum instances, additional environments, Maps, tasks, or document storage.

## 7. Risks and controls

| Risk | Control |
|---|---|
| Cloud learning curve creates misconfiguration | Managed services, least-privilege templates, reviewed infrastructure as code, staged non-production qualification |
| Cloud Run scales down but Cloud SQL remains costly | Separate cost model, smallest qualified instance, measured sizing, budget alerts, periodic rightsizing |
| Public/staff trust boundaries collapse | Separate identity audience, endpoints, credentials, deployment secrets, authorization, and later public runtime/data access |
| Platform support exposes client records | Separate Platform Administrator identity; time-bound approved break-glass path; attributable review |
| Rollout begins before workflow decisions | Stage 0 gates and explicit stop boundary before implementation or provisioning |
| Live data enters an unqualified system | Synthetic-only default and separate production-data approval gate |
| Logs or exports leak sensitive data | Structured allowlisted logs, redaction tests, scoped exports, access and retention controls |
| Failed migration or release corrupts operations | Migration tests, expand/contract evolution, backups, restore evidence, immutable artifact rollback/forward recovery |
| Feature expansion outruns agency capacity | Limited cohort, support metrics, go/no-go reviews, separate approval per data class/integration |
| Interim project billing is unclear or handoff interrupts service | Record Beatrice's temporary payment responsibility, budget owners, final-payment trigger, transfer checklist, effective handoff date, and client acceptance |

## 8. Open decisions before execution

1. Which GCP US region meets latency, service availability, recovery, and cost needs?
2. What account/project and billing topology will permit Beatrice's interim payment responsibility and a secure, documented transfer to the client after final payment?
3. Does the exact Identity Platform configuration satisfy `docs/planning/phase-1-mfa-recovery-support-ownership.md`, including passkey/security-key factors, recovery separation, session/revocation behavior, safe identity events, and handoff continuity?
4. What are the approved Cloud SQL HA, backup/PITR, RTO/RPO, and restore-test targets for pilot and production?
5. What exact pilot cohort, data fields, service zones, support hours, success thresholds, and observation period will the client approve?
6. Which infrastructure-as-code tool will manage GCP resources after the architecture decision is accepted?

## 9. Plan completion criteria

This rollout plan is ready for implementation planning only when:

- The Stage 0 client, workflow, security, ownership, recovery, and cost decisions are accepted.
- The GCP decision is recorded in the authoritative living documents and ADR register.
- The first coding slice has its own narrow TDD implementation plan.
- Separate approvals are understood for code implementation, GCP provisioning, first deployment, production-data use, and production promotion.
