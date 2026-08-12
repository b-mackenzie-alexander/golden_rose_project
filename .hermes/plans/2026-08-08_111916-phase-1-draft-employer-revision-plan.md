# Phase 1 Draft Employer Revision — Accepted Planning-Publication Candidate

> **Historical completion notice (2026-08-11):** PR #16 merged this planning packet at `1c66eeb`; Beatrice then authorized implementation from that exact tip; and PR #17 merged the bounded implementation at `1543248`. Publication-candidate, branch, and future-gate language below preserves planning-time evidence and is not current instruction. The active lane is the separately bounded `fix/draft-employer-revision-post-merge` remediation recorded in ADR-0007 and the living documents.

> **For implementation agents:** This is planning only. Do not execute Task 1 or any product-code task until this rebased packet is independently reviewed, committed, pushed, reviewed by planning-only PR, and merged to `develop`; the exact merged tip is verified to contain the accepted packet; and Beatrice explicitly authorizes coding from a fresh implementation branch.

**Status:** Accepted planning direction; publication candidate; not implementation authority
**Prepared:** 2026-08-08
**Planning baseline:** exact merged `origin/develop` at `7ae448eca3ac3192dda1e4dfcb5c02de3cd3256c` (`fix: close employer workspace post-merge findings (#15)`)
**Isolated planning branch:** `docs/draft-employer-revision-plan`
**Satisfied predecessor:** PR #15 merged the independently rereviewed and exact-head-qualified Employer-workspace closeout; this planning branch was fast-forwarded to that exact authority before reconciliation
**Accepted planning decision record:** `docs/adr/ADR-0007-phase-1-draft-employer-revision-boundary.md`; durable publication and explicit implementation authorization remain separate gates

## Purpose

Implement the next smallest useful Phase 1 product slice: an authorized staff user may explicitly revise only `display_name` and `employer_type` on one existing draft Employer, using expected-version concurrency, actor/payload-bound idempotency, current-state attribution, append-only minimized audit evidence, and a browser workflow that preserves one frozen command authority across unknown outcomes.

This planning branch starts from the exact merged closeout tip and deliberately contains no draft-revision product code.

## Evidence posture and authority

- **Observed merged truth:** PR #15 merged the bounded closeout to `develop` at `7ae448e`; the merged staff workspace provides synthetic/local create, bounded search, and exact detail only, with the reviewed browser/privacy/runtime/database/CI remediation and ADR-0006 now durable.
- **Observed rebaseline:** ADR-0006, Alembic file `migrations/versions/0002_enforce_command_authority_relationships.py` with revision ID `0002_enforce_authority_links`, `scripts/validate_sbom.py`, FastAPI lifespan ownership, BFCache lifecycle behavior, value-safe diagnostics, and the reconciled living documents all exist on the exact planning base.
- **Accepted planning boundary:** the next product slice remains draft Employer revision limited to `display_name` and `employer_type` with expected-version, idempotency, updated attribution, localized browser states, and no lifecycle or adjacent entity expansion.
- **Accepted planning detail:** exact endpoint, response metadata, receipt schema, audit event, failure matrix, state machine, migration, and task order.
- **Validated:** nothing in this slice until implementation and review evidence exist.

## Planning publication gate — complete before Task 1

This gate is planning work, not implementation authorization:

1. **Completed:** independently rereview, remediate, exact-head qualify, exact-range scan, and merge `fix/employer-workspace-closeout` through PR #15.
2. **Completed:** fetch `origin` and record exact merged `origin/develop` tip `7ae448eca3ac3192dda1e4dfcb5c02de3cd3256c`.
3. **Completed:** fast-forward the isolated **planning** branch from `b0a459b` to `7ae448e` while preserving the two reviewed candidate files byte-for-byte; do not create an implementation branch yet.
4. **Completed:** confirm ADR-0006, migration file `migrations/versions/0002_enforce_command_authority_relationships.py` with Alembic revision ID `0002_enforce_authority_links`, `scripts/validate_sbom.py`, FastAPI lifespan ownership, BFCache lifecycle behavior, value-safe diagnostics, and living-document reconciliation landed at their exact merged paths.
5. **Completed:** confirm ADR-0007 and migration filename/revision `0003_add_draft_employer_revision_authority` remain the next free identifiers and reconcile this packet against merged truth.
6. **Completed:** add planning-publication updates to exact files `AGENTS.md`, `README.md`, `CURRENT_WORK.md`, `ROADMAP.md`, `NOTES.md`, `ARCHITECTURE.md`, `TECHNICAL_REQUIREMENTS.md`, `SECURITY.md`, `TECHNOLOGY_DECISIONS.md`, `docs/adr/README.md`, ADR-0005, ADR-0006, `docs/planning/phase-1-correction-audit-event-contract.md`, and the two superseded closeout handoffs; describe ADR-0007 and the plan as an accepted planning boundary pending durable publication, reconcile replay semantics, mark the closeout as merged while preserving historical evidence, and grant no coding authority.
7. **Completed:** independently review the complete uncommitted planning diff. Backend/database/API/TDD review accepted with no findings; frontend and governance review identified three Mediums, all were remediated; focused rereviews accepted the exact remediated contracts with zero Blocker, High, Medium, or Low findings. No finding was dispositioned by exception.
8. With separate approval for each boundary, commit the planning packet, qualify the exact planning head, scan the exact non-empty `origin/develop..HEAD` range, push, open a planning-only PR to `develop`, obtain review, and merge it.
9. Fetch `origin/develop` after merge and verify by exact paths/content that it contains the accepted ADR, implementation plan, ADR index, technology register, replay-contract reconciliation, and living-document planning status.

Stop before Task 1 if the planning PR is unmerged, the merged packet differs from the reviewed packet, any required finding is undisposed, or explicit implementation authorization is absent.

## Fixed product and security boundary

### In scope

- staff-only synthetic/local revision of one draft Employer;
- exact fields `display_name` and `employer_type`;
- permission `employer:draft:revise`;
- UUIDv4 idempotency key;
- expected-version compare-and-swap;
- `updated_at`, `updated_by`, and one-step `version` increment;
- command receipts with committed result version and authorized result event type;
- one minimized `employer.draft_revised` audit event for each fresh successful save;
- current-authoritative replay representation plus explicit result-version metadata;
- inline localized edit/save/conflict/unknown/reload/success browser states;
- automated frontend/backend/migration/API/privacy/accessibility evidence; and
- living-document and review closeout for this slice.

### Out of scope

No contacts, worksites, staffing requests, shifts, notes, files, documents, source text, lifecycle transitions, deletion, audit timeline/read API, exports, public plane, identity-provider work, deployment, infrastructure, live data, client data, production role design, automatic matching/ranking/eligibility/hiring/referral/assignment, URL-carried values, browser storage, offline cache, or service worker.

Human browser, manual accessibility, and fluent English/Spanish review remain **not yet performed**, deferred until a shared deployable `develop` environment exists, and required before promotion/client acceptance. Automated bilingual/accessibility evidence is separate.

## Accepted planning contract summary

### Command

`POST /api/staff/v1/employers/{employer_id}/revisions`

Headers:

- `Idempotency-Key: <UUIDv4>`
- `Accept: application/json`
- `Content-Type: application/json`

Exact body:

```json
{
  "expected_version": 1,
  "employer_type": "household",
  "display_name": "Synthetic Household 001"
}
```

Fresh and replay success: `200`, `Cache-Control: no-store`, exact minimized Employer detail including `updated_at`, and `Idempotency-Result-Version`. Replay also has `Idempotency-Replayed: true`.

The body is always current authoritative Employer truth. On replay after later mutation, body `version` may exceed `Idempotency-Result-Version`; it must never be lower.

### Safe failures

| Condition | Status | Browser authority effect |
|---|---:|---|
| Invalid/missing/non-v4/nil idempotency key | 400 | Definitive; no write; release attempt/owner; retain editable values only; corrected submit mints a fresh key |
| Missing `employer:draft:revise` | 403 | Definitive; no write; release attempt/owner; retain editable values only; later authorized submit mints a fresh key |
| Employer absent | 404 | Definitive; clear/reload selected truth |
| Stale/non-draft compare-and-swap conflict | 412 | Definitive no-commit; release stale key but disable editing until canonical detail reload |
| Reused key with changed actor/type/version/target/payload | 409 | No write; freeze conflicting identity until canonical detail reload |
| Invalid body or normalized no-op | 422 | Definitive; no write; release attempt/owner; preserve editable values only; corrected submit mints a fresh key |
| Known persistence failure | 503 | Unknown command outcome in browser; preserve exact attempt |
| Unexpected server failure | 500 | Unknown command outcome in browser; preserve exact attempt |
| Network, redirect, wrong media type, unreadable/malformed success | n/a | Unknown command outcome; preserve exact attempt |

## Implementation discipline

- Use strict RED → GREEN → REFACTOR for each task.
- Before every RED, prove the exact node exists or explicitly label it `PROPOSED NEW TEST`.
- A test that passes before product code is not accepted RED. Classify harness-only failures honestly.
- Keep one application command as the transaction owner. Repositories do not commit.
- Run non-service tests freely after coding authorization. Starting PostgreSQL, Vite, or any service requires the applicable explicit approval.
- Source ignored `.env.test` only in the approved PostgreSQL shell and never print its values or URL.
- Never include dynamic Employer names, UUIDs, payloads, cursors, response bodies, connection strings, or secrets in CI diagnostics.
- Do not commit generated SBOMs or build output.

### Exact-node TDD execution ledger

The task-level RED/GREEN sections are contract summaries; this ledger controls execution. Within each task, process rows in order: add only the named test, run its exact selector, record the observed RED or pre-satisfied GREEN classification, make only the listed minimum production change, rerun that selector, then run the task's accumulated focused file. Never add a batch of tests before observing individual outcomes. A row marked “expected regression” must pass because of an earlier listed GREEN; if it fails, classify the real gap and fix only that gap. A row that unexpectedly passes is recorded as an immediate-pass GREEN regression, never fabricated as RED.

Exact command macros below are literal substitutions of `<node>` or `<name>`:

- `MIG(<node>)` → `env -u PYTHONPATH uv run pytest tests/integration/test_initial_migration.py::<node> -q`
- `CREATE(<node>)` → `env -u PYTHONPATH uv run pytest tests/integration/application/test_create_draft_employer.py::<node> -q`
- `PERM(<node>)` → `env -u PYTHONPATH uv run pytest tests/unit/auth/test_permissions.py::<node> -q`
- `REV(<node>)` → `env -u PYTHONPATH uv run pytest tests/integration/application/test_revise_draft_employer.py::<node> -q`
- `SCHEMA(<node>)` → `env -u PYTHONPATH uv run pytest tests/unit/api/test_employer_schemas.py::<node> -q`
- `API(<node>)` → `env -u PYTHONPATH uv run pytest tests/integration/api/test_staff_employers.py::<node> -q`
- `READAPI(<node>)` → `env -u PYTHONPATH uv run pytest tests/integration/api/test_staff_employer_reads.py::<node> -q`
- `CLIENT(<name>)` → `npm --prefix apps/web run test -- --run src/api/employerClient.test.ts -t '<name>'`
- `FORM(<name>)` → `npm --prefix apps/web run test -- --run src/employers/EmployerRevisionForm.test.tsx -t '<name>'`
- `WORKSPACE(<name>)` → `npm --prefix apps/web run test -- --run src/employers/EmployerWorkspace.test.tsx -t '<name>'`
- `LANG(<name>)` → `npm --prefix apps/web run test -- --run src/i18n/LanguageProvider.test.tsx -t '<name>'`
- `DIAG(<name>)` → `npm --prefix apps/web run test -- --run src/test/valueSafeDiagnostics.test.ts -t '<name>'`

PostgreSQL-backed `MIG`, `CREATE`, `REV`, and `API` selectors require the approved Task 12 service shell. Authoring may occur earlier, but no service is started implicitly.

#### Task 2 node order

| Selector | First expected classification | Smallest permitted GREEN |
|---|---|---|
| `MIG(test_revision_metadata_contains_updated_at_and_updated_by)` | RED: columns absent from metadata | add only Employer attribution columns/checks to metadata |
| `MIG(test_revision_metadata_binds_audit_event_to_command_result_version)` | RED: result-version/type correspondence absent | add only receipt columns and composite metadata authority |
| `MIG(test_revision_metadata_requires_exactly_one_receipt_event_pair_bidirectionally)` | RED: reverse correspondence absent | add matching five-column unique targets and both deferred cyclic FKs |
| `MIG(test_revision_migration_upgrades_existing_create_rows_and_receipts)` | RED: revision migration absent | add locked transactional expansion/backfill and create compatibility |
| `MIG(test_revision_migration_refuses_incomplete_existing_receipt_event_cardinality)` | RED until preflight exists | fail before trigger/constraint mutation; never fabricate missing audit history |
| `MIG(test_revision_migration_backfills_receipts_under_transactional_trigger_guard)` | expected regression after prior GREEN | close only any missing trigger-safe backfill behavior |
| `MIG(test_revision_migration_restores_receipt_mutation_denial_after_upgrade)` | expected regression after prior GREEN | recreate the exact UPDATE guard before commit |
| `MIG(test_revision_live_schema_enforces_one_step_event_version_authority)` | RED until live constraints match metadata | add only missing one-step/correspondence constraint |
| `MIG(test_revision_live_schema_rejects_mismatched_receipt_event_version)` | expected regression after live constraint GREEN | close only the demonstrated mismatch gap |
| `MIG(test_revision_live_schema_rejects_orphan_receipt_and_orphan_event_at_commit)` | RED until both deferred directions exist | add only missing reverse/forward commit-time correspondence |
| `MIG(test_revision_empty_downgrade_restores_closeout_schema_and_guards)` | RED: downgrade policy absent | implement revision-free locked downgrade and guard restoration |
| `MIG(test_revision_populated_create_only_downgrade_preserves_rows_correspondence_constraints_and_guards)` | RED until populated reversible authority is proven | preserve valid create rows/receipt/event pairs while restoring exact predecessor schema/guards |
| `MIG(test_revision_populated_downgrade_fails_closed_and_preserves_schema_data_guards)` | RED until refusal exists | add pre-mutation populated-state refusal in the downgrade transaction |
| `CREATE(test_existing_create_command_populates_revision_compatible_attribution_and_receipt)` | RED after non-null schema lands | minimally populate create attribution/result fields; no refactor |

#### Task 3 node order

| Selector | First expected classification | Smallest permitted GREEN |
|---|---|---|
| `PERM(test_employer_draft_revise_permission_constant_has_exact_value)` | RED: constant absent | add exact constant only |
| `PERM(test_principal_with_revision_permission_is_allowed)` | RED: predicate path absent | add permission-only predicate |
| `PERM(test_read_or_create_permission_does_not_imply_revision_permission)` | expected regression after predicate GREEN | remove only any implied-permission path found |
| `PERM(test_owner_or_platform_role_label_does_not_grant_revision_permission)` | expected regression from permission-only model | remove only any role-label grant found |
| `PERM(test_synthetic_principal_has_exact_bounded_employer_permissions)` | RED until tracer principal is extended | add revision permission to synthetic principal and no other permission |

#### Task 4 node order

| Selector | First expected classification | Smallest permitted GREEN |
|---|---|---|
| `CREATE(test_receipt_replay_rejects_changed_command_type_actor_target_or_payload)` | RED if any authority dimension is unbound; otherwise immediate-pass regression | add only a missing canonical fingerprint dimension in the existing create path; no extraction yet |
| `CREATE(test_replay_rejects_authority_state_where_current_version_precedes_receipt_result_version)` | RED: corruption guard absent | add bounded current-version/result-version invariant and safe persistence failure |
| `CREATE(test_create_replay_rejects_inconsistent_result_version_event_type_or_target)` | RED until receipt metadata integrity is exact | require create version `1`, authorized event type, requested target, and current version lower bound |
| `CREATE(test_existing_create_command_populates_revision_compatible_attribution_and_receipt)` | required regression from Task 2 | no production change unless refactor regressed create |

Task 4 expressly forbids shared-code extraction until all three proposed nodes are written and classified; only a missing in-place authority check may be added to obtain an individual GREEN first.

#### Task 5 node order

| Selector | First expected classification | Smallest permitted GREEN |
|---|---|---|
| `REV(test_revision_updates_only_name_type_updated_at_updated_by_and_version)` | RED: revision command absent | create command skeleton plus one bounded CAS success path |
| `REV(test_revision_requires_named_permission_before_record_or_writes)` | RED until authorization is first | move named authorization ahead of receipt/record access |
| `REV(test_revision_rejects_missing_employer_without_writes)` | RED until failed-CAS classifier exists | add absent-record `404` rollback path |
| `REV(test_revision_rejects_stale_expected_version_without_writes)` | RED until stale classifier exists | add version/lifecycle `412` rollback path |
| `REV(test_revision_rejects_normalized_noop_without_consuming_command_key)` | RED until normalized no-op exists | add matching-version no-op `422` rollback path |
| `REV(test_revision_stale_precedes_noop_when_values_match_later_current_truth)` | expected regression after ordered classifier GREEN | correct only precedence if stale was misclassified |
| `REV(test_revision_normalizes_before_fingerprint_compare_and_update)` | RED until canonicalization is shared | normalize once before fingerprint and CAS |
| `REV(test_identical_revision_replay_is_write_free_and_returns_current_truth)` | RED until replay branch exists | add identical-receipt current-read branch with no write |
| `REV(test_identical_revision_replay_precedes_stale_and_noop_evaluation)` | expected regression after replay branch | resolve identical receipt before any current-state CAS/no-op classification |
| `REV(test_conflicting_revision_replay_is_write_free)` | RED until all receipt dimensions compare | reject changed authority with existing safe `409` |
| `REV(test_changed_revision_replay_conflict_precedes_stale_evaluation)` | expected regression after conflict branch | return `409` before current version/lifecycle evaluation |
| `REV(test_revision_replay_rejects_inconsistent_result_version_event_type_or_target)` | RED until replay metadata integrity is exact | require expected+1 version, authorized event type, requested target, and current version lower bound |
| `REV(test_revision_replay_after_later_revision_returns_current_truth_and_original_result_version_without_writes)` | RED until later-mutation replay is explicit | return current v3 with original result v2 and unchanged counts |
| `REV(test_revision_races_use_two_read_committed_sessions_and_synchronization_barrier)` | harness-first: install minimum two-session/barrier/isolation instrumentation, then classify the first behavior run as product RED or immediate-pass GREEN regression | fix only an observed authority race; record setup-only failures separately and make no product change for immediate pass |
| `REV(test_two_distinct_commands_with_same_expected_version_have_one_winner)` | RED until CAS is race-safe | use one atomic version-qualified UPDATE; no process lock |
| `REV(test_concurrent_identical_revision_command_has_one_update_receipt_and_event)` | RED until receipt race is serialized by DB | make receipt reservation/replay transaction-safe |
| `REV(test_concurrent_same_key_changed_actor_or_payload_has_one_success_and_one_conflict)` | RED until same-key conflict race is deterministic | one fresh success, one `409`, one receipt/update/event |
| `REV(test_late_audit_failure_rolls_back_receipt_and_employer_update)` | expected RED until one transaction owns all writes | keep commit in application owner after event append |
| `REV(test_revision_audit_event_is_minimized_for_each_allowed_changed_field_set)` | RED until event payload is minimized | parameterize name-only/type-only/both and append exact deterministic field-name set only |
| `REV(test_revision_persistence_failures_are_value_safe)` | expected regression if safe boundary is reused | map only bounded safe persistence error without values |
| `REV(test_create_replay_after_later_revision_returns_current_truth_with_original_result_version)` | RED until cross-command replay semantics exist | return current Employer plus immutable create result version, no write |

#### Task 6 node order

| Selector | First expected classification | Smallest permitted GREEN |
|---|---|---|
| `SCHEMA(test_revision_request_accepts_only_expected_version_name_and_type)` | RED: schema absent | add exact request model fields/forbid-extra behavior |
| `SCHEMA(test_revision_request_requires_strict_non_boolean_expected_version_with_safe_integer_bounds)` | RED until strict bounds exist | add strict integer `1..2,147,483,646` constraint |
| `SCHEMA(test_revision_request_rejects_system_managed_and_unknown_fields)` | expected regression after exact schema GREEN | close only any extra-field acceptance |
| `SCHEMA(test_employer_detail_exposes_updated_at_but_not_updated_by)` | RED until response model changes | add `updated_at` only; keep actor internal |
| `API(test_post_staff_employer_revision_returns_exact_200_contract)` | RED: route absent | add route success mapping and exact no-store body/headers |
| `API(test_post_staff_employer_revision_replay_returns_current_truth_and_result_headers)` | RED until replay headers map | expose current body plus original result-version/replay headers |
| `API(test_post_staff_employer_revision_replay_after_later_revision_returns_current_truth_and_original_result_version_without_writes)` | RED until later-mutation replay is mapped end-to-end | return body v3/header v2/replay true and unchanged counts |
| `API(test_post_staff_employer_revision_maps_bounded_failure_matrix_without_values)` | RED until exception matrix maps | add only bounded status mappings and static problem bodies |
| `API(test_post_staff_employer_revision_returns_exact_noop_and_version_conflict_problem_contracts)` | RED until new domain problems map | add literal `412` and no-op `422` responses |
| `API(test_post_revision_identical_replay_precedes_stale_and_noop_and_returns_200)` | expected regression from application precedence | preserve replay `200` despite later stale/equal current state |
| `API(test_post_revision_changed_key_conflict_precedes_stale_and_returns_409)` | expected regression from application precedence | preserve `409` before CAS classification |
| `API(test_post_revision_fresh_stale_returns_412_without_receipt)` | expected regression from stale path | assert exact `412` and zero writes |
| `API(test_post_revision_fresh_matching_noop_returns_422_without_receipt)` | expected regression from no-op path | assert exact no-op `422` and unconsumed key |
| `API(test_post_staff_employer_revision_malformed_path_returns_exact_validation_without_writes)` | expected regression from validation handler | close only path-validation/no-write mismatch |
| `API(test_post_staff_employer_revision_denial_precedes_record_and_writes)` | expected regression from Task 5 authorization | correct route/dependency order only if it leaks |
| `API(test_post_staff_employer_revision_ignores_actor_role_permission_headers)` | expected regression from synthetic principal boundary | remove only any caller-controlled authority path |
| `API(test_post_staff_employers_fresh_and_replay_emit_result_version_without_changing_create_status_or_body_contract)` | RED: create header absent | add result-version header to existing create route, preserving `201`/body |
| `API(test_post_staff_employers_replay_after_revision_returns_current_truth_and_original_result_version)` | expected RED until create replay route uses current truth | map shared replay result without writes |
| `API(test_existing_create_failure_matrix_media_cache_body_headers_and_write_authority_remains_exact)` | expected regression except approved response metadata | correct only demonstrated create compatibility drift; keep mutation `500/503` transport-unknown |
| `READAPI(test_existing_search_success_media_cache_body_headers_and_read_only_contract_remains_exact)` | expected regression | correct only literal Search success drift |
| `READAPI(test_existing_search_failure_matrix_media_cache_body_headers_and_read_only_contract_remains_exact)` | expected regression | correct only literal Search failure/read-only drift |
| `READAPI(test_existing_detail_success_media_cache_body_headers_and_read_only_contract_remains_exact)` | RED only for approved `updated_at` addition | add `updated_at` and preserve every other literal Detail success field/header |
| `READAPI(test_existing_detail_failure_matrix_media_cache_body_headers_and_read_only_contract_remains_exact)` | expected regression | correct only literal Detail failure/read-only drift |
| `API(test_openapi_exposes_only_create_search_detail_and_revision_routes)` | RED when revision route first appears before allowlist update | update exact method/path allowlist only after ADR acceptance |

#### Task 7 node order

| Selector | First expected classification | Smallest permitted GREEN |
|---|---|---|
| `CLIENT(posts an exact revision command with frozen expected version and idempotency key)` | RED: client function absent | add exact same-origin no-store POST with frozen input |
| `CLIENT(accepts exact current-authoritative revision success and result-version metadata)` | RED until success parser exists | parse exact body and required result-version header |
| `CLIENT(accepts replay after later mutation without treating the older result version as malformed)` | RED until replay relation is allowed | permit replay body version greater than result version |
| `CLIENT(requires fresh body version to equal result version and replay body version to be at least result version)` | expected RED until header/body relation is enforced | add fresh-equality/replay-lower-bound checks |
| `CLIENT(rejects missing malformed or unexpected replay and result-version headers as unknown outcome)` | RED until metadata is strict | reject all non-exact metadata as unknown |
| `CLIENT(rejects body versions lower than the command result version)` | expected regression after relation GREEN | close only lower-version acceptance |
| `CLIENT(maps 400 403 404 409 412 and 422 to definitive bounded revision failures)` | RED until status union exists | add exact definitive status mapping only |
| `CLIENT(maps network 500 503 redirect media-type and malformed-success failures to unknown outcome)` | RED until unknown matrix exists | add conservative unknown classification only |
| `CLIENT(parses each accepted revision body exactly once and disposes every other terminal response body without exposing values)` | RED until the complete body lifecycle is explicit | parse accepted `200` JSON once through strict guards; cancel unread recognized-error, unexpected-2xx, unrecognized-status, and wrong-media bodies; consume/dispose malformed or guard-rejected success once; retain no raw value |

#### Task 8 node order

| Selector | First expected classification | Smallest permitted GREEN |
|---|---|---|
| `FORM(opens from current detail and submits one validated expected-version command)` | RED: form absent | add bounded edit state and one submit path |
| `FORM(rejects invalid and normalized no-op edits before command creation)` | RED until local validation exists | normalize/validate before key generation |
| `FORM(freezes target version payload and key while pending)` | RED until attempt object exists | create immutable in-memory attempt before dispatch |
| `FORM(retries unknown outcome with the identical command key and payload)` | RED until retry state exists | reuse frozen attempt exactly |
| `FORM(requires canonical reload before releasing conflict authority)` | RED until conflict recovery exists | keep conflict lock through exact reload |
| `FORM(releases stale command identity but blocks editing until canonical reload succeeds or returns terminal not-found)` | RED until stale transition exists | discard stale key, retain recovery lock through canonical terminal |
| `FORM(keeps unknown authority when a non-not-found canonical reload fails)` | RED until failed reload preserves attempt | retain original attempt/lock for non-404 failure |
| `FORM(releases frozen authority after successful canonical reload or terminal canonical not-found)` | expected regression after canonical transitions | close only leaked lock/attempt state |
| `FORM(releases definitive validation or forbidden attempt and rotates key on corrected submit while ignoring late completion)` | RED until definitive-failure disposition is explicit | invalidate generation, clear attempt/release matching owner, retain editable values only, and mint a fresh key after correction |
| `FORM(treats command not found as terminal and requires a new canonical selection)` | RED until direct `404` transition exists | clear attempt/selection/search authority and announce not-found |
| `FORM(treats canonical reload not found as terminal rather than an indefinite frozen failure)` | RED until refresh `404` transition exists | release recovery lock and clear target |
| `FORM(hides submitted values from disabled controls during unknown and conflict recovery)` | RED until recovery rendering is minimized | unmount value-bearing controls and render value-free notice |
| `FORM(ignores late completion after pagehide reset or unmount)` | RED until generation checks exist | guard every async completion by operation/generation identity |
| `FORM(blocks competing controls and warns before unload while authority is pending or unknown)` | RED until outward authority callback exists | expose authority state and bounded unload warning |
| `FORM(serializes repeated retry reload and cross-action same-tick activations in recovery)` | RED until synchronous recovery sub-lock exists | acquire handler-level sub-lock before dispatch |
| `FORM(focuses validation forbidden not-found stale conflict unknown refresh-failure and success headings)` | RED until focus owner exists | add explicit heading refs/focus transitions without values |
| `FORM(renders every definitive recovery and success state in English and Spanish with no automated axe violations)` | RED until catalogs/semantics complete | add exact bilingual keys and accessible state markup |

#### Task 9 node order

| Selector | First expected classification | Smallest permitted GREEN |
|---|---|---|
| `WORKSPACE(edits only the selected exact draft Employer)` | RED until form is integrated | render form only from authoritative selected draft detail |
| `WORKSPACE(serializes create and revision with one workspace command lock)` | RED: parent lock absent | add parent-owned synchronous owner/generation ref |
| `WORKSPACE(blocks revision during pending unknown conflict and recovery create authority)` | RED until Create reports authority outward | wire Create acquire/release/blocked callbacks |
| `WORKSPACE(blocks create during pending unknown conflict and recovery revision authority)` | RED until Revision reports authority outward | wire Revision acquire/release/blocked callbacks |
| `WORKSPACE(blocks same-tick create revision and repeated handler re-entry before React rerenders)` | RED until handlers acquire synchronously | guard every command-capable handler with owner ref |
| `WORKSPACE(renders search and revision as separate sibling forms without nested submit ownership)` | RED while detail remains inside the outer search form | end the search form after search controls and render result/detail/revision siblings |
| `WORKSPACE(revision submit dispatches one command and no competing read before settlement)` | RED if submit bubbles or a same-tick read handler runs | stop nested ownership and synchronously retire/guard reads before mutation dispatch |
| `WORKSPACE(all search selection pagination and read retry handlers synchronously reject while command authority is owned)` | RED until read handlers consult the ref | add handler-level owner checks before creating any read operation |
| `WORKSPACE(disables create search selection pagination and competing edit authority while revision is frozen)` | expected regression after parent lock wiring | close only unguarded control/handler paths |
| `WORKSPACE(revision success invalidates prior search results cursor and detail before exact refresh)` | RED until success orchestration exists | synchronously retire reads, clear projections, then refresh detail |
| `WORKSPACE(revision success retires every active read before clearing results cursor failures submitted search and old selection)` | expected RED until invalidation is atomic | centralize read-generation retirement before state clearing |
| `WORKSPACE(late search pagination and detail completions cannot repaint after revision acknowledgement)` | RED until all reads compare generation | add generation guards to every read completion |
| `WORKSPACE(confirmed save refresh failure never becomes unknown and never retries the command)` | RED until save-confirmed refresh state exists | separate command outcome from failed authoritative read |
| `WORKSPACE(command and canonical refresh not found clear authority and require a new selected exact detail)` | RED until terminal canonical `404` is parent-owned | clear target/attempt/lock and require new search/select |
| `WORKSPACE(revision conflict reloads exact detail before a new edit command can exist)` | expected regression after recovery wiring | prevent edit until canonical refresh terminal |
| `WORKSPACE(stale revision releases the command key but blocks editing until exact detail refresh)` | expected regression after stale form transition | preserve parent recovery lock without old key |
| `WORKSPACE(revision unknown reload failure preserves the original authority)` | expected regression after unknown form transition | retain exact attempt/owner on non-404 refresh failure |
| `WORKSPACE(pagehide invalidates revision search and detail late completions)` | RED until synchronous lifecycle owner exists | increment workspace generation in pagehide handler and abort reads only |
| `WORKSPACE(pagehide generation invalidation wins over an already queued mutation completion microtask)` | RED until handler ordering is synchronous | invalidate ref before any state scheduling; never abort mutation |
| `WORKSPACE(revision success heading retains final focus after refreshed detail renders)` | RED until focus ownership is coordinated | suppress detail autofocus and keep success heading owner |
| `WORKSPACE(persisted pageshow still uses canonical document reload)` | expected regression from closeout contract | retain exact production-route reload behavior |
| `WORKSPACE(revision values never enter URL history storage console or diagnostic output)` | harness-first: install non-vacuous URL/history/storage/console/cache instrumentation, then classify the first behavior run as product RED or immediate-pass GREEN regression | remove only an observed value-bearing side channel; record instrumentation-only failures separately |

#### Task 10 node order

| Selector | First expected classification | Smallest permitted GREEN |
|---|---|---|
| `LANG(keeps exact English and Spanish revision keys in parity)` | RED until every Task 10 revision/recovery key exists in both catalogs | add only missing paired catalog keys; do not approve translation quality |
| `FORM(passes axe in both locales across every revision and recovery state)` | expected regression after Task 8 bilingual/axe GREEN | correct only the demonstrated state-specific semantic defect |
| `FORM(announces and focuses every revision transition with reduced-motion-safe behavior)` | expected regression after Task 8 focus GREEN; RED only for uncovered announcements or motion | add only missing value-free status/alert/focus semantics or a demonstrated reduced-motion guard |
| `WORKSPACE(revision flow never accesses Cache API or service workers and never exposes values in browser or diagnostic channels)` | harness-first: install throwing/spying Cache API and service-worker instrumentation before import/render, then classify behavior as product RED or immediate-pass GREEN | remove only an observed access/disclosure; setup-only failures cause no product change |
| `DIAG(revision controls preserve value-independent Testing Library diagnostics)` | expected regression from the merged value-safe harness after new controls render | extend the harness only if a newly demonstrated diagnostic class bypasses value-safe output |
| `API(test_revision_error_and_exception_diagnostics_are_value_safe)` | expected regression after Task 6 static bounded failure mapping; RED only for an observed revision-specific leak | remove only the demonstrated Employer name, UUID, payload, SQL, connection-string, or response-body disclosure |
| `CLIENT(rejects actor attribution fields from routine revision and detail browser responses)` | RED if strict guards accept `updated_by` or any actor identifier | reject only unapproved actor fields while retaining `version` and `updatedAt` |

---

## Task 1: Create the authorized implementation branch from the merged planning tip

**Documentation only; no product code.**

**Inspect:**

- `AGENTS.md`
- `CURRENT_WORK.md`
- `ROADMAP.md`
- `NOTES.md`
- `SECURITY.md`
- `ARCHITECTURE.md`
- `TECHNICAL_REQUIREMENTS.md`
- `TECHNOLOGY_DECISIONS.md`
- `docs/adr/ADR-0002-first-phase-1-slice-and-synthetic-data-boundary.md`
- `docs/adr/ADR-0004-phase-1-employer-read-search-boundary.md`
- `docs/adr/ADR-0005-phase-1-employer-workspace-frontend-boundary.md`
- `docs/adr/ADR-0006-phase-1-employer-workspace-post-merge-closeout.md`
- `docs/planning/phase-1-correction-audit-event-contract.md`
- `docs/planning/phase-1-canonical-field-purpose-inventory.md`
- `docs/planning/phase-1-staff-permission-matrix.md`
- this plan and accepted planning ADR-0007

**Steps:**

1. Fetch and record branch, `HEAD`, `origin/develop`, merge-base, status, worktrees, and the planning-merge commit.
2. Verify the exact merged ADR/plan and planning-publication files are present on `origin/develop`; do not perform contract acceptance inside the implementation task.
3. Create a fresh implementation branch with an approved prefix from that exact merged tip. Do not reuse this planning branch, the closeout branch, or a retired feature branch.
4. Confirm no product code exists on the fresh branch and all conditional predecessor paths/nodes were rechecked after merge.
5. Record Beatrice's explicit implementation authorization in `CURRENT_WORK.md` and a dated `NOTES.md` entry only after the merged planning gate is verified.

**Verification:**

```bash
git status --short --branch
git rev-parse HEAD
git rev-parse origin/develop
git merge-base HEAD origin/develop
git diff --check origin/develop...HEAD
```

**Stop condition:** planning packet not merged exactly as reviewed, dirty or wrong-base implementation branch, or missing explicit coding authorization.

---

## Task 2: Add migration and SQLAlchemy metadata authority for revision

**Files:**

- Create proposed `migrations/versions/0003_add_draft_employer_revision_authority.py`
- Modify `src/golden_rose/persistence/models.py`
- Modify `src/golden_rose/application/create_draft_employer.py` only for revision-schema compatibility
- Modify `src/golden_rose/persistence/employers.py` only to populate new create attribution
- Modify `src/golden_rose/persistence/command_receipts.py` only to populate new create result authority
- Modify `tests/integration/test_initial_migration.py`
- Modify `tests/integration/application/test_create_draft_employer.py`

**PROPOSED NEW TEST nodes:**

- `test_revision_metadata_contains_updated_at_and_updated_by`
- `test_revision_metadata_binds_audit_event_to_command_result_version`
- `test_revision_metadata_requires_exactly_one_receipt_event_pair_bidirectionally`
- `test_revision_migration_upgrades_existing_create_rows_and_receipts`
- `test_revision_migration_refuses_incomplete_existing_receipt_event_cardinality`
- `test_revision_migration_backfills_receipts_under_transactional_trigger_guard`
- `test_revision_migration_restores_receipt_mutation_denial_after_upgrade`
- `test_revision_live_schema_enforces_one_step_event_version_authority`
- `test_revision_live_schema_rejects_mismatched_receipt_event_version`
- `test_revision_live_schema_rejects_orphan_receipt_and_orphan_event_at_commit`
- `test_revision_empty_downgrade_restores_closeout_schema_and_guards`
- `test_revision_populated_create_only_downgrade_preserves_rows_correspondence_constraints_and_guards`
- `test_revision_populated_downgrade_fails_closed_and_preserves_schema_data_guards`
- `test_existing_create_command_populates_revision_compatible_attribution_and_receipt`

**RED:**

1. Assert `employers.updated_at` and `updated_by` are non-null in final metadata.
2. Assert `command_receipts.result_record_version` is non-null, positive, and part of the command-result composite authority.
3. Assert receipts contain non-null `result_event_type` and existing create receipts backfill to `employer.created`.
4. Assert matching five-column unique targets exist on receipts and audit events; audit references receipt and receipt references audit over `(command_id, entity_id, record_version, event_type, actor_id)`, with both FKs `DEFERRABLE INITIALLY DEFERRED`.
5. Assert allowed command types are exactly create plus revise, allowed receipt result-event types are exactly created plus draft-revised, a check binds each command type to its one authorized result event type, and event schema names/types are exactly the same pair.
6. Assert `event_schema_name = event_type`, `correlation_id = command_id`, `entity_sequence = new_record_version`, `prior_record_version >= 0`, and `new_record_version = prior_record_version + 1`.
7. In live PostgreSQL, seed closeout-schema create data, upgrade, and prove backfills: `updated_at=created_at`, `updated_by=created_by`, receipt result version `1`, and receipt result event type `employer.created`.
8. Prove invalid cross-command/entity/version/event-type/actor combinations, orphan events, and orphan receipts fail at commit; both deferred directions match metadata/live schema.
9. Prove the existing create command still succeeds against the upgraded schema and writes `updated_at=created_at`, `updated_by=created_by`, result version `1`, and result event type `employer.created`.

**GREEN:**

1. Set exact Alembic `revision = "0003_add_draft_employer_revision_authority"` and `down_revision = "0002_enforce_authority_links"`. In Alembic's transaction, acquire `ACCESS EXCLUSIVE` locks on `command_receipts`, `audit_events`, and `employers`; verify predecessor trigger/constraint names against the exact merged closeout schema.
2. Add `employers.updated_at`, `employers.updated_by`, `command_receipts.result_record_version`, and `command_receipts.result_event_type` as nullable expansion columns.
3. Backfill Employer attribution from create attribution.
4. Before dropping a trigger or constraint, preflight existing create-only authority: every receipt has exactly one matching event and every event exactly one receipt; all versions/types/actors/targets match. Abort the migration rather than inventing missing history.
5. Drop only `command_receipts_no_update` under the locks; never drop the DELETE guard. Backfill create receipts to result version `1` and result event type `employer.created`.
6. Add exact command/event mapping checks plus matching five-column unique targets on receipts and events; then alter all expansion columns `NOT NULL`.
7. Drop dependent child FKs before replacing any parent unique constraint. Install the audit-to-receipt and reverse receipt-to-audit five-column FKs, both `DEFERRABLE INITIALLY DEFERRED`, plus the remaining exact one-step correspondence checks.
8. Recreate `command_receipts_no_update` with the existing deny function before commit. Any failure rolls schema, data, lock, and trigger changes back together; ordinary receipt UPDATE/DELETE remains denied.
9. For downgrade, acquire the same locks and perform **all** refusal/cardinality checks before DDL or trigger removal. Refuse if any revision receipt/event, Employer version above `1`, differing update attribution, orphan, or mismatch exists; prove schema, rows, constraints, and guards remain unchanged.
10. Only for revision-free exact authority, including a populated database containing valid create-only Employer/receipt/event rows, drop the reverse receipt-to-audit FK first, then audit-to-receipt and every dependent child FK, then new unique/check constraints. Restore the exact merged-0002 parent uniques/checks before its child FKs, remove the new columns last, and recreate the receipt UPDATE trigger before commit. The DELETE trigger remains continuously installed. Prove populated create rows and their predecessor correspondence survive exactly; a downgrade that rejects all non-empty state is not accepted.
11. Update SQLAlchemy metadata to match exact live names, columns, uniqueness, both FK directions, deferrability, and `initially="DEFERRED"`.
12. In the same local release, minimally adapt existing Create application/persistence to populate all new non-null fields. Old application binaries cannot write the upgraded schema; rolling/deployment compatibility is out of scope, so migration and new application are qualified/promoted together. Do not begin revision logic here.

**Focused verification after approved PostgreSQL startup:**

```bash
set -a
source .env.test
set +a
env -u PYTHONPATH uv run pytest \
  tests/integration/test_initial_migration.py::test_revision_metadata_contains_updated_at_and_updated_by \
  tests/integration/test_initial_migration.py::test_revision_metadata_binds_audit_event_to_command_result_version \
  tests/integration/test_initial_migration.py::test_revision_metadata_requires_exactly_one_receipt_event_pair_bidirectionally \
  tests/integration/test_initial_migration.py::test_revision_migration_upgrades_existing_create_rows_and_receipts \
  tests/integration/test_initial_migration.py::test_revision_migration_refuses_incomplete_existing_receipt_event_cardinality \
  tests/integration/test_initial_migration.py::test_revision_migration_backfills_receipts_under_transactional_trigger_guard \
  tests/integration/test_initial_migration.py::test_revision_migration_restores_receipt_mutation_denial_after_upgrade \
  tests/integration/test_initial_migration.py::test_revision_live_schema_enforces_one_step_event_version_authority \
  tests/integration/test_initial_migration.py::test_revision_live_schema_rejects_mismatched_receipt_event_version \
  tests/integration/test_initial_migration.py::test_revision_live_schema_rejects_orphan_receipt_and_orphan_event_at_commit \
  tests/integration/test_initial_migration.py::test_revision_empty_downgrade_restores_closeout_schema_and_guards \
  tests/integration/test_initial_migration.py::test_revision_populated_create_only_downgrade_preserves_rows_correspondence_constraints_and_guards \
  tests/integration/test_initial_migration.py::test_revision_populated_downgrade_fails_closed_and_preserves_schema_data_guards \
  tests/integration/application/test_create_draft_employer.py::test_existing_create_command_populates_revision_compatible_attribution_and_receipt
```

Never print `GOLDEN_ROSE_DATABASE_URL`.

---

## Task 3: Extend named revision permission without role-label authority

**Files:**

- Modify `src/golden_rose/auth/permissions.py`
- Modify `src/golden_rose/api/dependencies.py`
- Modify `tests/unit/auth/test_permissions.py`

**PROPOSED NEW TEST nodes:**

- `test_employer_draft_revise_permission_constant_has_exact_value`
- `test_principal_with_revision_permission_is_allowed`
- `test_read_or_create_permission_does_not_imply_revision_permission`
- `test_owner_or_platform_role_label_does_not_grant_revision_permission`
- `test_synthetic_principal_has_exact_bounded_employer_permissions`

**RED:** prove exact named permission `employer:draft:revise`, permission-only checks, and no inference from `employer:read`, create permission, or role labels.

**GREEN:** add the constant and predicate; add the revision permission to only the synthetic/local tracer principal alongside existing create/read permissions.

**Verify:**

```bash
env -u PYTHONPATH uv run pytest tests/unit/auth/test_permissions.py tests/unit/api/test_dependencies.py
```

---

## Task 4: Generalize receipt/fingerprint primitives and preserve create semantics

**Files:**

- Create proposed `src/golden_rose/application/idempotency.py`
- Modify `src/golden_rose/application/create_draft_employer.py`
- Modify `src/golden_rose/application/errors.py`
- Modify `src/golden_rose/persistence/command_receipts.py`
- Modify `src/golden_rose/persistence/employers.py`
- Modify `tests/integration/application/test_create_draft_employer.py`

**PROPOSED NEW TEST nodes:**

- `test_receipt_replay_rejects_changed_command_type_actor_target_or_payload`
- `test_replay_rejects_authority_state_where_current_version_precedes_receipt_result_version`
- `test_create_replay_rejects_inconsistent_result_version_event_type_or_target`

**Required GREEN regression anchor from Task 2:**

- `test_existing_create_command_populates_revision_compatible_attribution_and_receipt`

**RED:**

1. Add and classify `test_receipt_replay_rejects_changed_command_type_actor_target_or_payload` before changing production code.
2. Add and classify `test_replay_rejects_authority_state_where_current_version_precedes_receipt_result_version` before changing production code.
3. Add and classify `test_create_replay_rejects_inconsistent_result_version_event_type_or_target` before shared-code extraction.
4. Retain existing immediate-create-replay coverage and the Task 2 create-compatibility node as GREEN regressions; do not relabel them RED.

The Task 2 create-attribution/receipt node must remain GREEN throughout this refactor; do not misreport it as a new RED.

**GREEN:**

- Only after all three proposed nodes are classified, share generic fingerprint, conflict, receipt, and outcome mechanics; keep command-specific normalized payload construction explicit.
- Parameterize receipt reservation by exact command type, schema version, result entity, and result record version.
- Define an application outcome containing current Employer, `replayed`, and `result_record_version`.
- Keep transaction ownership in the application command.
- Do not store response snapshots or historical display names.

**Verify after approved PostgreSQL startup:**

```bash
env -u PYTHONPATH uv run pytest tests/integration/application/test_create_draft_employer.py
```

---

## Task 5: Implement the atomic revision application command

**Files:**

- Create proposed `src/golden_rose/application/revise_draft_employer.py`
- Modify `src/golden_rose/application/employer_text.py` only if sharing current normalization avoids duplication without changing behavior
- Modify `src/golden_rose/persistence/employers.py`
- Modify `src/golden_rose/persistence/audit_events.py`
- Create proposed `tests/integration/application/test_revise_draft_employer.py`

**PROPOSED NEW TEST nodes:**

- `test_revision_updates_only_name_type_updated_at_updated_by_and_version`
- `test_revision_requires_named_permission_before_record_or_writes`
- `test_revision_rejects_missing_employer_without_writes`
- `test_revision_rejects_stale_expected_version_without_writes`
- `test_revision_rejects_normalized_noop_without_consuming_command_key`
- `test_revision_stale_precedes_noop_when_values_match_later_current_truth`
- `test_revision_normalizes_before_fingerprint_compare_and_update`
- `test_identical_revision_replay_is_write_free_and_returns_current_truth`
- `test_identical_revision_replay_precedes_stale_and_noop_evaluation`
- `test_conflicting_revision_replay_is_write_free`
- `test_changed_revision_replay_conflict_precedes_stale_evaluation`
- `test_revision_replay_rejects_inconsistent_result_version_event_type_or_target`
- `test_revision_replay_after_later_revision_returns_current_truth_and_original_result_version_without_writes`
- `test_revision_races_use_two_read_committed_sessions_and_synchronization_barrier`
- `test_two_distinct_commands_with_same_expected_version_have_one_winner`
- `test_concurrent_identical_revision_command_has_one_update_receipt_and_event`
- `test_concurrent_same_key_changed_actor_or_payload_has_one_success_and_one_conflict`
- `test_late_audit_failure_rolls_back_receipt_and_employer_update`
- `test_revision_audit_event_is_minimized_for_each_allowed_changed_field_set`
- `test_revision_persistence_failures_are_value_safe`
- `test_create_replay_after_later_revision_returns_current_truth_with_original_result_version`

**RED contract:**

1. Authorize before returning record data or performing writes.
2. Normalize and validate exact fields.
3. Fingerprint command type/schema, target Employer, expected version, normalized name, and type; actor is separately receipt-bound.
4. Reserve the receipt in the same transaction with proposed result version `expected_version + 1` and authorized result event type `employer.draft_revised`.
5. On an existing key, compare all bound dimensions before current-state evaluation: identical authority validates stored result version/event type/target and replays current truth; changed authority returns `409`; inconsistent stored result authority returns safe persistence failure.
6. On a fresh receipt, perform one compare-and-swap update for ID, draft status, expected version, and at least one changed normalized field.
7. If CAS fails, use bounded follow-up reads and classify in exact order: absent → `404`; lifecycle/version mismatch → `412`; matching version with unchanged normalized fields → no-op `422`; roll back the receipt in every case.
8. Set server-controlled `updated_at`, `updated_by`, and version.
9. Parameterize audit assertions for exact `{"field_names":["display_name"]}`, `{"field_names":["employer_type"]}`, and `{"field_names":["display_name","employer_type"]}` payloads. Retain no old/new values, row snapshots, request body, unrestricted keys, or duplicate event.
10. Commit only after receipt, Employer, and event satisfy all database authority constraints.
11. Prove Revision-A replay after Revision-B returns an application outcome with current version `3`, original result version `2`, `replayed=true`, and unchanged counts; Task 6 proves headers. Separately replay the original Create after Revision and prove current truth plus result version `1` with no additional event.
12. Run every race with two independent PostgreSQL sessions/transactions, assert both use `READ COMMITTED`, and synchronize immediately before receipt reservation/CAS. Application outcomes are: same key/same input → one fresh result plus one replay result; same key/changed actor or payload → one success plus `IdempotencyConflictError`; distinct keys/same expected version → one success plus stale-version error with the loser receipt rolled back. Task 6 proves their exact `200`/`409`/`412` HTTP mappings.

**GREEN:** execute the controlling ledger as small cycles in dependency order: fresh revision → definitive failure/rollback → replay integrity and precedence → later-mutation replay → real PostgreSQL races → minimized audit variants. Do not batch the command into one RED/GREEN, and do not add generic patch infrastructure or lifecycle support.

**Verify after approved PostgreSQL startup:**

```bash
env -u PYTHONPATH uv run pytest tests/integration/application/test_revise_draft_employer.py
```

---

## Task 6: Expose the exact no-store staff revision API

**Files:**

- Modify `src/golden_rose/api/staff/schemas.py`
- Modify `src/golden_rose/api/staff/employers.py`
- Modify `src/golden_rose/api/errors.py`
- Modify `tests/unit/api/test_employer_schemas.py`
- Modify `tests/integration/api/test_staff_employers.py`
- Modify `tests/integration/api/test_staff_employer_reads.py` as needed for `updated_at`

**PROPOSED NEW TEST nodes:**

- `test_revision_request_accepts_only_expected_version_name_and_type`
- `test_revision_request_requires_strict_non_boolean_expected_version_with_safe_integer_bounds`
- `test_revision_request_rejects_system_managed_and_unknown_fields`
- `test_employer_detail_exposes_updated_at_but_not_updated_by`
- `test_post_staff_employer_revision_returns_exact_200_contract`
- `test_post_staff_employer_revision_replay_returns_current_truth_and_result_headers`
- `test_post_staff_employer_revision_replay_after_later_revision_returns_current_truth_and_original_result_version_without_writes`
- `test_post_staff_employer_revision_maps_bounded_failure_matrix_without_values`
- `test_post_staff_employer_revision_returns_exact_noop_and_version_conflict_problem_contracts`
- `test_post_revision_identical_replay_precedes_stale_and_noop_and_returns_200`
- `test_post_revision_changed_key_conflict_precedes_stale_and_returns_409`
- `test_post_revision_fresh_stale_returns_412_without_receipt`
- `test_post_revision_fresh_matching_noop_returns_422_without_receipt`
- `test_post_staff_employer_revision_malformed_path_returns_exact_validation_without_writes`
- `test_post_staff_employer_revision_denial_precedes_record_and_writes`
- `test_post_staff_employer_revision_ignores_actor_role_permission_headers`
- `test_post_staff_employers_fresh_and_replay_emit_result_version_without_changing_create_status_or_body_contract`
- `test_post_staff_employers_replay_after_revision_returns_current_truth_and_original_result_version`
- `test_existing_create_failure_matrix_media_cache_body_headers_and_write_authority_remains_exact`
- `test_existing_search_success_media_cache_body_headers_and_read_only_contract_remains_exact`
- `test_existing_search_failure_matrix_media_cache_body_headers_and_read_only_contract_remains_exact`
- `test_existing_detail_success_media_cache_body_headers_and_read_only_contract_remains_exact`
- `test_existing_detail_failure_matrix_media_cache_body_headers_and_read_only_contract_remains_exact`
- `test_openapi_exposes_only_create_search_detail_and_revision_routes`

**RED:**

- exact Pydantic body with `extra="forbid"`;
- path UUID validation and UUIDv4 idempotency header;
- exact success fields, including `updated_at` but excluding `updated_by`;
- exact no-store and replay/result-version headers;
- literal status/media/header/body/no-write matrix from ADR-0007 for every revision success/failure, including malformed path validation;
- explicit Create compatibility: fresh/replay remain `201`, exact body gains only approved `updated_at`, both emit original `Idempotency-Result-Version`, replay alone emits `Idempotency-Replayed: true`, and replay after revision returns current body truth without duplicate writes;
- one exact-node matrix each for existing Create failures, Search success, Search failures, Detail success, and Detail failures, covering status, `application/json`, complete body, no-store, mutation-header absence/presence, and write authority exactly as ADR-0007 specifies;
- 403 before record disclosure/write; and
- strict OpenAPI route/method set.

**GREEN:** add one route after existing static search and exact detail route considerations. Preserve staff-plane-only router, no-store middleware/handlers, minimized schemas, and strict response modeling.

**Focused verify after approved PostgreSQL startup:**

```bash
env -u PYTHONPATH uv run pytest \
  tests/unit/api/test_employer_schemas.py \
  tests/integration/api/test_staff_employers.py \
  tests/integration/api/test_staff_employer_reads.py
```

---

## Task 7: Add strict frontend revision transport contracts

**Files:**

- Modify `apps/web/src/api/employerContracts.ts`
- Modify `apps/web/src/api/employerClient.ts`
- Modify `apps/web/src/api/employerClient.test.ts`

**PROPOSED NEW TEST nodes:**

- `posts an exact revision command with frozen expected version and idempotency key`
- `accepts exact current-authoritative revision success and result-version metadata`
- `accepts replay after later mutation without treating the older result version as malformed`
- `requires fresh body version to equal result version and replay body version to be at least result version`
- `rejects missing malformed or unexpected replay and result-version headers as unknown outcome`
- `rejects body versions lower than the command result version`
- `maps 400 403 404 409 412 and 422 to definitive bounded revision failures`
- `maps network 500 503 redirect media-type and malformed-success failures to unknown outcome`
- `parses each accepted revision body exactly once and disposes every other terminal response body without exposing values`

**RED contract:**

- `ReviseEmployerInput` freezes target ID, command ID, expected version, name, and type; it has no `AbortSignal` or `keepalive` option because aborting a dispatched mutation does not establish its outcome;
- request uses same-origin/no-store/no-referrer/error-on-redirect settings;
- no values enter URL/query, storage, console, or error objects;
- an accepted `200 application/json` response body is consumed exactly once through strict guards for UUID identity, draft status, RFC 3339 timestamps, positive versions, updated timestamp, required positive-integer result-version header, and an absent-or-exact-`true` replay header; fresh body version equals result version, while replay body version may be greater but never lower;
- exact-detail parsing retains `version` and `updatedAt` for expected-version editing while continuing to omit actor IDs;
- 400/422 → validation, 403 → forbidden, 404 → not_found, 409 → idempotency conflict, and 412 → stale; all other command failures → unknown_outcome; and
- recognized error, unexpected 2xx, unrecognized-status, and wrong-media responses cancel any unread body; unreadable/malformed or strict-guard-rejected accepted-success bodies are consumed/disposed exactly once, retained nowhere, never reflected into errors or diagnostics, and map to `unknown_outcome`; and
- page lifecycle invalidates UI generations rather than aborting the mutation transport or fabricating a definitive outcome.

**GREEN:** add a command-specific client function. Do not weaken read-client classifications or parse dynamic problem bodies to decide browser authority.

**Verify:**

```bash
npm --prefix apps/web run test -- --run src/api/employerClient.test.ts
npm --prefix apps/web run typecheck
```

---

## Task 8: Build the inline revision authority component

**Files:**

- Create proposed `apps/web/src/employers/EmployerRevisionForm.tsx`
- Create proposed `apps/web/src/employers/EmployerRevisionForm.test.tsx`
- Modify `apps/web/src/i18n/messages.ts`
- Modify `apps/web/src/styles.css` only if existing classes cannot express the required layout/focus state

**PROPOSED NEW TEST nodes:**

- `opens from current detail and submits one validated expected-version command`
- `rejects invalid and normalized no-op edits before command creation`
- `freezes target version payload and key while pending`
- `retries unknown outcome with the identical command key and payload`
- `requires canonical reload before releasing conflict authority`
- `releases stale command identity but blocks editing until canonical reload succeeds or returns terminal not-found`
- `keeps unknown authority when a non-not-found canonical reload fails`
- `releases frozen authority after successful canonical reload or terminal canonical not-found`
- `releases definitive validation or forbidden attempt and rotates key on corrected submit while ignoring late completion`
- `treats command not found as terminal and requires a new canonical selection`
- `treats canonical reload not found as terminal rather than an indefinite frozen failure`
- `hides submitted values from disabled controls during unknown and conflict recovery`
- `ignores late completion after pagehide reset or unmount`
- `blocks competing controls and warns before unload while authority is pending or unknown`
- `serializes repeated retry reload and cross-action same-tick activations in recovery`
- `focuses validation forbidden not-found stale conflict unknown refresh-failure and success headings`
- `renders every definitive recovery and success state in English and Spanish with no automated axe violations`

**RED state machine:**

1. `viewing` → explicit Edit.
2. `editing` → local validation/no-op check.
3. `pending` → one frozen command; all competing authority disabled.
4. `unknown` → Retry exact command or Reload current Employer.
5. `stale_refreshing` after `412` → release stale identity, discard stale proposal, and reload current Employer before editing.
6. `conflict` after `409` → preserve blocked identity and reload current Employer only; no blind new-key retry.
7. `definitive_failure` after `400`, `403`, or `422` → synchronously invalidate the attempt generation, clear the frozen command key, release only the matching workspace owner/generation, retain editable values only, and reject any late completion. No automatic retry; after correction or later authorization, the next locally valid submit creates a fresh UUIDv4 key.
8. `save_confirmed_refreshing` after valid `200` → release command identity, invalidate stale reads/results, and perform exact detail `GET`; do not render the mutation body as final current truth.
9. `save_confirmed_refresh_failed` → confirmed write, no command retry, editing disabled, exact-detail refresh retry only.
10. `success` → render only accepted refreshed detail and localized confirmation.
11. `reset/pagehide/unmount` → increment generations, ignore late mutation completion, abort read requests when possible, and clear local values. Do not abort an already-dispatched mutation.
12. direct-command or canonical-refresh `not_found` → clear selected detail, results, cursor, submitted-search authority, frozen attempt, and owner; Edit remains absent until a new search and accepted exact detail.

Use an operation generation/request identity guard plus a synchronous lock ref; React disabled state alone is not authority. Retry and Reload must acquire the same recovery-operation sub-lock so repeated or cross-action same-tick activation dispatches exactly one operation. Expose canonical state classifications rather than translated strings so language switching cannot alter command authority.

**GREEN:** implement the smallest component that exposes callbacks for authority lock, canonical reload, success, and reset. Do not create URL state, storage, optimistic updates, or background saves.

**Verify:**

```bash
npm --prefix apps/web run test -- --run src/employers/EmployerRevisionForm.test.tsx
npm --prefix apps/web run typecheck
```

---

## Task 9: Integrate revision into exact detail and invalidate stale search projections

**Files:**

- Modify `apps/web/src/employers/EmployerDetail.tsx`
- Modify `apps/web/src/employers/EmployerSearch.tsx`
- Modify `apps/web/src/employers/EmployerWorkspace.tsx` to own shared command/read authority, lifecycle invalidation, and narrow child callbacks
- Modify `apps/web/src/employers/EmployerCreateForm.tsx` to participate in the shared create/revision command lock
- Modify `apps/web/src/employers/EmployerWorkspace.test.tsx`
- Modify `apps/web/src/app/App.test.tsx` if the exact route/control inventory changes

**PROPOSED NEW TEST nodes:**

- `edits only the selected exact draft Employer`
- `serializes create and revision with one workspace command lock`
- `blocks revision during pending unknown conflict and recovery create authority`
- `blocks create during pending unknown conflict and recovery revision authority`
- `blocks same-tick create revision and repeated handler re-entry before React rerenders`
- `renders search and revision as separate sibling forms without nested submit ownership`
- `revision submit dispatches one command and no competing read before settlement`
- `all search selection pagination and read retry handlers synchronously reject while command authority is owned`
- `disables create search selection pagination and competing edit authority while revision is frozen`
- `revision success invalidates prior search results cursor and detail before exact refresh`
- `revision success retires every active read before clearing results cursor failures submitted search and old selection`
- `late search pagination and detail completions cannot repaint after revision acknowledgement`
- `confirmed save refresh failure never becomes unknown and never retries the command`
- `command and canonical refresh not found clear authority and require a new selected exact detail`
- `revision conflict reloads exact detail before a new edit command can exist`
- `stale revision releases the command key but blocks editing until exact detail refresh`
- `revision unknown reload failure preserves the original authority`
- `pagehide invalidates revision search and detail late completions`
- `pagehide generation invalidation wins over an already queued mutation completion microtask`
- `revision success heading retains final focus after refreshed detail renders`
- `persisted pageshow still uses canonical document reload`
- `revision values never enter URL history storage console or diagnostic output`

**RED integration rules:**

- no edit control without an exact selected detail;
- `EmployerWorkspace` owns `{owner, generation}` in a synchronous ref plus render state and passes narrow acquire/release/invalidate contracts to both Create and Revision; release verifies owner and generation;
- both Create and Revision handlers acquire synchronously and check the lock even when their buttons have not rerendered disabled; each child reports pending, unknown, conflict, recovery, and terminal transitions bidirectionally;
- `EmployerSearch` ends its search `<form>` immediately after the search controls. Results, exact detail, and `EmployerRevisionForm` render outside that form as sibling regions; no form is nested and revision Enter-submit cannot bubble into search submission;
- every search submit, result selection, pagination, search retry, detail retry, and other read-capable handler checks the synchronous workspace owner ref before creating an operation, even if disabled props have not rerendered;
- successful Revision authority acquisition synchronously increments/retires read generations and aborts only active read controllers before the mutation is dispatched; the mutation has no abort signal;
- integrated same-tick coverage holds Revision unresolved after submit and proves exactly one revision request plus zero search, selection-detail, pagination, or read-retry requests before command settlement; after confirmed success, only the one required canonical exact-detail refresh is permitted;
- valid command success clears old detail/results/cursor/pagination state, preserves search inputs, enters `save_confirmed_refreshing`, and renders current Employer truth only after an accepted exact detail `GET` whose version is at least the acknowledged body and result-header versions;
- the success transition synchronously retires all active search/pagination/detail controllers and generations, clears pagination failures and submitted-search authority as well as results/cursor/old selection, preserves only editable search inputs, and rejects every late read completion;
- exact detail and revision success/recovery render outside the conditional results subtree so invalidating search cannot unmount them;
- failed exact refresh after confirmed save retains a distinct confirmed-save recovery state, never command unknown outcome;
- command `404` and exact-refresh `404` have separate tested transitions but both clear target/attempt/workspace authority and require a newly selected canonical detail;
- canonical reload uses the existing exact GET client, never search heuristics or field-equality inference;
- parent focus authority suppresses or sequences `EmployerDetail` autofocus so the localized revision-success heading remains rendered and finally focused after refreshed detail replacement;
- the workspace `pagehide` listener synchronously increments the shared ref generation and retires reads before React reset effects; it never aborts the mutation transport;
- create/search/detail behavior remains intact; and
- page lifecycle follows the merged closeout behavior.

**GREEN:** wire the component through narrow callbacks. Avoid a broad Employer workspace state rewrite.

**Verify:**

```bash
npm --prefix apps/web run test -- --run src/employers/EmployerWorkspace.test.tsx src/app/App.test.tsx
npm --prefix apps/web run typecheck
```

---

## Task 10: Prove privacy, localization, accessibility, and diagnostic boundaries

**Files:**

- Modify `apps/web/src/i18n/messages.ts`
- Modify `apps/web/src/i18n/LanguageProvider.test.tsx`
- Modify `apps/web/src/api/employerClient.test.ts`
- Modify `apps/web/src/employers/EmployerRevisionForm.test.tsx`
- Modify `apps/web/src/employers/EmployerWorkspace.test.tsx`
- `apps/web/src/test/valueSafeDiagnostics.test.ts`; modify only if the new controls expose an uncovered diagnostic class
- Modify `tests/integration/api/test_staff_employers.py` only for the named revision value-safety node

**PROPOSED NEW TEST nodes:**

- `keeps exact English and Spanish revision keys in parity`
- `passes axe in both locales across every revision and recovery state`
- `announces and focuses every revision transition with reduced-motion-safe behavior`
- `revision flow never accesses Cache API or service workers and never exposes values in browser or diagnostic channels`
- `revision controls preserve value-independent Testing Library diagnostics`
- `test_revision_error_and_exception_diagnostics_are_value_safe`
- `rejects actor attribution fields from routine revision and detail browser responses`

Execute these nodes individually in the Task 10 ledger order. Harness/instrumentation setup must become trustworthy before interpreting any browser side-channel behavior; setup-only failure is not product RED. An expected regression that passes immediately records predecessor-supplied GREEN evidence and causes no product edit.

**Required evidence:**

1. English/Spanish key parity for every revision label, instruction, validation, forbidden, not-found, stale, idempotency conflict, unknown, reload, confirmed-save refresh failure, success, and search-invalidated notice.
2. Keyboard operation, deterministic focus movement, status/alert semantics, associated labels, disabled controls, and reduced-motion-safe behavior for every definitive and recovery state.
3. Automated axe checks in both locales across editing, validation, pending, forbidden, not-found, stale, conflict, unknown, confirmed-save refresh failure, success, and the post-success search-invalidated notice.
4. Browser-side-channel assertions for URL/history, localStorage, sessionStorage, Cache API, service workers, console methods, and diagnostic text. Install explicit Cache API/service-worker spies, stubs, or throwing getters before module import/render (or add an equivalent static source gate) so absence assertions remain non-vacuous in jsdom; assert zero registration/cache access and no revision values in exposed result/error objects or data attributes.
5. Backend/API error and exception evidence contains no Employer name, UUID, payload, SQL, connection string, or response body.
6. No `updated_by` actor ID reaches routine browser contracts.

**Verify:**

```bash
npm --prefix apps/web run test -- --run \
  src/employers/EmployerRevisionForm.test.tsx \
  src/employers/EmployerWorkspace.test.tsx \
  src/test/valueSafeDiagnostics.test.ts
npm --prefix apps/web run test
```

Human qualifications remain deferred and must not be claimed.

---

## Task 11: Run complete non-service quality and security gates

Run after all focused GREEN nodes pass:

```bash
env -u PYTHONPATH uv lock --check
env -u PYTHONPATH uv run ruff format --check .
env -u PYTHONPATH uv run ruff check .
env -u PYTHONPATH uv run mypy src tests
env -u PYTHONPATH uv run bandit -q -r src
env -u PYTHONPATH uv run pytest tests/unit
npm --prefix apps/web run verify
npm --prefix apps/web audit --audit-level=high
env -u PYTHONPATH uv run pip-audit --skip-editable
```

This is an interim development gate, not final-head evidence. Do not add a dependency or scanner unless required by the slice; mandatory final-head SBOM regeneration/validation occurs in Task 14 even when dependencies are unchanged.

Also run:

```bash
git diff --check
git status --short
```

Classify every failure. Do not weaken gates to obtain GREEN.

---

## Task 12: Run approved PostgreSQL migration and application qualification

This task requires explicit approval to start/use the synthetic local PostgreSQL service. Execute every Task 12 shell block in one shell so the cleanup trap remains armed until the explicit final cleanup.

In one shell, source ignored configuration without printing values:

```bash
set -euo pipefail
set -a
source .env.test
set +a
```

Start and prove the approved loopback-only service:

```bash
cleanup_postgres() {
  local cleanup_status=0
  local remaining=""
  docker compose --env-file .env.test down --remove-orphans || cleanup_status=$?
  if ! remaining="$(docker compose --env-file .env.test ps -a --services)"; then
    cleanup_status=1
  fi
  if [ -n "$remaining" ]; then
    cleanup_status=1
  fi
  return "$cleanup_status"
}
trap cleanup_postgres EXIT
docker compose --env-file .env.test down --remove-orphans
test -z "$(docker compose --env-file .env.test ps -a --services)"
docker compose --env-file .env.test up -d postgres-test
test "$(docker compose --env-file .env.test port postgres-test 5432)" = "127.0.0.1:55432"
test "$(docker inspect -f '{{.State.Health.Status}}' "$(docker compose --env-file .env.test ps -q postgres-test)")" = "healthy"
```

Then run the repository-approved PostgreSQL lifecycle and exact tests:

```bash
env -u PYTHONPATH uv run alembic upgrade head
env -u PYTHONPATH uv run alembic downgrade base
env -u PYTHONPATH uv run alembic upgrade head
env -u PYTHONPATH uv run pytest tests/integration/test_initial_migration.py
env -u PYTHONPATH uv run pytest tests/integration/application/test_create_draft_employer.py
env -u PYTHONPATH uv run pytest tests/integration/application/test_revise_draft_employer.py
env -u PYTHONPATH uv run pytest tests/integration/api/test_staff_employers.py tests/integration/api/test_staff_employer_reads.py
env -u PYTHONPATH uv run pytest
```

Required concurrency evidence:

- each race asserts `READ COMMITTED` on two independent sessions/transactions and synchronizes immediately before reservation/CAS;
- identical same-key revision races produce one fresh result, one replay, and one receipt/update/event;
- same-key changed-actor or changed-payload races produce one success, one idempotency conflict, and one receipt/update/event;
- distinct keys with the same expected version produce one winner and one stale loser whose receipt rolls back;
- stale/no-op/denied/not-found commands leave no receipt or event;
- late audit failure rolls back the Employer update and receipt;
- revision-A replay after revision-B returns current truth plus revision-A's original result version with unchanged counts;
- create replay after later revision returns current truth plus original result version; and
- live constraints reject forged cross-command/entity/version authority plus orphan receipts and orphan events at deferred commit.

Always tear down, including after failure:

```bash
cleanup_postgres
trap - EXIT
```

Because `set -e` remains active, `trap - EXIT` executes only after cleanup and the empty-service proof return zero. A cleanup failure leaves the EXIT trap armed for another teardown attempt and fails the gate.

This is pre-documentation implementation evidence, not the final committed-head gate.

---

## Task 13: Reconcile living documentation and durable decision status

**Inspect every exact path and narrowly update every path whose implementation/status contract changed:**

- `AGENTS.md`
- `CURRENT_WORK.md`
- `ROADMAP.md`
- `NOTES.md`
- `SECURITY.md`
- `ARCHITECTURE.md`
- `TECHNICAL_REQUIREMENTS.md`
- `TECHNOLOGY_DECISIONS.md`
- `README.md`
- `docs/adr/README.md`
- `docs/adr/ADR-0005-phase-1-employer-workspace-frontend-boundary.md`
- `docs/adr/ADR-0006-phase-1-employer-workspace-post-merge-closeout.md`
- `docs/adr/ADR-0007-phase-1-draft-employer-revision-boundary.md`
- `docs/planning/phase-1-correction-audit-event-contract.md`
- `docs/planning/phase-1-canonical-field-purpose-inventory.md`
- `docs/planning/phase-1-staff-permission-matrix.md`
- create exact handoff `docs/review-handoffs/2026-08-08-draft-employer-revision-review-handoff.md`

**Rules:**

- distinguish Observed, Reported, Proposed, and Validated claims;
- record exact automated evidence and commit/range references available at that time;
- do not claim implementation complete before the final verified head;
- do not claim human browser, manual accessibility, or fluent-language review occurred;
- keep human qualification deferred until shared deployed `develop`, required before promotion/client acceptance;
- state that only draft Employer name/type revision exists;
- preserve public/staff separation, no matching/ranking, no live data, no deployment, and no audit timeline;
- record the replay policy: current authoritative body plus original command result version; and
- update Obsidian only after authoritative repository status is settled, with concise evidence-backed wording.

Run `git diff --check` after documentation changes.

---

## Task 14: Independent rereview, exact-final-head qualification, and PR workflow

### Independent rereview

Create a fresh handoff containing:

- exact base/head and working-tree state;
- accepted ADR/plan references;
- full changed-file list;
- exact focused and full verification results;
- migration upgrade/downgrade and live-constraint evidence;
- concurrency and replay evidence;
- frontend authority/failure/accessibility/privacy evidence;
- deferred human qualification statement; and
- known limitations/non-scope.

Review severity policy:

- every Blocker or High finding blocks PR preparation;
- every Medium must be remediated or explicitly documented with rationale, owner, and Beatrice's acceptance;
- Low findings may be recorded with disposition.

### Commit after uncommitted rereview

After rereview remediation, rerun affected focused checks. Plain `git diff --check` does not inspect untracked new files. With explicit commit approval, stage only the exact reviewed implementation/docs/handoff file list (never broad `git add -A`), run `git diff --cached --check`, inspect `git diff --cached --name-status`, and commit that complete surface. If staged diff hygiene fails, unstage/repair/rereview before commit. Do not push yet.

### Exact-final-head gate

After the commit, prove the outgoing range is non-empty and the worktree is clean:

```bash
set -euo pipefail
git diff --check origin/develop..HEAD
git diff --check
git status --short
test "$(git rev-list --count origin/develop..HEAD)" -gt 0
git diff --name-status origin/develop..HEAD
git diff --stat origin/develop..HEAD
```

`git status --short` must be empty. With separate explicit approval to start PostgreSQL, run every lifecycle block below in one shell so the cleanup trap remains armed, source ignored `.env.test` without printing it, and run the exact final-head lifecycle:

`scripts/validate_sbom.py` is merged predecessor authority at the exact path above. The final gate still fails closed if that accepted path is absent.

```bash
set -euo pipefail
cleanup_postgres() {
  local cleanup_status=0
  local remaining=""
  docker compose --env-file .env.test down --remove-orphans || cleanup_status=$?
  if ! remaining="$(docker compose --env-file .env.test ps -a --services)"; then
    cleanup_status=1
  fi
  if [ -n "$remaining" ]; then
    cleanup_status=1
  fi
  return "$cleanup_status"
}
trap cleanup_postgres EXIT
docker compose --env-file .env.test down --remove-orphans
test -z "$(docker compose --env-file .env.test ps -a --services)"
docker compose --env-file .env.test up -d --wait postgres-test
test "$(docker compose --env-file .env.test port postgres-test 5432)" = "127.0.0.1:55432"
test "$(docker inspect -f '{{.State.Health.Status}}' "$(docker compose --env-file .env.test ps -q postgres-test)")" = "healthy"
set -a
source .env.test
set +a
test "$(node --version)" = "v22.22.3"
test "$(npm --version)" = "10.9.8"
test "$(npm --userconfig apps/web/.npmrc config get registry)" = "https://registry.npmjs.org/"
test "$(npm --userconfig apps/web/.npmrc config get ignore-scripts)" = "true"
node --test apps/web/scripts/validate-lockfile.test.mjs
node apps/web/scripts/validate-lockfile.mjs apps/web/package-lock.json
test -f scripts/validate_sbom.py
env -u PYTHONPATH uv lock --check
env -u PYTHONPATH uv sync --locked --all-groups
npm --userconfig apps/web/.npmrc ci --ignore-scripts --prefix apps/web
npm --prefix apps/web run verify
npm --prefix apps/web ls --all
npm --userconfig apps/web/.npmrc --prefix apps/web audit --audit-level=high
mkdir -p build
npm --userconfig apps/web/.npmrc --prefix apps/web sbom --sbom-format cyclonedx --sbom-type application > build/frontend-sbom.cdx.json
env -u PYTHONPATH uv run python scripts/validate_sbom.py build/frontend-sbom.cdx.json --spec 1.5 --name web --version 0.0.0 --purl 'pkg:npm/%40golden-rose/web@0.0.0'
env -u PYTHONPATH uv run ruff format --check .
env -u PYTHONPATH uv run ruff check .
env -u PYTHONPATH uv run mypy src tests
env -u PYTHONPATH uv run bandit -q -r src
env -u PYTHONPATH uv run alembic upgrade head
env -u PYTHONPATH uv run pytest --cov=golden_rose --cov-report=term-missing --cov-fail-under=95
env -u PYTHONPATH uv run alembic downgrade base
env -u PYTHONPATH uv run alembic upgrade head
env -u PYTHONPATH uv run pip-audit --skip-editable
env -u PYTHONPATH uv run cyclonedx-py environment --pyproject pyproject.toml --output-reproducible --of JSON -o build/backend-sbom.cdx.json
env -u PYTHONPATH uv run python scripts/validate_sbom.py build/backend-sbom.cdx.json --spec 1.6 --name golden-rose --version 0.1.0
git diff --check origin/develop..HEAD
git diff --check
test -z "$(git status --short)"
```

Always tear down in `finally` and prove no service remains:

```bash
cleanup_postgres
trap - EXIT
```

Because `set -e` remains active, the trap is removed only after verified cleanup succeeds. Failure leaves the EXIT trap armed for another teardown attempt and keeps the exact-head gate nonzero.

Then run Gitleaks against the exact non-empty committed range before push:

```bash
set -euo pipefail
gitleaks git --redact --no-banner --log-opts="origin/develop..HEAD"
```

Never run a whole-working-tree secret scan where ignored credentials may exist, and never print ignored environment values.

Any later commit or amend invalidates the entire exact-final-head claim. Rerun the complete CI-parity, PostgreSQL migration downgrade/re-upgrade, full test, SBOM regeneration/validation, teardown/empty-service proof, committed-range `git diff --check origin/develop..HEAD`, clean-worktree proof, and exact-range Gitleaks scan on the new HEAD; an affected-check subset is never qualifying final-head evidence.

### Commit/push/PR

Push, PR creation, merge, any service reuse, and deployment each remain separate approval boundaries under `GIT_WORKFLOW.md` and the accepted plan. The PR must target `develop`, state exact scope/non-scope/trust-data impact/verification/approval dependencies, and must not claim deferred human qualification.

After merge, rebaseline `develop`, reconcile `CURRENT_WORK.md`/`ROADMAP.md`/`NOTES.md`, and stop. No contact/worksite/request/lifecycle slice begins without its own reviewed plan.

## Final acceptance checklist

- [ ] Closeout and reviewed planning packet merged; implementation branch based on that exact merged `origin/develop`
- [ ] ADR-0007 accepted through planning PR and implementation explicitly authorized
- [ ] Only `display_name` and `employer_type` are client-settable
- [ ] `employer:draft:revise` is server-enforced and role labels confer nothing
- [ ] Expected-version compare-and-swap allows one concurrent winner
- [ ] Idempotency binds actor, type, schema, target, expected version, and normalized payload
- [ ] Receipt records committed result version and authorized event type
- [ ] Replay returns current authoritative body plus original result-version metadata
- [ ] No historical response/display-name snapshots retained for replay
- [ ] `updated_at`, `updated_by`, and one-step version increment are server-controlled
- [ ] Fresh revision appends exactly one minimized `employer.draft_revised` event
- [ ] Bidirectional deferred database authority requires exactly one matching receipt/event pair across command/entity/version/type/actor
- [ ] No-op/stale/denied/not-found/conflicting commands leave no writes
- [ ] Browser freezes one command across unknown outcome and same-key retry
- [ ] Conflict requires canonical detail reload before new authority
- [ ] Revision success invalidates stale search results/cursor
- [ ] English/Spanish automated functional and accessibility parity pass
- [ ] Dynamic values remain absent from URL/storage/cache/console/diagnostics
- [ ] Full non-service and approved PostgreSQL gates pass
- [ ] Independent rereview disposition policy is satisfied
- [ ] Exact committed final head passed mandatory SBOM, full CI-parity, migration down/up, teardown, diff, and exact-range secret gates
- [ ] Human browser/accessibility/fluent-language review remains honestly deferred
- [ ] No out-of-scope feature, service, deployment, or live data was introduced
