# Technical Requirements — Golden Rose Operations Platform

**Status:** Proposed planning baseline. Requirements become build commitments only after the listed approval gates are satisfied.

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
- Charts and aggregate service-area demand/coverage visualizations may be included only after KPI definition, calculation, audience, aggregation/redaction, refresh, export, and location-privacy rules are approved. A map is optional; broad-zone aggregation is the proposed default.
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
- Staff authorization uses the server-enforced permission matrix in `docs/planning/phase-1-staff-permission-matrix.md`. Accepted roles are Owner, delegated Manager, interchangeable Operations Staff, and separately bounded Platform Administrator; role labels do not grant broad data access by themselves.
- Dates/times are stored once with time zone where relevant; calendar/month views are derived, not separate storage silos.
- Routine operational/reporting location uses the adaptive Owner-managed taxonomy in `docs/planning/phase-1-service-zone-taxonomy.md`: worksites may have overlapping memberships with one primary/default, while requests/shifts may be assigned later and remain visibly unassigned until then. Exact names/conventions are configuration discovered through use, not implementation prerequisites. Exact worksite/household address remains separately restricted.
- Phase 1 includes the authorized-staff NYC demand map defined by `docs/planning/phase-1-nyc-job-demand-map-contract.md`. It pins official DCP 2020 CDTAs, derives worksite CDTA server-side through a provider-neutral geocoder boundary, discards precise coordinates by default, and shows named request/shift/coverage measures with a synchronized accessible table. Worker supply is deferred to its own authoritative contract.
- Core workflow supports correction, cancellation, and replacement as atomic attributable events under the accepted correction/audit contract. Referral/delivery history remains follow-on scope.
- Policy/legal/business-controlled copy is versioned, owned, and approved before production use.

## Proposed domain model
```text
Employer → EmployerContact
         → Worksite → ServiceZone
         → StaffingRequest → ShiftNeed
                           → RequestRequirement (approved typed values + restricted source text)
Worker → WorkerProfile / governed preferences
WorkerAssignment → ReferralOrDeliveryEvent
All Phase 1 material actions → AuditEvent
```

The Phase 1 employer-demand structure and field purposes are accepted in `docs/planning/phase-1-canonical-field-purpose-inventory.md`. `Employer` is the neutral household/business hiring-party record; employer type controls approved extensions without separate stores. Workflow-state requiredness, role/field permissions, retention, and client terminology remain separate approval contracts. Worker, assignment, referral, and delivery records remain follow-on proposals.

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
- Primary hosting-region selection must prioritize the East-US/NYC-area user population and exact service availability. Central/western US comparisons may inform cost/recovery choices; EU primary, active-secondary, or default-backup data placement requires a separately approved need.
- CI validation for tests, lint/type checks, migrations, secret/dependency/SAST scanning, and relevant configuration/IaC checks.

## Out of scope without separate approval
- Public portals, public job posting, precise mapping, AI ranking/screening, and automatic decisions.
- Live data migration/import, résumé upload, e-signature, payment, messaging, calendar, screening, and identity-verification integrations.
- Hardcoded legal requirements, legal copy, fees, retention periods, or commercial policy.

## Acceptance gates per release
Each increment must name: users/access boundary; feature scope/non-scope; data classification; acceptance owner; support/incident path; monitoring/audit signals; rollback/forward-recovery plan; training/documentation impact; and client/counsel dependencies.
