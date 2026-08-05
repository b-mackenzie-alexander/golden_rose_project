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
- One application-owned NFC normalizer used before create-command payload hashing/persistence and before search fingerprinting/query construction; API validation remains defense in depth, not the authoritative normalization boundary.
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

`src/golden_rose/application/employer_text.py` owns NFC normalization shared by accepted Employer writers/readers. `create_draft_employer` normalizes before command payload fingerprinting and insertion, so composed/decomposed equivalents replay as one logical payload. `search_employers` authorizes first, then normalizes before filter fingerprinting and persistence. Direct persistence helpers assume already-normalized application input and are not alternate authoritative write boundaries.

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

Extend existing RFC 9457-style problem responses with the observed `application/json` media type and these exact JSON objects. Preserve that media type for existing and new problems in this slice; changing it to `application/problem+json` requires separate reviewed API-contract work rather than opportunistic drift here.

```json
{"type":"https://golden-rose.local/problems/forbidden","title":"Forbidden","detail":"forbidden","status":403}
{"type":"https://golden-rose.local/problems/employer-not-found","title":"Not Found","detail":"employer not found","status":404}
{"type":"https://golden-rose.local/problems/request-validation","title":"Unprocessable Entity","detail":"request validation failed","status":422}
{"type":"https://golden-rose.local/problems/service-unavailable","title":"Service Unavailable","detail":"service unavailable","status":503}
{"type":"https://golden-rose.local/problems/internal-error","title":"Internal Server Error","detail":"internal server error","status":500}
```

The existing create route's 400/403/409/422/503/500 status, media type, type/title/detail values, and exact success/replay bodies remain byte-for-byte stable. Tests must assert the full problem object for each new read/search error and rerun the existing exact create assertions.

Move the generic `SafePersistenceError` from `application/create_draft_employer.py` into a new `application/errors.py`, then update the create module, API exception handler, and existing tests to import that shared symbol. Add `EmployerNotFoundError` there for the new authorized-absence path. Keep `IdempotencyConflictError` in the create-command module. This is an import-location refactor with regression tests, not a behavior change to creation.

Do not reflect UUID existence details beyond authorized 404, submitted names, filters, cursors, SQL, database URLs, driver text, actor IDs/permissions, or exception text.

Apply `Cache-Control: no-store` to:

- successful detail responses;
- successful search responses;
- problem responses from these routes.

A narrowly safe implementation may add `no-store` to all application problem responses if tests prove the existing create endpoint remains compatible. Do not introduce broad caching middleware or unrelated response-policy refactors.

No application log may include request bodies, `display_name_query`, cursor, filter fingerprint, database URL, SQL parameters, or raw exception detail. Integration tests must capture application/error log records and assert absence of submitted synthetic markers. The approved loopback Uvicorn evidence run must capture access/error output to an ignored temporary file, assert that no body/query/cursor marker appears, record only the redacted pass/fail result in `NOTES.md`, and delete the temporary log during teardown.

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
    employer_text.py                                               # create shared NFC invariant
    create_draft_employer.py                                       # modify shared-error import + NFC write invariant
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
    application/test_employer_text.py                             # create
    application/test_employer_search_cursor.py                    # create
  integration/
    persistence/test_employer_reads.py                            # create
    application/test_get_employer.py                              # create
    application/test_search_employers.py                          # create
    application/test_create_draft_employer.py                      # modify imports + NFC write/replay tests
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

### Mandatory per-behavior RED → GREEN procedure

For every behavior explicitly listed under a `RED → GREEN cycles` heading, use the exact proposed pytest node ID shown in backticks and do not batch later behavior into the same cycle. Items explicitly labeled `GREEN regression` assert already-satisfied invariants: run them before and after the task, but do not fabricate a RED or production change for them.

1. Add only that one test (plus the minimum fixture/import needed to collect it).
2. Run `uv run pytest <exact-node-id> -v` and record the observed RED command, assertion/import failure, and reason in the coding evidence. The cycle text below names the expected RED and minimal GREEN checkpoint. A setup/environment failure is not RED and must be fixed before proceeding.
3. Write only the named minimal GREEN production change for that behavior. If that change makes a later proposed RED node pass, reclassify the later node as a GREEN regression and record why; never weaken production behavior to manufacture RED.
4. Rerun the same node and observe GREEN.
5. Run the task-level focused command after each GREEN to catch regressions; refactor only while green.
6. Commit only after every named node in the task has its own recorded RED and GREEN evidence.

If a proposed node name must change to match an existing neighboring convention, record the old/new node ID and rationale before creating it; do not silently replace or combine cycles.

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

1. `tests/unit/auth/test_permissions.py::test_employer_read_permission_constant_has_exact_value` — RED: importing `EMPLOYER_READ_PERMISSION` fails. Minimal GREEN: add only `EMPLOYER_READ_PERMISSION = "employer:read"` beside the existing create constant.
2. `tests/unit/auth/test_permissions.py::test_principal_with_read_permission_is_allowed` — RED: importing `can_read_employer` fails after cycle 1. Minimal GREEN: add only `can_read_employer(principal)` as exact permission-set membership, mirroring the create helper.
3. `tests/unit/api/test_dependencies.py::test_synthetic_principal_has_exact_create_and_read_permissions` — RED: expected `{employer:draft:create, employer:read}` differs from the current create-only set. Minimal GREEN: import `EMPLOYER_READ_PERMISSION` and add it to the configuration-owned synthetic principal permission set.

GREEN regressions before and after Task 1:

1. `tests/unit/auth/test_permissions.py::test_principal_without_read_permission_is_denied` — the exact-membership helper from cycle 2 should already satisfy absence denial; add no production branch.
2. `tests/unit/auth/test_permissions.py::test_role_labels_do_not_grant_read_permission` — role labels are already ignored by permission helpers; add no production role logic.
3. `tests/unit/api/test_dependencies.py::test_request_headers_cannot_grant_read_permission` — `get_staff_principal` already accepts settings rather than request/header grants; add no header parsing.
4. `tests/unit/test_main.py::test_create_app_rejects_production_synthetic_auth_before_serving` — preserve the observed startup guard; add no production change.

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
- Create first: `tests/unit/application/test_employer_text.py`
- Then create: `src/golden_rose/application/employer_text.py`
- Create first: `tests/unit/application/test_employer_search_cursor.py`
- Then create: `src/golden_rose/application/search_cursor.py`

Schema RED → GREEN cycles:

1. `tests/unit/application/test_employer_text.py::test_normalize_employer_text_returns_trimmed_nfc` — RED: normalizer import fails. Minimal GREEN: create only the typed strip-plus-`unicodedata.normalize("NFC", value)` helper.
2. `tests/unit/api/test_employer_schemas.py::test_name_only_search_is_trimmed_and_nfc_normalized` — RED: search request model import fails. Minimal GREEN: add the strict request model with required name wired to the shared normalizer.
3. `tests/unit/api/test_employer_schemas.py::test_search_accepts_name_with_optional_type` — RED: `employer_type` is absent. Minimal GREEN: add only the optional existing controlled Employer type field.
4. `tests/unit/api/test_employer_schemas.py::test_search_rejects_name_outside_two_to_one_hundred_characters` — RED: one boundary case validates. Minimal GREEN: add only the 2..100 post-normalization length constraint.
5. `tests/unit/api/test_employer_schemas.py::test_search_rejects_unicode_control_characters` — RED: control-bearing name validates. Minimal GREEN: add only Unicode category `C*` rejection.
6. `tests/unit/api/test_employer_schemas.py::test_search_forbids_unknown_fields_and_invalid_type` — RED: unknown field or invalid type validates. Minimal GREEN: forbid extras and reuse the controlled Employer type validation.
7. `tests/unit/api/test_employer_schemas.py::test_search_page_size_defaults_and_bounds` — RED: page-size field/default is absent. Minimal GREEN: add strict integer `page_size=25` constrained to 1..50.
8. `tests/unit/api/test_employer_schemas.py::test_search_rejects_cursor_over_512_characters` — RED: cursor field/limit is absent. Minimal GREEN: add optional cursor with maximum length 512.
9. `tests/unit/api/test_employer_schemas.py::test_employer_read_responses_expose_exact_accepted_fields` — RED: response model imports fail. Minimal GREEN: add only the exact detail/item/page response fields listed in Section 3.

Schema GREEN regression after cycle 2:

- `tests/unit/api/test_employer_schemas.py::test_search_rejects_type_only_and_missing_name` — required normalized name already rejects both forms; add no alternate browse behavior.

Cursor RED → GREEN cycles:

1. `tests/unit/application/test_employer_search_cursor.py::test_filter_fingerprint_is_deterministic_for_normalized_filters` — RED: fingerprint import fails. Minimal GREEN: canonical JSON plus SHA-256 over normalized name/optional type only.
2. `tests/unit/application/test_employer_search_cursor.py::test_cursor_round_trips_without_transport_padding` — RED: codec imports fail. Minimal GREEN: encode/decode only the version, UTC position, UUID, and fingerprint using unpadded URL-safe Base64.
3. `tests/unit/application/test_employer_search_cursor.py::test_cursor_rejects_malformed_or_invalid_typed_payloads` — RED: at least one malformed class escapes or decodes. Minimal GREEN: add strict exact-key/type/version/UUID/timestamp/fingerprint validation with one safe exception.
4. `tests/unit/application/test_employer_search_cursor.py::test_cursor_rejects_noncanonical_transport_payload` — RED: alternate encoding decodes. Minimal GREEN: compare submitted cursor to canonical re-encoding.
5. `tests/unit/application/test_employer_search_cursor.py::test_cursor_rejects_different_normalized_filters` — RED: mismatched fingerprint is accepted. Minimal GREEN: constant-time compare decoded and expected fingerprints.
6. `tests/unit/application/test_employer_search_cursor.py::test_cursor_encoder_canonicalizes_aware_timestamp_to_utc` — RED: offset-equivalent instants encode differently. Minimal GREEN: `astimezone(UTC)` and fixed six-digit fractional seconds plus `Z` before serialization.

Cursor GREEN regressions:

1. `tests/unit/application/test_employer_search_cursor.py::test_cursor_payload_contains_only_approved_keys` — cycle 2's minimal codec already emits the exact key set; add no extra payload data.
2. `tests/unit/application/test_employer_search_cursor.py::test_cursor_filter_binding_ignores_page_size` — cycle 1's canonical filter input already excludes page size; add no page-size binding.
3. `tests/unit/application/test_employer_search_cursor.py::test_cursor_errors_do_not_reflect_cursor_or_filter_text` — cycle 3's one constant safe exception should already avoid reflection; add no diagnostic payload.

Run:

```bash
uv run pytest tests/unit/api/test_employer_schemas.py \
  tests/unit/application/test_employer_text.py \
  tests/unit/application/test_employer_search_cursor.py -v
```

Expected final: PASS.

Commit: `feat(api): define bounded employer search contract`.

### Task 3: Add concrete PostgreSQL detail and search persistence

**Objective:** Prove literal matching, filters, ordering, and keyset behavior on the selected database.

**Files:**
- Modify first: `tests/integration/application/test_create_draft_employer.py`
- Then modify: `src/golden_rose/application/create_draft_employer.py`
- Create first: `tests/integration/persistence/test_employer_reads.py`
- Then modify: `src/golden_rose/persistence/employers.py`

After explicit PostgreSQL service approval, migrate a fresh synthetic database before tests.

Use the existing create command to seed canonical Employers for name-search behavior. A narrow persistence fixture may control UUID/timestamp tie boundaries only after passing NFC-normalized fictional names; it is not an alternate authoritative writer. Do not bypass schema constraints with client-like fixtures.

RED → GREEN cycles:

1. `tests/integration/application/test_create_draft_employer.py::test_create_normalizes_display_name_before_fingerprint_and_insert` — RED: decomposed direct input is stored unchanged. Minimal GREEN: compute one normalized display name and pass it to persistence; leave fingerprint input unchanged for this cycle.
2. `tests/integration/application/test_create_draft_employer.py::test_replay_treats_composed_and_decomposed_names_as_same_payload` — RED: raw display name still changes the payload hash. Minimal GREEN: use the same normalized value in command fingerprint input.
3. `tests/integration/persistence/test_employer_reads.py::test_find_employer_by_id_returns_minimized_detail_record` — RED: read record/function imports fail. Minimal GREEN: add the immutable minimized detail record and one scalar optional SELECT by UUID.
4. `tests/integration/persistence/test_employer_reads.py::test_name_search_is_case_insensitive_in_postgresql` — RED: search function import fails. Minimal GREEN: add a basic SELECT with `ILIKE` input and no type/cursor/order expansion yet.
5. `tests/integration/persistence/test_employer_reads.py::test_name_search_escapes_percent_underscore_and_escape_character` — RED: wildcard marker broadens matches. Minimal GREEN: add explicit escape-character transformation and SQLAlchemy `escape=` semantics.
6. `tests/integration/persistence/test_employer_reads.py::test_name_and_type_filters_use_and_semantics` — RED: type does not narrow. Minimal GREEN: add only the optional equality predicate combined with AND.
7. `tests/integration/persistence/test_employer_reads.py::test_search_orders_by_received_at_then_uuid_descending` — RED: rows follow database/default order. Minimal GREEN: add only the two descending order clauses.
8. `tests/integration/persistence/test_employer_reads.py::test_search_enforces_limit_without_count_query` — RED: result is unbounded. Minimal GREEN: apply only caller-supplied bounded limit and issue no count.
9. `tests/integration/persistence/test_employer_reads.py::test_keyset_continuation_has_no_duplicate_or_missing_rows` — RED: no continuation predicate exists. Minimal GREEN: add the strict older-timestamp branch for fixtures with distinct timestamps.
10. `tests/integration/persistence/test_employer_reads.py::test_equal_timestamp_boundary_uses_uuid_tiebreak` — RED: equal-timestamp continuation misses/duplicates rows. Minimal GREEN: add the equality-plus-descending-UUID branch.

Persistence/create GREEN regressions after the relevant cycles:

1. `tests/integration/persistence/test_employer_reads.py::test_find_employer_by_id_returns_none_when_absent` — cycle 3's optional scalar lookup already returns `None`; add no exception.
2. `tests/integration/persistence/test_employer_reads.py::test_newer_insert_is_excluded_from_existing_continuation_and_visible_fresh` — cycles 9–10's keyset predicate already provides this non-snapshot behavior; add no snapshot state.
3. `tests/integration/persistence/test_employer_reads.py::test_read_helpers_issue_no_writes_or_count` — the SELECT-only cycles should already satisfy this; add no transaction/write/count behavior.
4. `tests/integration/application/test_create_draft_employer.py::test_create_draft_employer_identical_replay_returns_original_result_without_duplicates` — preserve existing replay behavior before/after cycles 1–2.

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

1. `tests/integration/application/test_get_employer.py::test_permitted_get_returns_current_minimized_employer` — RED: query import fails. Minimal GREEN: add one query function that checks `can_read_employer` first, calls minimized lookup, and returns the record.
2. `tests/integration/application/test_get_employer.py::test_missing_get_raises_nonreflective_not_found` — RED: allowed missing lookup returns `None`. Minimal GREEN: add shared constant-message `EmployerNotFoundError` translation only after authorized lookup.
3. `tests/integration/application/test_search_employers.py::test_permitted_search_returns_page_and_next_cursor` — RED: search query import fails. Minimal GREEN: add one function that authorizes first, normalizes, decodes/binds optional cursor, requests `page_size + 1`, and emits a cursor only for an extra row.
4. `tests/integration/application/test_search_employers.py::test_persistence_failure_rolls_back_once_and_raises_safe_error` — RED: SQLAlchemy failure escapes. Minimal GREEN: move/reuse shared `SafePersistenceError`, roll back once, and raise it without raw detail.

Application GREEN regressions after the relevant cycles:

1. `tests/integration/application/test_get_employer.py::test_denied_get_never_calls_persistence` — cycle 1 authorizes first; spies must remain untouched and no alternate branch is added.
2. `tests/integration/application/test_search_employers.py::test_denied_search_never_decodes_fingerprints_or_queries` — cycle 3 authorizes before normalization/codec/query; malformed and mismatched cursors must not reach spies.
3. `tests/integration/application/test_search_employers.py::test_search_normalizes_decomposed_query_after_authorization` — cycle 3 already uses the shared normalizer before fingerprint/query construction; add no second normalization path.
4. `tests/integration/application/test_search_employers.py::test_role_label_without_permission_remains_denied` — Task 1 exact permission membership already ignores role labels; add no role grant.
5. `tests/integration/application/test_search_employers.py::test_successful_queries_perform_no_writes_or_transaction_control` — successful query paths are SELECT-only; add no commit/flush/rollback/event/receipt behavior.
6. `tests/integration/application/test_create_draft_employer.py::test_safe_persistence_error_redacts_driver_details_for_db_failures` and `tests/integration/api/test_staff_employers.py::test_post_staff_employers_known_database_unavailability_returns_safe_503` — preserve existing behavior before/after moving the shared error.

Run:

```bash
uv run pytest tests/integration/application/test_get_employer.py \
  tests/integration/application/test_search_employers.py \
  tests/integration/application/test_create_draft_employer.py \
  tests/integration/api/test_staff_employers.py -v
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

1. `tests/integration/api/test_staff_employer_reads.py::test_search_returns_minimized_page_cursor_no_total_and_no_store` — RED: POST search returns 404/405. Minimal GREEN: declare and implement only static POST `/search` request/query/response mapping with `no-store`.
2. `tests/integration/api/test_staff_employer_reads.py::test_authorized_invalid_search_inputs_return_nonreflective_no_store_422` — RED: at least cursor-originated validation is unhandled or lacks `no-store`. Minimal GREEN: map safe cursor validation to the exact 422 object and ensure route problems receive `no-store`.
3. `tests/integration/api/test_staff_employer_reads.py::test_search_failures_map_to_safe_redacted_503_and_500` — RED: injected failure is unhandled or differs from the exact object. Minimal GREEN: reuse the exact shared 503 and existing 500 handlers without reflective detail.
4. `tests/integration/api/test_staff_employer_reads.py::test_get_existing_returns_exact_detail_with_no_store` — RED: GET returns 404/405 because the dynamic route is absent. Minimal GREEN: after static `/search` exists, add only GET `/{employer_id}` mapping to the application query and exact response with `no-store`.
5. `tests/integration/api/test_staff_employer_reads.py::test_get_absent_returns_nonreflective_no_store_404` — RED: application not-found is unhandled. Minimal GREEN: add only the exact 404 handler/problem object and `no-store`.

API GREEN regressions after the relevant cycles:

1. `tests/integration/api/test_staff_employer_reads.py::test_denied_get_runs_no_sql_and_headers_cannot_elevate` — Task 4 query authorizes first and the principal dependency ignores authority headers; add no route-level grant.
2. `tests/integration/api/test_staff_employer_reads.py::test_search_filters_and_cursor_round_trip_over_http` — cycle 1 maps the already-tested schema/application page; add no alternate cursor path.
3. `tests/integration/api/test_staff_employer_reads.py::test_denied_search_precedes_cursor_and_sql_and_headers_cannot_elevate` — Task 4 authorization order remains authoritative through HTTP; add no pre-authorization decode.
4. `tests/integration/api/test_staff_employer_reads.py::test_detail_and_search_leave_authoritative_row_counts_unchanged` — the routes call read-only queries; add no write/audit/receipt behavior.
5. `tests/integration/api/test_staff_employer_reads.py::test_openapi_exposes_only_approved_staff_employer_routes` — cycles 1 and 4 add only the accepted routes; add no list/export/public route.
6. `tests/integration/api/test_staff_employer_reads.py::test_search_logs_do_not_include_body_cursor_filter_sql_url_actor_or_exception` — no request/query logging is introduced; add no logging of submitted markers.
7. `tests/integration/api/test_staff_employers.py::test_post_staff_employers_returns_201_and_exact_body_for_permitted_request` and `tests/integration/api/test_staff_employers.py::test_openapi_exposes_only_intended_staff_route` — preserve observed create behavior before/after route/error changes.

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
- captured TestClient/application and approved loopback Uvicorn access/error output contains none of the submitted name/cursor/filter/database/SQL/actor/exception markers; do not persist the raw log as review evidence.

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

After the final closeout commit, rerun `uv run ruff format --check .`, `uv run ruff check .`, `git diff --check origin/develop...HEAD`, `git diff --name-status origin/develop...HEAD`, and exact-range Gitleaks over `origin/develop..HEAD`. If closeout changed any source/test/runtime file, rerun the full Task 6 gate instead of the documentation-only subset. Push only after these final-head checks pass; then verify local `HEAD == @{upstream}` and report that final pushed SHA in the review handoff message. Do not attempt to embed a commit's own final SHA inside that same commit; keep the tested candidate SHA and final documentation-only head distinct and auditable.

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
