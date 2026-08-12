# Phase 1 Canonical Field-Purpose Inventory

**Status:** Accepted planning source of truth for the staff employer-demand structural baseline
**Accepted:** 2026-08-03
**Decision owner:** Beatrice, technical delivery owner; client validation may refine operational terminology, staged requiredness, and permitted visibility before implementation

## Decision

Phase 1 uses one canonical employer-demand structure:

```text
Employer
  ├─ EmployerContact
  ├─ Worksite
  └─ StaffingRequest
       ├─ ShiftNeed
       └─ RequestRequirement

Worksite ── WorksiteZoneMembership ── ServiceZone
Worksite ── WorksiteMapAreaAssignment ── MapArea (NYC CDTA)
ServiceZone ── ServiceZoneComposition ── MapArea (NYC CDTA)
All material records/transitions ── AuditEvent
```

`Employer` is the neutral hiring-party record. It replaces `EmployerOrganization` because Golden Rose serves household and business employers. An approved employer type distinguishes those contexts without creating separate forms, tables, or response stores.

This document controls the purpose and boundary of Phase 1 fields. It is not a final database migration, legal form, public intake specification, retention schedule, or permission matrix. Exact schema types, state-dependent requiredness, and client terminology must be derived from this inventory and separately approved contracts—not invented during implementation. Role and field permissions are accepted in `docs/planning/phase-1-staff-permission-matrix.md`.

## Inventory rules

Every implemented field must have:

- one stated operational purpose;
- an evidence/approval classification;
- a data classification;
- an authoritative source or attributable staff entry;
- a defined creation and correction path;
- explicit search, export, and external-visibility rules;
- a retention disposition before production data is admitted; and
- a prohibited-use statement when the field could enable discrimination, proxy filtering, unnecessary surveillance, or overexposure.

Additional rules:

1. Requiredness is staged by the approved request state. A field need not be mandatory at first contact merely because it is required before agency review or referral.
2. Exact worksite address and broad service zone are separate facts. A zone never silently replaces, derives, or exposes an exact address.
3. Employer-supplied assertions are unverified until an attributable agency review says otherwise.
4. Unstructured source wording is restricted, staff-only evidence. It must not become a default search filter, comparison signal, public statement, or worker-facing fact.
5. Material corrections append attributable events; they do not erase prior reviewed or issued meaning.
6. System identifiers and timestamps are system-managed. Users must not enter or change them directly.
7. No field in this inventory authorizes automated matching, ranking, eligibility, hiring, or referral decisions.

## Canonical field-purpose inventory

### Employer

**Purpose:** Represent the hiring party responsible for one or more staffing requests.

| Field / group | Purpose | Data classification | Phase 1 boundary |
|---|---|---|---|
| `employer_id` | Stable internal identity and relationship key | Internal operational | System-generated; never reused as an external identity assertion |
| `employer_type` | Distinguish approved household and business workflow extensions | Internal operational | Controlled values; does not create separate stores or imply legal classification |
| `display_name` | Give staff a recognizable operational label | Sensitive operational when it identifies a person/household | Staff-facing; must not expose a household publicly by default |
| `legal_name` | Preserve an approved legal/contracting name when required | Sensitive operational | Optional until an approved business/legal step requires it |
| `lifecycle_status` | Distinguish active, inactive, duplicate, or otherwise approved account states | Internal operational | Exact values and transitions belong to the account/workflow-state decision |
| `source_channel` and `received_at` | Record how and when the employer first entered the staff workflow | Internal operational | Controlled channel values; not proof of identity or consent |
| `created_at`, `created_by` | Attribute record creation | Audit metadata | System-managed and immutable |

**Prohibited uses:** Do not use employer type, name, neighborhood, household context, or source channel as an automatic worker-ranking or eligibility signal.

### EmployerContact

**Purpose:** Maintain a staff-entered candidate contact identity associated with an Employer for a later authorized communication workflow.

| Field / group | Purpose | Data classification | Phase 1 boundary |
|---|---|---|---|
| `employer_contact_id`, `employer_id` | Maintain stable contact identity and employer relationship | Internal operational | System-generated relationship; a contact may not silently move between employers |
| `full_name` | Record the name staff associates with the candidate contact identity | Contact PII | Staff-only unless a separately approved disclosure requires it; the name alone does not establish authority, identity verification, contactability, communication history, or consent |
| `role_or_relationship` | Explain the contact's authority or relationship to the employer | Sensitive operational | Controlled/short text; not a protected-trait field |
| `phone` | Permit approved operational follow-up | Contact PII | Format-validated; collection is not marketing consent |
| `email` | Permit approved operational follow-up | Contact PII | Format-validated; collection is not marketing consent |
| `preferred_language` | Support English/Spanish communication choice | Sensitive preference | Explicit, changeable choice; never inferred from name or location |
| `preferred_contact_method` | Help staff use an approved communication path | Sensitive preference | Operational preference only; vendor messaging remains separately gated |
| `contact_status` | Record whether the contact is current, superseded, or otherwise approved | Internal operational | Exact states require account-lifecycle approval |
| `created_at`, `created_by` | Attribute record creation | Audit metadata | System-managed and immutable |

**Prohibited uses:** Do not infer ethnicity, nationality, immigration status, religion, or other protected/proxy traits from names, language, phone, email, or relationship.

**Authority boundary:** An EmployerContact record and `full_name` are attributable staff-entered operational data, not proof that the person is authorized to act for the Employer, has been identity-verified, is currently contactable, has consented to a communication channel, or has participated in any communication. Those claims require separately approved fields/workflows and evidence.

### Worksite

**Purpose:** Represent where requested work is expected to occur while separating precise location from routine operational geography.

| Field / group | Purpose | Data classification | Phase 1 boundary |
|---|---|---|---|
| `worksite_id`, `employer_id` | Maintain stable worksite identity and employer relationship | Internal operational | System-generated; a request references a specific approved worksite |
| `internal_label` | Let staff distinguish multiple worksites safely | Sensitive operational | Staff-only; avoid unnecessary household-identifying labels |
| `address_line_1`, `address_line_2`, `locality`, `region`, `postal_code`, `country` | Preserve an exact worksite when operationally required | Restricted precise location | Need-to-know access; excluded from routine dashboards, maps, and broad exports |
| `service_area_status` | Show whether zone classification is assigned, unassigned, under review, or outside the approved service area | Internal operational | Workflow condition governed by `docs/planning/phase-1-service-zone-taxonomy.md`; exception values are not fake zones and do not make automatic acceptance decisions |
| `map_area_status` | Show whether pinned NYC CDTA derivation is assigned, pending, under review, outside NYC, or failed | Internal operational/location reference | Governed by `docs/planning/phase-1-nyc-job-demand-map-contract.md`; does not expose or retain a precise point by default |
| `location_verification_status` | Distinguish supplied address from approved agency review state | Internal operational | Geocoding match is not proof that an address, employer, or worksite has been independently verified |
| `restricted_access_or_safety_notes` | Preserve minimum necessary staff information for safe fulfillment | Highly sensitive free text | Deferred until purpose, allowed content, visibility, retention, and moderation are approved |
| `created_at`, `created_by` | Attribute record creation | Audit metadata | System-managed and immutable |

**Prohibited uses:** No public/worker address exposure by default; no individual-level map pins, live location, or automatic proximity ranking.

### MapAreaDatasetVersion and MapArea

**Purpose:** Preserve a pinned, checksummed NYC Department of City Planning CDTA release and its official map cells for deterministic aggregation.

| Field / group | Purpose | Data classification | Phase 1 boundary |
|---|---|---|---|
| dataset identity, publisher, source URL, release/version, retrieval time, checksum, importer/schema version | Make public boundary provenance reproducible | Public-source provenance/internal configuration | Initial geography is the official 2020 CDTA dataset; no silent “latest” updates |
| `map_area_id`, publisher CDTA identifier, publisher label, borough reference, normalized geometry | Represent one official fixed aggregation cell | Public geographic reference | Geometry is public CDTA boundary data, not a worksite/worker point |
| activation/retirement and approval metadata | Control which pinned release drives current derivation/rendering | Internal governance/audit | Historical assignments retain their dataset version |

### WorksiteMapAreaAssignment

**Purpose:** Preserve the worksite's derived or Owner-corrected CDTA without retaining an exact point by default.

| Field / group | Purpose | Data classification | Phase 1 boundary |
|---|---|---|---|
| `worksite_map_area_assignment_id`, `worksite_id`, `map_area_id`, dataset-version reference | Maintain attributable CDTA classification | Sensitive operational/location reference | One current assignment per worksite; history retained |
| assignment method, provider/interface version, match quality/status | Explain derived versus Owner-corrected classification | Sensitive operational/vendor metadata | Provider-neutral; no employer/contact/request/worker content in geocoding payload |
| derived/confirmed/corrected actor and time, prior assignment, correction reason | Preserve correction history | Audit metadata | Expected-version command; exact coordinates discarded by default |

**Prohibited uses:** CDTA assignment is not exact-address verification, service-zone assignment, legal-jurisdiction proof, worker matching, or commute evidence.

### WorksiteZoneMembership

**Purpose:** Preserve Owner-managed overlapping operational-zone memberships for a worksite while identifying one primary/default membership.

| Field / group | Purpose | Data classification | Phase 1 boundary |
|---|---|---|---|
| `worksite_zone_membership_id`, `worksite_id`, `service_zone_id`, `service_zone_version_id` | Maintain stable, versioned worksite-to-zone classification | Internal operational/location reference | Multiple active memberships allowed; no polygon, coordinate, geocoding, or proximity inference |
| `is_primary` | Identify the default proposed zone for new requests | Internal operational | Exactly one active membership is primary whenever active memberships exist |
| `effective_from`, `effective_to` | Preserve when the membership applies | Internal operational/audit | Effective-dated; prior classification is not overwritten |
| `assigned_by`, `assigned_at`, `source_reason` | Attribute the classification decision | Sensitive operational/audit | Owner or explicitly delegated staff entry; minimum-necessary reason |

**Prohibited uses:** Membership does not prove address, legal jurisdiction, service eligibility, commute feasibility, worker suitability, or acceptance of a request.

### StaffingRequest

**Purpose:** Represent an employer's agency-reviewed request for staffing without treating the request as automatically publishable, referable, or fulfilled.

| Field / group | Purpose | Data classification | Phase 1 boundary |
|---|---|---|---|
| `staffing_request_id`, `employer_id` | Maintain stable request identity and accountable employer | Internal operational | System-generated |
| `primary_contact_id`, `worksite_id` | Identify the contact and worksite governing this request | Contact/location relationship | Authorization-scoped references |
| `request_type` | Select approved household or general-labor workflow extensions | Internal operational | Controlled values; no duplicate canonical workflow |
| `role_title` | Give staff a concise job/request label | Operational content | Agency-reviewed before external use |
| `duties_summary` | Describe the work needed | Sensitive operational free text | Staff review required; not automatically worker-facing or searchable |
| `request_status` | Represent the approved request lifecycle | Internal operational | Controlled by `docs/planning/phase-1-request-shift-state-model.md`; state is changed only through guarded, attributable transitions |
| `received_at`, `source_channel` | Preserve intake timing and origin | Internal operational | Controlled source values; not proof of verification |
| `requested_start_date` | Record the employer's anticipated start and support the date-only request calendar milestone | Sensitive operational | An expectation, not a timed shift, confirmation, coverage assertion, or placement |
| `employment_arrangement` | Record approved temporary/permanent and part/full-time terms | Operational content | Controlled values require client terminology validation |
| `compensation_min`, `compensation_max`, `compensation_basis`, `currency` | Represent supplied compensation in structured form | Sensitive operational/financial | Agency review required; no legal/pay compliance claim without approved rules |
| `assigned_staff_user_id` | Identify staff accountable for the next request action | Internal operational | Shared-queue accountability under the accepted work-queue model; unassigned intake remains visible and ownership is not exclusive access |
| `follow_up_owner_staff_user_id`, `next_follow_up_at` | Assign and schedule the next employer-clarification action | Sensitive operational | Required in `needs_information`; governed by the accepted work-queue model and never triggers automatic contact/closure |
| `operational_service_zone_id`, `operational_service_zone_version_id` | Preserve the one confirmed zone used for this request's queue/calendar/reporting attribution | Internal operational/location reference | Optional during intake and active work; later Owner assignment is supported; secondary memberships do not duplicate counts |
| `service_area_status` | Distinguish assigned-zone workflow from unassigned/review/outside-area conditions | Internal operational | Unassigned/review values do not block `open` but must remain visible and countable; outside-area policy is separate |
| `created_at`, `created_by` | Attribute record creation | Audit metadata | System-managed and immutable |

**Prohibited uses:** A request may not encode or operationalize protected-trait preferences, discriminatory exclusions, or unreviewed proxy criteria. Creation does not equal verification, publication, referral, placement, or approval.

### ShiftNeed

**Purpose:** Represent a dated or scheduled quantity of workers needed under a staffing request.

| Field / group | Purpose | Data classification | Phase 1 boundary |
|---|---|---|---|
| `shift_need_id`, `staffing_request_id` | Maintain stable shift identity and request relationship | Internal operational | System-generated |
| `starts_at`, `ends_at`, `time_zone` | Preserve the requested work interval unambiguously | Sensitive operational | Timed interval with IANA timezone; overnight is one occurrence, all-day shifts are excluded, and calendar views are derived |
| `worker_count` | State how many workers are requested | Internal operational | Positive bounded value; does not imply coverage |
| `schedule_pattern` | Preserve an approved recurring-pattern source description when needed | Sensitive operational | Human-readable evidence only in Phase 1; it never generates occurrences or executes recurrence |
| `shift_status` | Represent review, active coverage, and terminal outcome in one guarded lifecycle | Internal operational | Controlled by `docs/planning/phase-1-request-shift-state-model.md`; coverage reversals are permitted and attributable |
| `confirmed_worker_count` | Support the accepted uncovered/partial/covered state invariant without adding worker identity | Sensitive operational | Aggregate count only in Phase 1; every change requires an attributable source and audit event |
| `coverage_owner_staff_user_id` | Identify staff accountable for the next coverage action when different from the request owner | Internal operational | Shared-queue accountability only; does not create private visibility or worker assignment |
| `operational_service_zone_id`, `operational_service_zone_version_id` | Preserve the inherited operational zone for this occurrence | Internal operational/location reference | Inherits the request classification; terminal history is not silently reclassified |
| `service_area_status` | Preserve the inherited assigned-zone or outside-area disposition | Internal operational | Must remain consistent with the parent request at creation/correction; terminal history is preserved |
| `supersedes_shift_need_id` | Link a governed rescheduled replacement to the prior active shift | Internal operational/audit | Required for active-shift calendar rescheduling; old/new records and events remain attributable and coverage is not inherited |
| `completion_outcome` | Distinguish fully staffed from understaffed work that actually occurred | Sensitive operational | Required only for `completed`; not a worker disciplinary or legal conclusion |
| `created_at`, `created_by` | Attribute record creation | Audit metadata | System-managed and immutable |

**Prohibited uses:** A shift must not be shown as assigned, covered, confirmed, completed, or placed merely because it exists. No-show or coverage-loss evidence must not become an automatic worker discipline, eligibility, comparison, or ranking input.

### RequestRequirement

**Purpose:** Represent approved, job-relevant request conditions separately from unrestricted employer wording.

| Field / group | Purpose | Data classification | Phase 1 boundary |
|---|---|---|---|
| `request_requirement_id`, `staffing_request_id` | Maintain stable requirement identity and request relationship | Internal operational | System-generated |
| `requirement_type` | Identify an approved typed category such as duty, schedule, work condition, or transportation fact | Potentially sensitive operational | Allowlist only; categories require field-purpose and discrimination review |
| `structured_value` | Store an approved normalized value for staff review | Potentially sensitive operational | Not automatically a comparison/filter signal |
| `source_text` | Preserve minimum necessary original wording for agency moderation | Highly sensitive free text | Restricted staff-only evidence; never public or filterable by default |
| `review_status`, `reviewed_by`, `reviewed_at` | Record whether staff accepted, rejected, or requested correction | Audit/operational | Exact review states require workflow approval |

**Prohibited uses:** No protected traits or proxies as default requirements, filters, comparisons, ranking inputs, eligibility rules, or referral decisions.

### ServiceZone

**Purpose:** Provide a governed broad geographic reference for routine staff operations and aggregate reporting.

| Field / group | Purpose | Data classification | Phase 1 boundary |
|---|---|---|---|
| `service_zone_id`, `code` | Stable internal zone identity | Internal reference | System-managed; no semantic meaning embedded in IDs |
| `display_label` | Give the Owner a practical, evolvable zone name | Internal operational reference | Required owner-supplied label; treated as an operational proper name rather than a legal/geographic claim |
| optional descriptions, aliases, translations, and guidance | Add context only when observed use demonstrates a need | Internal operational reference | Optional during pilot and audit-versioned; no executable geographic rule |
| `lifecycle_status`, `active_from`, `active_to` | Preserve draft/active/retired lifecycle and version applicability | Internal reference | Existing records retain historical zone identity and definition version; referenced zones are retired/superseded, not deleted |
| `changed_by`, `changed_at`, `predecessor_or_successor_reference` | Attribute catalog changes and preserve split/merge/supersession relationships | Internal governance/audit | Owner-managed; delegated authority requires permission-matrix approval |

**Prohibited uses:** A zone is not a proxy for protected identity, socioeconomic classification, household targeting, or automatic worker suitability.

### ServiceZoneComposition

**Purpose:** Let the Owner render an adaptive service zone by selecting one or more fixed CDTAs.

| Field / group | Purpose | Data classification | Phase 1 boundary |
|---|---|---|---|
| `service_zone_composition_id`, zone/version reference, map-area/dataset-version reference | Link a zone definition to official CDTA cells | Internal operational/public geography reference | Overlap permitted; no freehand polygon or exact point |
| `effective_from`, `effective_to`, `changed_by`, `changed_at` | Preserve composition history | Audit metadata | Changes do not silently reclassify workflow records |

### AuditEvent

**Purpose:** Preserve attributable operational history for material creation, review, correction, cancellation, replacement, and state transitions.

`docs/planning/phase-1-correction-audit-event-contract.md` is authoritative for current-state/history separation, event requiredness, atomic insertion, draft behavior, correction-of-correction, protected changed-field evidence, retention gates, and derived-projection consistency. `AuditEvent` is not a full-row snapshot, ordinary log, or full event-sourcing/replay store.

| Field / group | Purpose | Data classification | Phase 1 boundary |
|---|---|---|---|
| `audit_event_id` | Stable event identity | Internal audit | System-generated and immutable |
| `entity_type`, `entity_id` | Identify the affected authoritative record | Internal audit | Controlled entity types |
| `event_type` | Identify the material action | Internal audit | Allowlisted; exact events follow the state model |
| `actor_type`, `actor_id` | Attribute the action to staff/system/approved source | Sensitive audit | System-derived; no shared staff identity |
| `occurred_at` | Preserve authoritative action time | Internal audit | System-generated timezone-aware timestamp |
| event schema/version, entity sequence, prior/new record version | Preserve deterministic event interpretation and ordering | Internal audit | System-managed, immutable, and uniqueness constrained |
| command/idempotency ID, correlation ID | Make retries and atomic multi-record actions attributable | Internal audit | Identical retry returns prior result; conflicting reuse is rejected |
| `effective_at` | Preserve optional business-effective time distinct from recording time | Internal audit | Never replaces or backdates server-generated `occurred_at` |
| `reason_code`, `reason_text` | Explain corrections/exceptions when required | Sensitive audit/free text | Minimum necessary; reason text is restricted and not routine-search content |
| `source_reference` | Preserve an approved evidence or workflow reference | Sensitive audit | Must not contain secrets or unsafe arbitrary file paths |
| `related_event_id` | Link correction, cancellation, replacement, or supersession to prior meaning | Internal audit | Append-only relationship; no destructive rewrite |
| structured changed-field set and payload classification | Preserve minimum necessary prior/new meaning | Classification follows source fields | No unrestricted row snapshots; exact address/contact/restricted text uses a separately protected payload only when necessary |

## Explicitly excluded from this Phase 1 inventory

- Worker identity, profile, availability, skills, preferences, documents, and verification.
- Referral, assignment, placement, fee, payment, receipt, agreement, signature, refund, and register fields.
- Authentication secrets, passwords, identity-provider tokens, cloud identifiers, and infrastructure credentials.
- Public publication fields, mapping coordinates, live location, automated comparison scores, ranking features, and AI-generated decisions.
- Unbounded generic metadata/custom-field bags that could bypass field-purpose review.

These concerns require their own approved inventories before implementation.

## Implementation constraints

- Database/API/UI names may refine these labels only if the purpose and boundary remain traceable to this document.
- Migrations and fixtures must use wholly fictional synthetic data by default; de-identified, transformed, hashed, or otherwise client/live-derived values require a separately approved test-data procedure and cannot enter merely because a production-data gate is pending.
- Tests must prove separation of exact address from service zone, restriction of sensitive free text/history, atomic attributable corrections, append-only audit behavior, and rejection of prohibited automatic-decision uses.
- The accepted request/shift state model, `docs/planning/phase-1-staff-permission-matrix.md`, and `docs/planning/phase-1-correction-audit-event-contract.md` bind requiredness, access, correction, and history before the first functional implementation plan is accepted.

## Revisit triggers

Revisit this inventory when client workflow validation changes the meaning of an employer, contact, worksite, request, shift, requirement, or zone; before public/employer entry, worker data, referrals, documents, payments, exports, mapping/geocoding, or legacy migration; or when a proposed field lacks a documented purpose and owner.
