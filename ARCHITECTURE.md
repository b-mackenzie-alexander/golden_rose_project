# Architecture — Golden Rose Operations Platform

**Status:** Accepted Phase 1 structural/security baseline with ADR-0009's private GCP `develop` boundary, PR #33's merged source-controlled pre-deployment implementation at `3c0118a`, and accepted ADR-0013's post-merge remediation boundary. PR #37 merged the F1–F17 no-cloud remediation at `caf96a7`; PR #42 merged the bounded stage-aware verifier reconciliation at `b2d79b5`. Separately approved private operator work established a partial non-executable foundation, while remaining Gate 2 decisions and every later transition stay gated; no running shared system exists.

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

## Staff authorization and support boundary
- The accepted business roles are Owner, delegated Manager, and interchangeable Operations Staff. Their named permissions, field restrictions, delegations, exact-location controls, export denial, and verification obligations are controlled by `docs/planning/phase-1-staff-permission-matrix.md`; permissions must be server-enforced, attributable, and limited to approved operational records/actions.
- Platform Administrator is a distinct technical-support role, not a business-superuser role. It uses a separate privileged identity/access path for health, cache/job remediation, and approved troubleshooting; it has no standing access to operational personal data, documents, raw database records, or business-role administration.
- Exceptional production support access requires time bounds, approval, attribution, logging, automatic expiry/revocation, and Owner review. Owner authority over agency operations does not imply routine cloud-console, secret, backup, or database access.
- `docs/planning/phase-1-mfa-recovery-support-ownership.md` controls individual staff/privileged identities, required MFA factors, step-up actions, staff/privileged session limits, independent recovery, access reviews, and support ownership. The identity provider must be qualified against that contract and cannot silently weaken application authorization or combine public/staff identity audiences.

## Authoritative data and derived views
PostgreSQL is the accepted transactional system of record for approved operational entities. Domain rows are authoritative current truth; append-only `AuditEvent` records are authoritative material history, not a full event-sourcing/replay store. `docs/planning/phase-1-correction-audit-event-contract.md` controls draft revisions, material corrections, atomic domain/event commands, concurrency/idempotency, protected prior/new values, correction-of-correction, and projection failure behavior. The dashboard, calendar/month views, work queues, map, search, reporting, and metrics are disposable derived projections/queries, not independent manual response stores.

The accepted Phase 1 structural source of truth is `Employer → EmployerContact / Worksite / StaffingRequest → ShiftNeed / RequestRequirement`, supported by `WorksiteZoneMembership`, `ServiceZone`, `ServiceZoneComposition`, `MapAreaDatasetVersion`, `MapArea`, `WorksiteMapAreaAssignment`, and `AuditEvent`. Worksite-to-zone and worksite-to-map-area relationships use explicit versioned association records; they are not collapsed into a direct service-zone foreign key. `Employer` is neutral across household and business hiring parties; employer type enables governed extensions without separate forms or response stores. `docs/planning/phase-1-canonical-field-purpose-inventory.md` controls the purpose, classification, visibility boundary, prohibited uses, and exclusions for these fields.

`docs/planning/phase-1-request-shift-state-model.md` controls guarded lifecycle transitions. Active shift coverage is represented in the shift state and may reverse with attributable count/source evidence, including reported no-shows. Terminal shift outcomes remain authoritative when the parent request closes. State transitions and audit events must be committed consistently; dashboards and calendars derive from those records rather than maintaining separate status.

`docs/planning/phase-1-work-queue-aging-follow-up-model.md` controls derived queue timing, ownership, follow-up, provisional review triggers, and deterministic lanes. Request record age, agency-controlled review time, explicit follow-up deadlines, and continuous shift urgency remain separate measures. Queue escalation increases authorized visibility/priority only; it does not mutate domain state, reassign work, or send external messages automatically.

`docs/planning/phase-1-calendar-coverage-semantics.md` controls the derived staff calendar. Date-only request milestones and timed shift occurrences remain distinct projections over authoritative records. No executable recurrence or worker-conflict inference exists in Phase 1. Calendar drag issues governed commands: active-shift rescheduling atomically creates a linked replacement and cancels the prior shift without transferring coverage.

`docs/planning/phase-1-service-zone-taxonomy.md` controls broad operational geography. The Owner may evolve labels and group pinned NYC CDTAs into zones during pilot use without engineering changes. A worksite may have overlapping effective memberships with one primary/default; requests and shifts may remain visibly unassigned until later classification. Zone catalog/composition, membership, workflow-record classification, CDTA derivation, and exact address remain separate authorities.

`docs/planning/phase-1-nyc-job-demand-map-contract.md` controls the Phase 1 authorized-staff NYC map. A pinned/checksummed DCP 2020 CDTA release supplies fixed geometry. A provider-neutral server-side geocoder yields a transient point for local point-in-polygon assignment; exact coordinates are discarded by default. The map derives transparent demand/coverage measures and an accessible equivalent table. Renderer, tile, and geocoder providers remain replaceable and separately gated. No worker layer exists until its location/availability contract is approved.

Material operational changes preserve the accepted event envelope, changed-field evidence, actor, server time, reason where applicable, source/reference, and relationship to prior record/event. Required domain changes and audit inserts commit atomically through one reviewed authority boundary; stale writes are rejected. Corrections, cancellations, replacements, and supersessions are linked actions rather than silent overwrites. Projection failure never rolls back committed truth or becomes a false empty result.

## Accepted and proposed technology direction
- ADR-0005 accepts React 19, TypeScript 5.9, Vite 8, npm, Vitest/Testing Library, plain CSS, and a typed English/Spanish catalog for the first local/synthetic staff browser slice. PR #12 merged that planning packet into `develop`, and PR #13 merged the first implementation.
- ADR-0006 governed the closeout merged by PR #15. ADR-0007 governed draft-Employer revision merged by PR #17 and remediated by PR #18. PR #20 merged ADR-0008's independently reviewed EmployerContact authority implementation at `6eb05d5`. PR #22 merged ADR-0009 Slice B's local runtime/container contract at `f3cac4d`; human browser/manual accessibility/fluent-language review and cloud deployment/runtime-role qualification remain future evidence gates.
- ADR-0003 accepts Python 3.12, uv, FastAPI/Pydantic v2, synchronous SQLAlchemy 2/psycopg 3, Alembic, and PostgreSQL 16 for the first backend slice.
- GCP is the selected platform. Cloud Run + Cloud SQL is the managed-container/database baseline; private Cloud Storage, Secret Manager, Artifact Registry, Cloud Logging/Monitoring, and GitHub Actions with Workload Identity Federation are the proposed supporting services. Beatrice accepted `us-east4` / Northern Virginia as the single `develop` deployment location for Cloud Run, Cloud SQL, and Artifact Registry. Beatrice reports a new GCP account with one organization and two projects, one dedicated exclusively to cloud deployment/testing. The other project is the candidate durable bootstrap/state/WIF control-plane boundary pending read-only qualification; it must survive workload teardown and redeployment. Billing topology, named human identities/recipients, recovery targets, exact state controls, and first provisioning inputs still require review-facing evidence; EU primary, active-secondary, or default-backup placement is not proposed.
- ADR-0009 accepts one private same-origin staff-app Cloud Run service for the first shared tracer, an explicit one-shot migration job, Cloud SQL PostgreSQL 16, distinct runtime/migration/deploy identities and database roles, Terraform, digest promotion, Secret Manager, and value-safe observability. PR #22 implemented only the local package/runtime contract for that future target; Cloud Run IAM remains only an outer test-access perimeter while synthetic application authentication remains and is not staff business authorization.
- ADR-0013 requires one no-default staged workload root: `foundation` creates no executable Cloud Run workload, `migration` adds but does not execute the configured job, and `service` adds the staff service only after migration evidence. Terraform alone owns configuration. The deploy executor receives exact job execution/view authority only; direct-workflow `workflow_ref` separates publisher/deploy WIF trust; the provisioner has no GitHub WIF binding until a later accepted apply workflow exists.
- The first develop tester path is IAM-private but internet-reachable: `INGRESS_TRAFFIC_ALL` plus exact named service-level invokers and loopback proxy/token testing. Production staff identity remains separate. Publication requires keyless digest-bound Cosign/SLSA/image-SBOM/application-SBOM evidence, and availability requires an authenticated Cloud Monitoring `/readiness` check with exact monitoring-service-agent invocation.
- The accepted Terraform/IaC posture includes the 14-decision private synthetic-only develop baseline: Terraform-managed API enablement with disable safeguards; bootstrap-to-WIF Terraform provisioner identity; separate runtime/migration identities and PostgreSQL roles; private regional Artifact Registry with digest deploys and cleanup; Terraform-managed $50/$75/$100 budget alerts; Secret Manager metadata/IAM only; private Cloud SQL PostgreSQL 16 `db-f1-micro`/10 GiB SSD/no public IP; dedicated VPC/private service access; private Cloud Run invoker IAM only for approved principals; protected GitHub WIF apply/deploy gates; value-safe Logging/Monitoring; standard labels/tags; intentional teardown runbook support; and a durable remote-state control plane separate from disposable workload teardown. PR #29 completed the six static remediation tasks but did not implement the remaining authority chain. Accepted ADR-0012 places bootstrap/state/WIF, IAM, migration/database authority, budgets/observability, immutable workflows, recovery/teardown, and evidence in one later pre-deployment implementation PR. Terraform plan/apply, backend migration, cloud-authenticated operations, and deployment remain future separately approved gates. Secret payloads, PostgreSQL passwords, project IDs, billing accounts, user emails, domains, and client/live data must not be embedded in tracked Terraform source.
- GitHub-based CI/CD and repository governance as code; exact provider/account configuration remains unapproved.

See `TECHNOLOGY_DECISIONS.md` for rationale and `docs/adr/` for durable decisions.

## Data boundaries
- Minimize personal, household, location, document, and free-text data.
- Keep exact worksite/household address internal by default; use least-precise location outside approved workflows.
- Store documents outside database rows with private, controlled access only after document-ingestion qualification.
- Keep secrets out of Git, logs, client builds, and ordinary operational records.
- Use wholly fictional synthetic data in development until a separately approved test-data procedure exists; de-identified, transformed, hashed, or otherwise client/live-derived values are not allowed by default.

## Environment and promotion model
```text
feat/*    → PR/CI → develop (isolated non-production; wholly fictional synthetic data under ADR-0009)
develop   → PR/release evidence → main (immutable production candidate)
main artifact → protected explicit production promotion
```

`develop` and production require isolated projects/accounts/resources, identity clients, secrets, databases, buckets, and budgets. Production is a deliberate promotion of the qualified immutable artifact, not an automatic side effect of a merge.

The first implementation slice is narrower than this eventual environment model. ADR-0002 permits one local/test-only staff route, synthetic configuration-supplied principal, security-internal transactional `CommandReceipt`, draft `Employer` insert, and atomic creation `AuditEvent`; it creates no deployment, public plane, real identity, or live-data path.

ADR-0004 controls the implemented second bounded local/test slice: one `employer:read` permission, exact current-Employer detail, and privacy-conscious POST search over accepted Employer fields. Search remains a bounded query over authoritative PostgreSQL rows—not a second store or durable projection—and ordinary reads append no domain audit event. Filter-required literal matching, deterministic keyset pagination, minimized responses, no-store caching, and authorization before lookup/result derivation define the boundary.

ADR-0005 accepts the first standalone staff browser application boundary under `apps/web/`. Before browser consumption it adds `Cache-Control: no-store` to fresh and replayed create successes without changing status, body, authority, idempotency, persistence, route, or schema. It then consumes the Employer create/search/detail contracts through relative staff API paths, keeps Employer/search/command state in memory rather than URLs or browser persistence, and requires English/Spanish parity plus accessibility and frontend quality/security evidence. PR #13 merged that bounded implementation to `develop`.

ADR-0006 controlled the closeout merged by PR #15. ADR-0007 controlled draft-Employer revision merged by PR #17 and remediated by PR #18. ADR-0008's implementation merged through PR #20 at `6eb05d5`. PR #22 merged ADR-0009 Slice B's local runtime/container implementation at `f3cac4d`; PR #24 merged the local validate-without-apply Terraform scaffold at `50451b3`; PR #29 merged the six static remediation tasks at `08fe305`; PR #30 merged accepted ADR-0012's consolidated pre-deployment implementation authority at `f9b7903`; PR #37 merged the ADR-0013 no-cloud remediation at `caf96a7`; and PR #42 merged its bounded verifier reconciliation at `b2d79b5`. The completed source contracts preserve the High/open same-repository-CI residual risk and do not authorize cloud inspection, Terraform plan/apply, backend migration, provisioning, image push, secret injection, deployment, service start, live data, or production.

## Interim infrastructure billing and handoff
- **Accepted contractual constraint:** Beatrice is responsible for paying approved cloud-infrastructure charges until the final payment for the engagement has been rendered. Billing responsibility then transfers to the client through a documented handoff.
- The current starting account shape is reported as one Beatrice-owned GCP organization with two projects, including one project dedicated exclusively to cloud deployment/testing. Exact billing topology, project identifiers, domain/DNS, remote state, support, and transfer details remain controlled operational inputs; they must support least-privilege access, cost visibility, continuity, and an orderly transfer without exposing secrets or interrupting the staff workflow.
- The handoff record must identify the billing owner, account/project ownership, budget-alert recipients, support/incident contacts, recovery access, and effective transfer date. It does not itself authorize production provisioning, production-data use, or feature expansion.

## Deferred architecture decisions
Identity provider; billing/state/domain/support topology; named cloud/support roles and alert recipients; develop recovery targets and log-retention details; production topology; document/malware-scanning services; background workers; messaging/signature/payment/screening integrations; production RTO/RPO; WAF/CDN/network design; and exact dashboard/reporting technology.
