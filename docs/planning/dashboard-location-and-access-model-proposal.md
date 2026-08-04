# Dashboard, Location Analysis, and Staff Access Model — Proposal

**Status:** Historical discovery-to-delivery proposal, partially superseded by client-accepted Phase 1 map and staff-permission contracts.
**Recorded:** 2026-07-31
**Decision owners:** Golden Rose owner/client for operational policy and delegated roles; technical delivery owner for platform support boundaries; counsel/client approval for policy, privacy, and any employment-decision use.

## Why this proposal exists

The agency currently coordinates demand through fragmented workbooks, calendars, forms, messaging, and manual follow-up. Staff reportedly use Google Maps to investigate proximity between worker and hiring locations. The worker-preference evidence captures broad desired work zones and commute tolerance, and describes a potential measurement of areas with greater worker supply.

These are evidence of operational questions, not approval to collect precise locations, expose a map, select a mapping vendor, or automate placement decisions.

The proposal itself did not grant approval. Client acceptance was subsequently recorded for the aggregate authorized-staff Phase 1 demand map and the Owner/delegated Manager/Operations Staff/Platform Administrator role model in `docs/planning/phase-1-nyc-job-demand-map-contract.md` and `docs/planning/phase-1-staff-permission-matrix.md`. Precise-location use, live providers, named assignments, and worker mapping remain separately gated.

## Evidence and confidence

| Finding | Classification | Source / implication |
|---|---|---|
| Staff need one authorized operational place to enter, find, review, and follow up employer demand. | Proposed delivery requirement, supported by observed/reported fragmented workflows. | `CURRENT_WORK.md`; `docs/discovery/operational-discovery-2026-07-28.md` |
| The demand work queue is a mandatory staff-pilot capability because it directly supports request service time and accountability. | Proposed mandate; client validation of states/thresholds remains required. | Current planning decision; authoritative records must remain the source. |
| Staff use a calendar to understand when jobs are available and who covers them. | Reported operating practice. | Current discovery direction; validate owners, terms, and exception rules. |
| Calendar and coverage views must be derived from approved request, shift, assignment, and availability records rather than maintained as separate data stores. | Proposed architecture / delivery constraint. | `ARCHITECTURE.md`; `TECHNICAL_REQUIREMENTS.md` |
| Staff reportedly use Google Maps to investigate proximity between workers and hiring locations. | Reported observation. | `docs/discovery/operational-discovery-2026-07-28.md` |
| Broad zones and travel tolerance are candidate worker-preference inputs. | Observed legacy-form evidence; collection/use remains unapproved. | `docs/discovery/current-spanish-work-preferences-google-form-evidence.md` |
| Worker home addresses and precise household/worksite locations are sensitive and must not be broadly exposed. | Confirmed planning/security constraint. | `SECURITY.md`; `docs/discovery/current-job-description-evidence.md` |

## Mandated staff-pilot capabilities

### 1. Demand work queue

The staff workspace must provide an authorized queue over authoritative staffing requests and shift needs. It must support staff service work rather than merely display charts.

Minimum proposed behavior:
- show approved request/shift states, responsible or most-recent staff action, relevant date/time, and aging/follow-up indicators;
- filter/search only by approved, authorization-scoped operational fields;
- open a source record from a queue item;
- create attributable review, correction, cancellation, replacement, and follow-up events; and
- define empty, unavailable-data, and error states.

The accepted state model is defined in `docs/planning/phase-1-request-shift-state-model.md`; accepted queue timing, follow-up, ownership, provisional triggers, and deterministic lanes are defined in `docs/planning/phase-1-work-queue-aging-follow-up-model.md`. Remaining validation covers client business hours/thresholds/no-response policy, final role visibility, KPI approval, and retention/export rules.

### 2. Derived calendar and shift-coverage view

The staff dashboard must provide a calendar/coverage view derived from the same authoritative records used by the work queue. `docs/planning/phase-1-calendar-coverage-semantics.md` controls distinct request milestones, timed shift occurrences, state/coverage presentation, privacy, corrections, and governed rescheduling. It is not a parallel calendar or separate manual status store.

Minimum proposed behavior:
- view authorized staffing-request milestones and explicit shift occurrences by day/week/month and approved service area; worker assignment/availability remains deferred;
- navigate from a calendar item to its source record;
- show missing/incomplete scheduling data honestly rather than infer availability; and
- preserve actual dates/times and relevant timezone information once, then derive calendar views by query.

Active shift coverage uses the accepted uncovered/partial/covered state contract and explicit completed/unfulfilled/cancelled outcomes. The service-zone structure and command/field permission matrix are accepted. Remaining operational discovery covers future assignment authority, client-facing zone names, named exact-address recipients/delegations, and pilot terminology/usability.

## Proposed dashboard progression

1. **Phase 1 staff foundation:** demand work queue, request/shift search, detail and correction flows, derived calendar/shift-coverage view, and attributable operational history.
2. **Phase 2 descriptive dashboard:** role-scoped status, throughput, aging, follow-up, and approved service-area measures derived from authoritative records. Every KPI needs a named owner, definition, source records, refresh behavior, audience, aggregation/redaction, and export rule.
3. **Accepted Phase 1 location visualization:** authorized-staff NYC CDTA job-demand/coverage map with synchronized accessible table under `docs/planning/phase-1-nyc-job-demand-map-contract.md`. Worker supply remains a separately gated follow-on layer.

## Location model: accepted governed zones first, precise points exceptional

The product organizes operational location information under `docs/planning/phase-1-service-zone-taxonomy.md` and `docs/planning/phase-1-nyc-job-demand-map-contract.md`: a flat adaptive Owner-managed catalog composed from pinned official NYC CDTAs, optional late zone assignment, overlapping worksite memberships with one primary/default, and visible map/zone exceptions. Exact names may emerge through pilot use; exact points are not displayed or retained by default.

- Store any approved exact worksite/household address separately from its broad operational service zone.
- Use broad zones for routine dashboard, queue, calendar, and aggregate reporting behavior.
- Store worker work-zone preference and travel tolerance only if field purpose, audience, retention, and fairness controls are approved. Do not store or infer live worker location for ordinary operations.
- Do not display worker residences or household addresses on a dashboard, map, export, or public surface by default.
- Exact worksite disclosure remains a role-scoped, need-to-know workflow decision.
- Keep renderer/tile/geocoder providers replaceable. Do not enable live address transmission without separate vendor/privacy/security approval; synthetic testing uses deterministic fixtures.

The accepted job-demand visualization requires authorization, audit controls, accessible non-map parity, transparent metric definitions, export restrictions, and visible unassigned counts. Before the worker overlay, approve minimum group-size/suppression, worker-location purpose/precision, availability semantics, retention, and re-identification controls. Final zone labels may evolve without changing stable identities.

## Proposed staff-plane access model

Access must be permission-based and server-enforced. Role labels are a starting point, not a substitute for a permission matrix, field-level restrictions, auditability, MFA, account lifecycle, and recovery/deprovisioning controls.

| Proposed role | Intended operational purpose | Default boundary |
|---|---|---|
| Owner | Ultimate business authority for the agency: designate managers, approve high-impact operational configuration/policy actions that have been approved for platform use, and review authorized business-wide reporting. | Not an infrastructure-superuser account; no routine access to secrets, cloud consoles, backups, raw logs, or production databases. |
| Manager | Delegated higher-level agency operations when assigned by the Owner: manage staff operational access within approved policy and conduct higher-level request/reporting oversight. | No platform/infrastructure administration by default; cannot bypass audit or alter governed legal/business rules without the applicable approval path. |
| Operations Staff | Interchangeable day-to-day coverage role: create, review, correct, search, follow up, and manage employer-demand workflow records within approved scope. | Shared baseline operational permissions; no user/role administration, platform configuration, bulk sensitive export, or infrastructure access by default. |
| Platform Administrator | Technical support role for approved operational maintenance: health monitoring, cache/job remediation, incident/support procedures, and controlled configuration troubleshooting. | Separate admin identity and privileged-access path; no standing access to operational personal data, document contents, raw database records, or business-role management. Any exceptional access must be time-bounded, approved, logged, and reviewed. |

### Important separation: Owner is not Platform Administrator

The Owner/Manager hierarchy answers who may direct and govern agency business operations. Platform Administrator answers who may maintain the technical platform. Combining the two produces an avoidable data-access and audit risk.

The Platform Administrator should operate through separate staff/admin identities, least-privilege cloud roles, logged support actions, non-production-first troubleshooting where feasible, and a break-glass procedure for exceptional production access. “Clear caches” and “check infrastructure health” must be designed as safe, auditable operations rather than direct database or broad customer-data access.

## Non-negotiable boundaries

- No automated ranking, eligibility, hiring, or referral decision.
- Do not turn proximity, zones, commute tolerance, language, community labels, or other sensitive/proxy information into default filters or decision signals.
- Do not expose precise home/worksite addresses by default.
- No public mapping or individual-level map pins.
- English/Spanish functionality and accessibility must remain equivalent for every released staff surface.
- Do not collect/import live data, enable third-party mapping/geocoding, or provision infrastructure under this proposal.

## Continuing operational-discovery questions

1. Do the accepted request/shift state meanings match staff terminology, and which events should start, pause, resume, and stop service-time measurement?
2. What does “who is available” mean operationally, and what source record is authoritative for that fact?
3. Which accepted service-zone labels and conventions are understandable to staff and appropriate for reporting without revealing sensitive addresses?
4. Which dashboard questions are decision-critical, and what action should staff take from each answer?
5. Which named client actors receive the accepted permissions for business-wide reporting, staff-access management, and approved operational settings? Phase 1 exports remain denied.
6. What limited platform-administration tasks are needed, who performs them, and what emergency/break-glass access is acceptable?
7. What information must each role never see, change, export, or administer?

## Revisit triggers

Revisit this proposal before implementation of worker data, role assignment, dashboard KPIs, mapping/geocoding, exports, public workflows, or infrastructure support tooling; and whenever client workflow validation changes state, access, or privacy assumptions.
