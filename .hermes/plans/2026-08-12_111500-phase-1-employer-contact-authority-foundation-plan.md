# Phase 1 EmployerContact Authority Foundation Implementation Plan

> **For Hermes:** Publish and independently review this planning packet first. After it is accepted and merged to protected `develop`, use `plan-driven-tdd-execution` from a fresh branch at that exact merged tip. Do not implement from the current planning worktree.

**Goal:** Add the smallest adjacent Phase 1 entity slice: a synthetic/local backend-only EmployerContact create + bounded parent collection-query + exact-read tracer, while generalizing the Employer-only receipt/audit authority spine without weakening it.

**Architecture:** Add one strict child identity under a draft Employer, with only `full_name` supplied by the client. Migration `0004` introduces an internal entity-authority registry so command receipts and audit events can refer to Employer and EmployerContact through the same type-bound integrity contract. Create remains one atomic, idempotent transaction with ordinary-row mutation guards on receipt/audit authority; bounded parent collection-query and exact read remain authorized, minimized, no-store, and write-free. The collection query is the minimum authoritative rediscovery seam after tab-memory loss: no name filter, no count, and no global contact lookup.

**Tech Stack:** Python 3.12, FastAPI/Pydantic v2, synchronous SQLAlchemy 2/psycopg 3, Alembic, PostgreSQL 16, pytest, Ruff, mypy, Bandit, uv. No frontend files or new dependencies.

**Controlling accepted planning boundary:** `docs/adr/ADR-0008-phase-1-employer-contact-authority-foundation.md`; publication through protected `develop` remains required before Task 1.

---

## Why this target

PR #18 is merged at `a4d8f90`, and the complete current application-quality gate is green. EmployerContact is the narrowest next entity in the accepted canonical chain and establishes the reusable multi-entity command/audit integrity seam needed by later Worksite and StaffingRequest slices.

This plan intentionally does **not** try to close many unrelated roadmap rows at once. The unchecked Phase 1 list mixes production identity, live-data/counsel gates, worksites, requests, queue, calendar, map, accessibility, training, and broad persistence epics. Bundling them would create an unauditable migration and force unresolved business/privacy decisions. This slice makes measurable progress toward `Employer/contact/worksite/request/shift persistence`; it does not mark that broad item complete.

## Accepted planning contract at a glance

| Concern | Accepted planning contract |
|---|---|
| Create route | `POST /api/staff/v1/employers/{employer_id}/contacts` |
| Collection route | `POST /api/staff/v1/employers/{employer_id}/contacts/query` with strict `page_size` + opaque cursor body only |
| Exact read route | `GET /api/staff/v1/employers/{employer_id}/contacts/{employer_contact_id}` |
| Client field | Required normalized `full_name`, 1–200 Unicode scalar values, NFC, trimmed, no Unicode control-category characters |
| Server fields | IDs, parent ID, creator/updater attribution, timestamps, `version = 1` |
| Parent gate | Employer exists and is `draft` |
| Permissions | `employer:read` + `employer_contact:draft:create`; `employer:read` + `employer_contact:read` |
| Create result | `201`, strict JSON, `Cache-Control: no-store`, `Idempotency-Result-Version: 1`, replay header only on replay |
| Collection result | `200`, max 50 minimized items + opaque parent/page-size-bound `next_cursor`, no count/name filter |
| Exact read result | `200`, strict minimized JSON, `Cache-Control: no-store` |
| Empty collection | Existing parent returns `200` with `{"items":[],"next_cursor":null}` |
| Missing child | Parent-scoped `404`; no cross-parent disclosure |
| Event | `employer_contact.created`, sequence/version `1`, contact name omitted from approved audit values |
| Non-scope | Contact methods/status/edit/delete/name or global search/unbounded list/count/UI, Worksite/Request/Shift, communications, real auth, deployment/live data |

## Required approval gates

Implementation remains blocked until all are true:

1. PR #18 merged and the planning lane is based on exact `origin/develop` at `a4d8f90` — **observed complete**.
2. Beatrice accepts or revises ADR-0008’s field, lifecycle, permission, and multi-entity authority decisions — **accepted 2026-08-12**.
3. Independent API/security, persistence/migration, and TDD/executability reviews report no Blocker/High/Medium findings — **complete; exact-artifact closure rereviews passed**.
4. The accepted ADR, this plan, ADR/decision indexes, and living-doc lane update merge through protected `develop`.
5. A coding session fetches that merged tip, confirms a clean tree, and obtains separate approval before Git mutation or PostgreSQL service use.

## Exact non-scope

- Phone, email, relationship/title, preferred language/contact method, contact status, consent, outreach, notifications, or vendor messaging.
- Contact correction, later change, supersession, cancellation, deletion, name/global search, unbounded list/count, export, browser UI, localization, or accessibility surface. The bounded parent collection-query is explicitly in scope only as backend rediscovery.
- Worksite/exact address, CDTA/service zone/map, StaffingRequest/ShiftNeed/queue/calendar, household/general-labor extension fields.
- Real identity provider, staff accounts, MFA/sessions, Platform Administrator support path, deployment/GCP, client/live data, migration/import, documents, public routes, legal/business behavior.
- Generic arbitrary entity types, generic metadata/custom fields, event sourcing, unrestricted audit payloads, or relaxed receipt/event integrity.

---

## Task 0: Publish and accept the planning packet

**Objective:** Make the accepted planning decisions durable and independently reviewable before code.

**Files:**
- Create: `docs/adr/ADR-0008-phase-1-employer-contact-authority-foundation.md`
- Create: `.hermes/plans/2026-08-12_111500-phase-1-employer-contact-authority-foundation-plan.md`
- Modify: `docs/adr/README.md`
- Modify: `TECHNOLOGY_DECISIONS.md`
- Modify: `AGENTS.md`
- Modify: `CURRENT_WORK.md`
- Modify: `ROADMAP.md`
- Modify: `NOTES.md`
- Modify: `docs/planning/phase-1-staff-permission-matrix.md`
- Modify: `docs/planning/phase-1-canonical-field-purpose-inventory.md`
- Modify only where status language is stale: `README.md`, `ARCHITECTURE.md`, `SECURITY.md`, `TECHNICAL_REQUIREMENTS.md`, `docs/planning/phase-1-operational-discovery-register.md`

**Steps:**
1. Mark PR #18/remediation as merged history and set the active lane to EmployerContact planning publication.
2. Record ADR-0008 first as Proposed and then, only after review and Beatrice's decision, as an Accepted planning boundary; never call it implementation authority before protected merge and coding rebaseline.
3. Record the 2026-08-12 review evidence and target decision in the bottom-most current-date `NOTES.md` section.
4. Run path/reference and whitespace checks.
5. Dispatch independent API/security, persistence/migration, and TDD/handoff reviewers.
6. Remediate every Blocker/High/Medium planning finding and perform one complete finding-ledger rereview.
7. Obtain Beatrice’s explicit acceptance, then change ADR-0008/TD status to Accepted — **complete 2026-08-12**.
8. Commit/push/open planning-only PR only under separate approval; require protected checks and merge before Task 1.

**Verification:**
- `git diff --check`
- all referenced paths exist;
- the planning diff contains no product code, dependency, lockfile, or migration change;
- living docs preserve chronological Proposed-to-Accepted evidence and consistently say the current boundary is accepted planning, never implemented.

## Task 1: Coding-lane rebaseline

**Objective:** Prove implementation begins from the accepted merged planning tip.

**Files:** Read only.

**Steps:**
1. Fetch/prune and verify local `develop == origin/develop`.
2. Verify the accepted ADR/plan are present at the fetched tip.
3. Verify clean worktree and create a correctly prefixed feature branch only under approval.
4. Reserve Alembic revision ID `0004_employer_contact_authority` and re-check no competing revision exists.
5. Record exact base SHA and current service/runtime posture; do not start PostgreSQL until separately approved.

## Task 2: Migration and metadata — generalized entity authority

**Objective:** Generalize receipt/event integrity and add EmployerContact storage without accepting arbitrary authority shapes.

**Files:**
- Create: `migrations/versions/0004_employer_contact_authority.py`
- Modify: `src/golden_rose/persistence/models.py`
- Create: `src/golden_rose/persistence/entity_authorities.py`
- Modify: `src/golden_rose/application/create_draft_employer.py`
- Modify: `tests/integration/test_initial_migration.py`
- Modify: `tests/integration/application/test_create_draft_employer.py`

**Proposed tables:**

`entity_authorities`
- `entity_type varchar(32)`
- `entity_id uuid`
- `employer_id uuid` nullable, unique, FK → `employers.employer_id`
- `employer_contact_id uuid` nullable, unique, FK → `employer_contacts.employer_contact_id`
- composite primary key `(entity_type, entity_id)`
- check: `entity_type IN ('employer', 'employer_contact')`
- check: exactly one concrete-ID column is non-null, matches `entity_type`, and equals `entity_id`
- ordinary-row `UPDATE`/`DELETE` guards; do not claim protection from owner-level `TRUNCATE`, DDL, or trigger changes

`employer_contacts`
- `employer_contact_id uuid` primary key
- `employer_id uuid` FK → `employers.employer_id`
- `full_name varchar(200)` nonblank
- `created_at`, `updated_at` timezone-aware and non-null
- `created_by`, `updated_by` UUID and non-null
- `version integer`, check `version = 1` for this tracer
- unique `(employer_id, employer_contact_id)` for parent-scoped identity

**Authority changes:**
- Backfill `('employer', employer_id)` for every Employer.
- Use concrete deferrable foreign keys plus non-deferrable type/null/equality checks so a registry row cannot authorize a nonexistent Employer or EmployerContact; do not rely only on application insertion order.
- Replace `command_receipts.result_entity_id → employers` with `(result_entity_type, result_entity_id) → entity_authorities`.
- Replace `audit_events.entity_id → employers` with `(entity_type, entity_id) → entity_authorities`.
- Extend receipt↔event composite keys/FKs to include entity type.
- Extend allowlists only with `create_employer_contact` / `employer_contact.created` and exact version-1 authority shape. Enumerate command/entity/event bindings: `create_draft_employer` and `revise_draft_employer` require `result_entity_type='employer'` with their exact Employer event/version rules; `create_employer_contact` requires `result_entity_type='employer_contact'`, `result_event_type='employer_contact.created'`, and result version `1`. Each event schema/type is likewise bound to its exact `entity_type`.
- Preserve ordinary-row update/delete triggers on receipts/events and add them to the authority registry. Record that the synthetic/local owner role can bypass these through `TRUNCATE`, DDL, or trigger changes; production non-owner grants are a deployment gate, not evidence in this slice.
- Refuse downgrade when any EmployerContact or contact authority/receipt/event exists.

**Required upgrade order:**
1. In the migration transaction, take `SHARE ROW EXCLUSIVE` locks in writer-compatible fixed order on `command_receipts`, `employers`, then `audit_events`; hold them through validation and commit so no predecessor writer can race the backfill or constraint swap. This order follows the merged receipt-first command path and avoids a migration/writer lock inversion.
2. Create `employer_contacts` with its concrete parent FK and domain checks.
3. Create `entity_authorities` with concrete deferrable FKs to `employers` and `employer_contacts`, mutually exclusive concrete-ID columns, type/null/equality checks, and ordinary-row update/delete guards.
4. Backfill exactly one `('employer', employer_id, employer_id, NULL)` authority row per existing Employer; verify counts and absence of orphan/mismatched rows before changing receipt/event constraints.
5. Create the new type-inclusive receipt/event unique keys needed as referenced targets.
6. Add each new foreign key with its exact `DEFERRABLE INITIALLY DEFERRED` property and, independently, use PostgreSQL's staged `ADD CONSTRAINT ... NOT VALID` form where that constraint class permits it; then explicitly `VALIDATE CONSTRAINT` each while predecessor constraints still protect existing data. For constraint classes PostgreSQL cannot add as `NOT VALID`, use the lock-protected immediate-validation form and assert its catalog definition in the migration test. Do not conflate deferrability with validation state.
7. Replace command/event checks with the enumerated command→result-entity→event/version and event-schema/type→entity-type contract.
8. Only after every new constraint validates, drop the superseded Employer-only domain FKs and type-omitting receipt/event FKs and unique keys.
9. Run explicit correspondence/count probes before completing the migration. Do not disable ordinary-row guards or rewrite historical receipt/event rows.
10. In the same Task 2 checkpoint, adapt `create_draft_employer` to insert its Employer authority after the domain row and before flush/commit. The upgraded schema is not GREEN until fresh Employer create and replay succeed under `0004` and a late authority failure rolls back Employer + authority + receipt + event.

**Required downgrade lock and reversal order:**
1. Begin one transaction and take `SHARE ROW EXCLUSIVE` locks in writer-compatible fixed order on `command_receipts`, `employers`, `employer_contacts`, `entity_authorities`, then `audit_events` before any refusal query or DDL.
2. Preflight all contact domain/authority/receipt/event evidence. If any successor evidence exists, raise before schema mutation; prove the transaction leaves exact schema, data, constraints, and guards unchanged.
3. For an allowed downgrade, drop successor reverse/child foreign keys first; restore exact revision-0003 unique/check targets and Employer-only receipt/event foreign keys; validate them; then remove successor constraints, `entity_authorities`, and `employer_contacts` in dependency order.
4. Preserve receipt/event ordinary-row update/delete guards throughout. Add a concurrent-writer probe and a forced failed-preflight/DDL probe proving transactional rollback restores the exact pre-attempt state.

**Exact TDD cycles:**

1. `test_employer_contact_metadata_contains_exact_columns_and_constraints`
   - RED: table absent from metadata.
   - GREEN: add minimal metadata table/constraints.
2. `test_entity_authority_metadata_binds_receipts_and_events_by_type_and_id`
   - RED: current FKs are Employer-ID-only.
   - GREEN: add registry and type-bound composite metadata FKs.
3. Coupled migration/writer checkpoint: `test_employer_contact_migration_upgrades_populated_employer_authority_without_rewriting_history` and `test_existing_employer_create_remains_atomic_and_replay_safe_on_employer_contact_schema`
   - Write both tests before production changes. RED: migration/revision is absent; the upgraded-schema compatibility node cannot pass without both the schema and writer adaptation.
   - GREEN: in one minimum checkpoint, implement the complete head-schema upgrade in the required lock/order and adapt the merged Employer writer. Run both exact nodes together and require populated backfill/history preservation plus fresh Employer + authority + receipt + event, zero-write replay, and late-authority-failure rollback. Never declare either an intentionally broken intermediate GREEN.
4. `test_employer_contact_live_schema_rejects_cross_type_orphan_and_command_event_entity_mismatches_at_commit`
   - Expected GREEN regression after cycle 3 if the coupled checkpoint is correct; if it fails, repair only the exact concrete-domain FK, mutually exclusive ID/type/equality constraint, or enumerated command/event mapping defect.
   - Exercise every otherwise-valid command/entity and event/entity cross-product mismatch, including Employer authority used by contact command/event and EmployerContact authority used by Employer command/event.
5. `test_employer_contact_authority_tables_reject_ordinary_update_and_delete`
   - Expected GREEN regression after cycle 3 because registry guards are part of the complete head-schema upgrade; a failure is a product integrity defect, not a planned later feature.
   - Explicitly do not use owner-level `TRUNCATE`, DDL, or trigger changes as evidence for this row-mutation claim.
6. `test_employer_contact_upgrade_locks_out_concurrent_predecessor_writer_until_constraint_swap_commits`
   - RED until the fixed upgrade lock order exists.
   - GREEN: coordinated PostgreSQL writer cannot enter a backfill/constraint race and completes safely only after migration commit.
7. `test_employer_contact_empty_downgrade_restores_revision_schema_and_guards`
   - RED: downgrade absent.
   - GREEN: implement the minimum empty-state reversal to exact `0003` schema and guards.
8. `test_employer_contact_populated_employer_only_downgrade_preserves_rows_correspondence_constraints_and_guards`
   - First run may be GREEN if the minimum cycle-7 downgrade already preserves predecessor-compatible rows; classify it honestly. If RED, repair the exact populated Employer-only back-migration defect without widening successor support.
9. `test_employer_contact_populated_successor_downgrade_fails_closed_and_preserves_schema_data_and_guards`
   - RED unless cycle 7 already added the required preflight.
   - GREEN: preflight all contact domain/registry/receipt/event evidence before any schema mutation.
10. `test_employer_contact_downgrade_lock_prevents_preflight_race_and_failed_ddl_rolls_back_exact_state`
    - RED until downgrade holds the fixed lock set through refusal/reversal commit.
    - GREEN: coordinated successor writer cannot appear after preflight; forced failure leaves exact schema, data, constraints, and guards unchanged.

**Focused verification:**
- `env -u PYTHONPATH uv run pytest tests/integration/test_initial_migration.py -q`
- direct Alembic `upgrade head → downgrade 0003_revision_compat → upgrade head` on an approved disposable database.

## Task 3: Shared contact normalization

**Objective:** Normalize and validate contact names at the authoritative application boundary before fingerprinting or storage.

**Files:**
- Create: `src/golden_rose/application/contact_text.py`
- Create: `tests/unit/application/test_contact_text.py`

**Exact TDD cycles:**

1. `test_validate_contact_full_name_normalizes_nfc_and_outer_whitespace`
   - RED: validator absent.
   - GREEN: NFC + trim.
2. `test_validate_contact_full_name_rejects_blank_control_and_over_200_scalar_values`
   - RED: constraints absent.
   - GREEN: bounded value-safe `ValueError` messages that do not echo input.
3. `test_contact_name_boundary_accepts_200_and_rejects_201_unicode_scalars`
   - RED: exact count boundary absent.
   - GREEN: scalar-count contract aligned with Pydantic/Python.

## Task 4: Persistence primitives

**Objective:** Add narrow registry/contact persistence without transaction ownership leaking out of the application service.

**Files:**
- Modify: `src/golden_rose/persistence/entity_authorities.py` created in Task 2
- Create: `src/golden_rose/persistence/employer_contacts.py`
- Modify: `src/golden_rose/persistence/command_receipts.py`
- Modify: `src/golden_rose/persistence/audit_events.py`
- Reuse the Task 2 minimum Employer-create compatibility adaptation; modify it here only if a later narrow persistence-helper refactor preserves the Task 2 regressions unchanged.
- Test through Tasks 5–6 integration nodes; add focused unit doubles only for safe persistence translation.

**Required functions:**
- insert Employer/EmployerContact authority identity;
- insert/get exact parent-scoped EmployerContact;
- query one bounded parent-scoped EmployerContact page by deterministic keyset, without a count query;
- reserve contact-create receipt with exact command/result authority;
- insert minimized `employer_contact.created` event;
- no helper commits independently.

**Required Employer-create compatibility:** Task 2 already made the existing `create_draft_employer` transaction insert Employer authority after the domain row and before flush/commit. Task 4 may factor that primitive into the shared module but must not create the first working writer or weaken the upgraded-schema regression.

**Regression:** Existing Employer create/revise helpers and receipt replay remain exact; no generic stringly typed public helper is introduced.

## Task 5: Idempotent EmployerContact create command

**Objective:** Create one contact, registry identity, receipt, and event atomically beneath an authorized draft Employer.

**Files:**
- Create: `src/golden_rose/application/create_employer_contact.py`
- Create: `tests/integration/application/test_create_employer_contact.py`
- Modify only if shared errors are needed: `src/golden_rose/application/errors.py`

**Order of authority:**
1. Check both required permissions.
2. Parse and validate the raw idempotency header as UUIDv4, then normalize `full_name` and build the fingerprint including parent ID. The HTTP layer passes transport-valid raw strings; it does not perform these semantic operations.
3. Resolve replay/conflict without exposing another result.
4. Reserve receipt.
5. Lock/read exact draft parent and reject missing/non-draft parent.
6. Insert the contact domain row, then its concrete authority row, then the minimized event; all remain in the same deferred-constraint transaction.
7. Flush and commit once; translate known SQLAlchemy failures to `SafePersistenceError` after rollback.

**Exact TDD cycles:**

1. `test_create_employer_contact_creates_authority_contact_receipt_and_event_atomically`
   - RED: module/command absent.
   - GREEN: minimum successful transaction.
2. `test_create_employer_contact_denial_precedes_parent_receipt_and_writes`
   - Expected GREEN after cycle 1 if authorization order is already correct; classify honestly.
3. `test_create_employer_contact_requires_existing_draft_parent_without_receipt`
   - RED if parent gating is incomplete.
   - GREEN: locked parent check and rollback.
4. `test_create_employer_contact_normalizes_before_fingerprint_and_storage`
   - Expected GREEN regression if Task 3 is correctly reused.
5. `test_create_employer_contact_identical_replay_returns_current_contact_without_writes`
   - RED: replay absent.
   - GREEN: exact receipt validation and current read.
6. `test_create_employer_contact_rejects_changed_actor_parent_type_schema_or_payload_without_disclosure`
   - RED: conflict matrix incomplete.
   - GREEN: full authority comparison.
7. `test_create_employer_contact_concurrent_identical_same_key_has_one_fresh_and_one_replay_at_read_committed`
   - Harness first: use two independent sessions, assert `SHOW transaction_isolation = 'read committed'` on both, and install a barrier immediately before the receipt `INSERT ... ON CONFLICT` reservation; setup-only failures are not product REDs.
   - RED if the first behavior run produces duplicate authority or an unsafe outcome.
   - GREEN: one fresh result + one replay and exact counts of one contact, one authority, one receipt, and one event.
8. `test_create_employer_contact_concurrent_changed_authority_same_key_has_one_fresh_and_one_conflict_at_read_committed`
   - Harness first: reuse the verified two-session barrier immediately before receipt reservation.
   - RED if changed actor, parent, or normalized payload can replay or write a second authority chain.
   - GREEN: one fresh result + one bounded conflict and exact counts of one contact, one authority, one receipt, and one event. Parametrize actor, parent, and payload; command/schema type mismatch remains covered by the sequential authority matrix.
   - This slice supports PostgreSQL `READ COMMITTED`; any additional isolation-level retry/serialization contract requires a later reviewed decision.
9. `test_create_employer_contact_late_failure_rolls_back_every_authority_row`
   - RED if atomicity missing.
   - GREEN: one transaction/rollback.
10. `test_create_employer_contact_audit_event_omits_full_name_value`
   - Expected GREEN regression if event builder is minimized.
11. `test_create_employer_contact_safe_persistence_error_redacts_driver_and_submitted_values`
    - RED if raw details escape.
    - GREEN: bounded shared persistence error.

## Task 6: Bounded parent collection-query and exact read commands

**Objective:** Make contacts authoritatively rediscoverable under their parent and return exact detail without global lookup, count queries, or writes.

**Files:**
- Create: `src/golden_rose/application/contact_cursor.py`
- Create: `src/golden_rose/application/query_employer_contacts.py`
- Create: `src/golden_rose/application/get_employer_contact.py`
- Create: `tests/unit/application/test_contact_cursor.py`
- Create: `tests/integration/application/test_query_employer_contacts.py`
- Create: `tests/integration/application/test_get_employer_contact.py`

**Collection-query contract:**
- request fields: strict `page_size` integer, default `25`, range `1..50`; optional strict cursor string, max 512 characters; no name/filter/sort/count field;
- after framework transport-shape parsing, authorize both `employer:read` and `employer_contact:read`, then semantically validate/decode the raw optional cursor, then resolve the exact parent, then execute the contact query; no denied or invalid-cursor request reaches SQL;
- require the exact parent Employer to exist; missing parent uses the same bounded contact-not-found application error used by exact read;
- order by `created_at DESC, employer_contact_id DESC`; request `page_size + 1`, return at most `page_size`, and derive `next_cursor` only from the final returned row;
- cursor contains exactly version, parent Employer ID, page size, `after_created_at`, and `after_employer_contact_id`; canonical URL-safe base64 transport contains no name or actor data and must be byte-canonical;
- cursor parent/page-size mismatch, malformed shape/type/time/UUID, noncanonical transport, or overlength input is a value-safe validation error before the contact query;
- return exact minimized contact representations plus `next_cursor`; no total count, approximate count, global lookup, receipt/audit/domain write, or cursor persistence.

**Exact TDD cycles:**

1. `test_contact_cursor_round_trips_exact_parent_page_size_and_boundary`
   - RED: cursor helper absent.
   - GREEN: exact canonical payload/transport with no contact name or actor data.
2. `test_contact_cursor_rejects_malformed_noncanonical_cross_parent_and_page_size_mismatch`
   - RED if validation is incomplete.
   - GREEN: one value-safe `ValueError("invalid contact cursor")` boundary.
3. `test_query_employer_contacts_returns_bounded_parent_page_in_deterministic_order_without_count_or_writes`
   - RED: query command absent.
   - GREEN: parent-scoped `page_size + 1` keyset query and minimized page.
4. `test_query_employer_contacts_denial_precedes_cursor_parent_and_contact_access`
   - Expected GREEN if authority order is correct; prove no cursor decode and no SQL.
5. `test_query_employer_contacts_cursor_continues_without_duplicate_or_gap_and_is_parent_page_size_bound`
   - RED until keyset/cursor binding is complete.
   - GREEN: deterministic two-page proof with equal timestamps and UUID tie-break.
6. `test_query_employer_contacts_rejects_invalid_cursor_before_contact_query_without_writes`
   - RED if invalid transport reaches persistence.
   - GREEN: value-safe validation path with zero SQL because cursor validation precedes parent resolution.
7. `test_query_employer_contacts_missing_parent_is_bounded_and_write_free`
   - RED if missing parent is treated as an empty authoritative collection.
   - GREEN: bounded contact-not-found application error.
8. `test_query_employer_contacts_safe_persistence_failure_is_value_safe`
   - RED if SQLAlchemy details escape.
   - GREEN: rollback plus bounded persistence translation.
9. `test_get_employer_contact_returns_exact_parent_scoped_record_without_writes`
   - RED: exact command absent.
   - GREEN: minimized parent-scoped query.
10. `test_get_employer_contact_denial_precedes_parent_and_contact_lookup`
    - Expected GREEN if permission order is correct.
11. `test_get_employer_contact_cross_parent_and_missing_contact_are_indistinguishable`
    - RED if lookup is global.
    - GREEN: query by both parent/contact IDs.
12. `test_get_employer_contact_safe_persistence_failure_is_value_safe`
    - RED if SQLAlchemy details escape.
    - GREEN: bounded persistence translation.

## Task 7: Strict staff API boundary

**Objective:** Expose only approved nested create, bounded collection-query, and exact-read routes with complete no-store problem contracts.

**Files:**
- Create: `src/golden_rose/api/staff/employer_contacts.py`
- Modify: `src/golden_rose/api/staff/schemas.py`
- Modify: `src/golden_rose/api/dependencies.py`
- Modify: `src/golden_rose/auth/permissions.py`
- Modify: `src/golden_rose/main.py`
- Create: `tests/unit/api/test_employer_contact_schemas.py`
- Modify: `tests/unit/auth/test_permissions.py`
- Modify: `tests/unit/api/test_dependencies.py`
- Create: `tests/integration/api/test_staff_employer_contacts.py`
- Modify: `tests/integration/api/test_staff_employer_reads.py` for exact route-surface truth

**Success response fields:**
`employer_contact_id`, `employer_id`, `full_name`, `version`, `created_at`, `updated_at` only.

Collection response fields are exactly `items` (the same strict minimized representation) and `next_cursor` (`string | null`). Collection request fields are exactly `page_size` and `cursor`.

**Route declaration order:** declare static `/contacts/query` before dynamic `/contacts/{employer_contact_id}` so `query` is never parsed as a UUID. Add a direct route-order regression in the OpenAPI/API nodes; do not rely on accidental router behavior.

**Literal response contracts:**

The three approved operations and every explicitly enumerated operation error use `Content-Type: application/json` and `Cache-Control: no-store`, preserving the merged shared-response behavior. Error bodies contain exactly `type`, `title`, `detail`, and `status`; they carry neither `Idempotency-Result-Version` nor `Idempotency-Replayed`. Unmatched routes and unsupported methods retain the merged app/router-level 404/405 contract and are outside this operation-response claim; add route probes only to prove they do not execute contact SQL or reflect submitted path markers, not to invent contact-specific bodies.

**HTTP precedence:** FastAPI transport parsing may reject malformed path UUIDs, a missing required idempotency header, wrong JSON types, and extra/missing fields before principal authorization. Those failures use the literal `400/422` contracts below with no SQL or writes. For transport-valid requests, pass raw idempotency/name/cursor strings across the route boundary; the application command checks permissions first. A denied request with a syntactically shaped but non-UUIDv4 key, semantically invalid/PII-bearing name, malformed/overlength/cross-parent cursor, or valid path returns the exact `403` without UUIDv4 parsing, name normalization, cursor decode, SQL, or writes.

Replace route use of the merged parsing dependency with a contact-specific raw required-header dependency that returns the transport-valid string without UUID parsing. Keep the merged Employer routes and `get_idempotency_key` behavior unchanged. The contact application command owns UUIDv4 semantic validation after permission checks.

| Class | Status | Exact body |
|---|---:|---|
| Missing required `Idempotency-Key`, or semantically invalid UUIDv4 key after authorization | 400 | `{"type":"https://golden-rose.local/problems/invalid-idempotency-key","title":"Bad Request","detail":"invalid idempotency key","status":400}` |
| Malformed path UUID, extra/missing body field, wrong type, or semantically invalid normalized name/cursor after authorization | 422 | `{"type":"https://golden-rose.local/problems/request-validation","title":"Unprocessable Entity","detail":"request validation failed","status":422}` |
| Missing either required named permission | 403 | `{"type":"https://golden-rose.local/problems/forbidden","title":"Forbidden","detail":"forbidden","status":403}` |
| Missing/non-draft parent on create, missing parent on collection query, or missing/cross-parent contact on exact read | 404 | `{"type":"https://golden-rose.local/problems/employer-contact-not-found","title":"Not Found","detail":"employer contact not found","status":404}` |
| Changed actor/parent/type/schema/payload for a reused command ID | 409 | `{"type":"https://golden-rose.local/problems/idempotency-conflict","title":"Conflict","detail":"idempotency conflict","status":409}` |
| Known SQLAlchemy/persistence failure | 503 | `{"type":"https://golden-rose.local/problems/service-unavailable","title":"Service Unavailable","detail":"service unavailable","status":503}` |
| Unexpected exception | 500 | `{"type":"https://golden-rose.local/problems/internal-error","title":"Internal Server Error","detail":"internal server error","status":500}` |

Fresh/replayed create success is exactly `201 application/json`, the six-field strict body above, `Idempotency-Result-Version: 1`, and `Idempotency-Replayed: true` only on replay. Collection query is exactly `200 application/json`, the strict page body, and no idempotency headers. Exact read is exactly `200 application/json`, the same six-field body, and no idempotency headers. No response reflects submitted names, parent/contact IDs, command IDs, SQL, request URLs, or raw exception text outside approved success representations and the opaque cursor.

An existing parent with no contacts is a successful empty collection, not a 404. Only a missing parent produces the collection-query 404; exact read still makes a missing and cross-parent contact byte-equivalent.

**Exact TDD cycles:**

1. `test_employer_contact_create_transport_schema_preserves_raw_name_and_forbids_extra_fields`
   - RED: schema absent.
   - GREEN: strict transport schema rejects wrong/missing/extra fields but preserves the raw string; Task 3 normalization occurs only inside the authorized application command.
2. `test_employer_contact_response_schema_has_exact_minimized_fields_and_rejects_extras`
   - RED: response schema absent.
   - GREEN: exact six-field response contract with no actor/audit fields.
3. `test_employer_contact_permission_constants_have_exact_values_and_do_not_follow_role_labels`
   - RED: constants absent.
   - GREEN: add the two exact named permissions; platform/owner labels alone grant neither.
4. `test_synthetic_principal_has_exact_bounded_employer_and_contact_permissions`
   - RED: synthetic principal lacks the proposed contact permissions.
   - GREEN: add only the two accepted contact permissions to the configured synthetic local principal.
5. `test_request_headers_cannot_grant_employer_contact_permissions`
   - Expected GREEN regression if dependencies continue ignoring authority headers; keep it as a before/after regression and do not stage insecure behavior.
6. `test_employer_contact_query_schemas_have_exact_bounded_fields_and_minimized_page_shape`
   - RED: query/page schemas absent.
   - GREEN: strict page-size/cursor request and exact items/next-cursor response.
7. `test_post_staff_employer_contact_returns_exact_201_contract_and_replay_headers`
   - RED: route absent.
   - GREEN: router maps command result to the literal create success contract.
8. `test_post_staff_employer_contact_failure_matrix_is_exact_no_store_value_safe_and_write_free`
   - RED until every POST class in the literal matrix is mapped; assert exact bodies/media/header absence and zero writes for definitive failures.
   - GREEN: minimal exception mapping through shared no-store helpers.
   - Include combined precedence pairs: denied + syntactically shaped invalid UUIDv4 key/name returns `403` without semantic parsing/normalization/SQL; denied + missing header, malformed path UUID, wrong body type, or missing/extra field returns the transport `400/422` without SQL/writes.
9. `test_post_staff_employer_contact_query_returns_exact_200_bounded_page_without_count_or_writes`
   - RED: query route absent.
   - GREEN: strict query request maps to the Task 6 page contract.
10. `test_post_staff_employer_contact_query_failure_matrix_is_exact_no_store_value_safe_and_write_free`
    - RED until invalid page size/cursor, denied, missing parent, persistence, and unexpected classes match the literal 422/403/404/503/500 matrix.
    - GREEN: authorization-before-cursor/query mapping; no idempotency headers.
    - Include denied + malformed/overlength/cross-parent raw cursor: exact `403`, no cursor decoder call, SQL, or writes. Transport-invalid body shapes remain value-safe `422` before authorization and perform no SQL/writes.
11. `test_post_staff_employer_contact_query_cursor_is_parent_and_page_size_bound`
    - Expected GREEN if Task 6 is reused exactly; prove cross-parent and changed-page-size reuse is 422 with no contact query.
12. `test_get_staff_employer_contact_returns_exact_200_parent_scoped_contract_without_writes`
   - RED: route absent.
   - GREEN: exact read mapping with no idempotency headers.
13. `test_get_staff_employer_contact_failure_matrix_is_exact_no_store_value_safe_and_write_free`
   - RED until malformed UUID, denied, missing/cross-parent, persistence, and unexpected classes match the literal matrix.
   - GREEN: bounded read exception mapping; missing and cross-parent are byte-equivalent.
   - Include denied + malformed path UUID as the framework transport `422` with no SQL/writes, and denied + transport-valid absent/cross-parent UUID as exact `403` before lookup.
14. `test_staff_employer_contact_openapi_exposes_only_approved_contract`
    - RED before router inclusion.
    - GREEN: only the three nested paths/methods and strict schemas are exposed.
15. Update the three pre-existing exact route-set guards—`test_openapi_exposes_only_approved_staff_employer_routes`, `test_openapi_exposes_only_intended_staff_route`, and `test_openapi_exposes_only_create_search_detail_and_revision_routes`—with the three exact contact paths/methods.
    - Genuine RED immediately after router inclusion because each merged guard still names the predecessor route set.
    - GREEN: update only those exact approved route sets; no name/global search, unbounded list/count, update, delete, or public route. Keep `test_staff_employer_revision_openapi_exposes_only_approved_contract` aligned to the expanded global path set while preserving all revision-operation/schema assertions unchanged.
16. `test_staff_employer_contact_unmatched_and_method_not_allowed_routes_do_not_execute_or_reflect_contact_markers`
    - Expected GREEN against merged router behavior after route inclusion; classify honestly.
    - Probe unsupported methods on each approved path and one unmatched contact subpath. Preserve app-level 404/405 behavior; assert zero contact SQL/writes and no reflected path, parent, or contact marker. Do not claim these are contact-operation problem responses.
17. `test_staff_employer_contact_routes_do_not_log_contact_or_authority_markers`
    - RED if any new route/error logging reflects operational values.
    - GREEN: with `caplog` and configured access-log capture, exercise create/query/exact success, validation, denial, missing/cross-parent, known persistence, and unexpected failure. Use distinct markers for `full_name`, cursor, parent/contact IDs, idempotency key, SQL/driver text, request URL, authority headers, and raw exceptions; assert none appears in application or captured access logs. Retain the audit assertion that `full_name` occurs only as a changed-field name, never an approved value or ordinary log value.

**Focused verification:**
- `env -u PYTHONPATH uv run pytest tests/unit/api/test_employer_contact_schemas.py tests/unit/auth/test_permissions.py tests/unit/api/test_dependencies.py -q`
- `env -u PYTHONPATH uv run pytest tests/unit/application/test_contact_cursor.py tests/integration/application/test_create_employer_contact.py tests/integration/application/test_query_employer_contacts.py tests/integration/application/test_get_employer_contact.py tests/integration/api/test_staff_employer_contacts.py tests/integration/api/test_staff_employer_reads.py -q`

## Task 8: Preserve existing Employer contracts

**Objective:** Prove the generalized authority migration did not regress the merged Employer family.

**Files:** Tests only unless a genuine regression is found.

**Run:**
- `env -u PYTHONPATH uv run pytest tests/integration/application/test_create_draft_employer.py tests/integration/application/test_revise_draft_employer.py tests/integration/application/test_revise_draft_employer_post_merge.py tests/integration/application/test_get_employer.py tests/integration/application/test_search_employers.py tests/integration/api/test_staff_employers.py tests/integration/api/test_staff_employer_reads.py -q`

**Required invariants:** create/revise replay metadata, receipt/event bidirectional authority, locked no-op derivation, current-authoritative replay, read minimization, search cursor binding, no read writes, exact OpenAPI surface, and safe problem responses remain unchanged.

## Task 9: Complete quality/security gate and independent review

**Objective:** Produce review-grade evidence on the exact executable tree.

**Service boundary:** Use only an explicitly approved disposable PostgreSQL database with synthetic fixtures. Do not start the application, open non-loopback listeners, or use live/client data.

**Canonical sequence:**

```text
node/npm/config exact-version assertions
node lockfile validator tests + validation
env -u PYTHONPATH uv lock --check
env -u PYTHONPATH uv sync --locked --all-groups
npm ci --ignore-scripts and npm --prefix apps/web run verify (unchanged regression)
frontend dependency tree/audit/SBOM generation + validation
env -u PYTHONPATH uv run ruff format --check .
env -u PYTHONPATH uv run ruff check .
env -u PYTHONPATH uv run mypy src tests
env -u PYTHONPATH uv run bandit -q -r src
env -u PYTHONPATH uv run alembic upgrade head
env -u PYTHONPATH uv run pytest --cov=golden_rose --cov-report=term-missing --cov-fail-under=95
env -u PYTHONPATH uv run alembic downgrade base
env -u PYTHONPATH uv run alembic upgrade head
env -u PYTHONPATH uv run pip-audit --skip-editable
backend SBOM generation + validation
git diff --check
```

Dispatch independent reviewers for:
- API/auth/privacy/data-minimization;
- PostgreSQL migration/concurrency/idempotency/audit integrity;
- TDD/coverage/regression and scope compliance.

Do not close review from truncated summaries. Build a finding ledger, remediate all Blocker/High/Medium findings, and perform a complete focused rereview.

## Task 10: Living-doc and review handoff closeout

**Objective:** Record exactly what the slice proves and what remains deferred.

**Files:**
- Modify: `AGENTS.md`
- Modify: `CURRENT_WORK.md`
- Modify: `ROADMAP.md`
- Modify: `NOTES.md` (append bottom-most current date)
- Modify: `README.md`
- Modify if contract/status changed: `ARCHITECTURE.md`, `SECURITY.md`, `TECHNICAL_REQUIREMENTS.md`, `TECHNOLOGY_DECISIONS.md`, `docs/adr/README.md`, ADR-0008, operational discovery register
- Create: `docs/review-handoffs/<date>-employer-contact-authority-review-handoff.md`

**Truth requirements:**
- Record partial progress toward the broad persistence row; do not check it complete.
- Preserve synthetic/local-only and deferred human browser qualification truth.
- State that phone/email/status/edit/name or global search/unbounded list/count/UI and every later entity remain unauthorized; the bounded parent collection-query is the sole approved rediscovery surface.
- State whether the review surface is uncommitted or committed.
- Stop after review-ready handoff; commit/push/PR require separate approval.

## Task 11: Final-head evidence after approved commit

**Objective:** Qualify the immutable candidate, not a pre-closeout tree.

1. Under approval, commit the exact reviewed surface.
2. Rerun the entire canonical service-backed gate on final `HEAD` because docs/handoff edits are part of the candidate.
3. Run `git diff --check <merged-planning-base>...HEAD`.
4. Run exact-range Gitleaks over `<merged-planning-base>..HEAD`.
5. Verify clean tree and record local/upstream divergence.
6. Obtain separate approval before push/PR.

Any amend or later commit invalidates final-head evidence and requires the entire sequence again.

---

## Expected roadmap effect

After merge, the slice may truthfully record:

- EmployerContact identity persistence exists under a draft Employer;
- contact create/bounded-parent-query/exact-read authority is server-enforced and synthetic/local;
- the receipt/audit spine supports two explicit entity types with database-backed correspondence; and
- the broad Employer/contact/worksite/request/shift persistence row is **partially advanced but still unchecked**.

It must not claim completion of real staff authentication, production readiness, worksite/request/shift persistence, queue, calendar, map, released-workflow accessibility/language qualification, staff-pilot acceptance, or any live-data gate.

## Stop conditions

Stop immediately if implementation requires:

- phone/email/contact status or communications policy;
- a generic unconstrained entity/audit metadata system;
- weakening receipt↔event↔entity integrity;
- Worksite/Request/Shift/browser/auth/deployment changes;
- client/live-derived fixtures;
- an unreviewed migration decision or a start from anything other than the exact merged accepted planning tip.
