# Golden Rose Operations Platform — Production Notes

This is the concise, dated engineering and operational note log. It records observed evidence, decisions, verification, and handoffs. It is not a location for client personal data, credentials, raw exports, legal advice, or unapproved policy text.

## Evidence labels
- **Observed:** directly supplied, seen, or tool-verified.
- **Reported:** stated by client/staff but not independently validated.
- **Proposed:** a design direction, not yet approved.
- **Validated:** corroborated and approved for the stated use.

## 2026-07-30 — Living-document baseline
- **Observed:** Discovery includes duplicate Golden Rose/Balabusta employer-request forms, multiple worker forms, a general-labor request variant, a redacted work-request workbook, and a client-provided DCWP checklist.
- **Observed:** The workbook combines employer, contact, worksite, request, schedule, requirement, apparent assignment, and follow-up concepts in rows; it does not demonstrate a final database schema.
- **Proposed:** Begin delivery with an agency-staff employer-demand workflow: employer → contact → worksite → staffing request → shift need, with attributable events and authorized search.
- **Proposed:** Build the agency dashboard from authoritative operational records rather than separate metric-collection forms.
- **Proposed:** Follow employer demand with a staged worker profile and a transparent staff comparison aid. Matching remains human-reviewed and non-automated.
- **Confirmed constraint:** English/Spanish functional and accessibility parity applies across affected workflows, validation/errors, notices, notifications, documents, and staff surfaces.
- **Confirmed constraint:** Client artifacts are discovery evidence. Approved legal documents and the client’s codified business plan control production wording/rules.
- **Open gates:** field-purpose inventory; staff permissions/MFA; data classification; legal/business content; legacy-data governance; document-upload policy/security; retention/migration; production readiness.

## 2026-07-30 — Repository bootstrap
- **Observed:** GitHub repository `b-mackenzie-alexander/golden_rose_project` exists as a private repository; the local `main` branch was initialized with no commits and then configured with `origin`.
- **Observed:** The initial tracked surface is limited to the living-document baseline, ADR convention, and `.gitignore`.
- **Security decision:** Client-source images/rendered pages (`artifacts/`), generated client PDFs (`docs/client-deliverables/`), macOS metadata, local secret/environment files, caches, builds, and local infrastructure state are ignored.
- **Deferred review:** Existing discovery/compliance/governance Markdown notes and the PDF-generation script remain untracked pending a confidentiality/content review before a future documentation commit.
- **Verification:** `git diff --cached --check` passed for the initial staged surface. A gitleaks scan of a temporary materialization of the staged content reported no leaks.

## 2026-07-30 — Repository-governance direction
- **Observed:** `develop` was created from the initial `main` baseline and pushed to the private GitHub repository.
- **Proposed:** The active `docs/repository-governance-as-code` slice adds branch-source CI checks, GitHub policy IaC, drift verification, and ADR-0001 before protections are applied.
- **Required policy:** only `develop` or `hotfix/*` may target `main`; approved purpose-named branches target `develop`; both protected branches reject deletion and force pushes.
- **Constraint:** GitHub does not natively enforce a different merge method by base branch. Retain squash merging for feature → `develop`, and treat merge-commit selection for `develop` → `main` as a documented release gate pending a separately reviewed stronger control.

## 2026-07-30 — Repository-governance closeout
- **Validated:** PR #1 successfully added and exercised branch-source CI, repository-hygiene checks, secret scanning, policy IaC, and ADR-0001; PR #2 corrected the personal-repository protection payload.
- **Validated:** `infra/github/apply-repo-policy.sh` applied the committed policy and `infra/github/verify-repo-policy.sh` confirmed no checked-policy drift. Both `develop` and `main` report protected.
- **Validated:** Synthetic draft PR #3 from `develop` to `main` passed both required checks and was closed without merge, proving the permitted promotion source path without authorizing a release.
- **Known limitation:** source-branch policy is enforced by required CI; GitHub does not provide per-target merge-method enforcement. `develop` → `main` must select a merge commit under the documented release gate until a stronger reviewed mechanism is adopted.

## 2026-07-31 — Staff dashboard, service zone, and access-model proposal
- **Reported:** Agency staff use a calendar to understand jobs/coverage and Google Maps to investigate proximity between workers and hiring locations. Existing operational evidence remains fragmented across forms, calendars, workbooks, messaging, and manual follow-up.
- **Proposed mandate:** Phase 1 staff foundation includes an authorized demand work queue and a calendar/shift-coverage view derived from authoritative request, shift, assignment, and approved availability records; neither creates a parallel manual store.
- **Proposed location boundary:** Routine staff operations and reporting use approved broad service zones. Worker/home and exact household/worksite location remain restricted. Public/individual-level mapping, point-level proximity logic, third-party geocoding, and automated geographic ranking remain deferred pending separate approval.
- **Proposed staff-plane model:** Owner may delegate higher-level business operations to Manager; interchangeable Operations Staff cover day-to-day workflow. Platform Administrator is a separately bounded technical-support role with no standing operational-data, document, raw-database, secret, or business-role administration access. Exceptional access requires a defined, attributable break-glass process.
- **Detailed record:** `docs/planning/dashboard-location-and-access-model-proposal.md` records evidence labels, validation questions, non-goals, and revisit triggers.

## 2026-08-03 — Interim GCP billing and client handoff constraint
- **Accepted project direction:** GCP is the selected hosting platform. Cloud Run + Cloud SQL is the proposed managed-container/database baseline; region and detailed service configuration remain open decisions.
- **Reported contractual constraint:** Per Beatrice's account of the signed agreement, Beatrice is responsible for paying approved cloud-infrastructure charges until the engagement's final payment has been rendered. Billing responsibility then transfers to the client.
- **Accepted operational implication:** The rollout requires a documented billing/account/support handoff with final-payment confirmation, an effective transfer date, budget-alert recipients, recovery/emergency access, and service-continuity verification. The handoff does not authorize cloud provisioning, production-data use, or production promotion by itself.
- **Detailed plan:** `.hermes/plans/2026-08-03_gcp-rollout-management-plan.md`.

## 2026-08-03 — Canonical Phase 1 field-purpose inventory accepted
- **Accepted planning baseline:** The canonical employer-demand structure is neutral `Employer` → `EmployerContact` / `Worksite` / `StaffingRequest` → `ShiftNeed` / `RequestRequirement`, supported by `ServiceZone` and `AuditEvent`.
- **Rationale:** `Employer` represents both household and business hiring parties without forcing households into an organization model or creating duplicate workflows/stores. Employer type controls only approved extensions.
- **Security/data boundary:** Exact worksite address remains separate from broad service zone; employer-supplied assertions and free text remain restricted/unverified until agency review; no inventory field authorizes protected-trait/proxy filtering or automated matching, ranking, eligibility, hiring, or referral.
- **Source of truth:** `docs/planning/phase-1-canonical-field-purpose-inventory.md`. Workflow states, staged requiredness, client terminology, permission matrix, and retention remain separately gated.

## 2026-08-03 — Request and shift state model accepted
- **Accepted planning baseline:** Requests use guarded draft, review, information-needed, open, closed, and cancelled states. Shifts combine lifecycle and active coverage through draft, review, uncovered, partially covered, and covered states, with completed, unfulfilled, and cancelled terminal outcomes.
- **Reported operational evidence:** No-shows occur at the agency. Coverage may therefore reverse from covered to partial/uncovered through attributable events; prior coverage is not erased.
- **Integrity boundary:** Request closure requires terminal child shifts and never replaces their outcomes. Terminal requests/shifts may reopen only exceptionally by Owner/delegated Manager to pending review, with reason and preserved history.
- **Source of truth:** `docs/planning/phase-1-request-shift-state-model.md`. Queue timing/follow-up is governed separately by the accepted work-queue model; final field-by-state requiredness, permission matrix, and client terminology remain gated.

## 2026-08-03 — Work-queue aging and follow-up model accepted
- **Accepted planning baseline:** Request age, agency-controlled review time, explicit follow-up deadlines, and continuous shift coverage urgency are separate measures. Review/follow-up use a versioned business calendar where applicable; shift urgency uses continuous time.
- **Operational model:** Authorized staff share the queue with an accountable current owner. Queue presentation uses deterministic exception, urgent coverage, follow-up, request-review, and future-coverage lanes rather than an opaque score.
- **Provisional controls:** Review/follow-up/coverage thresholds and the three-attempt, three-business-day `no_response` safeguard are configurable review triggers requiring client validation before production; they are not SLAs or automatic actions.
- **Source of truth:** `docs/planning/phase-1-work-queue-aging-follow-up-model.md`. No trigger changes state, ownership, outcome, or contact behavior automatically.

## 2026-08-03 — Calendar and coverage semantics accepted
- **Accepted projection:** The staff calendar derives distinct date-only request milestones and timed shift occurrences from authoritative records. Pending, active, terminal, and cancelled states remain truthfully available; current state appears while prior facts remain in audit history.
- **Schedule/coverage boundary:** Shift intervals preserve IANA timezone and overnight behavior. Every occurrence is an explicit ShiftNeed; aggregate confirmed/requested counts are staff-only and no recurrence or worker-conflict inference is implemented in Phase 1.
- **Privacy boundary:** Service zone is the default. Exact worksite address requires permission-gated reveal in day/week views and remains excluded from month/aggregate/external surfaces.
- **Correction boundary:** Audited drag is permitted. Draft/pending shifts may be corrected after validation; active shifts use an atomic linked replacement and never carry coverage to the new interval; terminal shifts cannot be dragged.
- **Source of truth:** `docs/planning/phase-1-calendar-coverage-semantics.md`. No external sync or separate calendar status store is approved.

## 2026-08-03 — Service-zone taxonomy accepted and refined for owner-led discovery
- **Accepted structure:** Phase 1 uses a flat adaptive Owner-managed catalog. Worksites may have overlapping effective memberships with one primary/default; assigned requests/shifts preserve one zone/version so queues, calendars, and reports do not double count.
- **Assignment/governance:** The Owner may create, rename, deactivate, and assign zones as operational patterns emerge. Manager/Operations delegation remains a permission-matrix decision. ZIP/address automation, polygons, geocoding, coordinates, demographics, and proximity inference are not authorized.
- **Late-classification boundary:** Unassigned/review/outside-area conditions are not fake zones. Unassigned requests may open and must remain visible/countable. Later assignment does not alter lifecycle or coverage; terminal history changes only through explicit Owner correction.
- **Source of truth:** `docs/planning/phase-1-service-zone-taxonomy.md`. Exact names, descriptions, translations, and overlap conventions may emerge through pilot use and are not implementation prerequisites; local fixtures remain fictional.

## 2026-08-03 — NYC job-demand map accepted; client acceptance confirmed 2026-08-04
- **Required capability:** Phase 1 includes an authorized-staff NYC map. Official DCP 2020 Community District Tabulation Areas are pinned/checksummed base cells; the Owner groups cells into adaptive zones. Boroughs provide context only.
- **Derivation boundary:** Worksite addresses are geocoded server-side through a provider-neutral interface, then classified locally into the pinned CDTA geometry. Exact coordinates are transient/discarded by default; ambiguous/failed/outside results remain visible for Owner correction. A live provider remains separately gated.
- **Measures:** The map exposes named open-request, upcoming-shift, requested-worker, confirmed-coverage, remaining-gap, and classification-exception measures with accessible list parity—never an opaque heat/match score.
- **Worker boundary:** Phase 1 maps job demand only. Worker supply follows an approved worker-location/availability/privacy/suppression contract; geographic overlap does not establish suitability, referral, assignment, or commute feasibility.
- **Source of truth:** `docs/planning/phase-1-nyc-job-demand-map-contract.md`.

## 2026-08-03 — Staff permission matrix accepted; client acceptance confirmed 2026-08-04
- **Accepted authorization baseline:** Phase 1 uses server-enforced named permissions for Owner, delegated Manager, Operations Staff, and separately bounded Platform Administrator. Role labels alone never authorize broad data access or a bypass of record/field/state controls.
- **Operational boundaries:** Operations Staff share day-to-day employer-demand work but cannot reopen terminal records, govern zones/CDTAs, administer roles, export records, or access infrastructure. Manager elevation is explicitly delegated, attributable, revocable, and never self-granted. Exports are disabled in Phase 1.
- **Privacy/support boundaries:** Exact worksite access is a distinct, server-enforced permission and calendar access does not imply it. Platform Administrators use a separate technical identity/path with no standing operational-record, document, raw-database, backup, secret, or business-role access. Exceptional support is time-bounded, scoped, approved where feasible, attributable, automatically revoked, and Owner-reviewed.
- **Remaining live-use validation:** Name assigned Owners/Managers, delegated capabilities, precise-worksite permission recipients, recovery/access-review owners, and break-glass approvers; select/qualify MFA and account-lifecycle procedures.
- **Source of truth:** `docs/planning/phase-1-staff-permission-matrix.md`.

## 2026-08-03 — MFA, recovery, and support ownership approved for production policy
- **Accepted production baseline:** Every staff-plane and Platform Administrator account is individual and MFA-protected. Privileged/recovery roles require a phishing-resistant factor; TOTP is the approved fallback, recovery codes are recovery-only, shared accounts and knowledge-based questions are prohibited, and SMS/voice/email are not ordinary primary factors.
- **Recovery/session controls:** Assisted recovery requires pre-registered evidence, independent approval/execution, session/token revocation, fresh enrollment, notification, and safe attributable evidence. Initial limits are 30-minute inactivity/12-hour absolute for ordinary staff and 15-minute inactivity/4-hour absolute for the privileged technical path.
- **Ownership:** Owner/Manager business support and account approval remain separate from Platform Administrator technical execution. Beatrice/project technical lead coordinates security incidents during the engagement; a named client successor is required at handoff. Pilot access reviews are monthly, then quarterly after stabilization.
- **Production gate boundary:** Approval of this policy does not select Identity Platform or authorize deployment/live data. Name recovery/support personnel and contact paths, qualify the exact provider configuration, approve the initial cohort/data classification, and rehearse recovery/deprovisioning/support before production activation.
- **Source of truth:** `docs/planning/phase-1-mfa-recovery-support-ownership.md`.

## 2026-08-04 — Correction and audit-event behavior accepted
- **Authority boundary:** PostgreSQL domain rows are current operational truth; append-only `AuditEvent` records are authoritative material history. Phase 1 does not adopt full event sourcing, full-row snapshots, or ordinary-log authority.
- **Correction behavior:** Draft revisions need not preserve each prior value. Submitted material corrections, subsequent changes, replacements, transitions, restricted reveals, account-security actions, and correction-of-correction use linked attributable events. Required domain/event changes commit atomically with expected versions, idempotency keys, and all-or-nothing multi-record correlation.
- **Privacy/integrity:** Protected prior/new contact, exact-address, or restricted-text values inherit field authorization and stay out of routine logs/search/projections; secrets, MFA material, raw geocoding payloads, and precise coordinates are never audit payloads. Application paths append events but cannot update/delete them.
- **Projection boundary:** Queue, calendar, map, dashboard, reporting, and search are disposable authorized projections. Staleness/failure is explicit and never represented as false empty/zero state.
- **Live-data gates:** Client/counsel must still approve event/payload retention and disposal, restricted-history recipients, final reason terminology, legally required deletion/anonymization, and any stronger legal-record archival requirement.
- **Source of truth:** `docs/planning/phase-1-correction-audit-event-contract.md`.

## 2026-08-04 — Phase 1 coding-readiness drift closeout
- **Client acceptance:** The authorized-staff NYC job-demand map and the Owner/delegated Manager/Operations Staff/separately bounded Platform Administrator role model are accepted by the client. Named users, delegation details, map ergonomics, zone names, providers, and pilot configuration remain operational discoveries rather than reasons to reopen the accepted structural/security boundaries.
- **Legal posture correction:** Public-source legal research is suggested candidate guidance, not validated software behavior. Legal wording, fees, schedules, receipts, agreements, retention, and compliance claims remain disabled/unimplemented until current counsel documentation is translated into versioned requirements and acceptance tests and accepted by the client.
- **Operational discovery:** `docs/planning/phase-1-operational-discovery-register.md` records expected implementation/pilot questions and separates before-slice decisions from implementation discoveries, live-data gates, and public/legal release gates.
- **Model drift repair:** `TECHNICAL_REQUIREMENTS.md` and `ARCHITECTURE.md` now preserve explicit `WorksiteZoneMembership`, `WorksiteMapAreaAssignment`, `ServiceZoneComposition`, `MapAreaDatasetVersion`, and `MapArea` relationships instead of implying a direct Worksite-to-ServiceZone foreign key.
- **Migration clarification:** The audit contract prohibits unapproved legacy/live-data migration or import, not reviewed Alembic-style schema evolution for synthetic/local implementation.
- **Next handoff:** Approve a narrow first implementation plan and toolchain, including field-requiredness scope, synthetic-data classification, acceptance tests, and hard stop boundaries, before beginning the coding branch.

## 2026-08-04 — First Phase 1 implementation slice selected
- **Merged baseline:** PR #6 merged the coding-readiness closeout into `develop` at `bbe5c1d24d11d1ef9833e4af9de8da1c4ebcc887`; branch-policy, repository-hygiene, and CodeRabbit statuses succeeded. Local `develop` was fast-forwarded and verified equal to `origin/develop` before planning began.
- **Accepted tracer:** The first code slice will bootstrap the backend and expose only a synthetic/local staff command that transactionally reserves a security-internal actor/payload-bound `CommandReceipt`, creates one draft `Employer`, and appends `employer.created`. The client request supplies only `employer_type` and bounded `display_name`; state/source/actor/IDs/timestamps/version are server controlled.
- **Accepted stack:** Python 3.12 + uv/Hatchling, FastAPI/Pydantic v2/Uvicorn, synchronous SQLAlchemy 2 + psycopg 3, Alembic, PostgreSQL 16, pytest/HTTPX, Ruff, mypy, Bandit, pip-audit, and CycloneDX SBOM evidence. PostgreSQL integration evidence is required; SQLite is not a substitute.
- **Safety/data boundary:** No request-controlled synthetic actor/role/permission is allowed. Synthetic auth must fail closed outside local/test environments. Fixtures are fictional only; no client/live data, real identity, frontend, contact/worksite/request/shift, cloud, public route, external provider, or legal behavior is included.
- **Lane ownership:** This terminal session owns planning/project assessment. A fresh session implements the merged plan; a separate session independently reviews the code and manages PR readiness; a later bug/hotfix lane handles post-integration defects without bypassing the protected development flow.
- **Planning authority:** ADR-0002, ADR-0003, and `.hermes/plans/2026-08-04_phase-1-first-slice-plan.md`. Coding remains blocked until this planning packet is independently reviewed and merged to `develop`.
- **Independent planning audit:** Three read-only audit lanes assessed persistence/atomicity, project bootstrap/CI, and API/security behavior. The packet incorporates their command-receipt serialization, locked PostgreSQL test boundary, framework-default probe, actor-bound replay denial, redacted 503/500 behavior, static/dependency checks, and SBOM evidence. No audit identified a discovery/legal blocker to this synthetic staff-only slice.

## 2026-08-04 — Coding lane kickoff after PR #7 merge
- **Observed:** `git fetch origin --prune` showed `origin/develop` advanced from `bbe5c1d` to `3128762` and the planning branch `origin/docs/phase-1-first-slice-plan` was deleted after merge.
- **Observed:** Local `develop` was fast-forwarded to `3128762`, and `feat/staff-draft-employer-tracer` was created from that merged `origin/develop` tip for the coding lane.
- **Observed:** The merged planning authority is now present in-repo: ADR-0002, ADR-0003, and `.hermes/plans/2026-08-04_phase-1-first-slice-plan.md`.
- **Status correction:** `CURRENT_WORK.md` and `ROADMAP.md` were updated to reflect that PR #7 merged and coding is now active, while local PostgreSQL/API startup remains a separately approved runtime boundary.
- **Next coding boundary:** Begin Task 1 of the approved plan on `feat/staff-draft-employer-tracer`; do not start PostgreSQL or Uvicorn until explicit runtime approval is given.

## 2026-08-04 — FastAPI/Pydantic validation probe before Task 4 schema work
- **Observed:** With FastAPI 0.141.1 and Pydantic 2.13.4, a body model using `extra="forbid"` returns default `422` validation details with `type="extra_forbidden"` and `loc=["body", <field>]` when an unexpected request property is submitted.
- **Observed:** A required `Idempotency-Key` header declared through FastAPI returns default `422` validation details with `loc=["header", "Idempotency-Key"]` and `type="missing"` when the header is absent.
- **Implementation note:** Task 4 schema tests should rely on default model-level extra-field rejection unless the accepted contract later requires a custom response shape at the API boundary.

## 2026-08-04 — Task 5 non-runtime PostgreSQL scaffolding
- **Observed:** Non-runtime Task 5 scaffolding is now present: `compose.yaml`, `alembic.ini`, `migrations/env.py`, `migrations/script.py.mako`, `migrations/versions/0001_create_first_slice_tables.py`, `src/golden_rose/database.py`, `src/golden_rose/persistence/models.py`, and initial integration test files under `tests/integration/`.
- **Observed:** `docker compose config` rendered successfully with a dummy `GOLDEN_ROSE_TEST_DB_PASSWORD`, confirming loopback-only `127.0.0.1:55432` publication, PostgreSQL 16 image pinning, synthetic `golden_rose_test` database/user names, health check wiring, and ephemeral `tmpfs` data storage.
- **Observed:** The initial non-runtime integration surface passes: migration file exists at the expected path and SQLAlchemy metadata already contains `employers`, `command_receipts`, and `audit_events`.
- **Boundary reminder:** PostgreSQL service startup, live Alembic upgrade/downgrade execution, and real append-only/constraint qualification are still blocked pending explicit runtime approval.

## 2026-08-04 — Task 5 live PostgreSQL qualification
- **Observed RED:** Before startup, `uv run pytest tests/integration/test_initial_migration.py::test_live_schema_contains_expected_tables -v` failed with a PostgreSQL connection refusal at `127.0.0.1:55432`. After approved startup but before migrations, the same test failed because the database contained no application tables.
- **Observed startup:** Docker Desktop was not initially running; after launching it, `docker version` showed a live Docker Desktop 4.79.0 daemon. `docker compose --env-file .env.test up -d postgres-test` pulled `postgres:16.10`, started the loopback-only test container, and the container reached `healthy` state.
- **Observed migration evidence:** `uv run alembic upgrade head` succeeded against the synthetic `golden_rose_test` database. Live integration tests then passed for expected tables, exact column sets, check/unique constraints, append-only update/delete rejection on `command_receipts` and `audit_events`, and the repository guard that no Python file uses `create_all(`.
- **Observed downgrade evidence:** `uv run alembic downgrade base` succeeded; an immediate schema inspection showed only `alembic_version` remained. `uv run alembic upgrade head` then succeeded again and the combined unit + integration suite passed.
- **Observed teardown:** `docker compose --env-file .env.test down` removed the PostgreSQL test container and network; `docker compose ... ps -a` returned an empty service list.

## 2026-08-04 — Task 6 atomic command tracer
- **Observed RED 1:** The first focused Task 6 test failed with `ModuleNotFoundError: No module named 'golden_rose.application'` before the command module and persistence helpers existed.
- **Observed GREEN 1:** After adding `clock.py`, `identifiers.py`, `persistence/employers.py`, `persistence/command_receipts.py`, `persistence/audit_events.py`, and `application/create_draft_employer.py`, the happy-path integration test passed and proved one committed `command_receipts` row, one `employers` row, and one `audit_events` row with the expected version, actor, sequence, correlation, and payload-classification semantics.
- **Observed RED 2:** The changed-fields contract test failed because the first implementation recorded only field names and omitted the approved-value sub-object.
- **Observed GREEN 2:** The command now builds a narrow typed `changed_fields` payload containing only `field_names` plus approved safe values for `employer_type`, `lifecycle_status`, and `source_channel`, while omitting the `display_name` value and any row/request snapshot.
- **Observed RED 3:** A monkeypatched late failure during audit insertion left uncommitted employer and command-receipt rows visible inside the same session, proving the application command needed explicit rollback ownership.
- **Observed GREEN 3:** `create_draft_employer` now wraps the receipt/domain/audit write path in caller-owned rollback-on-error logic; the late-failure test passes and leaves zero rows in the same session after the exception.

## 2026-08-04 — Task 7 replay, conflict, and concurrency behavior
- **Observed RED 1:** A reused audit-event UUID raised a raw PostgreSQL/SQLAlchemy unique-violation message that exposed driver/SQL detail. After wrapping SQLAlchemy failures in `SafePersistenceError`, the same collision still rolled back the second command cleanly while returning the redacted message `persistence operation failed`.
- **Observed RED 2:** Reissuing the same command UUID with the same actor and identical payload failed as a persistence error on `command_receipts_pkey` instead of replaying the original success.
- **Observed GREEN 2:** `persistence/command_receipts.py` now reserves the command receipt with PostgreSQL `ON CONFLICT DO NOTHING`, re-loads the existing receipt on collision, compares actor + command metadata + request fingerprint, and replays the original `Employer` when the request is identical.
- **Observed GREEN 3:** Conflicting replays now raise `IdempotencyConflictError` without disclosing the original employer ID or request content, and conflicting actor/payload attempts leave row counts unchanged.
- **Validated concurrency:** Two independent sessions/threads racing the same command UUID now produce one authoritative create and one replay for identical payloads, and one authoritative create plus one `IdempotencyConflictError` for conflicting payloads. In both cases PostgreSQL persisted exactly one `command_receipts` row, one `employers` row, and one `audit_events` row.
- **Validation evidence:** `uv run pytest tests/integration/application/test_create_draft_employer.py -v` passed with `9 passed`; `uv run pytest tests/unit tests/integration -v` passed with `41 passed`; `git diff --check` passed.

## 2026-08-04 — Task 8 staff API endpoint tracer
- **Observed RED 1:** The first API integration test failed with `ModuleNotFoundError: No module named 'golden_rose.main'` before the FastAPI app and route existed.
- **Observed GREEN 1:** Added `src/golden_rose/api/errors.py`, `src/golden_rose/api/dependencies.py`, `src/golden_rose/api/staff/employers.py`, and `src/golden_rose/main.py`; the permitted POST now returns `201` with the exact draft-employer body and no retrieval `Location` header.
- **Observed RED 2:** The API originally surfaced framework `422` behavior for missing/malformed idempotency keys and accepted nil/non-v4 UUIDs. The route now validates `Idempotency-Key` through an explicit dependency and returns safe `400` problem details for missing, malformed, nil, and non-v4 keys.
- **Observed GREEN 2:** Identical replay now returns the same resource body with `Idempotency-Replayed: true`; conflicting replay maps to safe `409` problem details; denied principals return `403` before any receipt/employer/event write.
- **Observed validation/error boundary:** Request-body violations now return safe `422` problem details without framework internals. Known persistence failures return safe `503`, unexpected failures return safe `500`, and both leave zero rows in the database in the tested failure paths.
- **Observed route surface:** OpenAPI exposes the intended `POST /api/staff/v1/employers` route and no employer retrieval route.
- **Loopback proof:** After approval, loopback-only Uvicorn ran on `127.0.0.1:8001` against the synthetic PostgreSQL test database. A fictional POST returned `201`; the identical replay returned `201` with `Idempotency-Replayed: true`; direct DB inspection showed exactly one `employers` row, one `command_receipts` row, and one `audit_events` row.
- **Validation evidence:** `uv run pytest tests/integration/api/test_staff_employers.py -v` passed with `13 passed`; `uv run pytest tests/unit tests/integration -v` passed with `54 passed`; `git diff --check` passed.

## 2026-08-04 — Task 9 application CI quality gate
- **Observed implementation:** Added `.github/workflows/application-quality.yml` with one stable job/check named `application` for PRs targeting `develop` and `main`.
- **Workflow scope:** The job uses Python 3.12, `uv`, an ephemeral PostgreSQL 16 service, synthetic local/test auth env only, and no repository/environment secrets beyond the default read-only checkout token.
- **Quality steps encoded:** `uv lock --check`; locked sync; Ruff format/check; mypy on `src tests`; Bandit on `src`; pytest with `--cov-fail-under=95`; Alembic upgrade→downgrade→upgrade; `pip-audit`; reproducible CycloneDX SBOM generation to ignored `build/backend-sbom.cdx.json`; artifact upload via `actions/upload-artifact@v4`.
- **SBOM evidence boundary:** The SBOM is validated as JSON/CycloneDX during workflow generation and uploaded as CI evidence only; it is ignored locally and not committed.
- **Local verification evidence:** Ruby YAML parsing confirmed the workflow structure and the presence of the `application` job; a Python verification script confirmed the required workflow commands are present and that `pyproject.toml` dev dependencies include Ruff, mypy, Bandit, pip-audit, and CycloneDX tooling; `.gitignore` already ignores `build/`.

## 2026-08-04 — Task 10 coding-lane closeout and review handoff prep
- **Observed quality-gate tuning:** Local Task 10 qualification surfaced repo-level issues that the new CI workflow would have failed on: Ruff import/bugbear findings, strict mypy complaints on test helpers, and FastAPI `Annotated`/`Header` default incompatibility during route collection. The branch now uses FastAPI-compatible dependency signatures, a typed `occurred_at` audit insert parameter, a `Literal["local", "test"]` test annotation, Ruff per-file ignores only for the pre-existing PDF-generation helper's long lines/unused imports, and mypy configuration that still checks `src` and `tests` while disabling only `no-untyped-def` noise.
- **Observed verification ordering:** Running pytest before `alembic upgrade head` against the fresh ephemeral PostgreSQL runtime produced missing-table failures and misleading low coverage. Re-running in the workflow's intended order—upgrade before pytest, then downgrade→upgrade—resolved the issue.
- **Local verification evidence:** With `.env.test` loaded and approved `postgres-test` running healthy, `uv run pytest --cov=golden_rose --cov-report=term-missing --cov-fail-under=95` passed with `54 passed` and `99.03%` total coverage; `uv run mypy src tests` passed; `uv run ruff format --check .` and `uv run ruff check .` passed; `uv run alembic downgrade base && uv run alembic upgrade head` passed; `uv run pip-audit` reported no known vulnerabilities; and CycloneDX generation produced ignored `build/backend-sbom.cdx.json` with `bomFormat='CycloneDX'` and `specVersion='1.6'`.
- **Handoff status:** The branch was committed, exact-range checks passed (`git diff --check origin/develop...HEAD` and `gitleaks git --log-opts='origin/develop..HEAD'`), `postgres-test` was shut down, and `feat/staff-draft-employer-tracer` was pushed to `origin` for an independent review session before any PR is opened.

## 2026-08-04 — Review remediation for draft-employer tracer
- **Observed RED:** `create_app()` accepted `environment=production` with `auth_mode=synthetic`; the Pydantic validator ran only when a protected request resolved the settings dependency.
- **Observed GREEN:** `create_app()` now constructs `Settings` before returning the FastAPI application. `tests/unit/test_main.py` first failed because no startup validation existed and then passed; a direct import under prohibited production/synthetic settings was rejected before any server was started.
- **Observed CI remediation:** `.github/workflows/application-quality.yml` now applies `alembic upgrade head` before pytest, preserves downgrade→upgrade qualification, pins checkout/setup-python/setup-uv/upload-artifact to reviewed immutable SHAs, and uses `pip-audit --skip-editable` so the local editable project does not cause a false failing exit.
- **Observed scope remediation:** The unrelated formatting-only changes to `scripts/generate_client_prd_pdfs.py` were removed from the intended PR surface. Ruff excludes that existing client-deliverable helper from the backend gate rather than forcing formatting churn into this tracer branch.
- **Validated local CI-equivalent run:** A newly recreated loopback-only `postgres-test` container ran the migration-first sequence successfully: lock/sync, Ruff format/lint, mypy, Bandit, upgrade→pytest→downgrade→upgrade, editable-safe pip-audit, and CycloneDX generation. Pytest reported `55 passed` at `99.03%` coverage; SBOM validation reported CycloneDX `1.6`; pip-audit reported no known vulnerabilities.
- **Validated hygiene:** The workflow YAML parses; `git diff --check origin/develop` passed; Gitleaks scanned the uncommitted review surface materialization (`257580` bytes) with zero findings. The remediation remains uncommitted and requires an independent re-review before PR creation.

## 2026-08-04 — PR #8 merged and application-check governance handoff
- **Observed:** PR #8, `feat: implement staff draft employer tracer`, merged into protected `develop` at `0938c172806c6e9c50bec01e0c686e20c9dc7d68`; the remote feature branch was deleted after merge.
- **Validated:** PR #8 completed the owned `application`, `enforce`, and `check` checks successfully. The merged feature tree is patch-equivalent to the retired local feature branch.
- **Observed governance gap:** GitHub protection and `infra/github/repo-policy.json` still require only `enforce` and `check` on `develop` and `main`; `application` is qualified but not yet mandatory.
- **Active closeout:** `ci/require-application-check` adds `application` to both protected-branch required-context lists. The policy change must be independently reviewed and merged before the live branch protection is applied and verified under separate approval.
- **Validated candidate:** JSON parsing, policy semantic assertions, governance-script shell syntax, documentation assertions, and `git diff --check` passed. The drift verifier failed only because live `develop` and `main` still lack the newly desired `application` context, which is the expected pre-apply state.
- **Next product-planning boundary:** Plan an authorization-scoped employer read/search tracer using accepted Employer fields before adding contact, worksite, request, shift, or extension requiredness.

## 2026-08-04 — Solo-maintainer governance decision
- **Observed operating constraint:** `b-mackenzie-alexander` is the repository's only eligible collaborator. Requiring a conventional approval or CODEOWNERS review would deadlock owner-authored PRs; the repository is user-owned and has no organization-level ruleset alternative.
- **Accepted protocol:** Retain protected branches, required CI, branch/source policy, exact diff and secret scanning, independent delegated/separate-session review, documented blast-radius assessment, PR CI observation, and separate approval for policy application. Do not mandate CODEOWNERS or a separate-human reviewer while the repository has one maintainer.
- **Residual risk:** GitHub Actions status contexts come from PR-controlled workflow definitions and are not an immutable external trust boundary. The solo-maintainer protocol reduces rather than eliminates that risk; revisit a second reviewer, CODEOWNERS, or an external trusted-workflow boundary when the collaboration model supports it.
- **Validated governance-as-code hardening:** The apply script now derives every repository and branch-protection payload field from `repo-policy.json`; the verifier covers every declared applied control, including strict status checks, review flags, restrictions, lock/fork-sync, and block-creations. Both scripts fail closed if the policy branch scope is not exactly the supported `develop`/`main` pair. A mocked-API unit test exercises the generated apply payload without changing GitHub settings.

## 2026-08-04 — PR #9 merged and required application policy applied
- **Observed:** PR #9 merged the two-commit CI/governance slice into protected `develop` at `80f45053514c9854f9a100905028944eaf55fe9c`. Its `application`, `enforce`, and `check` checks all completed successfully.
- **Validated live control:** Under explicit approval, local `develop` was fast-forwarded to the merged tip and `infra/github/apply-repo-policy.sh` applied the committed repository/branch policy. `infra/github/verify-repo-policy.sh` then reported `Repository policy matches the checked committed controls.`
- **Validated direct evidence:** GitHub API responses for both `develop` and `main` reported strict required contexts `enforce`, `check`, and `application`, with administrator enforcement, conversation resolution, and force-push/deletion prevention retained.
- **Result:** The CI governance prerequisite is closed before the next product implementation plan.

## 2026-08-04 — Proposed Employer detail and bounded-search slice
- **Accepted planning direction:** The next bounded Phase 1 product slice retrieves one current Employer by UUID and searches current Employers through a privacy-conscious POST body using accepted Employer fields only.
- **Proposed authorization/privacy contract:** One named `employer:read` permission controls detail and search before any lookup/result derivation. Household/person-identifying name fragments stay out of URLs and logs; successful reads and applicable problems use `Cache-Control: no-store`.
- **Proposed search contract:** Require a normalized bounded name fragment; permit controlled employer type only as a secondary filter so the two exhaustive types cannot recreate list-all enumeration. Use literal case-insensitive substring matching, deterministic `received_at DESC`/UUID ordering, bounded filter-bound keyset pagination, no total count, and no unfiltered list/export.
- **Proposed authority boundary:** Query current PostgreSQL Employer truth directly. Ordinary reads/search create no Employer, `CommandReceipt`, or `AuditEvent`; no migration, index, extension, dependency, frontend, identity, adjacent entity, public route, or live data is included.
- **Planning artifacts:** ADR-0004 and `.hermes/plans/2026-08-04_phase-1-employer-read-search-plan.md` define the decision, exact TDD tasks, evidence, recovery, review focus, and stop conditions. They remain proposed until independently reviewed and merged.
- **Observed planning review:** Three independent read-only audit lanes found no application-code change but identified planning defects in the authoritative `AGENTS.md` boundary, type-only enumeration risk, authorization/cursor ownership, UTC cursor canonicalization, minimized persistence records, shared safe-error ownership, exact file surfaces, and evidence-SHA wording. Those findings were remediated; a concise cross-lane re-review found no High finding and one remaining contradictory cursor-sensitivity phrase, which was also corrected before commit.

## Updating this file
Add a short dated entry after a material planning, implementation, test, security, or release event. Link detailed evidence rather than duplicating it. Record commands and results only when they were actually run.
