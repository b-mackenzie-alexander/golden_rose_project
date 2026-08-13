# Phase 1 Staff Permission Matrix

**Status:** Client-accepted Phase 1 planning source of truth
**Technical acceptance:** 2026-08-03
**Client acceptance confirmed:** 2026-08-04
**Decision owners:** Golden Rose client for the operational role model; Beatrice for technical delivery and security boundaries. Named actors, delegated capabilities, and operational access-review owners are discovered and recorded before live use.
**Scope:** Agency-staff employer-demand workflow and bounded technical support; no public-plane, worker, document, export, or production-infrastructure authorization

## Decision

Phase 1 staff authorization is permission-based, server-enforced, attributable, and evaluated before records, fields, search results, counts, calendar/map projections, filters, drill-downs, or commands are returned or performed. A role is a bundle of named permissions; it is not a generic administrative bypass.

The accepted staff-plane roles are:

- **Owner:** ultimate agency-business authority. The Owner governs operational roles, high-impact operational configuration, and business-wide reporting, but is not a routine infrastructure superuser.
- **Delegated Manager:** a business-operations role explicitly delegated and revocably bounded by the Owner.
- **Operations Staff:** interchangeable day-to-day agency workflow coverage. Accountable queue ownership never creates private record visibility.
- **Platform Administrator:** a distinct technical-support role using a separate privileged identity and access path. It has no standing business-record, document, raw-database, secret, or business-role access.

The client accepts these role and separation boundaries. Implementation and pilot preparation may discover staff-facing labels, named assignees, delegation details, support contacts, and access-review ownership under `docs/planning/phase-1-operational-discovery-register.md`; those operational details may not weaken the accepted server-side permissions or separation of duties.

The matrix governs the approved Phase 1 canonical records and derived staff surfaces under `docs/planning/phase-1-canonical-field-purpose-inventory.md`, `docs/planning/phase-1-request-shift-state-model.md`, `docs/planning/phase-1-calendar-coverage-semantics.md`, `docs/planning/phase-1-service-zone-taxonomy.md`, `docs/planning/phase-1-nyc-job-demand-map-contract.md`, and `docs/planning/phase-1-correction-audit-event-contract.md`.

## Permission legend

| Symbol | Meaning |
|---|---|
| **Allow** | Included in the role's Phase 1 baseline. |
| **Delegable** | The Owner may grant the named capability to a Manager through an attributable, revocable delegation. It is not automatically present on every Manager account. |
| **Restricted** | Requires the distinct named permission, purpose-limited workflow, and applicable field/record authorization; it is not implied by access to a related view. |
| **Deny** | Not authorized in Phase 1. |
| **Break-glass only** | Exceptional support access under the procedure in this contract; never standing access. |

## Record, workflow, and field permissions

| Capability | Owner | Delegated Manager | Operations Staff | Platform Administrator | Phase 1 boundary |
|---|---|---|---|---|---|
| View and search authorized employer-demand records | Allow | Allow | Allow | Deny | Applies to `Employer`, `EmployerContact`, `Worksite`, `StaffingRequest`, `ShiftNeed`, approved `RequestRequirement`, and attributable audit history. Search remains field-authorized. |
| Create and correct draft employer, contact, worksite, request, and shift records | Allow | Allow | Allow | Deny | Material corrections append attributable evidence; system identifiers/timestamps remain system-managed. |
| Submit, review, and perform ordinary nonterminal request/shift transitions | Allow | Allow | Allow | Deny | Guards and expected-version checks in the state contract remain mandatory. |
| Correct schedules and invoke governed calendar rescheduling | Allow | Allow | Allow | Deny | Active-shift rescheduling uses the required atomic linked-replacement operation. |
| Record attributable aggregate coverage changes | Allow | Allow | Allow | Deny | Phase 1 aggregate counts only; no worker identity/assignment authority is granted. |
| Assign or reassign request, follow-up, and coverage accountability | Allow | Allow | Allow | Deny | This changes shared-work accountability, not record visibility or an automatic action. |
| Close or cancel ordinary records | Allow | Allow | Allow | Deny | Required controlled reasons and child-record invariants apply. |
| Exceptionally reopen terminal request/shift records | Allow | Delegable | Deny | Deny | Reopen only to `pending_review`, with the accepted reason, review, expected-version, and audit requirements. |
| View exact worksite address in authorized source-detail workflow | Restricted | Restricted | Restricted | Deny | Requires a dedicated precise-worksite permission. Routine queue, map, calendar, aggregate, and search access does not imply this permission. |
| Reveal an exact address in an authorized calendar day/week view | Restricted | Restricted | Restricted | Deny | Requires both calendar access and the dedicated precise-worksite reveal permission. Month, aggregate, map, export, screenshot, and external surfaces never inherit it. |
| View restricted source text, safety notes, and correction/no-show explanations | Restricted | Restricted | Restricted | Deny | Only minimum necessary content to perform the authorized workflow; never a default search/filter, map, calendar-summary, or export field. `restricted_access_or_safety_notes` remains deferred until its separate field-purpose gate is accepted. |
| View authorized business-wide operational reporting | Allow | Allow | Restricted | Deny | Operations Staff receives only approved scoped operational views. Map/calendar/queue aggregates require authorization before computation. |
| Create, rename, activate/retire service zones and change zone composition | Allow | Delegable | Deny | Deny | Zone identity/composition changes are attributable, effective-dated, and do not silently rewrite workflow history. |
| Assign/correct worksite CDTA and operational-zone classification | Allow | Delegable | Deny | Deny | CDTA correction, worksite membership, and request/shift operational attribution remain separate governed actions. No classification authorizes proximity or eligibility decisions. |
| Manage Operations Staff and Manager access | Allow | Delegable | Deny | Deny | A Manager may receive only a narrower named grant/revoke capability. No Manager may assign/remove an Owner or broaden their own permissions. |
| Manage Owner role or Platform Administrator entitlement | Allow | Deny | Deny | Deny | Requires attributable Owner action and the approved account-lifecycle process; it does not grant operational or cloud access. |
| Export records, reports, map data, or audit data | Deny | Deny | Deny | Deny | Phase 1 exports are disabled pending a separate disclosure, retention, audit, and data-classification contract. |
| Access cloud consoles, raw databases, backups, application secrets, document contents, or raw logs | Deny | Deny | Deny | Deny | No business role receives standing infrastructure/data-store access. Platform Administrator also has no standing operational-content access. |
| Health monitoring, cache/job remediation, and approved platform troubleshooting | Deny | Deny | Deny | Allow | Separate technical identity/path; support operations must be narrowly designed and attributable. |
| Exceptional production operational-record access for technical support | Approve/review only | Approve/review only when delegated | Deny | Break-glass only | The Platform Administrator does not self-authorize. Access is time-bounded, scoped, logged, and post-reviewed. |

### Accepted ADR-0008 planning permission mapping

The accepted capability rows above authorize Owner, Delegated Manager, and Operations Staff to view and create bounded draft contact records while denying ordinary Platform Administrator access. Accepted planning ADR-0008 maps only that capability into these future server-enforced names:

| Candidate permission | Owner | Delegated Manager | Operations Staff | Platform Administrator | Additional gate |
|---|---|---|---|---|---|
| `employer_contact:draft:create` | Allow | Allow | Allow | Deny | Also requires `employer:read`; parent must exist and remain `draft`. |
| `employer_contact:read` | Allow | Allow | Allow | Deny | Also requires `employer:read`; bounded collection-query and exact reads remain parent-scoped, with no global/name search or count. |

This mapping now controls the active EmployerContact coding lane after PR #19 merged ADR-0008 into protected `develop` at `745f9e8` and the separately authorized implementation branch rebaselined from that exact tip. It still grants no contact correction, lifecycle, name/global search, unbounded list/count, export, communication, public-plane, or support bypass authority; only the bounded parent collection query is included for authoritative rediscovery.

## Delegation and account-lifecycle controls

1. The Owner is the only Phase 1 business authority that may grant, narrow, revoke, or review Manager and Operations Staff role permissions.
2. A Manager's elevated capability is an explicit delegation record naming the permission, scope, grantor, grantee, reason, start time, and revocation/expiry condition.
3. Delegation does not permit a Manager to create/modify an Owner, grant Platform Administrator access, grant themselves new elevated permissions, or bypass address, export, audit, state, or break-glass controls.
4. Operations Staff accounts receive the shared operational baseline only. Elevated operational powers are not inferred from queue ownership, seniority, or possession of a calendar/map view.
5. Account creation, MFA enrollment/recovery, suspension, deprovisioning, periodic access review, and support ownership are controlled by `docs/planning/phase-1-mfa-recovery-support-ownership.md`. Named personnel, provider qualification, and rehearsal evidence remain gates before live use.
6. Role/delegation changes, authentication-recovery actions, suspension/deprovisioning, and denied privileged actions must produce attributable security/audit evidence without placing credentials or unnecessary personal data in ordinary logs.
7. Audit-event envelopes and protected changed-field payloads are separately authorized. Ordinary record access does not reveal restricted historical values, and Platform Administrator has no standing operational-audit access.

## Exact-location and restricted-field controls

1. Exact worksite address is a restricted field, separate from broad service zone and CDTA classification.
2. The dedicated precise-worksite permission is evaluated server-side for record detail and calendar reveal. A client must not receive the field, a derived precise hint, or a reveal control before authorization succeeds.
3. Day/week calendar address reveal must be purpose-limited and attributable. It is unavailable in month/aggregate/map views and must not propagate into exports, notifications, screenshots generated by the system, or external feeds.
4. Exact address, contact data, restricted source text, unreviewed requirements, and audit reasons remain excluded from map summaries/tooltips, ordinary queue rows, aggregate reporting, and routine search facets unless a separately approved field rule says otherwise.
5. CDTA/service-zone authority does not reveal exact address and does not authorize geography-based ranking, matching, referral, eligibility, assignment, or travel inference.

## Platform-support and break-glass procedure

Platform support is deliberately separate from agency operations. A Platform Administrator ordinarily uses only the approved technical path for health monitoring, narrowly scoped cache/job remediation, and troubleshooting. It must not use raw-database queries, broad log access, secrets, backups, documents, or operational-record browsing as ordinary support tools.

Exceptional production access is permitted only when an approved support operation cannot resolve a documented incident without it:

1. Record the incident/support purpose, requested system or record scope, justification, requester, and requested duration.
2. Obtain Owner approval before access where feasible. If immediate containment is necessary, record the emergency basis and obtain prompt retrospective Owner review.
3. Activate a separate privileged identity with the minimum technical and data scope needed, an automatic expiration, and no standing business-role grant.
4. Log access grant, actions, affected scope, start/end time, outcome, and any data-handling exception in a protected attributable record. Do not log credentials or unnecessary operational content.
5. Revoke access at expiry or completion, confirm the support result, and require Owner review of the event and follow-up remediation.
6. Break-glass access cannot authorize a business decision, role change, export, broad data extraction, or workaround for a missing ordinary operational permission.

## Non-negotiable prohibitions

No role or permission in Phase 1 authorizes:

- automatic matching, ranking, eligibility, hiring, referral, assignment, or worker discipline;
- protected-trait/proxy filtering or geographic suitability/travel inference;
- public-plane access, token reuse, or self-promotion into staff authority;
- unrestricted exports, external feeds, screenshots generated by the system, or bulk sensitive-data disclosure;
- silent rewrite/deletion of audit history, lifecycle transitions, coverage evidence, zone history, or dataset-version meaning;
- access to production infrastructure/data stores outside the separate technical-support boundary; or
- use of an emergency path to bypass staff authorization, field sensitivity, or ordinary account governance.

## Implementation and verification boundary

Before implementation is accepted, the authorization design and tests must demonstrate:

- server-side denial before record, field, filter, count, aggregate, drill-down, or command execution;
- no UI-only enforcement or role-name-only authorization;
- shared queue visibility despite accountable ownership;
- Operations Staff denial of terminal reopening, zone/CDTA governance, role administration, export, and platform access;
- Manager elevation only through a bounded delegation record;
- exact-address denial by default and authorized source/day-week reveal without propagation to month/map/aggregate surfaces;
- Platform Administrator denial of operational records, documents, raw databases, backups, secrets, and business-role management during ordinary support;
- break-glass approval, scope, expiry, attribution, revocation, and review; and
- audit evidence for privileged commands, authorization denials where appropriate, and account/delegation lifecycle changes.

This contract does not authorize implementation, cloud provisioning, live data, production access, an identity/MFA vendor, production exports, worker records, worker assignment/availability, public workflows, document handling, or a live mapping/geocoding provider.

## Remaining operational validation before live use

The permission baseline is accepted. The client/Owner must still name and record:

- individual Owners, Managers, and any delegated elevated Manager capabilities;
- recipients of the dedicated precise-worksite/view-reveal permission;
- primary and backup Owner approvers for access review, recovery, deprovisioning, and emergency support under the accepted MFA/recovery/support contract;
- named incident/support contacts and the post-engagement client successor; and
- any later one-record disclosure/export workflow through its separate approved contract.

## Revisit triggers

Revisit this matrix before enabling exports, documents, worker data, assignments, referrals, public workflows, external notifications/calendar feeds, production support tooling, direct database support, live data, changes to exact-address use, or any new role/permission that affects access to sensitive fields or operational authority.
