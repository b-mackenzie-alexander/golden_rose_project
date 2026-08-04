# Phase 1 Request and Shift State Model

**Status:** Accepted planning source of truth for Phase 1 request and shift lifecycle
**Accepted:** 2026-08-03
**Decision owner:** Beatrice, technical delivery owner
**Operational evidence:** No-shows reportedly occur at the agency, so active shift coverage must be reversible and historically attributable.

## Decision

Phase 1 uses explicit, server-enforced state machines for `StaffingRequest` and `ShiftNeed`. State transitions are authoritative operations, not freely editable labels. Every transition appends an `AuditEvent` and preserves prior meaning.

This document controls lifecycle states, transitions, guards, terminal outcomes, reopening, and cross-record invariants. `docs/planning/phase-1-work-queue-aging-follow-up-model.md` separately controls accepted clock, follow-up, ownership, trigger, and queue-lane semantics. This document does not approve final field-by-state requiredness, production permissions, worker assignments, or automated employment decisions.

## StaffingRequest state model

```text
draft → pending_review → open → closed
             ↕
      needs_information

any nonterminal state → cancelled

closed/cancelled -- exceptional Owner/Manager reopen --> pending_review
```

### State meanings

| State | Meaning | Important boundary |
|---|---|---|
| `draft` | Staff entry is incomplete or not yet submitted for agency review. | Not active demand; excluded from active-demand counts. |
| `pending_review` | Submitted to the agency intake/review queue. | Not yet approved as open demand. |
| `needs_information` | Required clarification is missing before agency acceptance. | Requires a controlled reason and accountable follow-up; does not imply employer fault. |
| `open` | Agency-reviewed active demand with one or more governed shift needs. | Does not mean public, matched, referred, assigned, covered, placed, or legally approved. |
| `closed` | Agency work on the request has concluded. | Does not claim that every shift was fulfilled; child shift outcomes remain authoritative. |
| `cancelled` | The overall demand was withdrawn or discontinued before ordinary conclusion. | Requires a cancellation reason; history remains available to authorized staff. |

### Ordinary transitions and guards

| From | To | Minimum guard |
|---|---|---|
| record creation | `draft` | Authorized staff creates an attributable record. |
| `draft` | `pending_review` | Minimum intake validation passes and at least one governed shift need exists. Exact required fields remain controlled by the staged-requiredness contract. |
| `draft` | `cancelled` | Controlled cancellation reason is recorded. |
| `pending_review` | `needs_information` | Controlled reason and accountable follow-up owner are recorded. |
| `needs_information` | `pending_review` | New or corrected information is recorded and resubmitted. |
| `pending_review` | `open` | Required-for-open validation passes; requirements have been reviewed; and no prohibited criteria are accepted. Service-zone assignment may remain unresolved under `docs/planning/phase-1-service-zone-taxonomy.md` and must stay visible as an exception rather than blocking `open`. |
| `pending_review` | `closed` | Agency concludes review without opening the demand; all child shifts are terminal and a close reason is recorded. |
| `needs_information` | `closed` | Agency concludes the request after the approved follow-up path; all child shifts are terminal and a close reason is recorded. |
| `open` | `closed` | Every child shift is terminal and a close reason is recorded. |
| any nonterminal state | `cancelled` | Cancellation reason is recorded; every nonterminal child shift receives its own attributable cancellation transition. |

`open` does not transition back to intake states during ordinary work. Material corrections append audit events. If a correction invalidates active demand, staff close/cancel the affected request and shifts or use the exceptional reopening/replacement path rather than silently rewinding state.

### Controlled request close reasons

Initial planning values:

- `all_shift_work_concluded`
- `not_accepted`
- `duplicate`
- `superseded`
- `no_response`
- `other_approved`

`other_approved` requires a minimum-necessary restricted explanation. Close reasons may be refined through client terminology validation, but their meanings must remain distinguishable and versioned.

Cancellation reasons are separate from close reasons. Initial categories are employer withdrawal, demand no longer needed, entry recorded in error, governed supersession/rescheduling, and other approved reason. Cancellation must not be used to hide a staffing failure that belongs in a shift's `unfulfilled` outcome. Active-shift calendar rescheduling uses the atomic linked-replacement contract in `docs/planning/phase-1-calendar-coverage-semantics.md`; it does not rewrite the active shift or inherit its coverage.

## ShiftNeed state model

```text
draft → pending_review → open_uncovered ↔ partially_covered ↔ covered
                             │                    │            │
                             └──────────────→ completed / unfulfilled / cancelled

Any nonterminal state may become cancelled.
completed/unfulfilled/cancelled -- exceptional Owner/Manager reopen --> pending_review
```

Direct `open_uncovered ↔ covered` transitions are permitted when all coverage is gained or lost in one attributable event. Coverage may move in either direction before a terminal outcome.

### State meanings

| State | Meaning | Coverage invariant |
|---|---|---|
| `draft` | Schedule information is incomplete or not submitted. | No coverage assertion. |
| `pending_review` | Schedule and worker count are awaiting agency review. | No approved coverage assertion. |
| `open_uncovered` | Reviewed active shift demand with zero currently confirmed workers. | `confirmed_worker_count = 0`. |
| `partially_covered` | Some but fewer than the requested workers are currently confirmed. | `0 < confirmed_worker_count < worker_count`. |
| `covered` | The requested worker count is currently confirmed. | `confirmed_worker_count = worker_count`; values above the requested count are rejected. |
| `completed` | Scheduled work occurred and staff recorded the outcome. | Requires `fully_staffed` or `understaffed` completion outcome. |
| `unfulfilled` | Scheduled work did not occur because required staffing was unavailable, including an unrecovered no-show. | Requires an approved staffing-failure reason. |
| `cancelled` | The shift was withdrawn or stopped for an approved reason other than staffing failure. | Requires a cancellation reason. |

`covered` is a current agency-recorded coverage statement. It is not a legal assertion of employment, worker consent, placement, payment, or successful completion.

### Ordinary transitions and guards

| From | To | Minimum guard |
|---|---|---|
| record creation | `draft` | Authorized staff creates an attributable child of a request. |
| `draft` | `pending_review` | Start/end/timezone and positive `worker_count` pass schedule validation. |
| `pending_review` | `open_uncovered` | Parent request is `open`; schedule and required-for-open fields pass review. |
| `open_uncovered` | `partially_covered` or `covered` | New aggregate confirmed-worker count and attributable coverage source satisfy the target-state invariant. |
| `partially_covered` | `open_uncovered` or `covered` | Revised count/source satisfy the target-state invariant. |
| `covered` | `partially_covered` or `open_uncovered` | Coverage-loss event records the revised count and controlled reason, including no-show or withdrawal when applicable. |
| any active coverage state | `completed` | Staff confirms work occurred and records `fully_staffed` or `understaffed`. A covered shift that suffers a no-show first records the coverage reversal. |
| any active coverage state | `unfulfilled` | Staff records that work did not occur because staffing was unavailable and provides an approved reason. |
| any nonterminal state | `cancelled` | Staff records an approved non-staffing-failure cancellation reason. |

Time passing never automatically marks a shift `completed`, `unfulfilled`, or `cancelled`. A past nonterminal shift is an overdue exception requiring staff action.

### Coverage evidence and no-shows

Phase 1 may store an aggregate `confirmed_worker_count` and attributable source without adding worker identity or assignment records. Each coverage change records prior/new count, actor, timestamp, and controlled source/reason.

Initial coverage-loss reasons include:

- `worker_no_show`
- `worker_withdrew`
- `coverage_record_corrected`
- `other_approved`

These events are operational evidence, not automatic disciplinary findings, worker eligibility decisions, or future ranking inputs.

When a worker-assignment model is separately approved, active assignments become the authoritative evidence for coverage. Independent manual state and assignment records must not be allowed to disagree; the migration and transition contract must preserve the audit history established here.

## Exceptional reopening

`closed` and `cancelled` requests, and `completed`, `unfulfilled`, and `cancelled` shifts, are terminal during ordinary Operations Staff work.

An Owner or delegated Manager may exceptionally reopen a mistakenly terminalized record subject to all of the following:

1. Reopening requires a controlled reason, actor, timestamp, and relation to the terminal event.
2. The target state is always `pending_review`, never `open` or a coverage state.
3. Current validation and review must run again.
4. Reopening a request does not reopen any shift automatically.
5. A terminal shift may reopen only after its parent request is nonterminal.
6. Prior terminal and coverage events remain append-only.
7. Materially new demand is represented by a new linked request or shift, not by recycling the historical record.

Role permissions and break-glass policy are controlled by `docs/planning/phase-1-staff-permission-matrix.md`. Implementations must not broaden exceptional reopening beyond the Owner/explicitly delegated Manager boundary accepted here.

## Cross-record invariants

1. A shift can enter an active coverage state only while its parent request is `open`.
2. A request can enter `closed` only when every child shift is terminal.
3. Request cancellation transitions every nonterminal child shift to `cancelled` through separately attributable child events; no silent cascade or destructive rewrite is allowed.
4. Reopening a request does not infer renewed demand or coverage and does not reopen children.
5. Request status does not summarize away shift outcomes. A closed request may contain completed, unfulfilled, and cancelled shifts.
6. Coverage count and active coverage state must agree transactionally.
7. Transition commands must check the expected current state/version and reject stale or forbidden transitions.
8. Corrections append attributable events; audit history is not rewritten. Current-state/history authority, expected-version/idempotency behavior, atomic multi-record commands, and correction-of-correction are controlled by `docs/planning/phase-1-correction-audit-event-contract.md`.

## Required transition evidence

Every transition records:

- entity type and ID;
- previous and new state;
- actor type and actor ID;
- authoritative timestamp;
- controlled reason where required;
- minimum-necessary restricted explanation where required;
- prior/new coverage count for coverage changes;
- relation to cancellation, correction, replacement, reopening, or prior event; and
- the record version used to reject stale updates.

The state change and required event commit in one transaction. Request cancellation creates separately attributable child events under one correlation ID; active-shift replacement commits old/new records and events all-or-nothing. An event-write failure rejects the transition.

## Explicitly separate decisions

The following remain unresolved and must not be inferred from this model:

- client validation of the accepted queue model's provisional business calendar, thresholds, and no-response policy;
- final field-by-state requiredness;
- named role assignments/delegations, exact-address recipients, and support/break-glass approvers under the accepted permission matrix;
- service-zone taxonomy;
- worker identity, assignment, referral, placement, attendance, discipline, and payment records;
- public/employer/worker visibility or notifications;
- production retention periods and export rules.

## Revisit triggers

Revisit this model when client workflow validation changes state terminology or operational meaning; before worker assignments become authoritative coverage evidence; before external notifications, public/employer updates, automated scheduling, attendance/discipline, payments, or legacy migration; or when a proposed transition cannot preserve the guards and audit evidence defined here.
