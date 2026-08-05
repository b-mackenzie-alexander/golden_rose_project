# ADR-0004: Phase 1 Employer Read and Search Boundary

**Status:** Proposed for planning review
**Date:** 2026-08-04

## Context and evidence posture

PR #8 established one synthetic/local staff command that creates a draft `Employer`, an actor/payload-bound `CommandReceipt`, and an append-only `employer.created` `AuditEvent` atomically in PostgreSQL. PR #9 qualified the owned `application` workflow and the merged governance policy now requires `enforce`, `check`, and `application` on both protected branches.

The Phase 1 product goal includes giving authorized agency staff a reliable way to create and find employer-demand records. The current tracer can create an Employer but intentionally exposes no retrieval route. Expanding directly into contacts, worksites, requests, or shifts would require affected field-requiredness and extension decisions that remain separately gated in the operational-discovery register.

Employer `display_name` may identify a person or household. It is accepted staff-facing operational data, but it should not be placed in URLs that are commonly retained by browser history, reverse-proxy access logs, monitoring systems, copied links, or intermediary caches.

## Decision

The next Phase 1 implementation slice is one synthetic/local, authorization-scoped Employer read/search tracer.

It adds:

1. `GET /api/staff/v1/employers/{employer_id}` for exact UUID detail retrieval;
2. `POST /api/staff/v1/employers/search` for bounded search using a validated JSON body;
3. one server-enforced named permission, `employer:read`, for both detail and search; this is the slice-level technical expression of the client-accepted matrix capability “View and search authorized employer-demand records,” not a new business-role grant;
4. authorization before any Employer lookup, search query, result derivation, or pagination operation;
5. literal, case-insensitive substring matching over a required NFC-normalized `display_name` fragment plus an optional controlled `employer_type` secondary filter;
6. rejection of missing-name and type-only searches so the two exhaustive Employer types cannot be paginated as a substitute for the prohibited list-all surface;
7. one application-owned NFC invariant applied before create-command payload fingerprinting/persistence and before search fingerprinting/query construction, so canonically equivalent accepted names remain findable regardless of API versus direct application invocation;
8. deterministic newest-first ordering by immutable `received_at DESC`, then `employer_id DESC`;
9. keyset pagination with a default page size of 25 and maximum of 50;
10. a versioned opaque cursor containing only the prior `received_at`, prior Employer UUID, and a SHA-256 fingerprint of normalized filters;
11. a filter-bound cursor: reuse with different filters is rejected rather than silently changing result meaning;
12. no total count and no unfiltered list-all operation;
13. minimized detail and search response fields with `Cache-Control: no-store`; and
14. safe, non-reflective errors for denial, absence, validation/cursor failure, persistence unavailability, and unexpected failures.

The search route uses POST because the potentially household-identifying name fragment belongs in a request body rather than a URL query string. It is a read operation: it requires no idempotency key, creates no `CommandReceipt`, and appends no `AuditEvent`. Request bodies and search text remain excluded from logs.

The cursor is not an authorization token and does not grant access. It need not be signed in this synthetic slice because a caller who fabricates a valid position gains no capability beyond the already authorized filtered search. Its structure is strictly validated, versioned, length bounded, and bound to the normalized filters. It contains no raw name or actor data, but its filter digest is derived from potentially identifying input and is not treated as anonymous; the entire cursor remains sensitive transient request data excluded from logs, errors, metrics, analytics, and audit events. A future record-scope model must still apply authorization before rows are selected or returned.

## Response boundary

Exact detail returns only the currently accepted safe Employer representation:

- `employer_id`;
- `employer_type`;
- `display_name`;
- `lifecycle_status`;
- `source_channel`;
- `version`;
- `received_at`; and
- `created_at`.

Search items return only:

- `employer_id`;
- `employer_type`;
- `display_name`;
- `lifecycle_status`;
- `received_at`; and
- `version`.

Neither route returns `created_by`, command receipts, request fingerprints, event payloads, actor internals, raw SQL, database configuration, or cursor internals. Search returns `items` and an optional `next_cursor`, but no total count, export, download, or audit-history surface.

## Error and privacy boundary

- Principals without `employer:read` receive the existing safe `403` `forbidden` problem before an Employer query executes.
- An authorized exact lookup of an absent UUID receives safe `404 employer_not_found`.
- Body, filter, page-size, and cursor violations receive the existing safe `422` `request-validation` problem without reflecting submitted values.
- Known database availability failures receive the existing safe `503` `service-unavailable` problem.
- Unexpected failures receive the existing safe `500` `internal-error` problem.
- Successful detail/search responses and applicable problem responses include `Cache-Control: no-store`.
- Error bodies and logs do not expose names, cursors, SQL, database URLs, actor details, or exception text.
- Role labels and request-supplied actor/role/permission headers never grant authority.

## Persistence and projection boundary

The slice queries the current authoritative `employers` table directly through concrete persistence functions. It does not create a competing search store or materialized projection. Search performs a bounded `page_size + 1` query to derive `next_cursor`; it does not compute a total count.

No migration, PostgreSQL extension, trigram index, dependency, or generic repository abstraction is added. Correctness is qualified on PostgreSQL 16. A measured performance problem, approved data volume, query plan, or explicit latency budget may justify a later reviewed index or projection. Implementation must stop and return to planning if the accepted behavior cannot be met without a schema/dependency expansion.

Ordinary authorized reads, searches, and projection rendering do not produce domain audit events under the accepted correction/audit contract. Tests must prove that read/search operations create no Employer, `CommandReceipt`, or `AuditEvent` rows.

## Consequences and constraints

- The first usable backend surface can create, retrieve, and find draft Employers without adding unresolved canonical entities.
- The slice establishes reusable authorization-before-read and privacy-safe search patterns without claiming real staff identity, record-scope authorization, frontend readiness, or production data admission.
- Search is deliberately bounded and transparent; it is not ranking, matching, recommendation, fuzzy inference, or relevance scoring.
- Results are current truth. Concurrent new inserts may appear before an existing cursor boundary on a later fresh search, but cursor continuation remains duplicate-free for immutable `received_at`/ID ordering. No snapshot-isolation promise is made across separate HTTP requests.
- Exact UUID lookup and filtered search do not authorize exports or unrestricted bulk extraction.
- The existing create command and its atomic/audit/idempotency behavior must remain unchanged.

## Explicit non-scope

- Employer mutation, draft revision, submission, correction, cancellation, or lifecycle expansion.
- EmployerContact, Worksite, StaffingRequest, ShiftNeed, RequestRequirement, zones, CDTAs, maps, queues, calendars, or audit timeline retrieval.
- Frontend, real authentication, MFA, sessions, identity-provider integration, record-level tenancy, public routes, cloud deployment, live/client data, legacy import, geocoding, documents, notifications, exports, or legal behavior.
- Fuzzy matching, full-text search, relevance ranking, suggestions, automatic decisions, or worker comparison.

## Alternatives considered

- **GET search with query parameters:** rejected for this slice because household/person-identifying name fragments would be more likely to appear in URL-oriented logs, history, copied links, and monitoring.
- **Exact detail only:** rejected because it would not satisfy the accepted bounded “create and find” increment.
- **Unfiltered recent-Employer list or type-only search:** deferred because the two exhaustive Employer types could otherwise be paginated to reconstruct the prohibited list-all surface. This slice requires a bounded name fragment and permits type only as a secondary filter.
- **Separate detail and search permissions:** rejected because the accepted Phase 1 matrix grants the same bounded view/search capability to operational roles; no current policy difference justifies extra permission complexity.
- **Total counts:** deferred because they are not required for this finding workflow and would enlarge query/aggregation behavior.
- **Trigram/full-text index or separate projection:** deferred until measured volume and latency evidence justify schema or operational complexity.
- **Signed cursor:** deferred because the cursor is sensitive transient but non-authoritative, contains no raw Employer/search field value, and grants no authority; strict validation, independent permission enforcement, and filter binding are sufficient for this synthetic boundary.

## Approval, handoff, and revisit triggers

This ADR becomes accepted only after the planning packet is reviewed and merged into `develop`. A fresh coding session may implement only the merged plan under strict RED → GREEN → REFACTOR sequencing. A separate review session must independently assess authorization-before-query, search privacy, cursor/filter correctness, PostgreSQL semantics, error/log redaction, route ordering, regression safety, and scope.

Revisit before adding record-scope/tenant authorization, unfiltered browsing, counts/aggregates, exports, fuzzy/full-text/relevance search, new Employer fields or mutations, contact/worksite/request/shift search, audit history retrieval, real identity, frontend/public access, live data, schema/index changes, or any cursor that carries raw sensitive fields, authoritative state, or authorization semantics.
