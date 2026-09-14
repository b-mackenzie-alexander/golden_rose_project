# Phase 1 Work-Queue Aging and Follow-Up Model

**Status:** Accepted Phase 1 planning source of truth
**Accepted:** 2026-08-03
**Decision owner:** Beatrice, technical delivery owner
**Policy posture:** Clock semantics and queue behavior are accepted. Numeric thresholds and no-response attempt rules are provisional review triggers requiring client validation before production; they are not SLAs, legal deadlines, or staff-performance standards.

## 2026-09-14 staff-intake amendment — narrow proposed supersession

**Status:** Proposed technical publication amendment under `../adr/ADR-0017-staff-intake-workflows.md`; docs-only approval is not implementation or live-use authorization. On accepted publication this section controls only the named staff-intake delta; the earlier baseline remains authoritative everywhere else.

The existing request `needs_information`, business-calendar aging, provisional no-response and ordinary request ownership rules remain unchanged. For new Intake only, `staff-intake-contract.md` §§2, 4 and 6 defines `needs_follow_up` as a review disposition requiring a reason, active scoped owner and RFC3339 due instant with explicit timezone. Shared intake queries do not inherit private ownership or request/shift queue lanes, counters or business-time thresholds.

Authorized reschedule, reassignment (mandatory reason) and reported contact attempts append history while preserving prior owner/due/actor/time. A contact attempt sends nothing and does not auto-review, finalize, close or change canonical demand. Passing due time derives overdue attention only; no domain write, messaging or automatic closure. A later current review supersedes the prior needs-follow-up disposition, retaining its history and independently displayed follow-up deadline; bookkeeping alone cannot assert reviewed completeness. Finalized snapshots remain immutable while attributable follow-up bookkeeping can continue. This narrowly supersedes unspecified intake-specific follow-up requiredness and worker-profile deferral only for the new intake surface; request no-response policy is not an intake closure policy.

## Decision

Phase 1 uses separate, transparent measures for record age, agency-controlled review time, employer follow-up, and shift coverage urgency. The work queue is a derived, authorization-scoped view over authoritative request, shift, ownership, follow-up, and audit records. It is not a separate status store.

No clock, deadline, review trigger, lane, or escalation changes lifecycle state, outcome, ownership, or assignment automatically.

## Clock model

### 1. Request record age

- Starts at attributable request creation.
- Uses continuous calendar time and never pauses or resets.
- Remains historically calculable after the request becomes terminal.
- Supports transparency and descriptive reporting; it is not a staff-performance measure by itself.

### 2. Request review-service clock

- Starts when a request enters `pending_review`.
- Counts only approved agency business hours.
- Pauses while the request is in `needs_information`.
- Resumes when the request returns to `pending_review`.
- Stops when the request enters `open`, `closed`, or `cancelled`.
- Accumulates across multiple review intervals without erasing earlier time.

The clock measures agency-controlled intake/review time. It does not include time awaiting employer clarification.

### 3. Follow-up deadline

- Entering `needs_information` requires `next_follow_up_at` and an accountable follow-up owner.
- The due instant is explicit and stored with timezone-safe semantics.
- Business-day intervals use the versioned agency business calendar.
- Every attempt is an attributable event.
- A new due instant does not reset request age, erase prior deadlines, or hide missed deadlines.
- An overdue follow-up raises queue attention only; it does not automatically close, cancel, reassign, or contact anyone.

### 4. Shift coverage-service clock and urgency

- Coverage-service time starts when a shift enters `open_uncovered`.
- It continues in `partially_covered`.
- It pauses in `covered`.
- It resumes when coverage reverses to partial or uncovered.
- It stops in `completed`, `unfulfilled`, or `cancelled`.
- It uses continuous elapsed time because coverage risk continues outside office hours.
- Operational urgency is derived primarily from `starts_at - now`, not record creation age.

A coverage loss or no-show recalculates urgency immediately. Time passing never chooses a terminal shift outcome.

## Time-accounting basis

The accepted hybrid model is:

| Measure | Time basis |
|---|---|
| Request record age | Continuous elapsed calendar time |
| Request review-service time | Approved agency business hours |
| Follow-up business-day intervals | Versioned agency business calendar |
| Follow-up due/overdue comparison | Actual due instant |
| Shift coverage-service time | Continuous elapsed time |
| Time to shift start | Continuous elapsed time in relation to the shift's timezone-aware `starts_at` |
| Audit events | UTC instant, displayed in the relevant approved timezone |

The business calendar must be versioned and effective-dated. It includes approved timezone, working weekdays, daily intervals, holidays/closures, and exceptional openings. Until the client validates this calendar, the product may show truthful wall-clock age and time-to-shift but must not claim an agency SLA breach.

## Provisional configurable review triggers

These values are accepted for deterministic planning, UI behavior, and synthetic tests. They remain configurable, versioned review triggers—not contractual or compliance commitments.

### Request review

| Agency-controlled review time | Indicator |
|---|---|
| Less than 8 business hours | `normal` |
| 8 through 16 business hours | `attention` |
| More than 16 business hours | `overdue` |

### Follow-up

| Condition | Indicator |
|---|---|
| More than 4 business hours before `next_follow_up_at` | `scheduled` |
| Within 4 business hours of `next_follow_up_at` | `due_soon` |
| Due instant has passed | `overdue` |
| More than 8 approved business hours overdue | `escalated` |

### Uncovered or partially covered shift

| Time remaining until `starts_at` | Indicator |
|---|---|
| More than 72 continuous hours | `normal` |
| More than 24 and at most 72 hours | `attention` |
| More than 4 and at most 24 hours | `urgent` |
| At most 4 hours and not past start | `critical` |
| Start instant has passed while shift remains nonterminal | `past_start_exception` |

A `covered` shift suppresses coverage urgency while preserving its scheduled time. A reversal to `partially_covered` or `open_uncovered` recalculates the indicator immediately. Any coverage loss within four hours of start is critical.

Changing configuration affects current indicators prospectively. It does not rewrite source timestamps, prior events, or the threshold version used for an earlier recorded escalation.

## Queue ownership

Phase 1 uses a shared authorized queue with an accountable current owner.

1. Authorized Operations Staff can see the shared queue within their approved record/field scope.
2. `assigned_staff_user_id` identifies the person accountable for the next request action; it does not create exclusive visibility or exclusive editing.
3. A new `pending_review` request may appear in the unassigned intake lane. Taking substantive action requires an attributable claim or assignment.
4. Entering `needs_information` requires an accountable follow-up owner and due instant.
5. A shift normally inherits the request owner for display, but may have a separately attributable coverage owner when operationally necessary.
6. Reassignment records previous owner, new owner, actor, time, and controlled reason.
7. Deactivated/unavailable staff must not leave hidden nonterminal work. Their items appear in an authorized reassignment view; policy determines who performs reassignment.
8. Escalation increases visibility and priority but does not silently change ownership.
9. Manager and Owner oversight does not authorize bypassing record/field restrictions.
10. Platform Administrator status grants no queue or operational-data access by itself.

## Follow-up attempts and provisional no-response safeguard

Each follow-up attempt records:

- request ID;
- follow-up owner and acting staff identity;
- authoritative time;
- approved contact method;
- controlled outcome;
- minimum-necessary restricted note where needed;
- next follow-up due instant when the request remains in `needs_information`; and
- relation to the prior follow-up/needs-information event.

Initial controlled outcomes:

- `no_answer`
- `voicemail_left`
- `email_sent`
- `callback_requested`
- `contact_reached_information_pending`
- `invalid_contact_information`
- `information_received`
- `other_approved`

`information_received` supports an attributable return to `pending_review`; it does not reset historical age. Invalid contact information creates an explicit correction exception and cannot be counted repeatedly as successful contact attempts.

Provisional `closed / no_response` eligibility requires:

1. At least three attributable contact attempts.
2. Attempts across at least three separate approved business days.
3. Up to two approved contact methods when both are available and operationally permitted.
4. No duplicative contact merely to satisfy the count.
5. Owner or delegated Manager approval of the final close transition until client policy is validated.
6. A deliberate transition; no automatic closure.

This model does not authorize external messaging automation, a messaging vendor, marketing contact, or unapproved communication channels.

## Deterministic queue lanes

The queue uses transparent lanes rather than an opaque aggregate priority score.

### Lane 1 — Exceptions

- Past-start nonterminal shifts.
- Invalid contact information requiring correction.
- Stale/conflicting transition, ownership, or data-integrity exceptions.

### Lane 2 — Critical and urgent shift coverage

- Uncovered/partial shifts at four hours or less.
- Uncovered/partial shifts more than four and at most 24 hours away.
- Newly lost coverage, ordered by nearest start instant.

### Lane 3 — Follow-up

- Escalated overdue.
- Overdue.
- Due soon.
- Scheduled.

### Lane 4 — Request review

- Overdue review time.
- Attention.
- Normal.
- Unassigned intake remains explicitly visible within this lane.

### Lane 5 — Future shift coverage

- Uncovered/partial shifts more than 24 hours away, ordered by urgency and start instant.

Within a lane, deterministic ordering uses indicator severity, due/start instant, oldest actionable event, then stable record ID. Authorization is applied before results are displayed or counted. Approved filters may include service zone and owner, but default views must not hide authorized unassigned or escalated work. Zone-assignment status is an independent classification flag/filter: `zone_unassigned` remains visible without replacing or outranking the record's service-work lane, so an urgent uncovered shift remains urgent while awaiting Owner classification.

These lanes prioritize agency work; they do not rank employers or workers, evaluate eligibility, or automate referral/hiring decisions.

## Escalation behavior

- Escalation creates a derived indicator and Manager/Owner oversight visibility.
- It does not send external messages, reassign work, change lifecycle state, or alter outcomes automatically.
- Acknowledgment, reassignment, follow-up, and state transition are separate attributable actions.
- Repeated or unresolved escalation history remains available for operational review, subject to approved retention and access rules.
- Alert delivery channels and Cloud Tasks/Scheduler usage remain separately gated infrastructure/integration decisions.

## Required evidence and consistency

Queue calculations must be reproducible from authoritative timestamps, state events, ownership records, business-calendar version, threshold version, and follow-up events. Implementations must:

- use timezone-aware instants and tested daylight-saving behavior;
- preserve elapsed intervals across pause/resume cycles;
- reject negative/impossible intervals and stale updates;
- apply authorization before search, filtering, counts, and exports;
- distinguish unavailable or incomplete scheduling data from zero/normal values;
- show which clock or deadline caused an indicator; and
- avoid storing manually editable duplicate queue status when it can be derived.

Attributable ownership, follow-up, transition, acknowledgment, correction, and configuration actions follow `docs/planning/phase-1-correction-audit-event-contract.md`. Time-driven indicator changes do not create domain events by themselves. A stale/missing queue projection is an explicit unavailable/rebuild state, never a false empty queue.

## Explicitly separate decisions

The following remain unresolved and must not be inferred from this model:

- client-approved business hours, holidays, closures, thresholds, and final no-response policy;
- final field-by-state requiredness and permission matrix;
- exact-address reveal permissions under the accepted calendar and service-zone contracts;
- external notifications, messaging vendor, Scheduler/Tasks implementation, and alert delivery;
- worker identity, assignment, attendance, discipline, ranking, eligibility, referral, placement, and payment;
- production retention, export, KPI, and staff-performance policy.

## Revisit triggers

Revisit this model when the client validates or changes operating hours, contact expectations, escalation ownership, no-response procedure, or shift urgency; before introducing external notifications, worker assignments, automated scheduling, staff-performance reporting, additional timezones, production retention/export, or legacy migration; or when a queue indicator cannot be reproduced from the authoritative records defined here.
