# Phase 1 Service-Zone Taxonomy

**Status:** Accepted Phase 1 planning source of truth
**Accepted:** 2026-08-03
**Decision owner:** Beatrice, technical delivery owner
**Evidence posture:** The broad-zone operating model is accepted. No repository evidence identifies stable Golden Rose service-area names or conventions. Zone naming and membership are therefore owner-managed operational configuration that may evolve through pilot use; they are not prerequisites for implementation or request opening.

## Decision

Phase 1 uses a flat, Owner-managed catalog of broad operational service zones. Zones support routine queue, calendar, workflow ownership, and authorized reporting without making exact address the default operating geography. The Owner may create, name, rename, deactivate, and assign zones as observed operating needs emerge.

The taxonomy does not hardcode NYC boroughs, neighborhoods, ZIP codes, or final naming conventions. Under `docs/planning/phase-1-nyc-job-demand-map-contract.md`, the Owner composes zones from pinned official NYC Community District Tabulation Areas. Phase 1 does not support freehand polygons, exact-point zone definitions, distance, proximity, routing, or demographic inference. Synthetic fixtures use clearly fictional zone values and must not be represented as client policy.

## Ownership boundaries

- `ServiceZone` is a governed business reference whose display boundary is the union of its selected pinned CDTA cells; it is not an exact-location or freehand map feature.
- `WorksiteZoneMembership` records which approved zones may operationally include a worksite.
- `StaffingRequest` records a confirmed operational/reporting zone when assigned, an approved outside-area disposition, or a visible unassigned/review condition.
- `ShiftNeed` preserves the zone or geographic workflow condition inherited for that occurrence.
- Exact address remains authoritative location detail on `Worksite` and is separately restricted.
- Queue, calendar, and reporting surfaces use the request/shift operational zone or explicit unassigned/review/outside-area condition rather than guessing from address or reading the worksite's latest membership.

## Flat zone catalog

Phase 1 zones have no parent/child hierarchy. Their renderable boundary is an effective-dated composition of official pinned CDTAs; no freehand polygon is authoritative.

Each stable zone identity minimally includes:

- opaque `service_zone_id` and stable code;
- an Owner-supplied display label;
- lifecycle status;
- effective dates and definition version;
- creating/changing actor and time; and
- predecessor/successor references where zones are superseded, split, or merged.

Optional owner-managed metadata may include descriptions, aliases, translations, and assignment guidance. These values may emerge during pilot use. A zone label is operational content, not a legal or geographic claim; the interface and controls still require English/Spanish functional parity even when the Owner has supplied only one proper-name label.

Stable IDs/codes are system-generated and immutable. Display labels and optional content are editable with audit history. Referenced zones are deactivated or superseded, never destructively deleted. Historical records retain stable identity and the definition version used for classification.

Initial lifecycle values:

- `draft`: optional work in progress; unavailable for routine assignment.
- `active`: Owner-enabled and available for assignment.
- `retired`: unavailable for new assignment but retained historically.

The Owner may create a zone directly as active or activate a draft. `docs/planning/phase-1-staff-permission-matrix.md` permits only an explicitly delegated Manager to receive named zone-governance capabilities; Operations Staff receive no catalog-editing or reclassification authority in Phase 1.

## Worksite zone memberships

A worksite may have multiple simultaneous active memberships.

Invariants:

1. Every membership links one worksite, one active zone identity, and one accepted zone-definition version.
2. Exactly one active membership is primary whenever the worksite has any active memberships.
3. A secondary membership may record a concise operational reason when useful; exact overlap conventions may emerge through testing.
4. Duplicate active membership in the same zone is rejected.
5. Memberships are effective-dated and attributable.
6. Correcting, ending, or changing a membership preserves prior history.
7. Adding or changing a worksite membership does not silently rewrite existing requests or shifts.
8. Zone membership is not public address verification and does not prove legal jurisdiction, commute feasibility, service eligibility, or worker suitability.

Initial membership evidence includes:

- worksite ID;
- zone identity and definition version;
- primary/secondary designation;
- effective start/end;
- assigned/confirmed actor and time;
- controlled source/reason; and
- relation to the prior membership event when corrected or superseded.

## Assignment method

Phase 1 service-zone classification is manual and Owner-led. The NYC map automatically derives a worksite CDTA through the separately gated provider-neutral geocoding boundary; CDTA derivation does not automatically assign a service zone.

- The Owner may assign or correct worksite membership using active catalog values.
- Manager assignment authority requires an explicit permission-matrix delegation; Operations Staff receive no assignment authority in Phase 1.
- Exact address may enter the approved server-side geocoding boundary solely to derive a pinned CDTA, subject to provider approval and minimum-data handling.
- ZIP/postal code alone does not automatically determine service-zone membership.
- Coordinates, neighborhood demographics, employer type, household status, language, and other proxies do not determine membership.
- If the Owner is not ready to classify a worksite, it remains `zone_unassigned`; `zone_review_required` may be used when an explicit review is needed.

Automatic CDTA derivation is governed by the accepted NYC map contract. Automatic service-zone assignment remains deferred until its accuracy, correction path, and human-review behavior are separately approved.

## Operational zone per request and shift

A worksite's primary membership provides the default proposal for a new request when one exists. A request may open without a zone and remain visibly `zone_unassigned`. When the Owner later assigns an operational zone, the system records one zone/version for deterministic attribution.

- Secondary memberships support worksite discovery and alternative approved classification; they do not duplicate the request in queues or reports.
- The request records both zone identity and accepted definition version, or the approved outside-area disposition when no zone applies.
- Each child shift inherits the request's confirmed operational zone/version or outside-area disposition.
- A request/shift appears once under its confirmed operational zone in ordinary queue, calendar, and aggregate measures.
- An “any worksite membership” search may locate a worksite through secondary memberships, but it does not change operational attribution.

This model avoids double counting while allowing Owner-defined overlapping operational areas.

## Geographic workflow conditions

The following are workflow conditions, not `ServiceZone` records:

- `zone_assigned`
- `zone_unassigned`
- `zone_review_required`
- `outside_approved_service_area`

Do not create catch-all zones named “Unknown,” “Other,” “Outside,” or “Unassigned.”

### `zone_unassigned`

No worksite membership or request-level operational zone has been recorded. The condition remains visible in intake, queue, calendar, and reporting exception views; it does not block request opening.

### `zone_review_required`

Available information does not support classification under the Owner's current conventions. The condition requires accountable review; no nearest-zone guess is permitted.

### `outside_approved_service_area`

Authorized staff determined that the location is outside the active catalog/coverage policy. The determination records actor, time, source/reason, and applicable catalog version.

This condition does not automatically reject, close, cancel, rank, or deprioritize a request. Owner/Manager-approved business policy separately controls whether Golden Rose accepts out-of-area work.

A later catalog expansion creates a new effective-dated membership/classification; it does not rewrite the earlier out-of-area determination.

## State-dependent requiredness

- A worksite may be created while `zone_unassigned`.
- A request may enter and remain `open` while `zone_unassigned` or `zone_review_required`.
- A shift may enter an active coverage state while zone classification is unresolved.
- Unassigned records must remain visible and countable; ordinary zone filters and reports may not silently omit them.
- When a request has a zone, child shifts inherit that zone/version. When it is unassigned, child shifts preserve the unassigned disposition until an audited classification is applied.
- `outside_approved_service_area` remains a separately governed determination and does not automatically close or reject a request.

No zone requirement or exception changes employer/worker eligibility or performs an employment decision.

## Corrections and historical behavior

### Before request opening

The Owner may create or correct worksite membership and request operational-zone selection with attributable evidence. Delegated roles may do so only if the permission matrix grants that command.

### After request opening

The Owner may assign or change an open request's operational zone because the adaptive catalog is intended to evolve during use. Delegated active-request correction requires explicit permission-matrix authority.

The correction command must:

1. Check current record versions and authority.
2. Confirm that the new zone is active and create/confirm the corresponding worksite membership, or record an approved exception path.
3. Update the request and all nonterminal child shifts atomically.
4. Record prior/new zone identity and definition version, actor, time, reason, and affected records.
5. Preserve terminal shifts under their historically accepted zone/version unless the Owner performs an explicit historical correction with a reason.
6. Leave lifecycle state, coverage, and outcomes unchanged unless a separate governed transition is explicitly required.

The request and all affected nonterminal child updates/events commit atomically under `docs/planning/phase-1-correction-audit-event-contract.md`, with expected versions, one correlation ID, and no partial propagation. Restricted history does not broaden exact-address access.

A worksite membership change alone never causes this request-level correction automatically.

## Queue, calendar, search, and reporting semantics

- Routine queue/calendar items use the record's confirmed operational zone.
- Service-zone filters apply authorization before results and counts.
- Records are counted once under their operational zone.
- Secondary memberships do not duplicate requests/shifts in zone totals.
- `zone_unassigned`, `zone_review_required`, and `outside_approved_service_area` appear as separate exception buckets, not as real-zone totals.
- Unassigned counts are always disclosed alongside zone-scoped totals so classification coverage is visible.
- Zone-assignment status is an independent classification flag/filter and does not replace or outrank the deterministic service-work queue lane; urgent coverage remains urgent even when its zone is unassigned.
- Retired zones remain available for authorized historical filtering and display with their historical label/version.
- Current labels must not silently replace historical meanings where a definition changed.
- Zone summaries do not reveal exact addresses, employer contacts, worker identities, or restricted notes.
- Small-group suppression, production exports, public metrics, and mapping remain separately approved decisions.

## Governance and permissions

### Owner

- Creates, names, renames, activates, deactivates, and assigns zones as operational needs emerge.
- Changes primary/default memberships and reclassifies current records.
- May explicitly correct historical classifications with attributable reason.
- Approves or delegates catalog, assignment, and exception authority through the permission model.

### Delegated Manager

- Has no zone-management authority by role label alone.
- May perform only specifically delegated catalog, assignment, or correction commands under `docs/planning/phase-1-staff-permission-matrix.md`.

### Operations Staff

- May view or use zones only as authorized by the permission matrix.
- Receives no catalog-editing or reclassification authority by default.

### Platform Administrator

- Receives no zone-policy, operational-classification, or exact-address authority merely through technical responsibility.
- Any exceptional support access remains separately approved, time-bounded, logged, and reviewed.

Command/field permissions are controlled by `docs/planning/phase-1-staff-permission-matrix.md`; it may narrow but must not silently broaden these business-authority boundaries.

## Prohibited uses

A service zone or zone membership must not be used to:

- infer race, ethnicity, nationality, religion, language, immigration status, income, household status, or other protected/proxy traits;
- rank or score employers or workers;
- determine worker eligibility, suitability, referral, assignment, hiring, discipline, or compensation;
- infer commute feasibility, travel tolerance, or availability;
- expose exact home/worksite coordinates or address in the default zone/map view;
- create public or individual-level map pins;
- silently accept/reject a request;
- replace authoritative address, legal jurisdiction, or compliance analysis; or
- transmit location data to an unapproved third party.

## Validation and synthetic implementation boundary

Pilot/product testing must validate:

- that the Owner can create, rename, deactivate, and assign zones without engineering changes;
- that unassigned work remains visible and does not disappear from counts;
- whether descriptions, translations, guidance, overlap reasons, and additional delegation are actually needed;
- whether the primary/default model matches observed work;
- the out-of-area handling workflow;
- named Manager delegations for classification and named recipients for the distinct exact-address permission;
- reporting/export and small-group suppression rules; and
- training/correction procedures.

Local synthetic implementation may use clearly fictional fixtures such as `Zone Alpha` and `Zone Beta`. Fictional values must be labeled as synthetic and must not appear in client-facing or production configuration as inferred policy.

This contract does not authorize a live geocoding vendor, production addresses, production data, cloud provisioning, or deployment. The NYC map and synthetic provider-neutral CDTA derivation are governed separately by `docs/planning/phase-1-nyc-job-demand-map-contract.md`.

## Explicitly separate decisions

- Final or evolving zone names, descriptions, aliases, translations, and overlap conventions; these do not block implementation or pilot use.
- Named recipients and delegations for the accepted distinct exact-address reveal permission.
- Out-of-area acceptance/business policy.
- Worker work-zone preferences, travel tolerance, assignment, availability, or matching.
- Freehand/custom polygons, retained precise coordinates, live geocoder/tile providers, routing, travel time, or distance calculations.
- Public/worker/employer zone visibility.
- Production retention, exports, public metrics, and small-group suppression.

## Revisit triggers

Revisit this contract when CDTA grouping no longer represents operational boundaries; when hierarchy or freehand/custom polygons become necessary; before routing, public visibility, worker preferences/assignments, proximity analysis, or cross-jurisdiction compliance rules; when overlapping memberships cannot preserve single operational attribution; or when a zone correction cannot preserve historical and audit meaning.
