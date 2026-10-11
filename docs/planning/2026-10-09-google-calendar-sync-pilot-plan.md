# Google Calendar Sync Pilot Plan

**Status:** Accepted pilot investigation and source-planning direction
**Accepted:** 2026-10-09
**Decision owner:** Beatrice, technical delivery owner
**Scope:** Two-PR path for a Google Calendar migration helper: first source documentation/contract, then a bounded pilot MVP. No cloud mutation, OAuth client activation, secret creation, token storage, live webhook, deployment, automatic record creation, or two-way sync is authorized by this document.

**Implementation note, 2026-10-11:** The functional follow-up branch implements source support for a one-time OAuth import bridge rather than persistent background sync. The application can enable the staff `Connect Google Calendar` action only when OAuth settings are configured, validate a signed short-lived `state` value on callback, exchange the authorization code server-side, fetch a bounded upcoming event window using the narrow Calendar Events read-only scope, and stage returned events as external review candidates. It does not persist access tokens or refresh tokens, expose webhooks, schedule background refresh, write back to Google Calendar, or activate any provider-side OAuth client/configuration by itself.

## Context

The controlled staff pilot is live, and the owner is beginning to work through real workflows. She asked whether syncing between her Google account calendar and the dashboard calendar could make migration easier.

The existing Golden Rose calendar is intentionally not a separate system of record. `docs/planning/phase-1-calendar-coverage-semantics.md` defines it as an authorization-scoped projection derived from authoritative `StaffingRequest` and `ShiftNeed` records. The current implementation also keeps browser-local personal calendar notes separate from request-derived operational shifts, and company-calendar mutation remains disabled unless a later permissioned write path is designed.

This plan accepts the owner request as a real pilot-discovery need, while preserving the current trust boundaries:

- PostgreSQL domain rows and append-only audit/history remain authoritative for Golden Rose operations.
- Google Calendar data may help staff migrate and compare existing schedules, but it must not automatically create, overwrite, rank, match, refer, assign, place, or validate Golden Rose records.
- Staff review remains required before any Google Calendar event affects operational data.
- Exact locations, worker identities, contact data, and restricted free text remain governed by the existing field and permission model.

## Decision

Golden Rose should pursue Google Calendar support in two protected PR phases:

1. **Planning/source contract PR:** document the integration boundary, OAuth/data custody posture, MVP behavior, implementation acceptance criteria, and stop conditions. This PR performs no runtime integration and no cloud/provider mutation.
2. **Pilot MVP implementation PR:** implement a read-only Google Calendar import/review flow for one connected staff account or owner account, with imported events staged as review candidates. Staff explicitly decide whether to ignore, link, or manually convert each candidate into Golden Rose draft work.

True bidirectional sync is deferred. It requires a separate decision because it introduces delete/edit conflict handling, recurrence semantics, stale-version behavior, webhook or scheduler operation, refresh-token custody, OAuth verification posture, audit requirements, and staff lifecycle/deprovisioning controls.

## Pilot MVP Product Shape

The first implemented feature should be a **Google Calendar migration assistant**, not a permanent mirror.

Staff flow:

1. A signed-in, authorized staff member opens the staff calendar.
2. The page offers a clearly bounded `Connect Google Calendar` action.
3. The staff member grants only the minimum Google Calendar scope needed for the selected import mode.
4. Golden Rose shows connection status and lets staff choose an import date range.
5. Imported Google events appear in a separate `Google Calendar candidates` review lane.
6. Staff can:
   - ignore the candidate;
   - mark it already represented in Golden Rose;
   - link it to an existing Golden Rose request or shift when an exact authorized record is selected;
   - use it as a draft starter for a Golden Rose request, shift, or follow-up, with staff review before save.

Default behavior:

- Nothing imported from Google becomes operational truth automatically.
- Event location is hidden or minimized unless the current staff permission would allow the equivalent exact-address field in Golden Rose.
- Google event descriptions, attendees, conference links, attachments, private notes, and reminders are not imported in the first MVP.
- Event title, start/end time, timezone, calendar identifier alias, source event stable ID, and source update timestamp are enough for deduplication and review.
- Imported candidate text must be visibly labeled as external and unverified.
- English and Spanish UI copy, errors, and empty states ship together.

## Non-Goals

The MVP must not include:

- two-way synchronization;
- automatic creation of `StaffingRequest`, `ShiftNeed`, worker assignment, referral, placement, eligibility, ranking, or matching records;
- worker conflict detection or availability inference;
- Google Calendar event deletion or update from Golden Rose;
- importing attendee lists, event descriptions, attachments, Meet links, reminders, private notes, or unrestricted location detail;
- external calendar webhooks in the first implementation unless separately approved after deployment-surface review;
- support for recurrence expansion beyond displaying individual instances returned by the Google Calendar API for the chosen date range;
- external calendar export, ICS feeds, mobile-device integration, or notification delivery;
- provider-side Google account recovery, factor reset, forced logout, token revocation, or session revocation claims.

## OAuth and Token Boundary

Calendar access is separate from Google staff sign-in.

The existing staff OIDC flow verifies identity for Golden Rose. Calendar import requires user authorization to access Google Calendar data. The implementation must keep these concepts separate in code, UI copy, records, and evidence.

Preferred authorization model for the MVP:

- Use Google OAuth authorization code flow when background import or refresh is needed.
- Store refresh tokens only in an encrypted, server-side table or approved secret-backed custody path.
- Encrypt token material at rest using an application-managed envelope or approved cloud secret/KMS mechanism before any live pilot use.
- Store only value-safe connection metadata in ordinary application rows.
- Never log access tokens, refresh tokens, authorization codes, raw provider payloads, raw calendar IDs, or raw private event content.
- Disconnecting a staff account must revoke or delete Golden Rose's stored token material and stop future imports.
- Suspending or deprovisioning a staff account must disable calendar import for that account.

Initial scopes should be selected by least privilege:

- For import-only review, prefer a read-only event scope over broad calendar management.
- For future one-way export, prefer a dedicated app-created or owned calendar/event scope rather than broad access to all calendars.
- Avoid the broad full-calendar scope unless a separately reviewed use case genuinely requires it.

Google documentation currently describes relevant constraints:

- Calendar scopes should be narrow and user-visible during consent: <https://developers.google.com/workspace/calendar/api/auth>
- Server-backed offline access requires OAuth authorization code flow and refresh-token custody: <https://developers.google.com/identity/protocols/oauth2/web-server>
- Sensitive-scope use may require OAuth verification, scope justification, and a demo: <https://developers.google.com/identity/protocols/oauth2/production-readiness/sensitive-scope-verification>

## Data Model Direction

The implementation PR should add explicit storage rather than overloading existing calendar projection rows:

- `staff_calendar_connections`
  - Golden Rose staff account ID;
  - provider name;
  - value-safe calendar label or alias;
  - encrypted token reference/material boundary;
  - granted scope set;
  - connection status;
  - connected/disconnected timestamps;
  - last sync status and error category.
- `external_calendar_imports`
  - connection ID;
  - provider event stable ID;
  - provider event updated timestamp;
  - event start/end/timezone;
  - minimized title;
  - optional minimized location review value if allowed;
  - import status: candidate, ignored, linked, draft_started, superseded, unavailable;
  - linked Golden Rose record reference when staff explicitly creates one;
  - audit/correlation metadata.
- `AuditEvent` or equivalent application history for connect, disconnect, import run, candidate disposition, link, and draft-start decisions.

Candidate rows are migration/review evidence, not operational schedule truth.

## Sync Mechanics

For the MVP, prefer staff-triggered or scheduled polling over Google push notifications.

Rationale:

- Google incremental sync tokens support efficient polling, but invalid tokens can require a full resync.
- Google push notifications require an HTTPS callback and channel renewal. They also do not include the changed event body, so the application still needs a follow-up API call.
- A webhook creates a new public/provider callback surface and operational renewal duty, which is more than the first pilot needs.

The first implementation should:

- perform a bounded initial import by date range;
- store enough source event identity to deduplicate;
- support a manual `Refresh from Google` action;
- surface stale/unavailable/permission-denied states honestly;
- avoid pretending an import failure means the calendar is empty;
- preserve exact retry/idempotency behavior for import runs and candidate dispositions.

Google documentation currently describes incremental sync and push behavior here:

- Incremental sync tokens and `410` full-resync behavior: <https://developers.google.com/workspace/calendar/api/guides/sync>
- Push notifications, HTTPS callbacks, expiration, renewal, and empty notification bodies: <https://developers.google.com/workspace/calendar/api/guides/push>

## Authorization and Privacy Requirements

The backend must enforce all calendar import permissions before returning connection status, candidate counts, event summaries, exact source detail, or candidate actions.

Required controls:

- Only signed-in named staff may connect or import.
- A separate permission should guard Google Calendar connection/import management.
- Imported candidates must be staff-account attributable.
- Candidate detail returned to the browser must be no-store and authorization-scoped.
- Exact locations must not appear in month, aggregate, external export, or broad summary surfaces.
- Candidate search and filter behavior must not expose hidden event detail through counts or labels.
- Imported Google text remains unverified discovery evidence.
- Calendar candidates must not be used as protected-trait/proxy filters or comparison controls.

## Implementation Acceptance Criteria

The implementation PR is not ready until it has:

- backend tests for OAuth callback state validation, missing/denied scopes, expired/revoked token handling, disconnect behavior, duplicate import suppression, import-range bounds, candidate disposition idempotency, and staff authorization failure;
- frontend tests for connection status, import-range controls, candidate review actions, bilingual labels, error states, and no automatic operational-record creation;
- tests showing imported candidates stay separate from request-derived shift projections and browser-local personal calendar entries;
- no-store headers on staff calendar connection/import/candidate routes;
- redacted/value-safe diagnostics for provider failures;
- migration tests or Alembic head checks for the new tables;
- updated `CURRENT_WORK.md`, `ROADMAP.md`, and `NOTES.md`;
- `git diff --check` and a redacted secret scan before publication.

Browser/manual acceptance before staff reliance should include:

- owner/staff connecting a test Google Calendar account;
- importing a narrow date range;
- verifying candidate labels and boundaries in English and Spanish;
- creating or linking a draft only after explicit staff action;
- disconnecting the calendar and confirming future refresh is disabled;
- checking that raw Google payloads and token material are absent from visible logs/docs.

## Stop Conditions

Stop and return to planning if implementation requires any of the following:

- broad calendar scopes when a narrower scope can satisfy the MVP;
- importing private event descriptions, attendees, attachments, Meet links, reminders, or unrestricted exact locations;
- background refresh-token storage without an approved encryption/custody design;
- public webhook exposure or Cloud Scheduler/worker activation without a separate deployment-surface review;
- automatic matching, ranking, eligibility, referral, assignment, placement, or worker-conflict inference;
- treating Google Calendar as authoritative operational truth;
- changing production/client-owned transition, export/import, support, repository stewardship, or provider-side recovery/session-revocation boundaries.

## Next Executable Action

Land this planning/source contract as PR 1. After it merges, create PR 2 from protected `develop` to implement the pilot MVP locally, with migrations and tests, but still no cloud/OAuth-client/provider mutation until a separately approved deployment/configuration packet exists.
