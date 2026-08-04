# Phase 1 NYC Job-Demand Map Contract

**Status:** Accepted Phase 1 planning source of truth
**Accepted:** 2026-08-03
**Decision owner:** Beatrice, technical delivery owner
**Scope:** Authorized staff NYC map foundation and employer-demand/coverage layer; worker-supply overlay is separately gated

## Decision

Phase 1 includes an interactive New York City map for authorized staff. Its immediate purpose is to help the client understand where employer demand and coverage gaps occur. It uses aggregate geographic cells and Owner-defined service zones rather than exact job or worker pins.

The Phase 1 map contains employer-demand and shift-coverage measures only. A worker-supply overlay is an intended follow-on capability, but it cannot be enabled until worker location, availability, authorization, correction, retention, and anti-ranking rules are accepted as an authoritative contract.

The map is a derived visualization over authoritative operational records. It is not a separate response store, assignment system, matching engine, or source of lifecycle/coverage truth.

## Evidence and official base geography

The fixed base geography is the NYC Department of City Planning 2020 Community District Tabulation Areas (CDTAs):

- publisher: NYC Department of City Planning;
- NYC Open Data dataset ID: `xn3r-zk6y`;
- purpose reported by DCP: approximate NYC's 59 Community Districts for statistical reporting using whole 2020 census tracts;
- catalog version observed on 2026-08-03: `26b`; and
- source: `https://data.cityofnewyork.us/City-Government/2020-Community-District-Tabulation-Areas-CDTAs-/xn3r-zk6y`.

The implementation must pin and record the exact downloaded release/checksum rather than silently track “latest.” The observed `26b` release is a candidate, not authorization to ingest or deploy data before implementation approval.

Borough boundaries provide navigation/context only. ZIP codes, neighborhoods, hand-drawn polygons, and exact point locations are not the authoritative Phase 1 aggregation geography.

## Authoritative map records

### `MapAreaDatasetVersion`

Records the imported public boundary release:

- dataset identity and publisher;
- source URL;
- publisher release/version;
- retrieval time;
- file/artifact checksum;
- coordinate reference system and normalization details;
- importer/schema version;
- activation/retirement status; and
- approving actor/time.

A new public release creates a new version. It never silently rewrites historical map-area or zone-composition meaning.

### `MapArea`

Represents one CDTA from a pinned dataset version:

- stable publisher CDTA identifier;
- dataset-version reference;
- publisher label and borough reference;
- normalized multipolygon geometry;
- source metadata; and
- active/retired status within the imported release.

Publisher names are reference labels, not client service-zone policy.

### `WorksiteMapAreaAssignment`

Records a worksite's CDTA classification:

- worksite ID;
- CDTA and dataset-version references;
- assignment method (`derived` or `owner_corrected`);
- geocoding provider/interface version when derived;
- match quality/status;
- derivation/confirmation/correction actor and time;
- source-result reference or minimum necessary evidence;
- prior assignment relationship; and
- correction reason where applicable.

Exact returned coordinates are transient processing data and are not retained by default.

### `ServiceZoneComposition`

Links an Owner-managed service-zone definition version to one or more CDTA/version identifiers.

- The Owner creates a zone by selecting fixed CDTAs and supplying a practical zone label.
- A CDTA may participate in more than one service zone when the Owner needs overlapping operational groupings.
- One service zone may contain one or more CDTAs.
- Composition changes are effective-dated and attributable.
- A changed composition does not silently rewrite a request/shift's recorded operational zone.
- Zone boundaries render as unions of selected official CDTA geometry; Phase 1 has no freehand polygon editing.

## Address-to-CDTA derivation

Automatic worksite-to-CDTA assignment is approved as a provider-neutral capability subject to the vendor/data-processing gate.

Required processing boundary:

1. Run geocoding server-side; browser clients do not call the geocoder with exact addresses.
2. Send only the minimum address fields needed for a match. Never send employer/contact identity, request text, worker data, notes, or coverage details.
3. Record provider/interface version, request time, result quality, and derivation status without logging the raw address or precise returned coordinates.
4. Perform point-in-polygon classification against the pinned local CDTA geometry.
5. Store the CDTA/version assignment and audit evidence.
6. Discard precise coordinates after classification by default.
7. Send ambiguous, low-confidence, conflicting, failed, or outside-NYC results to accountable review.
8. Permit the Owner to correct the CDTA through an attributable command.

Selecting a geocoder requires separate approval of provider terms, address disclosure, subprocessors, API-key restrictions, caching/storage limits, retention, deletion, cost controls, outage behavior, and incident ownership.

Synthetic/local tests use deterministic geocoder fixtures and synthetic addresses. They do not transmit addresses to a live provider.

## Map-area statuses

Initial controlled values:

- `map_area_unassigned`: no derivation has been attempted or accepted;
- `geocoding_pending`: an authorized derivation is awaiting completion;
- `map_area_assigned`: a current CDTA/version assignment exists;
- `map_area_review_required`: result is ambiguous, low-confidence, conflicting, or corrected review is pending;
- `outside_nyc`: the result does not fall within the pinned NYC CDTA dataset; and
- `geocoding_failed`: the provider/process failed without an accepted assignment.

These statuses do not change request/shift lifecycle or coverage. Unassigned/review/failed/outside records remain visible and countable outside mapped totals.

## Separation between CDTA and service zone

CDTA assignment and service-zone assignment are related but distinct:

- CDTA answers which pinned public map area contains the worksite.
- Service zone answers how the Owner currently organizes work operationally.
- A derived CDTA does not automatically create, rename, select, or change a service zone.
- Owner zone composition may suggest available service zones for review, but no zone assignment occurs without an authorized command.
- Requests/shifts retain their operational-zone/version history even if a worksite CDTA or zone composition changes.
- CDTA metrics and service-zone metrics identify their aggregation basis explicitly.

## Phase 1 job-demand layer

The map supports named, transparent measures over an authorized selected time window.

### Open staffing-request count

Count distinct authorized `StaffingRequest` records in `open`, grouped by authoritative worksite CDTA or recorded operational zone.

### Upcoming nonterminal shift count

Count distinct authorized `ShiftNeed` records whose requested interval intersects the selected future window and whose state is `pending_review`, `open_uncovered`, `partially_covered`, or `covered`. Draft and terminal shifts are excluded by default; explicit historical filters may include authorized terminal records.

### Requested worker count

Sum `worker_count` over the included shifts.

### Confirmed coverage count

Sum authoritative `confirmed_worker_count` over the included shifts. This is aggregate Phase 1 coverage evidence, not worker identity or assignment.

### Remaining coverage gap

For each included shift, compute `max(worker_count - confirmed_worker_count, 0)`, then sum. The map must not derive this from color, labels, or an opaque score.

### Classification exceptions

Show counts for:

- `map_area_unassigned`;
- `map_area_review_required`;
- `geocoding_failed`;
- `outside_nyc`;
- `zone_unassigned`; and
- `zone_review_required`.

These records are not silently omitted from totals.

## Presentation and interaction

- The user explicitly selects the displayed metric; no combined “opportunity,” “priority,” or “match” score is approved.
- Every metric has a visible definition, selected time window, refresh time, aggregation basis, and legend.
- Map color is never the sole carrier of state or magnitude.
- A synchronized accessible table/list provides the same authorized metrics and records without requiring map interaction.
- Keyboard navigation, focus visibility, text alternatives, zoom-independent controls, and English/Spanish UI parity are required.
- Selecting a CDTA or service zone may open authorized aggregate details and record lists.
- Exact worksite address is excluded from map summaries and tooltips. Any reveal uses the separate permission-gated worksite workflow.
- No individual worker layer or point appears in Phase 1.
- Basemap tiles, renderer, and geocoder remain replaceable providers; record data must not be embedded in tile requests.

## Authorization and privacy

Authorization applies before map records, aggregates, filters, counts, lists, and drill-downs are computed or returned.

- The map is staff-only in Phase 1.
- Exact worksite coordinates are not persisted by default.
- Exact worker/home coordinates are not collected or displayed under this contract.
- The basemap/tile provider does not receive employer, contact, request, worker, address, coverage, or zone-assignment records.
- Ordinary logs exclude raw addresses, geocoding payloads, exact coordinates, and provider credentials.
- API credentials are server-side or domain/API-restricted as appropriate and never embedded with broader cloud authority.
- Map export, public sharing, screenshots generated by the system, and external feeds remain disabled until approved.
- Production aggregation/small-group suppression rules remain unresolved. The later worker layer must not ship without an approved re-identification boundary.

## Correction and consistency

Owner correction of a derived CDTA must:

1. Require authorization and an expected record version.
2. Preserve the provider-derived result as audit evidence without retaining prohibited precise data.
3. Record prior/new CDTA and dataset versions, actor, time, and reason.
4. Recompute current authorized CDTA aggregates.
5. Not automatically change service-zone membership, operational zone, lifecycle state, coverage, or outcome.
6. Preserve historical reports against their recorded dataset/assignment version where required.

Dataset-version activation and service-zone-composition changes are separate governed commands.

CDTA corrections, dataset activation/retirement, and zone-composition actions follow `docs/planning/phase-1-correction-audit-event-contract.md`. Required domain changes and events commit atomically; restricted evidence never retains raw geocoder payloads or precise coordinates. A stale/missing map projection is shown honestly and cannot become a false zero-demand result.

## Worker-supply overlay boundary

The intended later map may compare authorized aggregate job demand with aggregate worker supply using the same CDTA/service-zone geography. Before that overlay is enabled, a separate worker-location contract must approve:

- worker location field and purpose;
- collection source and informed notice/consent where required;
- precision and geocoding treatment;
- whether residence, preferred work area, or another location concept is authoritative;
- availability definition and time window;
- verification/correction process;
- role visibility and export restrictions;
- aggregation and small-group suppression;
- retention/deletion;
- no-location and outside-NYC treatment; and
- anti-ranking, anti-proxy, and human-review safeguards.

A worker profile count is not the same as available supply. Geographic overlap does not establish suitability, availability, eligibility, referral, assignment, commute feasibility, or willingness.

## Prohibited uses

The map, CDTA, service zone, geocoding result, or derived metrics must not:

- rank, score, recommend, match, refer, assign, hire, or exclude workers;
- infer worker availability, travel tolerance, commute feasibility, or willingness;
- infer protected traits or use geography as their proxy;
- expose exact household, worker-home, or worksite points by default;
- silently alter request/shift state, coverage, ownership, or zone assignment;
- claim legal jurisdiction or compliance based on map boundaries;
- use an opaque combined heat/priority score; or
- represent aggregate proximity as evidence that a worker should take a job.

## Implementation and verification boundary

A bounded synthetic Phase 1 implementation must verify:

- pinned CDTA import identity/checksum/version behavior;
- geometry normalization and deterministic point-in-polygon fixtures;
- provider-neutral geocoder interface and no live calls in tests;
- ambiguous/failure/outside-NYC review paths;
- Owner CDTA correction and zone composition;
- deterministic metric definitions and no double counting;
- unassigned/review counts;
- authorization before aggregation/drill-down;
- exact-location/log redaction;
- accessible synchronized non-map view; and
- no worker layer or ranking behavior.

This contract does not authorize a live geocoding vendor, production addresses, production data, public maps, worker-location collection, cloud provisioning, or deployment.

## Revisit triggers

Revisit before selecting a renderer/tile/geocoder provider; enabling live address geocoding; importing a newer CDTA release; displaying individual or approximate points; enabling worker supply; adding custom polygons, routes, distance, travel time, or proximity; exporting/sharing maps; admitting production data; or changing the map from descriptive context to decision support.
