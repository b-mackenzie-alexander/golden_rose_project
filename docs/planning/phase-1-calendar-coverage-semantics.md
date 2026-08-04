# Phase 1 Calendar and Coverage Semantics

**Status:** Accepted Phase 1 planning source of truth
**Accepted:** 2026-08-03
**Decision owner:** Beatrice, technical delivery owner
**Scope:** Authorized staff calendar/coverage projection only; no external calendar integration, worker-assignment authority, or separate calendar datastore.

## Decision

Phase 1 provides an authorization-scoped calendar derived from authoritative `StaffingRequest` and `ShiftNeed` records. Requests and shifts both appear, but they have explicitly different visual and semantic roles. The calendar may issue governed correction/rescheduling commands; it does not own dates, state, coverage, or history.

The accepted request/shift lifecycle remains controlled by `docs/planning/phase-1-request-shift-state-model.md`. Queue urgency remains controlled by `docs/planning/phase-1-work-queue-aging-follow-up-model.md`.

## Authoritative item types

### Request milestone

A request milestone is a date-only marker derived from `StaffingRequest.requested_start_date`.

- It is labeled as a request and as an anticipated requested start.
- It shows request lifecycle state only.
- It has no invented start/end time or duration.
- It never asserts shift coverage, worker availability, assignment, placement, or completed work.
- It links to the authoritative request.
- If `requested_start_date` is absent or invalid, no marker is inferred; the request appears in the appropriate scheduling/data-quality exception view.

A request must not be rendered as a continuous span from its earliest to latest child shift. Such a span would imply uninterrupted demand and would change meaning when children change.

### Shift occurrence

A shift occurrence is a timed block derived from one authoritative `ShiftNeed`.

- It uses the shift's `starts_at`, `ends_at`, and originating `time_zone`.
- It shows shift lifecycle/coverage state and approved aggregate coverage.
- It links to the authoritative shift and parent request.
- It represents one actual requested work occurrence.
- It is not an independent calendar event and is never duplicated into a calendar-specific store.

Future worker assignment or availability records may enrich the shift occurrence only after their authority, permissions, and consistency contract is approved.

## State visibility

### Request milestones

| Request state | Calendar behavior |
|---|---|
| `draft` | Excluded from the operational calendar. Missing/invalid dates remain discoverable through exceptions. |
| `pending_review` | Shown as tentative/review required. |
| `needs_information` | Shown with a distinct information-needed indicator. |
| `open` | Shown as active demand. |
| `closed` | Retained in authorized historical/date-range views; close reason is available on source inspection. |
| `cancelled` | Retained, clearly cancelled, and visually de-emphasized. |

### Shift occurrences

| Shift state | Calendar behavior |
|---|---|
| `draft` | Excluded from the operational calendar. Missing/invalid schedule data remains discoverable through exceptions. |
| `pending_review` | Shown as tentative; never presented as active or covered. |
| `open_uncovered` | Shown as active, `0 / N confirmed`. |
| `partially_covered` | Shown as active, `X / N confirmed`. |
| `covered` | Shown as currently covered, `N / N confirmed`; does not imply completion. |
| `completed` | Retained as historical work that occurred; shows `fully_staffed` or `understaffed`. |
| `unfulfilled` | Retained as a distinct outcome: scheduled work did not occur because staffing was unavailable. |
| `cancelled` | Retained, clearly cancelled, de-emphasized, and excluded from active-demand counts. |

Pending items remain visible so near-term unreviewed demand does not disappear from scheduling awareness. Terminal/cancelled records are not deleted from date-based history. Default filters may reduce visual noise only when the active filter is disclosed and authorized staff can restore hidden states.

Calendar presence never changes lifecycle state.

## Time and interval semantics

1. Every submitted shift requires valid timezone-aware `starts_at`, `ends_at`, and an IANA timezone identifier such as `America/New_York`.
2. Authoritative instants and the originating timezone are preserved; a fixed UTC offset is insufficient.
3. `ends_at` must be after `starts_at`.
4. Phase 1 shifts are timed intervals. An all-day shift is not allowed because it would conceal the actual coverage window.
5. An overnight shift remains one `ShiftNeed` spanning the relevant date boundaries; it is not split into separate records.
6. The calendar defaults to the agency's approved operational timezone.
7. A shift whose originating timezone differs receives an explicit timezone indicator. Source detail shows both shift-local and agency-converted times.
8. Day/week/month placement is derived from the selected display timezone.
9. Impossible or ambiguous local times caused by daylight-saving transitions require explicit validation and resolution; the system must not silently reinterpret them.
10. Request milestones are date-only values governed by the agency's approved operational calendar and are not converted into timed events.

Audit timestamps remain UTC instants and are displayed in the appropriate approved timezone.

## Recurrence and repeated demand

Phase 1 has no executable recurrence engine.

- Every work occurrence is an explicit `ShiftNeed` with independent schedule, state, coverage, owner, and outcome.
- Staff may create multiple shifts under one request.
- `schedule_pattern` may preserve a restricted human-readable source description, but it does not generate calendar items or infer occurrences.
- Changing or cancelling one occurrence does not mutate sibling shifts.
- There is no Phase 1 “edit this and all future events” operation.

A future recurrence capability requires separately approved series identity, bounded generation horizon, preview/confirmation, effective dates, timezone/DST behavior, duplicate prevention, per-occurrence exceptions, and attributable bulk changes.

## Coverage presentation

Authorized staff calendar summaries show controlled state plus aggregate requested/confirmed counts:

- `pending_review`: requested count may be shown with “coverage not yet approved”; do not show `0 / N` because zero coverage has not been asserted.
- `open_uncovered`: `0 / N confirmed`.
- `partially_covered`: `X / N confirmed`.
- `covered`: `N / N confirmed`.
- `completed`: show `fully staffed` or `understaffed`, not a stale pre-work confirmation count.
- `unfulfilled`: show that work did not occur because staffing was unavailable.
- `cancelled`: show cancellation, not coverage.

Request milestones never display their own coverage count. A request detail may show a clearly labeled derived child-shift summary, but the request status does not replace child outcomes.

Safeguards:

- No worker names, worker contact data, attendance detail, or assignment list appears in the Phase 1 calendar.
- Exact small aggregate counts are preferred over percentages.
- “Available” is not used as a synonym for requested, confirmed, assigned, or covered.
- State uses text plus a non-color cue; color alone is never authoritative.
- Covered does not imply legal placement, worker consent, payment, or completed work.

## Location and identifying-data boundary

The default summary uses the least identifying information necessary:

- approved broad `ServiceZone` when assigned, otherwise an explicit unassigned/review/outside-area indicator;
- internal request/shift reference;
- approved job/role category when available;
- state and aggregate coverage; and
- the applicable milestone date or shift interval.

Exact worksite/household address is restricted:

1. Service zone remains visible by default when assigned; an unresolved classification remains explicitly visible rather than being guessed or omitted.
2. Authorized day/week operational views may provide a permission-gated address reveal.
3. Address reveal requires authority to view the exact worksite field; calendar access alone is insufficient.
4. Month and aggregate views never show exact addresses.
5. External feeds, notifications, screenshots/exports, or aggregate views do not inherit exact addresses.
6. Employer name appears only when permitted by the final field/role matrix.
7. Employer contacts, worker identity/contact data, restricted free text, unreviewed requirements, notes, and no-show narratives are excluded from calendar summaries.
8. The source record remains authoritative for exact address and contact data.

Authorization is applied before query results, counts, filters, summaries, and reveal controls are returned.

## Corrections, coverage loss, and no-shows

The ordinary calendar shows current authoritative truth; prior facts remain in the source audit timeline under `docs/planning/phase-1-correction-audit-event-contract.md`. The calendar is neither the writable record nor an audit/event-replay store.

- Coverage loss updates the existing occurrence to partial/uncovered and recalculates queue urgency immediately.
- The item is not deleted and recreated merely because coverage changed.
- No-show reason/narrative is excluded from the calendar summary.
- Work that proceeds with fewer workers becomes `completed / understaffed` through the governed workflow.
- Work that does not occur because staffing is unavailable becomes `unfulfilled`.
- Incorrect terminal outcomes use the accepted exceptional reopening/review path.
- Corrected or reopened items carry a visible indicator without exposing restricted reasons in the summary.
- Prior state, count, actor, timestamp, and reason remain append-only.
- Phase 1 does not provide an “as-of historical replay” calendar. Audit history, not duplicated calendar items, preserves earlier versions.

Exports or captured views must not imply that a corrected current label was always the historical label.

## Overlap and conflict semantics

- Overlapping request milestones and shift occurrences are allowed and rendered distinctly.
- Overlapping shifts are stacked/grouped, never merged into a synthetic shift.
- Multiple shifts under one request may overlap because they can represent different roles, worksites, or quantities.
- Dense views may show an expandable authorized count, but aggregation must not hide critical/uncovered states.
- Phase 1 does not infer worker scheduling conflicts, staffing capacity, travel feasibility, proximity, or suitability.
- Duplicate suspicion uses an explicit review/correction workflow; overlap alone is not proof of duplication.

Automatic worker-conflict detection is deferred until authoritative worker assignment and availability records exist. That future contract must define active assignment identity, interval overlap, timezone/cancellation behavior, stale-state handling, override authority, and audit evidence.

## Audited drag-and-drop rescheduling

The calendar may initiate governed rescheduling commands. A visual drag never writes calendar-local state.

### Request milestone

- A nonterminal request milestone may propose a new `requested_start_date`.
- Confirmation and correction reason are required.
- Child shifts never move automatically.
- The interaction states clearly that the milestone is anticipated request timing, not a shift occurrence.

### Draft or pending-review shift

- A drag proposes new start/end instants while preserving duration.
- Timezone, DST, interval, permission, and expected-record-version validation run before commit.
- Confirmation and correction reason are required.
- The authoritative shift is updated and the calendar refreshes only after success.

### Active shift

Dragging an `open_uncovered`, `partially_covered`, or `covered` shift initiates one governed atomic replacement operation:

1. Validate the proposed interval, authority, parent state, and expected versions.
2. Create a new linked shift for the proposed interval with no inherited coverage assertion.
3. Cancel the prior shift with controlled reason `superseded_by_reschedule` and a link to the replacement.
4. Preserve all prior schedule and coverage events on the original shift.
5. Require the replacement to pass current review and coverage workflow.

If the operation cannot complete atomically, neither the replacement nor cancellation is committed.

### Terminal shift

Terminal shifts cannot be dragged. Staff use the accepted exceptional reopening or linked-replacement workflow.

### Interaction safeguards

- Drop opens a confirmation/reason dialog; the move is not committed beforehand.
- Failure or stale-version rejection restores the original position and shows an honest error.
- Phase 1 drag preserves duration.
- Resize-to-change-duration, copy, series edit, and bulk move are deferred.
- Successful actions record actor, old/new schedule, timezone, reason, expected version, and replacement relation where applicable.

## Presentation and accessibility

- Request milestones and shift occurrences use distinct labels, shapes/icons, and detail affordances.
- State and coverage are never communicated by color alone.
- Keyboard and non-pointer users can perform every approved calendar action through an equivalent source workflow.
- Day/week/month views disclose timezone and active filters.
- Empty, loading, stale, unavailable-data, authorization-denied, and error states are distinct.
- Dense rendering must preserve access to critical/uncovered items and must not expose unauthorized details in counts or previews.
- English/Spanish functional and accessibility parity applies to labels, state meanings, errors, confirmations, and legends; policy/legal translation remains separately approved.

## Required consistency and audit evidence

Calendar projections and commands must be reproducible from authoritative request/shift records, transitions, schedule fields, coverage events, correction/replacement links, timezone data, and authorization policy. Implementations must:

- avoid calendar-specific duplicate status/date storage;
- apply authorization before rendering and aggregation;
- reject stale schedule/state changes;
- preserve parent/child and coverage invariants;
- show projection freshness/error state honestly;
- preserve attributable correction/replacement events; and
- ensure calendar and queue derive from the same current source versions.
- treat a stale/missing projection as a visible unavailable/rebuild condition rather than a false empty calendar.

## Explicitly separate decisions

The following remain unresolved and must not be inferred from this model:

- actual production zone values, named exact-address recipients, and address-reveal delegations under the accepted service-zone taxonomy and `docs/planning/phase-1-staff-permission-matrix.md`;
- final field-by-state requiredness;
- worker identity, assignment, availability, attendance, conflict detection, discipline, referral, placement, and payment;
- external calendar sync, ICS feeds, notifications, messaging, or mobile-device integration;
- executable recurrence, bulk scheduling, resize-to-change-duration, or “edit series” behavior;
- production retention, export, screenshot/device policy, and historical replay;
- final visual design tokens and client terminology.

## Revisit triggers

Revisit this model when the client changes request/shift terminology, timezone/service-area practice, address-access needs, or calendar workflow; before worker assignments/availability, external sync/notifications, executable recurrence, bulk edits, mobile/offline behavior, historical replay, production exports, or additional public/employer/worker calendar views; or when a calendar command cannot preserve the state, coverage, authorization, and audit contracts defined here.
