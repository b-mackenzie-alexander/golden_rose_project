# Staff Intake Workflows — Implementation Publication Plan

## 2026-09-14 — PR A source activation

PR #100 merged this intake planning contract at `ce38fb0`; PR #101 merged the Wave 1 UX predecessor at `9a6b66735f7261ca705f7e8ba5b7c2afcd815f92`. The owner subsequently authorized PR A implementation and disposable local PostgreSQL tests. The active branch is `feat/staff-intake-drafts` from that exact integration tip. Older docs-only/unmerged-predecessor statements below describe the planning snapshot and are superseded for this source lane. Browser UX verification is deferred until PR A is finished at the owner's request.

PR A adds only durable candidate drafts, separately authorized address sections, bounded shared recovery and typed atomic receipt/result/audit authority. Review/follow-up, links, canonical finalization and corrections remain PRs B–D. The v28 runtime is historical and remains `not_qualified`; no deployment, cloud inspection/mutation, live data or production is authorized or claimed.


## Delivery lock
- Staffing: one independent developer; fresh agent reviews supply independent quality evidence, not human authorization.
- Human-visible outcome: v28 private synthetic develop exists. The improved Wave 1 UI is an uncommitted candidate in the original checkout, not present in this clean planning worktree or deployed as new intake functionality.
- Gate budget: v28 packet consumed. This source-only plan grants no infrastructure, database runtime mutation, live-data, public-plane, or production authority. Any synthetic deployment uses one fresh bounded packet.
- Next executable action: fresh-review and publish the docs-only planning packet independently of UI merge. Both accepted protected planning merge AND preserved improved-UI predecessor merge are mandatory before rebaselining a separately authorized coding lane from the exact merged integration tip.
- Do not regress: keep improved UI, centralized authoritative records, restricted addresses, permission checks, typed audit/receipt authority, synthetic-only evidence, private SQL and existing deployment protections. Do not replace durable proof with fixture responses or bring back prominent synthetic disclaimers.

> For Hermes: use outcome-scale execution with small test-first checkpoints and the subagent-driven-development skill, not a new planning cycle per node. This docs-only publication packet is not coding or runtime authorization.

**Status:** Finalized technical proposal for approved docs-only publication; fresh review, acceptance/merge and the improved-UI predecessor remain activation gates. Exact normative technical definitions are in `docs/planning/staff-intake-contract.md` §§2–7 and ADR-0017. No implementation, deployment, live-data admission or client/counsel acceptance is claimed.
**Goal:** Authorized staff can save partial worker/employer intakes, recover them across sessions, complete them, record version-bound review/follow-up and explicitly finalize linked authoritative records using the improved bilingual UI.
**Architecture:** Separate durable intake aggregates from canonical party records. Use transactional SQLAlchemy/PostgreSQL writes with optimistic versions, command receipts and append-only events; use bounded minimized read models. Existing Employer contracts are preserved rather than weakened to permit unnamed identities.
**Stack:** Existing Python 3.12/FastAPI/Pydantic/SQLAlchemy/psycopg/Alembic and React/TypeScript/Vite/Vitest/axe toolchain; no new service/vendor or browser persistence.

## 1. Evidence and source identity
Local HEAD and local origin/develop ref observed at `a6f0791f53f9e0d4a344cd104e6237b20ad34dbb`; this is not independent live-remote verification. Original checkout is `feat/staff-intake-workflows` with inherited uncommitted Wave 1 edits. Planning checkout: `docs/staff-intake-implementation-plan`, created from that commit, with no UI edits copied. UI predecessor merge and exact-tip reread remain activation dependencies.

Private conversational authority: Obsidian note **Golden Rose Employment Agency - Staff Intake Workflow Contract and Gap Matrix**, including accepted architecture/follow-up/finalization addenda. Do not copy raw client records or private operational access notes to Git.

Repository controlling references:
- `AGENTS.md`, `CURRENT_WORK.md`, `ROADMAP.md`, `GIT_WORKFLOW.md`.
- `docs/planning/phase-1-canonical-field-purpose-inventory.md`.
- `docs/planning/phase-1-staff-permission-matrix.md`.
- `docs/planning/phase-1-request-shift-state-model.md`.
- `docs/planning/phase-1-work-queue-aging-follow-up-model.md`.
- `docs/planning/phase-1-correction-audit-event-contract.md`.
- `SECURITY.md`, `TECHNICAL_REQUIREMENTS.md`, `ARCHITECTURE.md`, `TECHNOLOGY_DECISIONS.md`.

Observed code: Employer requires nonblank display name/type; EmployerContact presently stores full_name and version=1, not a complete phone/address record (`src/golden_rose/persistence/models.py`). Contact creation commits inside its application service (`src/golden_rose/application/create_employer_contact.py`), so finalization must NOT compose committing services and claim atomicity. Typed entity/receipt constraints enumerate only current Employer/contact commands and must be expanded deliberately. `src/golden_rose/auth/permissions.py` contains Employer/contact capabilities, not the proposed intake review/worker permissions.

## 2. Accepted operational contract
- Incomplete drafts save without contact information; absent values never become fabricated names or dates. Validate supplied values.
- Shared authorized draft lists and search support cross-computer recovery. Stable references distinguish unnamed drafts; no automatic identity merge.
- Explicit section-local saves: non-address content and each restricted address have separate Save controls, statuses, immutable command keys/payloads and edit generations. Aggregate all-saved is forbidden while any section is dirty/pending/failed/unknown. Serialize pending/unknown commands per intake; confirmed aggregate versions never clobber other unsaved buffers. Retry the original command before saving another section; later edits stay dirty. Duplicate-safe retry and best-effort leave warning; autosave deferred.
- Version-checked saves prevent stale overwrite; no long-lived edit locks.
- Accessible Incomplete labels in lists are separate from Saved and Intake reviewed.
- Worker review minimum: name, physical address, phone, work interests and availability. Interests allow multiple governed categories plus Other description. Availability allows days/time ranges or explicit flexibility, never implicit flexibility from absence.
- Employer review minimum: representative name, phone, business/contact address and worksite address; role, duties, worker count, schedule/start or explicit To be discussed; employer-offered compensation amount/range, currency, per-worker pay basis. Negotiability alone is insufficient; other terms optional.
- Precise addresses are restricted, absent from routine list/search previews. Same-address convenience does not collapse meanings or silently propagate later edits.
- Review outcomes Needs follow-up and Intake reviewed; append reviewer identity/name, server time, outcome/reason and reviewed version. Relevant edits invalidate current review without deleting history.
- Needs follow-up requires reason, responsible staff and due instant. Reassignment/rescheduling/contact attempts append history. Time passing triggers attention only.
- Owner/authorized Manager and explicitly delegated Operations Staff can review/finalize. Technical support role has no implied operational authority; same authorized person may review/finalize.
- Link incomplete intake to existing canonical record explicitly. New canonical records require explicit Finalize intake after complete, current-version review. Recheck permissions/review/version transactionally; retries cannot create duplicate identities.
- Finalization is neither open demand, referral approval nor finalized compensation.

## 3. Frozen technical reconciliation and precedence
`docs/planning/staff-intake-contract.md` is normative for this outcome; the following references replace the former missing-definition checklist, not the preserved employer-demand baseline:
1. §4: exact independent intake review/finalize and restricted field permissions; ordinary Operations Staff request/shift review stays Allow.
2. §§3, 5: structurally complete intake can finalize to draft request only; no ShiftNeed, open demand, coverage, verification or agreed compensation.
3. §§2, 6: aggregate/content version distinction, current latest review, mandatory follow-up reason/owner/due instant, typed commands and replay.
4. §§3, 5: exact field bounds, save floor, canonical output sets, new-vs-reused relationships and no silent overwrite. Employer name/type and old API DTOs remain unchanged.
5. §§4, 7: trusted synthetic directory, field projections, append-only protected history, multi-result receipt/audit migration and fixed transaction lock order.
6. §§2, 5, 9: finalized intake snapshots and original review/output links are immutable. PR D supplies bounded canonical corrections and current-facts re-review, distinct from intake editing; existing Employer draft revision remains unchanged. No hidden sync, identity merge or lifecycle expansion.

Technical choices are Proposed safe synthetic choices, not new client policy. Remaining business questions are recorded in the discovery register amendment below; they do not grant live use. Fresh review must resolve contradictions before acceptance rather than interpreting this reference map as proof of approval.

## 4. Persistence and HTTP contract to implement
Implement `docs/planning/staff-intake-contract.md` §§2–7 without changing existing Employer/contact request/response or permission contracts. §6 defines every new route, strict DTO, bounded query, field projection, HTTP status/header/media policy, idempotency behavior and information-disclosure boundary. §§5 and 7 define exact output identities, concrete typed FKs, append-only authority, grants, migration ordering, populated upgrade and fail-closed downgrade.

Do not compose committing legacy application services. A single outer transaction owns intake, canonical created outputs, exact typed command results, events and receipt. Reused output IDs are typed references, not fabricated creation events. Resolve replay only after current authorization and before stale-version checks. Section §7's migration design is the implementation specification; executable DDL is future test-first code, not a docs-only artifact or permission to migrate deployed SQL.

## 5. Ordered implementation PRs under this single plan
Each PR requires focused RED/GREEN evidence and fresh review. Subsequent PRs rebaseline after predecessors merge, without another planning cycle unless a material contract changes.

### PR A — Durable intake save, update, query and resume
**Outcome:** both intake kinds save partial data through real API/database and reopen from shared authorized lists in the preserved UI. No fake finalization or review buttons.
**Existing files to modify:** `src/golden_rose/persistence/models.py`, `src/golden_rose/persistence/entity_authorities.py`, `src/golden_rose/persistence/command_receipts.py`, `src/golden_rose/persistence/audit_events.py`; `src/golden_rose/auth/permissions.py`, `src/golden_rose/auth/principal.py`, `src/golden_rose/api/dependencies.py`, `src/golden_rose/api/errors.py`, `src/golden_rose/main.py` (register before SPA catchall), `src/golden_rose/static_app.py`; `apps/web/src/app/App.tsx`, `apps/web/src/app/AppShell.tsx`, `apps/web/src/i18n/messages.ts`, `apps/web/src/styles.css`.
**Proposed new files:** `src/golden_rose/application/intake_contracts.py`, `intake_commands.py`, `query_intakes.py`; `src/golden_rose/persistence/intakes.py`; `src/golden_rose/api/staff/intakes.py`, `intake_schemas.py`; `apps/web/src/api/intakeClient.ts`, `intakeContracts.ts`; `apps/web/src/intakes/IntakeWorkspace.tsx`, `IntakeForm.tsx`, `IntakeList.tsx` and colocated tests.
**Migration:** proposed `migrations/versions/0006_intake_drafts.py`, following existing `migrations/versions/0005_database_authority.py`; recheck number availability after predecessor merge. Implement contract §7 compatibility result backfill, intake/address shell and typed draft authority. Address capture/read authorization is required in PR A, not deferred to PR B. Link routes stay absent until PR C. PR A stores only Other interest descriptions; catalog selections arrive with PR B and must not refer to nonexistent catalogs. No deployed SQL mutation.
**TDD tasks:**
- Proposed `tests/unit/test_intake_contracts.py::test_partial_worker_and_employer_fields_remain_absent`: RED before typed draft validation; GREEN with bounded optional fields, invalid supplied values rejected.
- Proposed `tests/integration/test_intake_commands.py::test_create_commits_intake_event_and_receipt_atomically`: RED before command; GREEN atomic writer and injected rollback proof.
- Same file `::test_stale_revision_cannot_overwrite_current_intake`, `::test_retry_does_not_duplicate_intake`: independent adversarial commands, not manufactured harness failures.
- Proposed `tests/integration/test_intake_queries.py::test_second_session_recovers_unnamed_draft_with_bounded_cursor`: independent DB sessions, permission-before-results, strict page/cursor tests.
- Proposed `apps/web/src/intakes/IntakeWorkspace.test.tsx`: exact titles `saves partial intake and reopens the authoritative version`, `keeps later edits unsaved after a pending save`, `warns before abandoning unsaved changes`, `retries unknown saves with the original command identity`. First classify harness failures separately; implement one behavior checkpoint at a time.

### PR B — Review, restricted fields and follow-up
**Outcome:** incomplete markers, authorized version-bound review, append-only history and shared follow-up are usable for both intake kinds.
**Existing/new files:** PR A modules plus proposed `src/golden_rose/application/review_intake.py`, `src/golden_rose/application/follow_up_intake.py`, `src/golden_rose/auth/staff_directory.py`, `src/golden_rose/application/work_interests.py`, `src/golden_rose/api/staff/work_interests.py`, `src/golden_rose/persistence/work_interests.py`; `apps/web/src/intakes/IntakeReview.tsx`, `apps/web/src/intakes/IntakeFollowUp.tsx`, `apps/web/src/intakes/IntakeHistory.tsx`, `apps/web/src/intakes/WorkInterestPicker.tsx` and colocated tests. Proposed `migrations/versions/0007_intake_review_follow_up.py` adds catalog, review, protected payload and follow-up authority per contract §7. No intake link/finalize controls before PR C.
**TDD:** proposed `tests/integration/test_intake_review.py::test_review_binds_actor_time_and_exact_version`, `::test_relevant_edit_requires_new_review_without_erasing_prior_review`, `::test_ordinary_staff_cannot_review_without_delegation`; `tests/integration/test_intake_follow_up.py::test_follow_up_requires_owner_reason_and_due_instant`, `::test_reassignment_preserves_prior_owner_and_deadline`; frontend exact titles `shows missing information before opening intake`, `separates saved completeness and review status`, `shows follow-up history without granting private ownership`.
Backend gate is authoritative; do not equate hidden buttons with authorization. Test complete permission and field-disclosure matrix, review/save interleaving and stale completion focus/announcement suppression. New role names are not a new identity provider.

### PR C — Canonical linking/finalization and tranche qualification
**Outcome:** explicit existing-party links and reviewed new-party finalization produce real canonical records atomically; staff can reopen results without duplicate creation or losing intake history.
**Proposed new files:** `src/golden_rose/application/finalize_intake.py`, `src/golden_rose/application/link_intake.py`, `src/golden_rose/application/read_intake_outputs.py`, `src/golden_rose/persistence/workers.py`, `src/golden_rose/persistence/intake_outputs.py`, `src/golden_rose/persistence/command_results.py`, `src/golden_rose/api/staff/workers.py`, `src/golden_rose/api/staff/intake_outputs.py`, `src/golden_rose/api/staff/intake_output_schemas.py`; `apps/web/src/intakes/IntakeFinalization.tsx`, `apps/web/src/intakes/IntakeLinks.tsx`, `apps/web/src/api/workerClient.ts`, `apps/web/src/api/workerContracts.ts`, `apps/web/src/api/intakeOutputClient.ts`, `apps/web/src/api/intakeOutputContracts.ts`, `apps/web/src/workers/WorkerDetail.tsx`, `apps/web/src/intakes/CanonicalOutputDetail.tsx` and colocated tests. `command_results.py` is introduced already in PR A for compatibility and extended here. `intake_outputs.py` owns new contact-details/business-address/worksite/request reads and transaction-local insert primitives; DTOs map exactly to contract §6. Proposed `migrations/versions/0008_intake_finalization.py` adds concrete canonical links/output constraints and finalization cardinality checks.
**Existing files:** extend PR A authority/router files, `src/golden_rose/persistence/employers.py`, `src/golden_rose/persistence/employer_contacts.py` with flush-only primitives; preserve `src/golden_rose/application/create_draft_employer.py` and `src/golden_rose/application/create_employer_contact.py` outer-commit contracts. Browser navigation in `apps/web/src/app/App.tsx` registers new `/staff/intakes/workers`, `/staff/intakes/employers`, `/staff/intakes/:intakeId`, `/staff/workers/:workerId`, and `/staff/intake-outputs/:intakeId` screens; output screen resolves typed finalization IDs through canonical APIs, not stale snapshots. Preserve existing Employer route/navigation after predecessor rebaseline.
**TDD:** proposed `tests/integration/test_intake_finalization.py::test_new_worker_finalization_is_atomic_and_duplicate_safe`, `::test_employer_finalization_links_contact_worksite_and_request_without_opening_demand`, `::test_linking_existing_party_does_not_overwrite_it`, `::test_finalize_rechecks_review_version_and_revoked_permission`. Later-correction replay proof belongs to PR D below.
Proposed frontend titles: `finalizes reviewed intake and opens linked canonical records`, `does not treat finalization as placement or agreed compensation`, `retains current form after failed finalization`. Use real DB tests to prove transaction semantics, not component mocks.

### PR D — Canonical corrections, re-review and outcome qualification
**Outcome:** staff can recover finalized results, correct worker name/phone/residence/interests/availability, current employer representative/phone/party address, worksite address and request role/duties/count/offer/schedule descriptions through explicit canonical commands. Original intake/review/finalization remains immutable; current corrected facts can be separately reviewed. PR C alone does not complete the recover/correct outcome.

**Normative scope:** contract §9 exact route/DTO/value bounds, expected target and review/dependency versions, delegated correction/review rights plus restricted field permissions, mandatory reason and protected before/after audit, same-key retry, immutable original links, stale current-facts review and no intake overwrite. No identity merging, missing-child upsert, request reclassification, open demand, shift, verification or live/cloud authority.

**Proposed new files:** `migrations/versions/0009_canonical_corrections.py`; `src/golden_rose/application/canonical_correction_contracts.py`, `src/golden_rose/application/correct_canonical_records.py`, `src/golden_rose/application/review_canonical_outputs.py`; `src/golden_rose/persistence/canonical_corrections.py`, `src/golden_rose/persistence/canonical_reviews.py`; `src/golden_rose/api/staff/canonical_corrections.py`, `src/golden_rose/api/staff/canonical_correction_schemas.py`, `src/golden_rose/api/staff/canonical_reviews.py`; `apps/web/src/api/canonicalCorrectionClient.ts`, `apps/web/src/api/canonicalCorrectionContracts.ts`; `apps/web/src/intakes/CanonicalCorrectionForm.tsx`, `apps/web/src/intakes/CanonicalCurrentReview.tsx` and colocated tests.

**Existing/preceding files to extend:** `src/golden_rose/persistence/models.py`, `entity_authorities.py`, `command_receipts.py`, `command_results.py`, `audit_events.py`, `workers.py`, `intake_outputs.py` in that persistence directory; `src/golden_rose/auth/permissions.py`, `src/golden_rose/api/dependencies.py`, `src/golden_rose/main.py`, `src/golden_rose/api/staff/intake_output_schemas.py`, `src/golden_rose/application/finalize_intake.py`, `src/golden_rose/application/link_intake.py`; `apps/web/src/workers/WorkerDetail.tsx`, `apps/web/src/intakes/CanonicalOutputDetail.tsx`, `apps/web/src/api/intakeOutputContracts.ts`, `apps/web/src/i18n/messages.ts`; §6's exact authority/readback verifier and synthetic-admission files. Add current ContactDetails representative name without changing legacy EmployerContact DTO/version constraints. Column grants and protected payload/history constraints are migration-managed; no runtime migration is authorized here.

**Exact proposed tests:** `tests/unit/test_canonical_correction_contracts.py::test_correction_dtos_require_reason_version_and_only_authorized_section`; `tests/integration/test_canonical_corrections.py::test_each_supported_section_corrects_current_facts_with_atomic_reason_audit`, `::test_stale_and_changed_key_payload_cannot_overwrite`, `::test_unknown_commit_retry_replays_once_and_revocation_denies`, `::test_finalized_intake_review_and_original_output_versions_never_change`, `::test_contact_correction_preserves_legacy_name_and_unedited_address`, `::test_direct_sql_rejects_unaudited_correction_and_identity_change`; `tests/integration/test_canonical_reviews.py::test_correction_stales_current_review_and_rereview_binds_all_current_versions`, `::test_concurrent_correction_rejects_stale_rereview`, `::test_linked_draft_requires_refresh_and_new_intake_review`; `tests/integration/test_intake_migrations.py::test_populated_0008_upgrade_preserves_original_snapshots_and_legacy_contact`, `::test_0009_populated_downgrade_stops_before_ddl`; `tests/integration/api/test_canonical_corrections.py::test_restricted_correction_and_history_require_each_field_permission`. Parameterize every §9 command, not one representative happy path. Move PR C's later-correction replay acceptance proof to this tranche: `tests/integration/test_intake_finalization.py::test_replay_preserves_original_identity_links_after_later_correction`.

**Exact UI/browser acceptance:** `apps/web/src/intakes/CanonicalCorrectionForm.test.tsx` titles `corrects canonical facts without editing finalized intake`, `keeps address dirty after contact correction and unknown retry`, and `requires current facts re-review after correction`. Proposed `apps/web/tests/browser/staffIntakeRecovery.spec.ts` title `finalize correct rereview and reopen preserves original intake and review` uses an approved real app/PostgreSQL and production build in English/Spanish. Assert changed canonical reads, immutable original finalization IDs/versions, stale then current separate review, reasons visible only through authorized history, no duplicated records and no open demand. These are future tests, not execution evidence.

### Exact boundary tests and execution procedure (proposed new nodes)
- PR A M1 integration: `tests/integration/test_intake_commands.py::test_section_success_then_unknown_retry_preserves_other_section_and_versions`: save content successfully; commit address but lose response; retain original key/version; edit content again; retry address exactly; prove one address event, advanced aggregate version and unchanged persisted intake content until a later explicit content Save.
- PR A M1 frontend: `apps/web/src/intakes/IntakeWorkspace.test.tsx` title `keeps aggregate unsaved after one section succeeds and the next is unknown with later edits`. Proposed browser `apps/web/tests/browser/staffIntakeRecovery.spec.ts` title `section success then unknown with later dirty edits never reports all saved`: real app/DB, network response interruption after commit, later content edits while address unknown, same-key retry, dirty content survives response/refetch, only explicit later save clears aggregate unsaved, second session confirms exact persisted values. Exercise restricted denial and both languages; no guessed success or concealed-field round trip.
- PR A: `tests/integration/test_intake_authority.py::test_populated_0005_upgrade_preserves_legacy_result_bijection`, `::test_direct_sql_rejects_wrong_kind_null_authority_and_extra_result`, `::test_restricted_address_denial_has_no_response_or_log_value`; `tests/unit/api/test_intake_schemas.py::test_recursive_extra_keys_and_coercion_are_rejected`.
- PR B: `tests/integration/test_intake_review.py::test_follow_up_version_does_not_stale_content_review`, `::test_needs_follow_up_supersedes_prior_review`, `::test_reviewer_identity_is_server_resolved`, `::test_retired_interest_requires_current_selection`; `tests/integration/test_intake_queries.py::test_cursor_is_bound_to_scope_filter_and_page_size`.
- PR C: `tests/integration/test_intake_finalization.py::test_linked_dependency_change_blocks_finalize`, `::test_existing_worker_missing_children_blocks_without_writes`, `::test_existing_employer_explicit_reuse_never_overwrites`, `::test_one_intake_finalize_race_has_one_output_set`, `::test_finalize_rollback_leaves_no_partial_canonical_group`, `::test_commit_rejects_missing_extra_or_wrong_actor_results`, `::test_legacy_employer_type_revision_does_not_reclassify_finalized_request`; `tests/integration/api/test_intake_output_reads.py::test_created_and_reused_outputs_reopen_with_field_authorization`; `tests/integration/test_intake_migrations.py::test_populated_successor_downgrade_stops_before_ddl`.
- All four PRs: `tests/integration/api/test_intakes.py::test_every_response_branch_has_safe_problem_and_privacy_headers` and `::test_static_routes_precede_uuid_and_spa_catchalls`; frontend colocated tests exercise restricted-denied versus absent, stale response/focus ownership and bilingual parity. Expand parameterized branches for 401/403/404/405/409/413/415/422/503 and replay, not a lone happy-path request.

Each named node above is a **new proposed test**, not an observed collected symbol or executed pass. For each node: write the assertion/fixture first; run `env -u PYTHONPATH uv run pytest <exact-file>::<exact-node> -q`; classify import/setup/schema-fixture failures separately from intended behavior RED; implement only that behavior; rerun the identical node to GREEN; then run the affected file and predecessor regression set. Use `--collect-only -q` to verify actual node names after adding them. Use actual `tests/integration/conftest.py` database URL and permission fixtures, not invented receipt rows that fail before reaching the intended invariant.

Frontend single-file gate: `npm --userconfig apps/web/.npmrc --prefix apps/web run test -- src/intakes/IntakeWorkspace.test.tsx`; after focus/recovery checkpoints run `npm --userconfig apps/web/.npmrc --prefix apps/web run verify`. All expected results are criteria, not evidence already obtained. No test service starts in this docs-only lane.

## 6. Migration and compatibility gates
- Test fresh upgrade, populated existing Employer/contact upgrade, schema/constraint/role authority alignment and exact command receipt relationships.
- Test populated successor downgrade stop before DDL and empty-successor downgrade to 0005. Existing 0005 downgrade-base prohibition remains; update `.github/workflows/application-quality.yml` only as needed to give that legacy probe a verified empty successor-data disposable target after populated tests. Do not assume full pytest leaves it empty. No destructive deployed recovery.
- All existing Employer create/search/revision/contact tests remain regressions; classify immediate passes honestly, not as new REDs.
- Extend generated-fictional guards to new field categories before any synthetic develop admission. Never weaken existing allowlists to admit live names/addresses.
- Modify existing `scripts/verify_database_authority.py`, `scripts/verify_migration_database_readback.py`, `tests/integration/test_database_authority.py`, `tests/integration/test_initial_migration.py`, `tests/unit/test_verify_database_authority.py`, `tests/unit/test_verify_migration_database_readback.py` for exact new tables/constraints and grants. Update `src/golden_rose/application/synthetic_data.py` and `tests/unit/application/test_synthetic_data_admission.py` for deterministic fictional-only intake fixture admission; no broad default table grants or automatic develop activation.

## 7. Verification and runtime boundary
Source commands (expected successful results are criteria, not executed results):
```
env -u PYTHONPATH uv run pytest tests/unit -q
env -u PYTHONPATH uv run ruff check .
env -u PYTHONPATH uv run ruff format --check .
env -u PYTHONPATH uv run mypy src tests
env -u PYTHONPATH uv run bandit -q -r src
env -u PYTHONPATH uv run python scripts/validate_terraform_static.py
npm --userconfig apps/web/.npmrc --prefix apps/web run verify
git diff --check
```
Use repository CI-parity commands after rereading the workflow; do not interpret these focused commands as the complete security gate. Full service-backed pytest/migrations require an explicitly approved disposable local PostgreSQL target with no live data. Run dependency/SAST/SBOM/secret scans prescribed by current policy on final candidate; no fabricated pass totals. Test downgrade/upgrades and disposable cleanup.

Browser evidence: real production build with approved local application/database, not the temporary fixture server. Both journeys: enter partial → section-local save → reload → independently authenticated/authorized second session retrieves → correct → review → change → re-review → finalize → reopen canonical records → explicit canonical correction with reason → current-facts re-review → compare unchanged original intake/review/output links. Include one section success then next unknown with later unsaved changes. Verify narrow/desktop/zoom/keyboard/reduced-motion and bilingual errors, pending/unknown/retry states, restricted fields, no persistence/diagnostic leaks. Automated axe is not full manual accessibility or fluent-language evidence.

A private browser tool previously refused loopback URLs. Resolve a supported approved local browser path, or record NO EVIDENCE; do not bypass tool network restrictions or label jsdom/HTTP probes visual review. Record/clean exact disposable processes after testing. Actual cloud rollout requires a new bounded approval and produces independent runtime evidence after source merge.

## 8. Publication, drift and closeout
- Keep this planning worktree separate from the dirty improved-UI candidate. Never discard inherited changes or claim the worktree contains them.
- `docs/adr/ADR-0017-staff-intake-workflows.md` records this proposed boundary; numbering verified against current local ADR index, recheck before publication.
- Amend canonical field-purpose, permission, correction/audit, request/shift and follow-up contracts with precise scope/supersession wording; new intake review does not silently alter existing demand review.
- Align AGENTS/CURRENT_WORK/ROADMAP/NOTES/SECURITY/TECHNICAL_REQUIREMENTS/ARCHITECTURE/TECHNOLOGY_DECISIONS and the Obsidian contract. Preserve dated historical evidence; active status must identify proposed versus accepted versus implemented/deployed.
- Obtain fresh architecture/security/persistence and workflow/accessibility review over the complete frozen planning packet, reconcile findings, then publish only when approved. No automatic commit/push/PR from this drafting request.
- After implementation, full candidate gates and review precede protected promotion; final committed-head and exact outgoing-range scans must follow any final edit.

## 9. Publication completion checklist
- [x] Accepted conversation outcomes consolidated.
- [x] Existing Employer/contact constraints and committing-service hazard inspected.
- [x] Separate clean planning worktree created; improved UI preserved.
- [x] Independent audit findings captured and mapped to planning obligations in `docs/planning/staff-intake-source-of-truth-drift-audit.md`; 11 findings, repairs not yet applied.
- [ ] Complete root-document coverage: independent audit was limited by truncated reads and a consent timeout; no exhaustive drift clearance.
- [x] Exact technical DTO/status/header/field bounds, migration strategy and finalization output inventory written in `docs/planning/staff-intake-contract.md`; source compatibility inspected, not executed.
- [x] Canonical authority amendments and ADR written with scoped precedence.
- [ ] Fresh whole-packet review/acceptance; authored documents are not independent validation.
- [ ] Predecessor UI and protected planning publication/rebaseline gates satisfied.
- [ ] Full implementation and real runtime workflow evidence (future work).

### Local publication verification — 2026-09-14
Observed: 29 explicitly named existing source/CI/migration/test paths resolved in this checkout; all ADR relative document references resolved; missing-definition placeholder scan returned no matches. `git diff --check` and separate whitespace checks on new untracked plan/contract/ADR passed. Source inspection confirmed unchanged 200-character Employer/contact name limits, Employer draft/staff_entry constraints, contact version=1, existing router registration in `src/golden_rose/main.py`, legacy result FK/command-event uniqueness, existing grant verifier and 0005 downgrade prohibition. Frontend focused command uses the observed package `test` script.

These checks establish documentation/source anchoring, not SQL executability, independent architecture approval or working intake. New migrations/DTOs/tests remain proposed files and nodes. Fresh whole-packet review, preserved improved-UI predecessor merge, accepted protected planning publication and exact-tip coding rebaseline remain explicit stops. Parent-lane root/coverage edits are outside this author's ownership and are not independently cleared here.
