# Phase 1 Correction and Audit-Event Contract

**Status:** Accepted Phase 1 planning source of truth
**Accepted:** 2026-08-04
**Decision owner:** Beatrice, technical delivery owner
**Scope:** Phase 1 canonical operational records, material corrections, attributable events, restricted historical values, and derived-view consistency

## Decision

PostgreSQL domain records are the authoritative current operational state. `AuditEvent` is the append-only authoritative history of material actions. Calendar, queue, map, dashboard, reporting, and search surfaces are authorization-scoped derivative projections; ordinary application/security logs are observability evidence, not competing operational truth.

Phase 1 is not a full event-sourced system. Current domain rows are not reconstructed solely by replaying every audit event, and the system does not retain every keystroke or draft value. Domain changes and required audit events are committed consistently through one reviewed command boundary.

This contract is accepted for Phase 1 implementation. Production live-data admission still requires approved retention/disposal periods, restricted historical-value access, production data classification, tested backup/restore, and the separately named production-readiness controls. This contract does not authorize deployment, live data, legacy/live-data import or migration, exports, or legal/compliance claims. It does authorize reviewed migration-managed schema evolution for synthetic/local implementation, provided migrations preserve current truth and append-only audit history under this contract.

## Correction vocabulary

| Operation | Meaning | Required behavior |
|---|---|---|
| Draft revision | Authorized staff changes incomplete information before submission/review | Update current draft with attribution and optimistic versioning; prior draft values need not be retained after every save |
| Correction | A previously recorded fact was incorrect when recorded | Update current truth and append a linked correction event preserving necessary prior/new meaning |
| Subsequent change | The prior fact was accurate, but circumstances later changed | Append an ordinary change event with its effective time; do not characterize the earlier fact as erroneous |
| Replacement or supersession | The old record must remain historically intact while a new record takes over | Create a linked replacement and close, cancel, or supersede the old record through its governed workflow |

Examples:

- A typo fixed before draft submission is a draft revision.
- An incorrect phone number discovered after submission is a correction.
- An employer later changing its phone number is a subsequent change.
- Moving an active shift to a new interval is a linked replacement, not an overwrite.
- Coverage loss is a coverage-change event unless the recorded count itself was incorrect.
- An incorrect terminal outcome uses exceptional reopen-to-review; it is never directly rewritten.

## Current state, history, and projections

1. Domain tables hold current operational state.
2. Audit events preserve material history.
3. Audit events are structured application records and remain separate from ordinary operational/security logs.
4. Logs must not duplicate unrestricted audit payloads or become a second source of business truth.
5. Derived projections never write authoritative fields back into domain records.
6. A stale, missing, or failed projection is shown as stale/unavailable or rebuilt; it must not create a false empty or zero state.
7. Audit history explains material actions, but Phase 1 does not promise full database reconstruction from events alone.

## Actions that require audit events

The following always produce an event:

- canonical-record creation;
- submission for review;
- every request/shift lifecycle transition;
- coverage-count or coverage-state changes;
- completed, unfulfilled, closed, or cancelled outcomes;
- terminal reopening;
- submitted/reviewed/open/terminal record correction;
- schedule correction, cancellation, replacement, or supersession;
- request, follow-up, or coverage ownership assignment/reassignment;
- follow-up attempts and due-instant changes;
- requirement review, acceptance, rejection, or correction;
- exact-worksite address correction after submission or operational reliance;
- CDTA derivation confirmation/correction;
- service-zone catalog, composition, membership, and operational-zone changes;
- map-dataset activation/retirement;
- role, permission, and delegation changes;
- MFA/recovery, suspension, reactivation, and deprovisioning operations;
- break-glass approval, activation, expiration/revocation, and review;
- policy-driven retention/disposal actions when approved; and
- correction or supersession of an earlier audit event.

The following do not create domain audit events by themselves:

- ordinary authorized record reads;
- clock advancement or a derived urgency change caused only by time;
- calendar/map/dashboard rendering;
- ordinary search/filter use; or
- successful projection refresh.

Exact-address reveal, restricted audit-payload reveal, and break-glass operational-data access remain attributable restricted-access events. Authentication telemetry belongs in protected identity/security telemetry; material account-security actions also produce security audit events.

## Draft behavior

Before submission:

- authorized staff may revise draft fields without preserving every prior value;
- each persisted draft records `created_by`, `created_at`, `updated_by`, `updated_at`, and an incrementing record version;
- creation, assignment, submission, cancellation, and security-sensitive actions remain audited;
- autosave does not create an event per keystroke; and
- a persisted draft save may be coalesced as one record update.

When a record enters `pending_review`, later material changes follow the correction rules below.

## Material-correction threshold

After submission, an event is mandatory when changing:

- employer, contact, or worksite identity or relationships;
- exact address or contact data;
- request type, role title, duties, compensation, or employment arrangement;
- requested start date;
- shift start/end, timezone, or requested-worker count;
- requirements, source text, or review disposition;
- lifecycle state, coverage state/count, terminal outcome, or controlled reason;
- ownership or follow-up deadlines;
- service zone, CDTA, map dataset, or classification meaning;
- reviewed/verified status;
- restricted-field visibility;
- roles, permissions, account state, recovery, or privileged access; or
- a fact already used in an operational decision, issued record, report, or external communication.

A local presentation preference that does not change authoritative meaning does not belong in domain audit history.

## Command, transaction, and consistency rules

Every material command passes through one reviewed application authority boundary.

For a single-record command:

1. Authorize actor, command, record, and fields.
2. Validate the expected record version.
3. Validate domain and cross-record invariants.
4. Update the authoritative domain record.
5. Append the required audit event.
6. Commit both in one database transaction.

If event insertion fails, the domain change fails. “Record updated but audit failed” is not an accepted state.

For multi-record commands:

- use one atomic transaction;
- append an event for every affected authoritative record;
- link events with one command/correlation ID;
- record parent/child and replacement relationships; and
- commit none of the command if any required update/event fails.

This controls request/child cancellation, active-shift replacement, operational-zone propagation to nonterminal shifts, permission/delegation changes with account effects, and any later governed bulk operation.

## Concurrency and retries

Every correction/material command requires:

- expected record version;
- unique command/idempotency key;
- server-generated event ID;
- transactional duplicate protection; and
- deterministic retry behavior.

A stale version is rejected rather than resolved by last-write-wins or silent field merging. The user must review current truth and resubmit.

Reusing an idempotency key with the same command payload returns the already committed result. Reusing it with a different payload is rejected as a conflict.

## Required audit-event envelope

Every `AuditEvent` includes:

- immutable `audit_event_id`;
- event-schema name/version;
- allowlisted `event_type`;
- `entity_type` and `entity_id`;
- per-entity event sequence;
- prior/new record version;
- actor type and stable actor ID;
- initiating staff actor when a system process executes on their behalf;
- server-generated UTC `occurred_at`;
- optional business `effective_at`;
- command/idempotency ID;
- multi-record correlation ID where applicable;
- controlled reason code where required;
- minimum-necessary reason text where necessary;
- safe source reference;
- related prior event/correction/cancellation/replacement/supersession IDs;
- structured changed-field set; and
- payload classification/access category.

Clients cannot choose event IDs, actor IDs, sequence numbers, record versions, or `occurred_at`. `effective_at` never replaces or backdates `occurred_at`.

## Changed-field evidence and sensitive values

Audit events do not store unrestricted full-row snapshots. They store changed fields and the minimum evidence needed to explain the action.

| Field class | Audit treatment |
|---|---|
| State, counts, dates, controlled reasons, ownership IDs, zone/CDTA/version IDs | Structured prior/new values |
| Ordinary reviewed operational fields | Prior/new values only for changed fields |
| Contact data, exact address, restricted free text | Prior/new values only in a separately restricted payload when needed to preserve relied-upon meaning |
| Draft values never submitted or relied upon | Prior values need not be retained |
| Passwords, tokens, MFA secrets, recovery codes, API keys, session identifiers | Never stored |
| Raw geocoding payloads or precise coordinates | Never stored under the accepted map contract |
| Whole domain rows or arbitrary unrestricted JSON blobs | Never stored |

Restricted event payloads:

- inherit at least the source field's authorization;
- are excluded from routine search, filters, counts, map/calendar/queue summaries, and logs;
- use the approved encryption-at-rest boundary;
- are not disclosed merely because the event envelope is visible;
- are unavailable to Platform Administrators outside approved break-glass access; and
- follow the approved retention/disposal policy once established.

## Reasons and source references

A controlled reason is required for:

- post-submission factual correction;
- cancellation/closure;
- active rescheduling/replacement;
- coverage loss/correction;
- terminal reopening;
- historical zone/CDTA correction;
- reassignment;
- permission/delegation changes;
- recovery/break-glass actions;
- correction of an earlier event; and
- retention/disposal actions.

Use allowlisted codes first. `other_approved` requires concise restricted text.

Reason/source data must not include secrets, credentials, unnecessary personal data, discriminatory/proxy criteria, raw messages/documents, unrestricted local paths, or unsupported disciplinary claims. Source references use controlled types and safe identifiers rather than arbitrary URLs or uploaded content.

## Correcting an audit event

Audit events are never edited or deleted through application workflows.

When an event carries incorrect business meaning:

1. Append `audit_event_corrected` or a domain-specific correction event.
2. Link it to the incorrect event.
3. Record correction reason and actor.
4. Preserve the original event.
5. Update current domain truth only if it is also incorrect.
6. Clearly mark the prior event as corrected/superseded in authorized timelines.

A structurally malformed event caused by a defect is preserved. The system records an integrity/correction event where possible, opens a security/data-integrity incident, and repairs the application/read model rather than rewriting the row.

## Deletion, retention, and disposal

Phase 1 exposes no ordinary hard-delete command.

- Draft mistakes use cancellation/abandonment behavior.
- Submitted, reviewed, referenced, cancelled, replaced, and terminal records remain attributable.
- Owner and Platform Administrator cannot directly update/delete audit rows.
- Retention or legally required disposal uses a separately approved policy-driven process.
- When a sensitive payload is disposed of and retention of the non-sensitive envelope is permitted, preserve disposal time, policy/version, approving/executing authority, and the fact that the payload is unavailable.
- The system does not claim perpetual retention before client/counsel policy is approved.

Production live-data admission remains blocked until retention/disposal periods for event envelopes and restricted prior/new values are approved.

## Audit authorization and presentation

- Apply authorization before events, counts, filters, summaries, or payloads are returned.
- Operations Staff may see ordinary timelines for records in authorized scope.
- Restricted historical values require the corresponding restricted-field permission.
- Owner/Manager labels do not bypass field restrictions.
- Platform Administrator has no standing operational-audit access.
- Audit export remains disabled in Phase 1.
- Routine timelines show event type, actor, time, safe reason label, and correction/replacement relationship.
- Sensitive reasons and protected prior/new values require deliberate authorized reveal.
- Corrected records show a visible correction indicator without disclosing restricted detail.
- Current truth and historical events remain visually/semantically distinct.

## Storage and tamper-resistance posture

Phase 1 uses database-enforced append-only application semantics:

- the application runtime may insert approved events but cannot update/delete them;
- all domain writes/event inserts use the reviewed command boundary;
- event IDs and per-entity sequences are unique;
- schema constraints reject malformed envelopes;
- migrations/retention operations use separate privileged paths and independent change evidence;
- backup/restore includes audit history;
- attempted audit mutation/bypass is detected and alerted; and
- Platform Administrators perform no routine direct-database correction.

This is controlled append-only history, not a claim of cryptographic immutability, legal WORM storage, or immunity from every cloud-account owner. Cryptographic chaining/external immutable archival is deferred unless legal, insurance, client, or threat-model requirements justify it.

## Derived projection behavior

Queue, calendar, map, dashboard, reporting, and search layers:

- derive from current authorized domain records and required event/timestamp history;
- are disposable/rebuildable;
- cannot alter authoritative records;
- expose stale/unavailable/error states honestly;
- do not silently omit records because a projection is incomplete; and
- do not widen access to restricted event payloads.

Projection failure after a committed domain/event transaction does not undo authoritative truth; it creates a visible rebuild/recovery condition.

## Implementation verification

Tests must prove:

- draft editing does not create per-keystroke events;
- submitted material corrections always append an event;
- event failure rolls back domain changes;
- multi-record commands are all-or-nothing;
- stale versions and conflicting idempotency reuse are rejected;
- identical retries are idempotent;
- duplicate command/event IDs are rejected;
- domain invariants remain transactional;
- correction-of-correction preserves the original event;
- application paths cannot update/delete audit rows;
- no ordinary hard-delete path exists;
- protected values require field-level authorization;
- secrets, MFA material, coordinates, and raw geocoder payloads never enter events/logs;
- Platform Administrator cannot browse operational history;
- stale/missing projections do not create false empty results; and
- backup/restore preserves audit history.

## Separate live-data decisions

The baseline is accepted. Before production live-data admission, client/counsel approval must establish:

1. Retention periods for event envelopes and restricted prior/new values.
2. Whether historical exact-address/contact values require earlier disposal.
3. Final reason-code terminology.
4. Named roles/people allowed to reveal restricted historical values.
5. Any stronger immutable archival required for future legal/financial records.
6. Legally required deletion/anonymization procedure.

## Revisit triggers

Revisit before production live-data admission; legacy migration/import; exports; documents; worker/assignment/referral/payment records; bulk operations; external messaging; offline/mobile writes; legal/financial record issuance; cryptographic archival; changed retention/deletion duties; or any workflow that cannot atomically preserve current truth, material history, authorization, and projection consistency.