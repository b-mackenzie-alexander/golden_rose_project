# Technical Requirements — Golden Rose Operations Platform

**Status:** Proposed planning baseline. Requirements become build commitments only after the listed approval gates are satisfied.

## Product outcome
Provide agency staff a reliable browser-based operations workspace that replaces fragmented paper/form/spreadsheet employer-demand handling, supports governed operational reporting, and later supports transparent staff review of worker-to-employer/job compatibility.

## Priority delivery scope
### First release: agency-staff employer demand
- Authorized staff can create, view, correct, and find employer organizations, employer contacts, worksites, staffing requests, and one or more shift needs.
- The system provides an authorized operational work queue/search, rather than separate monthly files or manual row tracking.
- The system records who performed material actions and preserves attributable history/corrections.
- The system supports household and general-labor request details as governed extensions of one canonical workflow.

### Follow-on release: dashboard and comparison aid
- Agency-only dashboard derives approved KPIs from authoritative workflow records; staff do not re-enter information solely to create metrics.
- Charts may include pie/bar visualizations only after KPI definition, calculation, audience, aggregation/redaction, refresh, and export rules are approved.
- Comparison aid exposes only approved, job-relevant, explainable signals and missing information for staff review.
- The aid must not rank people, make eligibility/hiring/referral decisions, or use unapproved protected-trait/proxy fields.

### Follow-on release: worker profile
- Worker records use staged, inclusive, bilingual onboarding and explicit agency review.
- Self-reported skills/preferences remain unverified unless a separately governed verification procedure establishes otherwise.
- Employer visibility and referral content are controlled and snapshot-capable.

## Functional requirements
- Web UI works on constrained office hardware and common modern browsers.
- English/Spanish functional and accessibility parity across all affected flows, validation/errors, notices, notification paths, documents, and staff interfaces.
- Staff search honors record/field authorization before showing results.
- Dates/times are stored once with time zone where relevant; calendar/month views are derived, not separate storage silos.
- Core workflow supports correction, cancellation, replacement, and referral/delivery history as attributable events.
- Policy/legal/business-controlled copy is versioned, owned, and approved before production use.

## Proposed domain model
```text
EmployerOrganization → EmployerContact
                     → WorksiteLocation
StaffingRequest → ShiftNeed
                → RequestRequirement (approved typed values + source text)
Worker → WorkerProfile / governed preferences
WorkerAssignment → ReferralOrDeliveryEvent
All material transitions → AuditEvent
```

The model is a proposal. Field names, categories, requiredness, visibility, retention, and validation require a field-purpose review.

## Non-functional requirements
- Separate staff and public security planes; public traffic must not have staff credentials, endpoints, tokens, or data access.
- Server-enforced authorization, staff MFA, audit logging, encryption in transit/at rest, secret management, isolated environments, backups, and recovery qualification before real data.
- Migration-managed schema evolution: expand → backfill/map → switch reads/writes → retire. Do not rewrite authoritative/audited history to fit a new schema.
- Accessible, responsive, and understandable error/recovery states.
- Observability without logging secrets or unnecessary personal data.
- CI validation for tests, lint/type checks, migrations, secret/dependency/SAST scanning, and relevant configuration/IaC checks.

## Out of scope without separate approval
- Public portals, public job posting, precise mapping, AI ranking/screening, and automatic decisions.
- Live data migration/import, résumé upload, e-signature, payment, messaging, calendar, screening, and identity-verification integrations.
- Hardcoded legal requirements, legal copy, fees, retention periods, or commercial policy.

## Acceptance gates per release
Each increment must name: users/access boundary; feature scope/non-scope; data classification; acceptance owner; support/incident path; monitoring/audit signals; rollback/forward-recovery plan; training/documentation impact; and client/counsel dependencies.
