# Technical Requirements — Golden Rose Operations Platform

**Status:** Phase 1 technical implementation baseline through protected source `develop@375038e`. Gate P is complete; Gate S has one validated bounded `synthetic-staff-id` version. Approved migration preflight removed an unused auto-mode default network after proving zero dependents. The first approved saved-plan attempt stopped before Terraform initialization because exact local provisioner token-mint authority was absent. The active source correction adds one validated operator-held named-human input, one exact provisioner service-account-level Token Creator member, and static guards against any second/project-wide/WIF/key path; no IAM mutation or Terraform plan/apply occurred. Runtime/migration database URLs and every database/migration, service, tester, qualification, real-identity, live-data, and production action remain separately gated. The same-repository-CI High remains accepted residual risk.

## Product outcome
Provide agency staff a reliable browser-based operations workspace that replaces fragmented paper/form/spreadsheet employer-demand handling, supports governed operational reporting, and later supports transparent staff review of worker-to-employer/job compatibility.

## Priority delivery scope
### First release: agency-staff employer demand
- Authorized staff can create, view, correct, and find employers, employer contacts, worksites, staffing requests, and one or more shift needs.
- The system provides an authorized demand work queue/search, rather than separate monthly files or manual row tracking. `docs/planning/phase-1-work-queue-aging-follow-up-model.md` controls separate record/review/follow-up/coverage clocks, shared accountable ownership, provisional triggers, and deterministic queue lanes. Client validation is required before provisional thresholds become production policy.
- The system provides an authorization-scoped calendar derived from distinct request milestones and timed shift occurrences under `docs/planning/phase-1-calendar-coverage-semantics.md`; it must not become a separate manual calendar store. Worker assignments/availability remain future authorities.
- The system records who performed material actions and preserves attributable history/corrections under `docs/planning/phase-1-correction-audit-event-contract.md`; current domain rows and append-only material history remain distinct authorities.
- The system supports household and general-labor request details as governed extensions of one canonical workflow.

### Follow-on release: dashboard and comparison aid
- Agency-only dashboard derives approved KPIs from authoritative workflow records; staff do not re-enter information solely to create metrics.
- Charts and aggregate service-area demand/coverage visualizations may be included only after KPI definition, calculation, audience, aggregation/redaction, refresh, export, and location-privacy rules are approved. The client-accepted Phase 1 authorized-staff job-demand map is not optional; optional follow-on mapping refers to worker-supply, comparison, or additional dashboard layers, all of which require separate contracts.
- Comparison aid exposes only approved, job-relevant, explainable signals and missing information for staff review.
- The aid must not rank people, make eligibility/hiring/referral decisions, or use unapproved protected-trait/proxy fields.

### Follow-on release: worker profile
- Worker records use staged, inclusive, bilingual onboarding and explicit agency review.
- Self-reported skills/preferences remain unverified unless a separately governed verification procedure establishes otherwise.
- Employer visibility and referral content are controlled and snapshot-capable.

## Functional requirements
- Web UI works on constrained office hardware and common modern browsers. Future worker/employer public workflows must be mobile-first, resilient to constrained networks, and measured against an approved responsiveness/performance budget before release.
- English/Spanish functional and accessibility parity across all affected flows, validation/errors, notices, notification paths, documents, and staff interfaces.
- Staff search honors record/field authorization before showing results.
- The implemented Employer read/search slice uses one server-enforced `employer:read` permission before exact lookup, filtered query, or pagination. Potentially household-identifying name fragments use a validated POST body rather than URL query parameters, remain excluded from logs, and are matched literally with bounded deterministic keyset pagination. It adds no unfiltered list, total count, export, ranking, read-side audit event, schema/index, or separate search store; ADR-0004 controls the exact contract.
- The accepted first-frontend boundary uses one `/employers` route and the existing Employer create/search/detail status/body/schema/authority contracts after one prerequisite test-first `Cache-Control: no-store` header is added to fresh and replayed create successes. Employer names/types, search values, cursors, command IDs, and problems stay out of browser navigation URLs, browser persistence, logs, analytics, and third-party runtime calls; the selected UUID appears only in the required detail API path. English/Spanish parity, accessibility, idempotent unknown-outcome retry, frontend quality/audit/SBOM gates, and synthetic/local-only use are mandatory; ADR-0005 controls the exact boundary and PR #13 merged the first implementation.
- ADR-0006 deferred human browser/manual accessibility/fluent-language qualification until a shared deployed `develop` target exists. ADR-0007's revision and PR #18 remediation remain implemented; PR #69 later merged the bounded delayed receipt-visibility race remediation. PR #20 merged ADR-0008's backend-only EmployerContact create/query/exact-read and typed authority generalization. PR #22 merged ADR-0009 Slice B's local runtime/container contract; later ADR-0013 source and operator work completed state establishment, ownership alignment, exact foundation apply, workload-free post-apply verification, and Gate P publication. Gate S created only the bounded `synthetic-staff-id` version. Database-URL versions, executable workload stages, real identity, live data, and production remain separate.
- Staff authorization uses the server-enforced permission matrix in `docs/planning/phase-1-staff-permission-matrix.md`. Accepted roles are Owner, delegated Manager, interchangeable Operations Staff, and separately bounded Platform Administrator; role labels do not grant broad data access by themselves.
- Dates/times are stored once with time zone where relevant; calendar/month views are derived, not separate storage silos.
- Routine operational/reporting location uses the adaptive Owner-managed taxonomy in `docs/planning/phase-1-service-zone-taxonomy.md`: worksites may have overlapping memberships with one primary/default, while requests/shifts may be assigned later and remain visibly unassigned until then. Exact names/conventions are configuration discovered through use, not implementation prerequisites. Exact worksite/household address remains separately restricted.
- Phase 1 includes the authorized-staff NYC demand map defined by `docs/planning/phase-1-nyc-job-demand-map-contract.md`. It pins official DCP 2020 CDTAs, derives worksite CDTA server-side through a provider-neutral geocoder boundary, discards precise coordinates by default, and shows named request/shift/coverage measures with a synchronized accessible table. Worker supply is deferred to its own authoritative contract.
- Core workflow supports correction, cancellation, and replacement as atomic attributable events under the accepted correction/audit contract. Referral/delivery history remains follow-on scope.
- Policy/legal/business-controlled copy is versioned, owned, and approved before production use. Public-source legal research supplies suggested candidate controls only; legal behavior becomes validated software only after counsel documentation is translated into approved versioned requirements and acceptance tests.

## Accepted Phase 1 domain model
```text
Employer → EmployerContact
         → Worksite → WorksiteZoneMembership → ServiceZone
                    → WorksiteMapAreaAssignment → MapArea
         → StaffingRequest → ShiftNeed
                           → RequestRequirement (approved typed values + restricted source text)
MapAreaDatasetVersion → MapArea
ServiceZone → ServiceZoneComposition → MapArea
Worker → WorkerProfile / governed preferences
WorkerAssignment → ReferralOrDeliveryEvent
All Phase 1 material actions → AuditEvent
```

The Phase 1 employer-demand structure and field purposes are accepted in `docs/planning/phase-1-canonical-field-purpose-inventory.md`. `Employer` is the neutral household/business hiring-party record; employer type controls approved extensions without separate stores. Worksite-to-zone and worksite-to-map-area relationships are explicit versioned association records, not a direct `Worksite.service_zone_id` shortcut. `MapAreaDatasetVersion`, `MapArea`, `ServiceZoneComposition`, and `WorksiteMapAreaAssignment` preserve pinned public-geography provenance and evolving client-managed zones. Workflow-state requiredness, retention, named role assignments, and client terminology remain tracked operational discoveries. Worker, assignment, referral, and delivery records remain follow-on proposals.

Request and shift lifecycle is controlled by `docs/planning/phase-1-request-shift-state-model.md`. Shift coverage is part of the active shift state and may reverse when coverage changes or a no-show occurs. Terminal shift outcomes are `completed`, `unfulfilled`, and `cancelled`; request `closed` never erases or replaces those outcomes. No state transition implies automated matching, referral, placement, payment, or worker discipline.

Queue indicators are derived from authoritative states, timestamps, ownership, follow-up events, versioned business-calendar configuration, and versioned review-trigger configuration. They do not form a separate editable queue status and never change lifecycle state, ownership, contact behavior, or outcomes automatically.

The calendar shows pending, active, terminal, and cancelled records with distinct request/shift semantics, timezone-aware intervals, and approved aggregate coverage. Phase 1 materializes every shift occurrence explicitly. Permission-gated day/week address reveal is separate from broad-zone defaults. Audited drag-and-drop invokes authoritative correction/replacement commands; active shifts are replaced atomically and do not carry coverage to a new interval.

Zone classification is optional during intake and active work. Unassigned, review-required, outside-area, and map-area derivation exceptions remain visible rather than disappearing from map/list totals. Owner-led late assignment and reclassification preserve versions/history and never alter lifecycle/coverage or perform eligibility, matching, or proximity decisions.

## Non-functional requirements
- Separate staff and public security planes; public traffic must not have staff credentials, endpoints, tokens, or data access.
- Server-enforced authorization and the accepted individual-account, MFA, recovery, session, access-review, and support controls in `docs/planning/phase-1-mfa-recovery-support-ownership.md`; append-only application events and atomic correction semantics in `docs/planning/phase-1-correction-audit-event-contract.md`; encryption in transit/at rest, secret management, isolated environments, backups, and recovery qualification remain required before real data.
- Migration-managed schema evolution: expand → backfill/map → switch reads/writes → retire. Do not rewrite authoritative/audited history to fit a new schema.
- Accessible, responsive, and understandable error/recovery states.
- Observability without logging secrets or unnecessary personal data.
- Primary hosting-region selection must prioritize the East-US/NYC-area user population and exact service availability. The accepted `develop` location is `us-east4` / Northern Virginia for Cloud Run, Cloud SQL, and Artifact Registry. Central/western US comparisons may inform production cost/recovery choices; EU primary, active-secondary, or default-backup data placement requires a separately approved need.
- CI validation for tests, lint/type checks, migrations, secret/dependency/SAST scanning, and relevant configuration/IaC checks.
- The proposed first cloud target requires a cheap database-independent liveness endpoint, bounded database/schema readiness, and a separate synthetic qualification workflow; health probes must not mutate domain state.
- The proposed runtime database role must be non-owner and unable to perform routine DDL, `TRUNCATE`, trigger management, or append-only authority update/delete; migrations use a separate serialized identity and role.
- Terraform/IaC remains reviewable before each cloud execution. PR #74 is merged at `develop@92b104e`; successful run `33882394981` completed the full Gate P immutable publication and repository-admission chain. Gate P is complete. State/handoff evidence and every later Terraform plan/apply or cloud-authenticated mutation remain separately gated; secrets and environment identifiers remain outside tracked source.
- ADR-0013 requires a no-default `deployment_stage` (`foundation`, `migration`, `service`), Terraform-only resource/configuration mutation, exact-job migration execution without overrides, exact direct-workflow WIF separation, and independently verified keyless Cosign signature plus SLSA v1/image-SBOM/checksum-bound application-SBOM attestations on the exact digest.
- The fictional-synthetic develop service may be IAM-private and internet-reachable for named technical testers, but this is not production staff authentication. An authenticated Cloud Monitoring service-agent check of `/readiness` must supply no business payload and must alert on repeated failures using provisional develop triggers rather than an SLA.

## Out of scope without separate approval
- Public portals, public job posting, public or individual-level precise mapping, AI ranking/screening, and automatic decisions. The accepted aggregate authorized-staff Phase 1 demand map remains in scope.
- Live data migration/import, résumé upload, e-signature, payment, messaging, calendar, screening, and identity-verification integrations.
- Hardcoded legal requirements, legal copy, fees, retention periods, or commercial policy.

## Acceptance gates per release
Each increment must name: users/access boundary; feature scope/non-scope; data classification; acceptance owner; support/incident path; monitoring/audit signals; rollback/forward-recovery plan; training/documentation impact; and client/counsel dependencies.
