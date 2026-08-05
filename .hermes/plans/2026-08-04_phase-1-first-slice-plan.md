# Phase 1 First Slice — Draft Employer + Atomic Audit Event Implementation Plan

> **For Hermes:** Execute this plan only from a fresh coding session after this planning packet is reviewed and merged. Use the `plan-to-code-handoff`, `test-driven-development`, and `python-project-test-environment` skills. Keep each behavior in a real RED → GREEN → REFACTOR cycle. Stop before opening a pull request so the independent review session can inspect the branch first.

**Status:** Historical implemented plan; PR #8 merged the reviewed tracer into `develop` at `0938c17`. The qualified `application` check passed and now requires a separate governance-as-code activation slice.
**Planning baseline:** `develop` at `bbe5c1d24d11d1ef9833e4af9de8da1c4ebcc887` (merged PR #6)
**Implementation branch after plan merge:** `feat/staff-draft-employer-tracer` from current `origin/develop`
**Goal:** Establish the minimum tested backend path through which an authorized synthetic staff principal creates one draft `Employer` and the application atomically appends the required `AuditEvent`.

**Architecture:** One modular Python application exposes only a versioned staff API. PostgreSQL domain rows remain authoritative current state; `AuditEvent` is append-only explanatory history, not an event-sourced primary store. One synchronous SQLAlchemy application command owns authorization, idempotency, validation, domain insertion, audit insertion, and commit/rollback behavior.

**Tech Stack:** Python 3.12, uv, Hatchling 1.31.0, FastAPI 0.141.1, Uvicorn 0.52.1, Pydantic 2.13.4, pydantic-settings 2.14.2, SQLAlchemy 2.0.51, `psycopg[binary]` 3.3.4, Alembic 1.19.0, PostgreSQL 16, pytest 9.1.1, HTTPX 0.28.1, pytest-cov 7.1.0, Ruff 0.16.1, mypy 2.3.0, Bandit 1.9.4, pip-audit 2.10.1, and cyclonedx-bom 7.3.1. Direct dependencies/build requirements are pinned and `uv.lock` controls the full graph.

---

## 1. Approval and lane boundaries

### Planning-session deliverables

This session owns:

- implementation assessment and decisions;
- ADR-0002 and ADR-0003;
- this exact implementation plan;
- living-document alignment;
- a documentation PR to `develop`.

It does **not** write application code or start PostgreSQL.

### Coding-session deliverables

A fresh coding session must:

1. re-read this merged plan and the controlling contracts;
2. fetch/prune and prove local `develop == origin/develop`;
3. create `feat/staff-draft-employer-tracer` from that merged baseline;
4. obtain explicit approval before starting the local PostgreSQL or API service;
5. execute the tasks below in strict TDD order;
6. commit focused checkpoints;
7. run the full local quality/security evidence set;
8. push the branch for review; and
9. stop without opening a PR.

### Review-session deliverables

A separate review session must independently inspect code, tests, migration safety, authorization, audit atomicity, dependency/security evidence, and scope. It may open the feature PR to `develop` only after High/Blocker findings are resolved. GitHub CI and conversations must clear before merge.

A later bug/hotfix session owns defects discovered after integration/release. Review findings against the active feature remain remediation on that feature branch; they must not be mislabeled as production hotfixes.

## 2. Scope contract

### Included

- Reproducible Python/backend manifest and lockfile.
- Local/test-only PostgreSQL 16 definition; no database or API process starts without explicit coding-session approval.
- Alembic environment and one reversible initial migration.
- `Employer` and append-only `AuditEvent` relational models plus one security-internal `CommandReceipt` for deterministic idempotency.
- Synthetic/test staff principal with a named permission.
- `POST /api/staff/v1/employers` only.
- One atomic `create_draft_employer` application command.
- Deterministic idempotency and concurrency behavior.
- Permission denial before persistence.
- Real PostgreSQL integration tests.
- Only fictional fixtures explicitly labeled synthetic; no copied or transformed client values.
- Application quality/security CI.
- Living-document and review handoff updates.

### Explicit non-scope

- Frontend or public API.
- Real authentication, MFA, recovery, sessions, or identity-provider integration.
- Employer contacts, legal names, worksites, addresses, requests, shifts, requirements, zones, CDTAs, maps, queues, calendars, corrections, search, or exports.
- Client or production data, legacy migration/import, cloud services, live geocoding, uploads, notifications, documents, payments, legal behavior, and retention automation.
- Async SQLAlchemy, workers, queues, caches, event buses, event sourcing, generic repositories, or speculative plug-in abstractions.
- Runtime table creation via `metadata.create_all`.

## 3. API and authorization contract

### Endpoint

```text
POST /api/staff/v1/employers
Content-Type: application/json
Idempotency-Key: <non-nil UUIDv4>
```

The idempotency key is the command ID. It is required, must be a non-nil UUIDv4, and is never accepted from the body. Creation has no existing row version to match; the command records prior version `0` and new version `1`.

### Request

```json
{
  "employer_type": "household",
  "display_name": "Synthetic Household 001"
}
```

Rules:

- `employer_type` is exactly `household` or `business`.
- `display_name` is UTF-8 text, normalizes to Unicode NFC, trims outer whitespace, is 1–200 characters after normalization/trimming, rejects control characters, and preserves allowed internal spacing/content.
- Unknown request properties are rejected.
- `legal_name`, source channel, timestamps, actor, state, IDs, and version are not client-settable.

### Server-assigned values

- `employer_id`: UUID4.
- `lifecycle_status`: `draft`.
- `source_channel`: `staff_entry`.
- `received_at` and `created_at`: same server UTC instant.
- `created_by`: stable synthetic principal UUID.
- `version`: `1`.

These values are accepted only for this tracer; they do not establish generalized account lifecycle or intake policy.

### Success response

Status `201 Created` and:

```json
{
  "employer_id": "<uuid>",
  "employer_type": "household",
  "display_name": "Synthetic Household 001",
  "lifecycle_status": "draft",
  "source_channel": "staff_entry",
  "version": 1,
  "received_at": "<UTC RFC3339>",
  "created_at": "<UTC RFC3339>"
}
```

An identical replay returns the same status/body/resource and adds `Idempotency-Replayed: true`. Initial success omits the header or sets it to `false`; choose one representation and assert it consistently.

### Authorization

- Named permission: `employer:draft:create`.
- Owner, delegated Manager, and Operations Staff may eventually receive it under the accepted matrix, but this slice checks the permission—not a role label.
- Platform Administrator and principals without the permission receive `403` before a database write.
- The principal comes from an application dependency/configuration seam. Actor, role, or permission must never be chosen by a request header/body.
- `synthetic` auth mode is valid only when `environment` is `local` or `test`. Settings validation rejects `environment=production` with `auth_mode=synthetic` before the application serves traffic.

Use these configuration names and no aliases in the first slice:

```text
GOLDEN_ROSE_ENVIRONMENT=local|test|production
GOLDEN_ROSE_AUTH_MODE=synthetic
GOLDEN_ROSE_DATABASE_URL=postgresql+psycopg://...
GOLDEN_ROSE_SYNTHETIC_STAFF_ID=<UUID>
GOLDEN_ROSE_TEST_DB_PASSWORD=<local/CI ephemeral value>
```

`.env.example` documents variable names/placeholders only. A real `.env.test` remains ignored and must never be committed.

### Errors

Use RFC 9457-style `application/problem+json` responses with stable non-sensitive codes:

- `400 invalid_idempotency_key` — missing, malformed, nil, or non-v4 idempotency UUID (if FastAPI maps header validation to 422, install a narrow handler so the contract remains explicit).
- `403 permission_denied` — principal lacks `employer:draft:create`.
- `409 idempotency_conflict` — key was already committed for a different actor, command contract, or canonical payload; do not reveal which.
- `422 validation_error` — body shape/value failure.
- `503 persistence_unavailable` — known database connectivity/availability failure; the caller retries with the same idempotency key.
- `500 internal_error` — unexpected failure; no request body, database URL, SQL, actor internals, or exception text is returned.

Validation problem details may name the rejected field and stable validation code but must not echo the raw submitted value. Do not disclose whether a protected record exists through error variation. Do not log `display_name`, request bodies, database URLs, idempotency keys, or raw SQL parameters.

## 4. Persistence contract

### `employers`

| Column | Type / constraint |
|---|---|
| `employer_id` | PostgreSQL UUID primary key; application-generated UUID4 |
| `employer_type` | varchar; check in (`household`, `business`) |
| `display_name` | varchar(200); trimmed non-empty check |
| `lifecycle_status` | varchar; initial check allows only `draft` |
| `source_channel` | varchar; initial check allows only `staff_entry` |
| `received_at` | timezone-aware timestamp, not null |
| `created_at` | timezone-aware timestamp, not null |
| `created_by` | UUID, not null |
| `version` | integer, not null; check `version >= 1`; initial value `1` |

No duplicate-name constraint is allowed; two employers may share a display name.

### `command_receipts`

This security-internal table reserves a command result inside the same transaction as the domain/audit writes. It is not a business entity, event store, queue, or public read model.

| Column | Type / constraint |
|---|---|
| `command_id` | PostgreSQL UUID primary key; supplied UUIDv4 idempotency key |
| `command_schema_version` | integer, initial `1` |
| `command_type` | varchar, initial `create_draft_employer` |
| `actor_id` | UUID, not null |
| `request_fingerprint` | bytea, exactly 32 bytes; SHA-256 digest, never logged/returned |
| `result_entity_type` | varchar, initial `employer` |
| `result_entity_id` | UUID, not null |
| `created_at` | timezone-aware server UTC timestamp |

The fingerprint covers canonical JSON containing only command schema version, command type, normalized `employer_type`, and normalized `display_name`. Actor identity is compared separately and must match. A different actor or payload receives the same non-enumerating `409` and never receives the prior result.

### `audit_events`

The initial table supports the accepted required envelope without storing whole-row snapshots or arbitrary unrestricted payloads:

| Column | Type / constraint |
|---|---|
| `audit_event_id` | UUID primary key |
| `event_schema_name` | varchar, initial `employer.created` |
| `event_schema_version` | integer, initial `1` |
| `event_type` | varchar, allowlisted initial `employer.created` |
| `entity_type` | varchar, initial `employer` |
| `entity_id` | UUID, foreign key to `employers.employer_id` |
| `entity_sequence` | integer, initial `1`; unique with entity type/id |
| `prior_record_version` | integer, `0` for creation |
| `new_record_version` | integer, `1` for creation |
| `actor_type` | varchar, initial `staff` |
| `actor_id` | UUID, not null |
| `initiating_staff_actor_id` | nullable UUID; unnecessary when actor is already staff |
| `occurred_at` | timezone-aware server UTC timestamp |
| `effective_at` | nullable timezone-aware business time |
| `command_id` | UUID, foreign key to `command_receipts.command_id` |
| `correlation_id` | UUID; same as command ID for this single-record command |
| `reason_code` / `reason_text` | nullable; creation requires neither |
| `source_type` | varchar, initial `staff_api` |
| `source_reference` | nullable safe identifier; no URL/path/body |
| `related_event_ids` | JSONB array, empty for creation |
| `changed_fields` | typed JSONB object containing field names and approved safe values only |
| `payload_classification` | varchar, initial `sensitive_operational` |

For `employer.created`, `changed_fields` records the names `employer_type`, `display_name`, `lifecycle_status`, and `source_channel`; it includes approved structured values for type/status/channel but omits the display-name value from the ordinary event payload. Current `display_name` remains in the authoritative domain row. No full row or request body is copied to audit history.

The migration installs PostgreSQL triggers that reject `UPDATE` and `DELETE` against `command_receipts` and `audit_events`. This protects deterministic replay and append-only audit behavior from ordinary application mutation. Production database-role separation and retention/disposal remain later gates.

### Transaction and retry algorithm

1. Parse/validate request and non-nil UUIDv4 idempotency key.
2. Resolve principal from dependency/config and require `employer:draft:create`.
3. Canonicalize the command schema/type and accepted command fields and calculate the fingerprint without logging the payload/digest.
4. Begin one SQLAlchemy transaction.
5. Generate the prospective employer ID and attempt `INSERT ... ON CONFLICT DO NOTHING` for the `CommandReceipt` containing command ID, actor ID, fingerprint, and result ID. PostgreSQL serialization at the unique key is the only ownership mechanism.
6. If the receipt was not inserted, read the now-committed receipt. If actor, command type/schema, and fingerprint all match, load and return its employer as a replay; otherwise raise `idempotency_conflict` without revealing the prior actor/result.
7. If this transaction inserted the receipt, insert the employer and one creation audit event referencing that command ID.
8. Flush to force all constraints, then commit once.
9. If audit insertion, flush, or commit fails, roll back the receipt, employer, and audit insert together and return the safe persistence error. A concurrent waiter may then acquire the absent receipt and execute normally.

The application command owns this algorithm. Route handlers and ORM event hooks must not create alternate audit/write paths.

The wished-for application interface is intentionally narrow:

```python
def create_draft_employer(
    *,
    session: Session,
    principal: StaffPrincipal,
    command_id: UUID,
    employer_type: EmployerType,
    display_name: str,
    clock: Clock,
    identifiers: IdentifierFactory,
) -> CreateDraftEmployerResult:
    """Authorize, replay-or-conflict, and atomically create Employer + AuditEvent."""
```

The result contains the created employer plus `replayed: bool`. Persistence helpers may query/add/flush but may not authorize, commit, roll back, construct arbitrary event payloads, or translate API errors.

## 5. Exact proposed file surface

```text
.python-version
.env.example
compose.yaml
pyproject.toml
uv.lock
alembic.ini
migrations/
  env.py
  script.py.mako
  versions/
    0001_create_first_slice_tables.py
src/golden_rose/
  __init__.py
  main.py
  config.py
  database.py
  api/
    __init__.py
    errors.py
    dependencies.py
    staff/
      __init__.py
      employers.py
      schemas.py
  application/
    __init__.py
    create_draft_employer.py
  auth/
    __init__.py
    permissions.py
    principal.py
  persistence/
    __init__.py
    models.py
    employers.py
    command_receipts.py
    audit_events.py
  clock.py
  identifiers.py
tests/
  conftest.py
  factories.py
  unit/
    test_config.py
    auth/test_permissions.py
    api/test_employer_schemas.py
  integration/
    conftest.py
    test_initial_migration.py
    application/test_create_draft_employer.py
    api/test_staff_employers.py
.github/workflows/application-quality.yml
```

Keep the three persistence helpers limited to concrete lookups/inserts required by this command; do not create a generic repository framework. `clock.py` and `identifiers.py` are tiny injectable seams for deterministic tests, not utility dumping grounds.

## 6. Implementation tasks — strict TDD

### Task 0: Re-baseline and establish the coding lane

**Objective:** Prove the implementation starts from the reviewed planning baseline.

**Files:** None.

1. Run `git fetch origin --prune`.
2. Run `git switch develop && git merge --ff-only origin/develop`.
3. Verify `git status --short --branch` is clean and `git rev-parse HEAD` equals `git rev-parse origin/develop`.
4. Verify merged `CURRENT_WORK.md`, ADR-0002, ADR-0003, and this plan are present.
5. Create `git switch -c feat/staff-draft-employer-tracer`.
6. Obtain explicit approval before any `docker compose up` or other service start.

Expected: clean feature branch based exactly on reviewed `develop`.

### Task 1: Create the locked Python test environment

**Objective:** Make later RED failures about missing behavior, not host package drift.

**Files:**
- Create: `.python-version`
- Create: `pyproject.toml`
- Create: `uv.lock`
- Create: `.env.example`
- Modify: `.gitignore` only if a test-specific local env/cache path is not already excluded.

1. Add Python `>=3.12,<3.13`, the exact direct/build versions in the plan header, Hatchling build metadata for `src/golden_rose`, Ruff target `py312`, strict mypy, pytest markers, and coverage configuration excluding migrations.
2. Run `uv lock`.
3. Run `uv sync --locked --all-groups`.
4. Run `uv run python --version`; expected Python 3.12.x.
5. Run `uv lock --check`; expected success.
6. Run `git diff --check`.
7. Commit: `chore(api): establish locked Python toolchain`.

No production module is created in this task; TDD begins before application code.

### Task 2: Reject unsafe synthetic-auth configuration

**Objective:** Prevent the test principal seam from becoming a production authentication bypass.

**Files:**
- Create first: `tests/unit/test_config.py`
- Then create: `src/golden_rose/__init__.py`
- Then create: `src/golden_rose/config.py`

**RED 1:** Test that `environment=production` plus `auth_mode=synthetic` raises a settings-validation error. Run:

```bash
uv run pytest tests/unit/test_config.py::test_production_rejects_synthetic_auth -v
```

Expected RED: import/module missing.

**GREEN 1:** Add the minimal Pydantic settings model and validator. Re-run; expected PASS.

**RED 2:** Test that explicit `local` and `test` settings accept synthetic auth only with a valid synthetic staff UUID and database URL. Expected RED: missing validation/field behavior.

**GREEN 2:** Add only the required fields and secret-safe representations. Ensure settings/database URL are never logged through `repr`.

Run all unit tests and commit: `security(auth): constrain synthetic principal to local tests`.

### Task 3: Define permission and principal behavior

**Objective:** Establish named-permission authorization without role-name shortcuts.

**Files:**
- Create first: `tests/unit/auth/test_permissions.py`
- Then create: `src/golden_rose/auth/principal.py`
- Then create: `src/golden_rose/auth/permissions.py`

**RED→GREEN cycles:**

1. Principal with `employer:draft:create` is allowed.
2. Principal without it is denied.
3. Platform-style role labels without the named permission are denied.
4. Actor ID is stable UUID data and cannot be request supplied.

Run `uv run pytest tests/unit/auth/test_permissions.py -v`; expected all PASS after individual cycles.

Commit: `security(auth): add draft employer permission boundary`.

### Task 4: Define the minimal request/response schemas

**Objective:** Enforce the accepted first-slice field boundary before persistence exists.

**Files:**
- Create first: `tests/unit/api/test_employer_schemas.py`
- Then create: `src/golden_rose/api/staff/schemas.py`

Use separate RED→GREEN cycles for:

1. accepted household request;
2. accepted business request;
3. NFC normalization and outer-whitespace trimming;
4. blank-name rejection;
5. >200-character rejection;
6. control-character rejection;
7. invalid employer type;
8. unknown-property rejection;
9. rejection of client-supplied `legal_name`, state, source, actor, timestamp, ID, or version;
10. UTC/RFC3339 response serialization.

Before writing custom validation/error handling, run a disposable FastAPI/Pydantic probe against the locked versions to observe actual `extra="forbid"`, header parsing, and default `422` body behavior. Remove the probe after recording the observed behavior in `NOTES.md`; write RED tests only for defaults that violate this accepted contract.

Run `uv run pytest tests/unit/api/test_employer_schemas.py -v` after each cycle.

Commit: `feat(staff): define draft employer API contract`.

### Task 5: Add the PostgreSQL test boundary and initial migration

**Objective:** Prove schema creation/evolution and append-only constraints on the selected database.

**Files:**
- Create: `compose.yaml`
- Create: `alembic.ini`
- Create: `migrations/env.py`
- Create: `migrations/script.py.mako`
- Create first: `tests/integration/conftest.py`
- Create first: `tests/integration/test_initial_migration.py`
- Then create: `migrations/versions/0001_create_first_slice_tables.py`
- Then create: `src/golden_rose/database.py`
- Then create: `src/golden_rose/persistence/models.py`

The Compose service must:

- use PostgreSQL 16;
- bind only to `127.0.0.1:55432`;
- require a local ignored password/environment value;
- use synthetic/test database/user names;
- expose a health check;
- avoid production-like persistence; and
- have no cloud/network integration.

After explicit service-start approval:

1. Start only the test database with `docker compose --env-file .env.test up -d postgres-test`; do not rely on ambient Compose variables.
2. **RED:** run the migration test before the migration file exists; expected failure because required tables/constraints are absent.
3. **GREEN:** add migration/models and run `uv run alembic upgrade head`.
4. Assert exact columns/types/checks for all three tables, command-receipt primary-key serialization, receipt/event foreign key, entity-sequence uniqueness, and immutability triggers.
5. Assert direct `UPDATE` and `DELETE` on both `command_receipts` and `audit_events` fail.
6. Run `uv run alembic downgrade base`; expected all three tables plus trigger/function removed.
7. Run `uv run alembic upgrade head` again; expected clean success.
8. Prove the application never calls `metadata.create_all` through a repository search/test guard.

Commit: `feat(db): add employer command receipt and audit schema`.

### Task 6: Create one successful atomic command

**Objective:** Create the domain row and audit event in one transaction.

**Files:**
- Create first: `tests/integration/application/test_create_draft_employer.py`
- Then create: `src/golden_rose/clock.py`
- Then create: `src/golden_rose/identifiers.py`
- Then create: `src/golden_rose/persistence/employers.py`
- Then create: `src/golden_rose/persistence/command_receipts.py`
- Then create: `src/golden_rose/persistence/audit_events.py`
- Then create: `src/golden_rose/application/create_draft_employer.py`

**RED 1:** Invoke the wished-for command with fixed clock/IDs, permitted principal, command UUID, type, and display name. Assert one receipt, one employer, and one event with exact version/actor/sequence/classification semantics. Expected RED: command missing.

**GREEN 1:** Implement the minimum transaction path.

**RED 2:** Assert event `changed_fields` contains only approved shape/values and omits the display-name value/full row/request body. Expected RED until typed event construction is enforced.

**GREEN 2:** Implement the narrow typed changed-field builder.

**RED 3:** Assert no implicit commit occurs in persistence helpers; only the application command controls commit/rollback. Expected RED if a helper commits.

**GREEN 3:** Keep persistence helpers flush/query-only under the caller-owned transaction.

Run focused tests, then all unit/integration tests.

Commit: `feat(staff): create draft employer with atomic audit event`.

### Task 7: Prove rollback and idempotency under real PostgreSQL

**Objective:** Demonstrate failure and retry behavior, not just the happy path.

**Files:**
- Extend first: `tests/integration/application/test_create_draft_employer.py`
- Modify only after RED: `src/golden_rose/application/create_draft_employer.py`
- Modify only if needed: `src/golden_rose/persistence/employers.py`
- Modify only if needed: `src/golden_rose/persistence/command_receipts.py`
- Modify only if needed: `src/golden_rose/persistence/audit_events.py`

Use separate RED→GREEN cycles:

1. **Audit failure rollback:** deterministically collide a supplied audit-event ID with an existing event; assert the new receipt/employer do not persist and no partial event appears.
2. **Identical replay:** same actor, command UUID, command type, and canonical payload returns the original employer/event with no duplicate receipt/domain/event rows.
3. **Conflicting replay:** same command UUID with a changed actor or accepted field raises `idempotency_conflict`; original rows remain unchanged and the prior resource is not disclosed.
4. **Concurrent identical commands:** two independent sessions/threads race on the same command UUID; assert one receipt, one employer, one event, and two successful equivalent results.
5. **Concurrent conflicting commands:** one commits, the other receives conflict; assert one authoritative result.
6. **Transaction failure hygiene:** safe application exception carries no SQL, URL, request body, display name, or driver detail.

Do not mock transaction behavior for these tests. Use real independent PostgreSQL connections.

Commit: `test(staff): prove atomic retry and conflict behavior`.

### Task 8: Expose the staff endpoint and denial-before-write path

**Objective:** Complete the vertical HTTP tracer without introducing real auth or public routes.

**Files:**
- Create first: `tests/integration/api/test_staff_employers.py`
- Then create: `src/golden_rose/api/errors.py`
- Then create: `src/golden_rose/api/dependencies.py`
- Then create: `src/golden_rose/api/staff/employers.py`
- Then create: `src/golden_rose/main.py`

Use separate RED→GREEN cycles:

1. permitted request returns `201` and the exact body without advertising an unimplemented retrieval route;
2. identical replay returns same resource plus replay evidence;
3. conflicting replay returns safe `409` problem details;
4. denied principal returns `403` and database counts remain unchanged;
5. missing, malformed, nil, or non-v4 idempotency returns the approved `400` problem details;
6. body violations return `422` without framework internals;
7. actor/role/permission headers are ignored or rejected and cannot elevate authority;
8. known database unavailability returns safe `503`; unexpected failure returns safe `500`; both leave no partial receipt/employer/event;
9. OpenAPI exposes only the intended staff route (plus framework schema endpoints if retained), no public route, no GET employer route, and no client-settable system fields;
10. response/log capture contains no database URL, SQL parameters, request body, or internal exception.

Use dependency overrides only in tests. The normal local synthetic dependency obtains its fixed principal from validated settings.

After all API tests pass, obtain/confirm service-start approval, run Uvicorn on loopback only, submit one fictional synthetic request with a generated idempotency UUID, verify the real `201` response and one replay, then stop the API process and test database. Do not paste the database URL/password into the command transcript or evidence.

Commit: `feat(api): expose authorized draft employer command`.

### Task 9: Add application CI and supply-chain evidence

**Objective:** Make the code PR self-verifying without provisioning application infrastructure.

**Files:**
- Create: `.github/workflows/application-quality.yml`

The workflow targets PRs to `develop` and `main`, uses Python 3.12/uv locked dependencies, and an ephemeral PostgreSQL 16 service. One stable job/check named `application` runs:

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
uv run cyclonedx-py environment --pyproject pyproject.toml --output-reproducible --of JSON -o build/backend-sbom.cdx.json
```

Validate the SBOM during generation and upload ignored `build/backend-sbom.cdx.json` as non-production CI evidence; do not commit it. Do not start cloud services or use repository/environment secrets. Ephemeral CI database credentials are non-production and scoped to the job.

Do not change desired branch-protection policy in the feature slice before the new check is qualified. After `application` succeeds on the reviewed real PR and that PR merges, create a separate `ci/require-application-check` governance slice to update `infra/github/repo-policy.json`; apply/verify that reviewed policy only with separate approval.

Commit: `ci: add backend application quality gate`.

### Task 10: Close the coding lane and produce review evidence

**Objective:** Leave a clean branch for independent review.

**Files:**
- Modify: `CURRENT_WORK.md`
- Modify: `ROADMAP.md`
- Modify: `NOTES.md`
- Modify: `TECHNOLOGY_DECISIONS.md` only if implementation evidence changes a decision status/boundary.
- Modify: `docs/planning/phase-1-operational-discovery-register.md` with actual discoveries only.

Run locally, with the project environment and approved synthetic PostgreSQL service:

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
uv run cyclonedx-py environment --pyproject pyproject.toml --output-reproducible --of JSON -o build/backend-sbom.cdx.json
git diff --check origin/develop...HEAD
```

Run Gitleaks against the exact commit range. Record exact base/head SHAs, bytes/commits scanned, migration output, tests passed, coverage, audit result, and any warnings. Confirm generated/client artifacts, local `.env` files, database files, logs, and caches are untracked/ignored.

Update living docs with observed evidence only. Push `feat/staff-draft-employer-tracer`, then stop and hand the branch to the review session without opening a PR.

Suggested final coding commit: `docs: hand draft employer tracer to review`.

## 7. Acceptance evidence

The first slice is implementation-complete only when all are true:

- [ ] Plan and ADR packet was reviewed and merged before code began.
- [ ] Coding branch began at the exact merged `origin/develop` tip.
- [ ] Every production behavior was preceded by an observed, correctly failing test.
- [ ] Only synthetic test data appears in fixtures/evidence.
- [ ] PostgreSQL migration upgrade→downgrade→upgrade succeeds.
- [ ] Authorized create returns the server-controlled draft employer.
- [ ] Denied principal causes zero domain/audit writes.
- [ ] Employer and audit event commit atomically.
- [ ] Forced event failure leaves no employer row.
- [ ] Identical retry/concurrent retry yields one employer and one event.
- [ ] Conflicting idempotency reuse returns safe conflict without mutation.
- [ ] Audit rows reject update/delete.
- [ ] Synthetic auth cannot start in production mode.
- [ ] No request-controlled actor/role/permission seam exists.
- [ ] No sensitive body/database/SQL detail appears in errors or logs.
- [ ] Ruff, mypy, pytest/coverage, migrations, pip-audit, Gitleaks, and diff checks pass.
- [ ] Independent review reports no unresolved High/Blocker issue.
- [ ] GitHub branch-policy, repository-hygiene, application, and secret-scan checks pass before merge.

## 8. Recovery, rollback, and stop boundaries

### Local/test recovery

The database contains fictional disposable data only. Stop the API/test process, stop the approved Compose service, remove its disposable test state, restart, and run `alembic upgrade head` plus the full suite. Do not preserve or restore test state as if it were client authority.

### Schema rollback evidence

The initial migration is reversible only because this slice admits no live data. CI/local evidence must prove downgrade to base and re-upgrade. Once live data is ever admitted, dropping authoritative tables is not an accepted operational rollback; future changes use expand/backfill/switch/retire and forward recovery.

### Code rollback

Before merge, revert/fix on the feature branch. After merge to `develop`, revert the squash commit or apply a focused fix through the ordinary protected flow. A `hotfix/*` branch is reserved for an urgent releasable/production issue and does not bypass review, checks, migration safety, or evidence.

### Hard stops

Stop and return to planning if implementation would require:

- a new field or state beyond this request contract;
- real identity, client/live data, cloud, public access, external provider, or exact location;
- weakening permission, atomicity, append-only, or idempotency behavior;
- storing request bodies, unrestricted JSON, display-name values in ordinary audit payloads, or secrets in logs;
- changing the accepted domain/audit authority model;
- starting an unapproved service; or
- bypassing the independent review lane.

## 9. Review focus

The review session should prioritize:

1. synthetic-auth escape or request-controlled identity/permission;
2. authorization occurring after any read/write;
3. split employer/audit commits or hidden ORM hooks;
4. broken concurrent idempotency/race handling;
5. audit mutability or unrestricted payloads;
6. migration downgrade/constraint/trigger correctness;
7. PostgreSQL-only behavior accidentally replaced by SQLite/mocks;
8. PII/credential/SQL leakage in errors, logs, test output, or CI;
9. unapproved fields/routes/services/dependencies;
10. CI/policy changes that could create bypasses or unstable required checks.

Any High/Blocker finding blocks PR readiness.