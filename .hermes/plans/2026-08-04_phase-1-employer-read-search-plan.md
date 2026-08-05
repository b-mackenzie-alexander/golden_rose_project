# Phase 1 Employer Detail + Bounded Search Implementation Plan

> **For Hermes:** Execute this plan only from a fresh coding session after ADR-0004 and this planning packet are reviewed and merged into `develop`. Use the `plan-to-code-handoff`, `test-driven-development`, and `python-project-test-environment` skills. Keep every production behavior in a real RED → GREEN → REFACTOR cycle. Stop before opening a pull request so a separate review session can inspect the branch first.

**Status:** Proposed planning packet; implementation unauthorized until reviewed and merged

**Planning baseline:** `develop` at `80f45053514c9854f9a100905028944eaf55fe9c` (merged PR #9)

**Proposed implementation branch after plan merge:** `feat/staff-employer-read-search` from current `origin/develop`

**Goal:** Let an authorized synthetic staff principal retrieve one current Employer and perform a privacy-conscious, bounded filtered search without introducing new domain entities, mutations, audit events, schema changes, or live-data behavior.

**Architecture:** Add two read-only application queries behind one named `employer:read` permission. Query the authoritative PostgreSQL `employers` table through concrete persistence functions, use a POST body for sensitive name search, and paginate with a versioned filter-bound keyset cursor containing no name or actor data. Existing draft-Employer creation, command receipt, audit event, and error boundaries remain intact.

**Tech Stack:** Existing Python 3.12, uv/Hatchling, FastAPI/Pydantic v2, synchronous SQLAlchemy 2/psycopg 3, Alembic, PostgreSQL 16, pytest/HTTPX, Ruff, mypy, Bandit, pip-audit, CycloneDX, and the required GitHub `application` check. No dependency or migration is planned.

---

## 1. Approval and lane boundaries

### Planning-session deliverables

This planning session owns:

- ADR-0004;
- this exact implementation plan;
- alignment of controlling/living documents;
- independent read-only plan audits and remediation;
- a focused documentation branch for review.

It does **not** modify application code, start PostgreSQL or Uvicorn, apply infrastructure, admit live/client data, or begin the implementation branch.

### Coding-session deliverables

A fresh coding session must:

1. fetch/prune and prove the planning PR merged into current `origin/develop`;
2. create `feat/staff-employer-read-search` from that exact merged tip;
3. re-read ADR-0004, this plan, the permission matrix, field inventory, correction/audit contract, `SECURITY.md`, and current code/tests;
4. obtain explicit approval before starting the local PostgreSQL or API service;
5. execute Tasks 1–7 below in strict TDD order;
6. preserve the existing create command and no-live-data boundary;
7. run the complete local quality/security evidence set;
8. commit focused checkpoints and push the branch for independent review; and
9. stop without opening a PR.

### Review-session deliverables

A separate review session must independently inspect:

- authorization before any detail/search query;
- denial of role/header-based elevation;
- literal search and SQL wildcard escaping;
- cursor validation, filter binding, ordering, and pagination boundaries;
- minimized responses, no-store headers, and safe error/log behavior;
- no receipt/audit/domain writes from reads;
- route ordering and OpenAPI surface;
- PostgreSQL-only correctness and regression behavior;
- dependencies, CI, secret scan, and scope.

Any unresolved High/Blocker finding prevents PR readiness.

### Acceptance ownership and operational impact

- Beatrice owns technical plan acceptance, synthetic/local implementation acceptance, service-start approval, security evidence review, and authorization to hand the coding branch into independent review.
- The independent review lane supplies review evidence but does not replace Beatrice's acceptance decision. High/Blocker findings prevent PR readiness.
- The Golden Rose client remains owner of operational role policy and later staff-workflow/pilot acceptance. This backend tracer introduces no staff UI or production behavior, so terminology/ergonomics walkthroughs remain discover-during-implementation or later frontend/pilot work rather than blockers for this synthetic query slice.
- Counsel approval is not required for this internal synthetic read/search tracer because it adds no legal copy, fee, receipt, agreement, retention, eligibility, referral, or public behavior. Those gates remain unchanged.
- Support, training, incident response, monitoring, and production acceptance are unchanged because no deployment/live data is authorized. Local evidence is limited to safe response/error behavior, absence of sensitive logs, no read-side writes, service teardown, and the required CI/security checks.

## 2. Scope contract

### Included

- Named permission `employer:read`.
- Synthetic local/test principal receives existing create permission plus `employer:read`; production/synthetic startup remains prohibited.
- `GET /api/staff/v1/employers/{employer_id}`.
- `POST /api/staff/v1/employers/search` with a validated body.
- Current Employer detail response using already accepted fields.
- Minimized search result items.
- Literal case-insensitive substring match over normalized display name.
- Required bounded display-name fragment.
- Optional controlled employer-type secondary filter; type alone is rejected.
- Keyset pagination ordered by `received_at DESC`, `employer_id DESC`.
- Default page size 25, maximum 50.
- Versioned opaque filter-bound cursor with no name/actor data.
- `items` plus optional `next_cursor`; no total count.
- Safe 403/404/422/503/500 problem responses.
- `Cache-Control: no-store` for these successful reads and applicable problem responses.
- Real PostgreSQL integration evidence.
- Fictional synthetic fixtures only.
- Living-document and review-handoff updates.

### Explicit non-scope

- Employer update, draft revision, submission, correction, cancellation, lifecycle expansion, or delete.
- New `AuditEvent` type, generic event writer, or `CommandReceipt` change.
- EmployerContact, Worksite, StaffingRequest, ShiftNeed, RequestRequirement, service zone, CDTA, map, queue, calendar, dashboard, or audit-timeline retrieval.
- Unfiltered list-all/recent Employers, total counts, exports, downloads, reports, or bulk APIs.
- Fuzzy search, full-text search, trigram extension, relevance score, ranking, suggestions, worker comparison, or automatic decisions.
- New migration, index, PostgreSQL extension, dependency, cache, worker, queue, or search service.
- Frontend, real authentication, MFA, recovery, session, identity-provider, public route, cloud, live/client data, legacy import, geocoder, upload, notification, legal, fee, payment, or retention behavior.

### Stop-and-return conditions

Stop implementation and return to planning if the accepted behavior appears to require:

- a schema migration, index, extension, or new dependency;
- a new field, state, entity, mutation, permission split, count, export, or unfiltered browse operation;
- record-scope/tenant assumptions not present in the accepted matrix;
- logging a search term, cursor, request body, database URL, raw SQL, or actor internals;
- a signed/authoritative cursor or persistent server-side search state;
- weakening existing create authorization, atomicity, append-only, or idempotency behavior;
- starting an unapproved service or admitting non-synthetic data.

### Slice-specific data classification and fixture procedure

- Production-analog `display_name` is sensitive operational data because a household Employer may identify a person or residence-associated hiring party. The required search fragment inherits that classification.
- Employer UUID, lifecycle status, type, version, and timestamps are internal operational data. `created_by` is restricted actor data and is neither selected by the new minimized read records nor returned.
- A cursor is sensitive transient request data. Its filter fingerprint is derived from potentially identifying input and is **not** anonymized or safe to log merely because SHA-256 is one-way; the cursor/fingerprint remains excluded from logs, errors, metrics, analytics, and audit events.
- Development/test values are fictional synthetic fixtures only, using obvious forms such as `Synthetic Household 001` and `Synthetic Business 001`. Do not copy, transform, hash, or derive fixtures from client documents, legacy rows, real people, addresses, or operational systems.
- Tests use deterministic UUIDs/timestamps only where ordering assertions require them. Generated fixture files, database dumps, request logs, and test artifacts remain disposable and untracked.
- The slice does not change production/live-data admission. Real Employer records remain blocked until the separate classification, identity, environment, retention, support, and acceptance gates are satisfied.

## 3. API contract

### Detail endpoint

```text
GET /api/staff/v1/employers/{employer_id}
```

Rules:

- `employer_id` is a UUID path parameter.
- No idempotency key is required.
- `employer:read` is required before the lookup function executes.
- Authorized existing record: `200 OK`.
- Authorized absent record: safe `404 employer_not_found`.
- Denied principal: the existing safe `403` `forbidden` problem before persistence lookup.
- Success includes `Cache-Control: no-store`.

Response:

```json
{
  "employer_id": "11111111-1111-4111-8111-111111111111",
  "employer_type": "household",
  "display_name": "Synthetic Household 001",
  "lifecycle_status": "draft",
  "source_channel": "staff_entry",
  "version": 1,
  "received_at": "2026-08-05T03:00:00Z",
  "created_at": "2026-08-05T03:00:00Z"
}
```

Do not return `created_by`, receipt/event data, request fingerprint, actor internals, database state, or a `Location` header.

### Search endpoint

```text
POST /api/staff/v1/employers/search
Content-Type: application/json
```

Example request:

```json
{
  "display_name_query": "household",
  "employer_type": "household",
  "page_size": 25,
  "cursor": null
}
```

Body rules:

- unknown properties are rejected;
- `display_name_query` is required, NFC-normalized, outer-trimmed, 2–100 characters, and rejects Unicode control characters;
- `employer_type` is optional and exactly `household` or `business`; it may only narrow a name search and is never accepted by itself;
- `page_size` defaults to 25 and is an integer from 1 through 50;
- `cursor` is optional, maximum 512 characters, and validated by the cursor codec;
- cursor filters must match the normalized current request filters;
- no idempotency key is required or interpreted;
- success includes `Cache-Control: no-store`.

Search response:

```json
{
  "items": [
    {
      "employer_id": "11111111-1111-4111-8111-111111111111",
      "employer_type": "household",
      "display_name": "Synthetic Household 001",
      "lifecycle_status": "draft",
      "version": 1,
      "received_at": "2026-08-05T03:00:00Z"
    }
  ],
  "next_cursor": null
}
```

Do not return total count, source channel, creation actor/time, command/event data, filter fingerprint, cursor fields, or SQL/query-plan information.

### Matching and ordering

- Treat the normalized name fragment literally.
- Escape PostgreSQL `LIKE` metacharacters `%`, `_`, and the chosen escape character before applying `ILIKE` with an explicit escape clause.
- Do not accept caller-controlled SQL wildcard behavior.
- Combine name and type filters with logical AND.
- Order only by `received_at DESC`, then `employer_id DESC`.
- Do not compute or claim relevance.
- Query `page_size + 1` rows, return at most `page_size`, and derive `next_cursor` from the last returned item only when another row exists.
- Use keyset comparison consistent with the descending order.

### Cursor envelope

Before coding, run a small pure-Python probe for the chosen base64url/JSON encoding and a PostgreSQL ordering probe for equal timestamps. Record observed behavior in `NOTES.md`; remove disposable probe files.

Canonical cursor payload:

```json
{
  "v": 1,
  "after_received_at": "2026-08-05T03:00:00.000000Z",
  "after_employer_id": "11111111-1111-4111-8111-111111111111",
  "filter_fingerprint": "<64 lowercase hex SHA-256>"
}
```

Encoding rules:

- canonical JSON uses sorted keys and compact separators;
- UTF-8 bytes are base64url encoded without padding for transport;
- decoder restores required padding internally;
- exact key set only; reject extra/missing fields;
- `v` must equal `1`;
- timestamp input must be timezone-aware; the encoder calls `astimezone(UTC)` and emits exactly six fractional digits plus `Z`, while the decoder rejects a transport payload that is not already in that canonical UTC form;
- Employer ID must be a non-nil UUID;
- fingerprint must be exactly 64 lowercase hexadecimal characters;
- malformed, oversized, wrong-version, non-canonical, or filter-mismatched cursors map to safe validation failure without reflection.

Filter fingerprint canonical JSON contains the required normalized name fragment and optional type:

```json
{
  "display_name_query": "household",
  "employer_type": "household"
}
```

Use `null` for an absent employer type, sorted keys, compact separators, UTF-8, and SHA-256. The display-name query is never absent. Do not include page size. Do not log the canonical filter JSON, digest, or cursor.

The cursor is not signed and grants no authority. Authorization and filters are applied independently on every request.

## 4. Authorization and application-query contract

Add the following technical permission as the direct slice-level implementation of the client-accepted matrix capability “View and search authorized employer-demand records”; it does not create a new business-role entitlement:

```python
READ_EMPLOYER_PERMISSION = "employer:read"


def can_read_employer(principal: StaffPrincipal) -> bool:
    return READ_EMPLOYER_PERMISSION in principal.permissions
```

The normal synthetic local/test principal receives:

```python
frozenset({CREATE_DRAFT_EMPLOYER_PERMISSION, READ_EMPLOYER_PERMISSION})
```

Do not infer permission from `role_name`. Actor/role/permission headers remain ignored and cannot elevate authority.

The application interfaces are deliberately narrow:

```python
def get_employer(
    *,
    session: Session,
    principal: StaffPrincipal,
    employer_id: UUID,
) -> EmployerDetailRecord:
    """Authorize before lookup and return minimized detail or safe not-found."""
```

```python
@dataclass(frozen=True, slots=True)
class EmployerSearchPosition:
    after_received_at: datetime
    after_employer_id: UUID


@dataclass(frozen=True, slots=True)
class SearchEmployersResult:
    items: tuple[EmployerSearchRecord, ...]
    next_cursor: str | None


def search_employers(
    *,
    session: Session,
    principal: StaffPrincipal,
    display_name_query: str,
    employer_type: Literal["household", "business"] | None,
    page_size: int,
    cursor: str | None,
) -> SearchEmployersResult:
    """Authorize, then decode/filter-bind the cursor and return a bounded page."""
```

Application query modules own authorization, cursor decode/filter validation/encode after authorization, safe not-found translation, and SQLAlchemy-failure translation. Persistence functions own concrete SELECT construction only. API code owns schema validation, response mapping, and problem-response mapping; it passes the opaque cursor unchanged to the application query. Successful reads never commit, flush, or roll back; a caught SQLAlchemy failure rolls back the failed session transaction before raising the shared safe persistence error. No read creates receipts/events or turns ordinary retrieval into a domain audit action.

## 5. Persistence contract

Modify only the concrete Employer persistence module.

Retain the existing `EmployerRecord` and strict `get_employer_by_id` unchanged for create-command replay. Add minimized read-side records so exact detail/search do not select or carry `created_by` merely to discard it at the API boundary:

```python
@dataclass(frozen=True, slots=True)
class EmployerDetailRecord:
    employer_id: UUID
    employer_type: Literal["household", "business"]
    display_name: str
    lifecycle_status: Literal["draft"]
    source_channel: Literal["staff_entry"]
    received_at: datetime
    created_at: datetime
    version: int


@dataclass(frozen=True, slots=True)
class EmployerSearchRecord:
    employer_id: UUID
    employer_type: Literal["household", "business"]
    display_name: str
    lifecycle_status: Literal["draft"]
    received_at: datetime
    version: int
```

Recommended interfaces:

```python
def find_employer_by_id(*, session: Session, employer_id: UUID) -> EmployerDetailRecord | None: ...
```

```python
def find_employers(
    *,
    session: Session,
    display_name_query: str,
    employer_type: Literal["household", "business"] | None,
    limit: int,
    after_received_at: datetime | None,
    after_employer_id: UUID | None,
) -> tuple[EmployerSearchRecord, ...]: ...
```

Rules:

- select only Employer columns required by the accepted representation;
- apply name/type filters before ordering and limiting;
- escape literal search text before `ILIKE`;
- use explicit `ESCAPE` behavior;
- require both cursor position fields or neither;
- use keyset predicate equivalent to:

```text
received_at < after_received_at
OR (received_at = after_received_at AND employer_id < after_employer_id)
```

- order by `received_at DESC, employer_id DESC`;
- limit to the caller-supplied bounded `page_size + 1`;
- perform no count query;
- perform no insert/update/delete/flush/commit/rollback; transaction cleanup for a caught SQLAlchemy failure belongs to the application query boundary;
- do not create a generic repository or projection table.

The existing create-command replay path requires an existing Employer and continues using the strict existing `get_employer_by_id`, which raises if its internally referenced result is missing. Do not rename or relax that helper in this slice; `find_employer_by_id` is the separate optional/minimized read helper.

## 6. Error, cache, and logging contract

Extend existing RFC 9457-style problem responses with stable safe behavior:

- `403` `https://golden-rose.local/problems/forbidden` — unchanged safe forbidden body;
- `404 employer_not_found` — title `Not Found`, detail `employer not found`;
- `422` `https://golden-rose.local/problems/request-validation` — unchanged generic request-validation body for body/filter/cursor violations;
- `503` `https://golden-rose.local/problems/service-unavailable` — unchanged safe service-unavailable body;
- `500` `https://golden-rose.local/problems/internal-error` — unchanged safe internal-error body.

Move the generic `SafePersistenceError` from `application/create_draft_employer.py` into a new `application/errors.py`, then update the create module, API exception handler, and existing tests to import that shared symbol. Add `EmployerNotFoundError` there for the new authorized-absence path. Keep `IdempotencyConflictError` in the create-command module. This is an import-location refactor with regression tests, not a behavior change to creation.

Do not reflect UUID existence details beyond authorized 404, submitted names, filters, cursors, SQL, database URLs, driver text, actor IDs/permissions, or exception text.

Apply `Cache-Control: no-store` to:

- successful detail responses;
- successful search responses;
- problem responses from these routes.

A narrowly safe implementation may add `no-store` to all application problem responses if tests prove the existing create endpoint remains compatible. Do not introduce broad caching middleware or unrelated response-policy refactors.

No application log may include request bodies, `display_name_query`, cursor, filter fingerprint, database URL, SQL parameters, or raw exception detail. Tests should capture response/log output where feasible and assert absence of submitted synthetic markers.

## 7. Exact proposed file surface

```text
docs/adr/ADR-0004-phase-1-employer-read-search-boundary.md       # planning packet
.hermes/plans/2026-08-04_phase-1-employer-read-search-plan.md     # planning packet

src/golden_rose/
  api/
    errors.py                                                     # modify
    dependencies.py                                               # modify synthetic grants
    staff/
      employers.py                                                # modify routes
      schemas.py                                                  # modify schemas
  application/
    errors.py                                                      # create shared safe/not-found errors
    create_draft_employer.py                                       # modify shared-error import only
    get_employer.py                                               # create
    search_cursor.py                                              # create
    search_employers.py                                           # create
  auth/
    permissions.py                                                # modify
  persistence/
    employers.py                                                  # modify

tests/
  unit/
    auth/test_permissions.py                                      # modify
    api/test_dependencies.py                                      # create
    api/test_employer_schemas.py                                  # modify
    application/test_employer_search_cursor.py                    # create
  integration/
    persistence/test_employer_reads.py                            # create
    application/test_get_employer.py                              # create
    application/test_search_employers.py                          # create
    application/test_create_draft_employer.py                      # modify imports only
    api/test_staff_employer_reads.py                              # create
    api/test_staff_employers.py                                    # modify imports only

CURRENT_WORK.md                                                    # closeout/handoff
ROADMAP.md                                                         # milestone
NOTES.md                                                           # observed evidence
README.md                                                          # coding closeout after routes are implemented
```

Modify `README.md`, `ARCHITECTURE.md`, `TECHNICAL_REQUIREMENTS.md`, `SECURITY.md`, or the operational-discovery register during coding only if implementation evidence changes their current accepted/planned status. The planning packet already aligns those controlling documents; avoid duplicative churn.

No migration, manifest, lockfile, Compose, CI workflow, repository-policy, or dependency file should change.

## 8. Implementation tasks — strict TDD

### Task 0: Re-baseline and establish the coding lane

**Objective:** Prove implementation begins from the reviewed planning baseline.

**Files:** None.

1. Run `git fetch --all --prune`.
2. Verify the planning PR is merged into `origin/develop` and record its merge SHA.
3. Run `git switch develop && git merge --ff-only origin/develop`.
4. Verify clean status and `HEAD == origin/develop`.
5. Verify ADR-0004 and this plan are present and accepted/merged.
6. Create `git switch -c feat/staff-employer-read-search`.
7. Obtain explicit approval before any `docker compose up` or Uvicorn startup.

Expected: clean feature branch from the exact merged plan tip.

### Task 1: Add the named read permission

**Objective:** Establish the authorization boundary before any read implementation.

**Files:**
- Modify first: `tests/unit/auth/test_permissions.py`
- Then modify: `src/golden_rose/auth/permissions.py`
- Create first: `tests/unit/api/test_dependencies.py`
- Then modify: `src/golden_rose/api/dependencies.py`

RED → GREEN cycles:

1. A principal with `employer:read` is allowed.
2. A principal without it is denied.
3. Owner/Operations/Platform-style role labels without the permission remain denied.
4. The synthetic local/test principal receives create + read permissions from validated configuration, not request input.
5. Request headers cannot add `employer:read`.
6. Production plus synthetic auth remains rejected during application creation.

The dependency unit test constructs validated non-production synthetic `Settings`, calls `get_staff_principal`, and asserts the configured actor UUID, synthetic role label, and exact permission set. It must not instantiate a database engine or accept request/header permission input.

Run:

```bash
uv run pytest tests/unit/auth/test_permissions.py \
  tests/unit/api/test_dependencies.py tests/unit/test_main.py -v
```

Expected final: PASS.

Commit: `security(auth): add employer read permission`.

### Task 2: Define search schemas and cursor codec

**Objective:** Make malformed/sensitive search input fail safely before persistence exists.

**Files:**
- Modify first: `tests/unit/api/test_employer_schemas.py`
- Then modify: `src/golden_rose/api/staff/schemas.py`
- Create first: `tests/unit/application/test_employer_search_cursor.py`
- Then create: `src/golden_rose/application/search_cursor.py`

Schema RED → GREEN cycles:

1. Name-only filter is accepted and NFC/outer-space normalized.
2. Type-only and missing-name requests are rejected.
3. Combined name/type filters are accepted.
4. Name shorter than 2 or longer than 100 is rejected.
5. Control characters are rejected.
6. Unknown properties and invalid employer type are rejected.
7. Page size defaults to 25; 1 and 50 are accepted; 0/51/non-integers are rejected.
8. Cursor over 512 characters is rejected.
9. Detail and search response models expose exact accepted fields only.

Cursor RED → GREEN cycles:

1. Canonical filters produce deterministic SHA-256 fingerprint.
2. Position encodes/decodes round-trip without padding in transport.
3. Cursor contains only exact approved keys and no query/type/actor data.
4. Missing/extra keys, invalid base64/UTF-8/JSON, wrong version, bad UTC timestamp, nil/bad UUID, or bad fingerprint fail safely.
5. Non-canonical equivalent payload is rejected or canonicalized according to one asserted rule; prefer reject after decode/re-encode mismatch.
6. Cursor from different normalized filters is rejected.
7. Page-size changes do not invalidate the same filter-bound cursor.
8. Exception messages and repr do not contain the raw cursor or filter text.
9. Encoder converts any timezone-aware position to UTC before emitting fixed six-digit fractional seconds plus `Z`; equivalent non-UTC-offset and UTC instants produce the same canonical cursor.

Run:

```bash
uv run pytest tests/unit/api/test_employer_schemas.py \
  tests/unit/application/test_employer_search_cursor.py -v
```

Expected final: PASS.

Commit: `feat(api): define bounded employer search contract`.

### Task 3: Add concrete PostgreSQL detail and search persistence

**Objective:** Prove literal matching, filters, ordering, and keyset behavior on the selected database.

**Files:**
- Create first: `tests/integration/persistence/test_employer_reads.py`
- Then modify: `src/golden_rose/persistence/employers.py`

After explicit PostgreSQL service approval, migrate a fresh synthetic database before tests.

Use the existing create command or a narrowly approved synthetic factory to seed canonical Employers. Do not bypass schema constraints with client-like fixtures.

RED → GREEN cycles:

1. Existing UUID lookup returns the exact current Employer.
2. Missing UUID returns `None` at persistence only.
3. Name search is case-insensitive for observed PostgreSQL behavior.
4. Name search treats `%`, `_`, and escape character literally.
5. Combined required-name/optional-type filters apply AND semantics; persistence receives no type-only public request.
7. Result order is newest `received_at`, then descending UUID for equal timestamps.
8. Limit is enforced with no count query.
9. First keyset page plus continuation yields no duplicate/missing fixture rows.
10. Equal-timestamp boundary uses UUID tie-break correctly.
11. A newly inserted newer row after page one does not appear in continuation behind the existing cursor; a fresh search sees it. Record that this is not snapshot isolation.
12. Persistence read helpers create no Employer/receipt/event rows and issue no UPDATE/DELETE.
13. Existing create replay still resolves its authoritative Employer and all create tests pass.

Run focused tests, then:

```bash
uv run pytest tests/integration/application/test_create_draft_employer.py \
  tests/integration/persistence/test_employer_reads.py -v
```

Expected final: PASS.

Commit: `feat(db): add bounded employer read queries`.

### Task 4: Add authorization-first application queries

**Objective:** Prove no persistence function runs before named-permission authorization.

**Files:**
- Extend first: `tests/integration/application/test_get_employer.py`
- Extend first: `tests/integration/application/test_search_employers.py`
- Modify first: shared-error import assertions in `tests/integration/application/test_create_draft_employer.py` and `tests/integration/api/test_staff_employers.py`
- Then create: `src/golden_rose/application/errors.py`
- Then modify: `src/golden_rose/application/create_draft_employer.py`
- Then modify: `src/golden_rose/api/errors.py`
- Then create: `src/golden_rose/application/get_employer.py`
- Then create: `src/golden_rose/application/search_employers.py`

RED → GREEN cycles:

1. Permitted exact query returns current Employer.
2. Denied exact query raises safe permission error before persistence lookup; monkeypatch/spy must fail if called.
3. Permitted missing exact query raises application `EmployerNotFoundError` without exposing UUID internals.
4. Permitted search authorizes first, then decodes and filter-binds the cursor, returns at most page size, and emits `next_cursor` from `page_size + 1` rows.
5. Denied search raises before cursor decode/filter validation and before persistence query; a length-valid malformed cursor still returns 403 for a denied principal and no SELECT/count executes.
6. Role label without permission remains denied.
7. Successful application queries perform no flush/commit/rollback/domain/event/receipt writes.
8. SQLAlchemy availability failures roll back the failed transaction once and are translated through shared `SafePersistenceError` without SQL/URL/filter detail.
9. Moving `SafePersistenceError` preserves every existing create-command and API error contract.

Run:

```bash
uv run pytest tests/integration/application/test_get_employer.py \
  tests/integration/application/test_search_employers.py -v
```

Expected final: PASS.

Commit: `feat(staff): add authorized employer read queries`.

### Task 5: Expose detail and POST search routes

**Objective:** Complete the read-only HTTP vertical slice without widening identity or data scope.

**Files:**
- Create first: `tests/integration/api/test_staff_employer_reads.py`
- Then modify: `src/golden_rose/api/errors.py`
- Then modify: `src/golden_rose/api/staff/employers.py`
- Modify schemas/cursor only after an observed RED requires it.

Before final route code, run a disposable FastAPI probe against the locked version to verify static `/search` and dynamic `/{employer_id}` route matching for different methods. Declare the static route before the dynamic route regardless; remove the probe and record the observation in `NOTES.md`.

RED → GREEN cycles:

1. Permitted GET existing returns exact detail and `Cache-Control: no-store`.
2. Permitted GET absent returns safe 404 with no reflected UUID and no-store.
3. Denied GET returns safe 403 before SQL and header-based elevation fails.
4. Permitted POST search returns minimized ordered items, optional next cursor, no total, and no-store.
5. Name/type filters and next cursor round-trip through HTTP.
6. Missing-name/type-only, unknown-field, malformed/foreign cursor, invalid type/name/page size return generic safe 422 without reflection and with no-store for an otherwise authorized principal.
7. Denied search returns 403 before SQL/result derivation; actor/role/permission headers cannot elevate.
8. Known persistence failure maps to safe 503; unexpected failure maps to safe 500; neither leaks synthetic markers, cursor, SQL, URL, actor, or exception.
9. Detail/search leave receipt/employer/event row counts unchanged.
10. OpenAPI contains root POST create, POST `/search`, and GET `/{employer_id}` only; no public/list/export/audit route.
11. Existing create API tests remain unchanged except narrowly compatible no-store error behavior if the common handler adds it.

Use dependency overrides only in tests. The normal synthetic dependency remains configuration supplied.

After focused/full tests pass and runtime approval is confirmed, run loopback-only Uvicorn against the disposable synthetic PostgreSQL database. Create two fictional Employers through the existing POST command, retrieve one, search by a fictional fragment/type, follow one cursor if present, verify no additional receipt/event rows from reads, then stop API/database services.

Commit: `feat(api): expose authorized employer detail and search`.

### Task 6: Run regression, quality, and security evidence

**Objective:** Prove the read slice does not weaken the create tracer or repository gates.

**Files:** Modify production/test files only for observed failures within scope.

With approved synthetic PostgreSQL running and migrations applied:

```bash
uv lock --check
uv sync --locked --all-groups
uv run ruff format --check .
uv run ruff check .
uv run mypy src tests
uv run bandit -q -r src
uv run alembic upgrade head
uv run pytest --cov=golden_rose --cov-report=term-missing --cov-fail-under=95
uv run alembic downgrade base
uv run alembic upgrade head
uv run pip-audit --skip-editable
mkdir -p build
uv run cyclonedx-py environment --pyproject pyproject.toml \
  --output-reproducible --of JSON -o build/backend-sbom.cdx.json
git diff --check origin/develop...HEAD
```

Also prove:

- `git diff --name-status origin/develop...HEAD` contains no migration, dependency, lockfile, Compose, CI, policy, frontend, or generated artifact change;
- `gitleaks git --log-opts='origin/develop..HEAD' --redact` reports no leak;
- exact routes and permission strings appear only in intended files;
- no Python source contains an unrestricted `SELECT *`, count endpoint, query logging, or new create/update/delete path for this slice;
- no local `.env`, database state, logs, SBOM, caches, or client/generated artifacts are tracked.

Do not claim a test ran unless its real output was observed.

### Task 7: Close the coding lane and hand off for review

**Objective:** Leave a clean, auditable branch for independent review.

**Files:**
- Modify: `CURRENT_WORK.md`
- Modify: `ROADMAP.md`
- Modify: `NOTES.md`
- Modify: `README.md` because route behavior becomes implemented
- Modify controlling docs only if implementation evidence changes an accepted boundary

Record:

- exact merged planning base SHA and the pre-closeout implementation-candidate SHA that was actually tested/reviewed;
- RED → GREEN observations;
- PostgreSQL version/service boundary and migration order;
- focused/full test counts and coverage;
- Ruff/mypy/Bandit/pip-audit/SBOM results;
- exact-range Gitleaks bytes/commit count;
- route/privacy/cursor/authorization/no-write evidence;
- any warnings or operational discoveries;
- service teardown evidence.

Commit focused closeout, push `feat/staff-employer-read-search`, and stop without opening a PR.

After the final closeout commit and push, verify local `HEAD == @{upstream}` and report that final pushed SHA in the review handoff message. Do not attempt to embed a commit's own final SHA inside that same commit; keep the tested candidate SHA and final documentation-only head distinct and auditable.

Suggested final commit: `docs: hand employer read search to review`.

## 9. Acceptance evidence

Implementation is complete only when all are true:

- [ ] ADR-0004 and this plan were reviewed and merged before coding.
- [ ] Coding branch began at exact merged `origin/develop` tip.
- [ ] Every production behavior was preceded by an observed failing test.
- [ ] Only fictional synthetic fixture values appear.
- [ ] Existing create authorization/idempotency/atomic audit behavior still passes.
- [ ] `employer:read` controls detail and search; role/header labels cannot grant it.
- [ ] Denied detail/search executes no Employer query or result derivation.
- [ ] Authorized absent detail returns safe non-reflective 404.
- [ ] Search requires a bounded name fragment; employer type is optional and cannot be used alone to enumerate the two exhaustive type partitions.
- [ ] Search rejects unknown fields.
- [ ] Name search is NFC-normalized, bounded, literal, and case-insensitive under observed PostgreSQL behavior.
- [ ] `%`, `_`, and escape-character input is treated literally.
- [ ] Combined type/name filtering uses AND semantics.
- [ ] Ordering and equal-timestamp UUID tie-break are deterministic.
- [ ] Cursor is versioned, opaque, sensitive transient but non-authoritative, length bounded, canonical, filter bound, and excluded from logs/errors/metrics/audit events.
- [ ] Page continuation is duplicate-free and returns no total count.
- [ ] Responses contain only approved fields and `Cache-Control: no-store`.
- [ ] Safe 403/404/422/503/500 bodies do not reflect names/cursors/SQL/URL/actor/exception data.
- [ ] Detail/search create no Employer, receipt, or audit row and perform no mutation.
- [ ] OpenAPI exposes only approved create/detail/search staff routes and no public/list/export/audit route.
- [ ] No migration, dependency, lockfile, Compose, CI, policy, or frontend change exists.
- [ ] Full PostgreSQL application suite and required quality/security checks pass.
- [ ] Exact-range Gitleaks reports no leaks.
- [ ] Independent review has no unresolved High/Blocker finding.
- [ ] Required `enforce`, `check`, and `application` GitHub checks pass before merge.

## 10. Recovery and rollback

### Local/test recovery

All data is fictional and disposable. Stop API/database processes, remove disposable Compose state, restart the approved test database, run `alembic upgrade head`, and rerun the suite. Do not preserve synthetic test state as operational authority.

### Schema posture

This slice has no migration. Existing upgrade→downgrade→upgrade remains regression evidence for migration health, not a rollback mechanism for read behavior.

### Code rollback

Before merge, fix/revert on the feature branch. After merge to `develop`, revert the squash commit or apply a focused fix through the protected flow. Read/search creates no authoritative state requiring data rollback.

### Projection/search failure

A failed read/search returns safe unavailable/error state. It never changes current truth, inserts an audit event, or reports false zero/empty as authoritative. Retry performs a fresh authorized query; cursor reuse remains filter bound.

## 11. Review focus

The independent review should prioritize:

1. authorization after query or role/header-based elevation;
2. search text/cursor leakage through URL, logs, errors, repr, or monitoring;
3. SQL wildcard injection or failure to escape `%`, `_`, and escape character;
4. cursor carrying names/actors, accepting malformed/non-canonical state, or permitting filter substitution;
5. pagination duplicates/gaps from incorrect descending keyset comparison;
6. unbounded query, total count, unfiltered list, export, or hidden relevance ranking;
7. response overexposure (`created_by`, receipts, events, fingerprints, internal fields);
8. ordinary reads creating audit/receipt/domain writes;
9. dynamic route swallowing `/search` or OpenAPI exposing unintended paths;
10. schema/dependency/CI/policy drift or weakening existing create behavior;
11. SQLite/mock-only evidence replacing real PostgreSQL semantics;
12. frontend, identity, public, live-data, or adjacent-domain scope creep.

Any High/Blocker finding blocks PR readiness.
