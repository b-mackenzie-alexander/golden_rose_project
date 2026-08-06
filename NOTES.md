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
- **Observed planning review:** Three independent read-only audit lanes found no application-code change but identified planning defects in the authoritative `AGENTS.md` boundary, acceptance/evidence ownership, type-only enumeration risk, cursor sensitivity, authorization/cursor ownership, UTC cursor canonicalization, minimized persistence records, shared safe-error ownership, exact file surfaces, strict TDD executability, NFC write/search invariants, and final-head evidence wording. The initially visible findings were remediated before the first push. Delayed complete summaries then exposed omitted NFC and per-behavior TDD findings; a later re-review also found that already-satisfied deny/header/no-write invariants had been mislabeled as RED and that safe-error objects needed literal complete contracts. The packet was reopened to add the application-owned normalization invariant, composed/decomposed create/replay/search tests, genuine RED versus GREEN-regression classification, exact pytest node IDs with expected failures and minimal production checkpoints, literal full error objects with observed media type, mandatory log-redaction checks, and post-closeout exact-range verification. Implementation remains blocked until the corrected planning tip is reviewed and merged.

## 2026-08-05 — PR #10 merged; coding lane re-baselined for Employer read/search
- **Observed merge evidence:** `git fetch origin --prune` showed `origin/develop` advanced to `bde9143` with commit subject `docs: plan employer detail and bounded search (#10)`. `git show origin/develop:.hermes/plans/2026-08-04_phase-1-employer-read-search-plan.md` and `git show origin/develop:docs/adr/ADR-0004-phase-1-employer-read-search-boundary.md` both succeeded, proving the planning packet is present on the merged integration tip.
- **Observed re-baseline:** Local `develop` was fast-forwarded to `bde9143`, verified equal to `origin/develop`, and a fresh `feat/staff-employer-read-search` branch was created from that exact merged tip.
- **Observed drift repair target:** `CURRENT_WORK.md` still claimed the next slice remained planning-only and `ROADMAP.md` still showed ADR-0004/plan merge as unchecked. The coding lane now owns repair of those living-doc mismatches before the first RED test.
- **Coding boundary:** The approved slice remains limited to one named `employer:read` permission, exact UUID Employer detail, privacy-conscious POST search, filter-bound keyset pagination, no read-side writes, no schema/dependency changes, no frontend, no real identity, and no live/client data.
- **Immediate next step:** Re-read ADR-0004 and Task 1 of `.hermes/plans/2026-08-04_phase-1-employer-read-search-plan.md`, then begin with `tests/unit/auth/test_permissions.py::test_employer_read_permission_constant_has_exact_value` as the first required RED cycle.

## 2026-08-05 — Task 1 cycle 1 RED observed
- **Observed RED:** After adding only `tests/unit/auth/test_permissions.py::test_employer_read_permission_constant_has_exact_value`, `uv run pytest tests/unit/auth/test_permissions.py::test_employer_read_permission_constant_has_exact_value -v` failed during collection with `ImportError: cannot import name 'EMPLOYER_READ_PERMISSION' from 'golden_rose.auth.permissions'`.
- **Interpretation:** This is the expected Task 1 cycle 1 RED from the merged plan: the test fails because the exact read-permission constant does not yet exist, not because of an environment or unrelated collection problem.
- **Minimal GREEN checkpoint:** Add only `EMPLOYER_READ_PERMISSION = "employer:read"` beside the existing create constant before re-running the exact node.

## 2026-08-05 — Task 1 cycle 1 GREEN observed
- **Observed GREEN:** After adding only `EMPLOYER_READ_PERMISSION = "employer:read"` beside `CREATE_DRAFT_EMPLOYER_PERMISSION`, `uv run pytest tests/unit/auth/test_permissions.py::test_employer_read_permission_constant_has_exact_value -v` passed with `1 passed`.
- **Scope check:** No read helper, dependency grant, or role-based authorization logic was added in this cycle; the production change is limited to the exact permission constant required by Task 1 cycle 1.
- **Next TDD step:** Add `tests/unit/auth/test_permissions.py::test_principal_with_read_permission_is_allowed`, observe the expected RED on missing `can_read_employer`, then add only the exact membership helper.

## 2026-08-05 — Task 1 cycle 2 RED observed
- **Observed RED:** After adding only `tests/unit/auth/test_permissions.py::test_principal_with_read_permission_is_allowed`, `uv run pytest tests/unit/auth/test_permissions.py::test_principal_with_read_permission_is_allowed -v` failed during collection with `ImportError: cannot import name 'can_read_employer' from 'golden_rose.auth.permissions'`.
- **Interpretation:** This is the expected Task 1 cycle 2 RED from the merged plan: the test fails because the exact read-membership helper does not yet exist.
- **Minimal GREEN checkpoint:** Add only `can_read_employer(principal)` as direct membership in `EMPLOYER_READ_PERMISSION`, mirroring the existing create helper.

## 2026-08-05 — Task 1 cycle 2 GREEN observed
- **Observed GREEN:** After adding only `can_read_employer(principal)` in `src/golden_rose/auth/permissions.py`, `uv run pytest tests/unit/auth/test_permissions.py::test_principal_with_read_permission_is_allowed -v` passed with `1 passed`.
- **Scope check:** This cycle added no deny-path special case, no role-based branch, and no dependency wiring; it is limited to the exact permission-set membership helper required by Task 1 cycle 2.
- **Next TDD step:** Add the Task 1 cycle 3 dependency test for the synthetic principal permission set, observe RED against the current create-only grant, then add only `EMPLOYER_READ_PERMISSION` to the synthetic principal configuration.

## 2026-08-05 — Task 1 cycle 3 environment prerequisite and RED observed
- **Observed prerequisite issue:** The first run of `uv run pytest tests/unit/api/test_dependencies.py::test_synthetic_principal_has_exact_create_and_read_permissions -v` failed during import because session `PYTHONPATH` injected `/Users/genie/.hermes/hermes-agent` and its Python 3.11 site-packages ahead of the repo venv, producing `ModuleNotFoundError: No module named 'pydantic_core._pydantic_core'` while importing FastAPI/Pydantic.
- **Environment correction:** `uv run python` showed the repo interpreter was correct (`/Users/genie/Desktop/golden_rose_project/.venv/bin/python3`) but `sys.path` was polluted by the inherited Hermes-agent `PYTHONPATH`. Re-running the exact node with `env -u PYTHONPATH uv run pytest ...` isolated the project-local environment without changing the repo.
- **Observed RED:** With the polluted `PYTHONPATH` removed, `env -u PYTHONPATH uv run pytest tests/unit/api/test_dependencies.py::test_synthetic_principal_has_exact_create_and_read_permissions -v` failed for the intended reason: `principal.permissions` was only `frozenset({'employer:draft:create'})`, missing `employer:read`.
- **Minimal GREEN checkpoint:** Add only `EMPLOYER_READ_PERMISSION` to the synthetic principal permission set in `get_staff_principal()`.

## 2026-08-05 — Task 1 cycle 3 GREEN observed
- **Observed GREEN:** After adding only `EMPLOYER_READ_PERMISSION` to the `get_staff_principal()` synthetic permission set, `env -u PYTHONPATH uv run pytest tests/unit/api/test_dependencies.py::test_synthetic_principal_has_exact_create_and_read_permissions -v` passed with `1 passed`.
- **Scope check:** This cycle added no request/header grant path, no database/session behavior, and no extra role logic; it is limited to the exact configuration-owned synthetic principal permission set required by Task 1 cycle 3.
- **Next TDD step:** Run the Task 1 GREEN regressions before moving on: read-denial exact-membership behavior, role-label non-escalation, header non-escalation, and preserved startup rejection for production+synthentic auth.

## 2026-08-05 — Task 1 GREEN regressions passed
- **Observed regression coverage:** Added `tests/unit/auth/test_permissions.py::test_principal_without_read_permission_is_denied`, `tests/unit/auth/test_permissions.py::test_role_labels_do_not_grant_read_permission`, and `tests/unit/api/test_dependencies.py::test_request_headers_cannot_grant_read_permission` as the explicit Task 1 regression assertions for read-denial exact-membership, role-label non-escalation, and header non-escalation.
- **Validation evidence:** `env -u PYTHONPATH uv run pytest tests/unit/auth/test_permissions.py tests/unit/api/test_dependencies.py tests/unit/test_main.py::test_create_app_rejects_production_synthetic_auth_before_serving -v` passed with `11 passed`.
- **Preserved boundary:** The production+synthentic-auth startup rejection remained green, synthetic principal wiring stayed configuration-owned, and no new role/header escalation path was introduced while adding `employer:read`.
- **Next TDD step:** Task 1 is now fully green. Proceed to Task 2 with the next exact RED cycle: `tests/unit/application/test_employer_text.py::test_normalize_employer_text_returns_trimmed_nfc`.

## 2026-08-05 — Task 2 cycle 1 RED observed
- **Observed RED:** After creating only `tests/unit/application/test_employer_text.py::test_normalize_employer_text_returns_trimmed_nfc`, `env -u PYTHONPATH uv run pytest tests/unit/application/test_employer_text.py::test_normalize_employer_text_returns_trimmed_nfc -v` failed during collection with `ModuleNotFoundError: No module named 'golden_rose.application.employer_text'`.
- **Interpretation:** This is the expected Task 2 cycle 1 RED from the merged plan: the test fails because the shared text normalizer module does not yet exist.
- **Minimal GREEN checkpoint:** Create only `src/golden_rose/application/employer_text.py` with the typed helper that strips outer whitespace and applies `unicodedata.normalize("NFC", value)`.

## 2026-08-05 — Task 2 cycle 1 GREEN observed
- **Observed GREEN:** After creating only `src/golden_rose/application/employer_text.py` with `normalize_employer_text(value: str) -> str` implemented as `unicodedata.normalize("NFC", value.strip())`, `env -u PYTHONPATH uv run pytest tests/unit/application/test_employer_text.py::test_normalize_employer_text_returns_trimmed_nfc -v` passed with `1 passed`.
- **Scope check:** This cycle added only the shared typed normalizer helper. It did not yet wire search schemas, create-command normalization, cursor logic, or validation rules.
- **Next TDD step:** Continue to Task 2 cycle 2 with `tests/unit/api/test_employer_schemas.py::test_name_only_search_is_trimmed_and_nfc_normalized`.

## 2026-08-05 — Task 2 cycle 2 RED observed
- **Observed RED:** After adding only `tests/unit/api/test_employer_schemas.py::test_name_only_search_is_trimmed_and_nfc_normalized`, `env -u PYTHONPATH uv run pytest tests/unit/api/test_employer_schemas.py::test_name_only_search_is_trimmed_and_nfc_normalized -v` failed during collection with `ImportError: cannot import name 'SearchEmployersRequest' from 'golden_rose.api.staff.schemas'`.
- **Interpretation:** This is the expected Task 2 cycle 2 RED from the merged plan: the search request model does not yet exist.
- **Minimal GREEN checkpoint:** Add only `SearchEmployersRequest` in `src/golden_rose/api/staff/schemas.py` with the required name field wired to the shared `normalize_employer_text()` helper.

## 2026-08-05 — Task 2 cycle 2 GREEN observed
- **Observed GREEN:** After adding only `SearchEmployersRequest` with required `display_name_query` normalization via `normalize_employer_text()`, `env -u PYTHONPATH uv run pytest tests/unit/api/test_employer_schemas.py::test_name_only_search_is_trimmed_and_nfc_normalized -v` passed with `1 passed`.
- **Scope check:** This cycle added only the strict search request model shell plus shared normalization wiring. It did not yet add `employer_type`, page size, cursor support, response models, or new validation constraints.
- **Next TDD step:** Continue to Task 2 cycle 3 with `tests/unit/api/test_employer_schemas.py::test_search_accepts_name_with_optional_type`.

## 2026-08-05 — Task 2 cycle 3 RED observed
- **Observed RED:** After adding only `tests/unit/api/test_employer_schemas.py::test_search_accepts_name_with_optional_type`, `env -u PYTHONPATH uv run pytest tests/unit/api/test_employer_schemas.py::test_search_accepts_name_with_optional_type -v` failed with Pydantic `extra_forbidden` validation on `employer_type`.
- **Interpretation:** This is the expected Task 2 cycle 3 RED from the merged plan: `SearchEmployersRequest` does not yet accept the optional controlled employer-type filter.
- **Minimal GREEN checkpoint:** Add only `employer_type: Literal["household", "business"] | None = None` to `SearchEmployersRequest`.

## 2026-08-05 — Task 2 cycle 3 GREEN observed
- **Observed GREEN:** After adding only `employer_type: Literal["household", "business"] | None = None` to `SearchEmployersRequest`, `env -u PYTHONPATH uv run pytest tests/unit/api/test_employer_schemas.py::test_search_accepts_name_with_optional_type -v` passed with `1 passed`.
- **Scope check:** This cycle added only the optional controlled employer-type field. It did not yet add name-length bounds, control-character rejection, page size, cursor support, or response models.
- **Next TDD step:** Continue to Task 2 cycle 4 with `tests/unit/api/test_employer_schemas.py::test_search_rejects_name_outside_two_to_one_hundred_characters`.

## 2026-08-05 — Task 2 cycle 4 RED observed
- **Observed RED:** After adding only `tests/unit/api/test_employer_schemas.py::test_search_rejects_name_outside_two_to_one_hundred_characters`, `env -u PYTHONPATH uv run pytest tests/unit/api/test_employer_schemas.py::test_search_rejects_name_outside_two_to_one_hundred_characters -v` failed because a one-character `display_name_query` validated successfully (`Failed: DID NOT RAISE ValidationError`).
- **Interpretation:** This is the expected Task 2 cycle 4 RED from the merged plan: `SearchEmployersRequest` does not yet enforce the required 2..100 post-normalization length bounds.
- **Minimal GREEN checkpoint:** Add only the 2..100 length constraint to the normalized `display_name_query` validator in `SearchEmployersRequest`.

## 2026-08-05 — Task 2 cycle 4 GREEN observed
- **Observed GREEN:** After adding only the 2..100 post-normalization length check to `SearchEmployersRequest.display_name_query`, `env -u PYTHONPATH uv run pytest tests/unit/api/test_employer_schemas.py::test_search_rejects_name_outside_two_to_one_hundred_characters -v` passed with `1 passed`.
- **Scope check:** This cycle added only the name-length constraint. It did not yet add control-character rejection, unknown-field/type rejection updates for search, page size, cursor support, or response models.
- **Next TDD step:** Continue to Task 2 cycle 5 with `tests/unit/api/test_employer_schemas.py::test_search_rejects_unicode_control_characters`.

## 2026-08-05 — Task 2 cycle 5 RED observed
- **Observed RED:** After adding only `tests/unit/api/test_employer_schemas.py::test_search_rejects_unicode_control_characters`, `env -u PYTHONPATH uv run pytest tests/unit/api/test_employer_schemas.py::test_search_rejects_unicode_control_characters -v` failed because `display_name_query="Bad\nName"` validated successfully (`Failed: DID NOT RAISE ValidationError`).
- **Interpretation:** This is the expected Task 2 cycle 5 RED from the merged plan: `SearchEmployersRequest` does not yet reject Unicode control characters in the normalized search text.
- **Minimal GREEN checkpoint:** Add only Unicode category `C*` rejection to the `SearchEmployersRequest.display_name_query` validator.

## 2026-08-05 — Task 2 cycle 5 GREEN observed
- **Observed GREEN:** After adding only Unicode category `C*` rejection to `SearchEmployersRequest.display_name_query`, `env -u PYTHONPATH uv run pytest tests/unit/api/test_employer_schemas.py::test_search_rejects_unicode_control_characters -v` passed with `1 passed`.
- **Scope check:** This cycle added only control-character rejection. It did not yet add the remaining search-schema behaviors: unknown-field/type rejection updates, page size, cursor support, or response models.
- **Next TDD step:** Continue to Task 2 cycle 6 with `tests/unit/api/test_employer_schemas.py::test_search_forbids_unknown_fields_and_invalid_type`.

## 2026-08-05 — Task 2 cycle 6 reclassified as GREEN regression
- **Observed result:** After adding `tests/unit/api/test_employer_schemas.py::test_search_forbids_unknown_fields_and_invalid_type`, `env -u PYTHONPATH uv run pytest tests/unit/api/test_employer_schemas.py::test_search_forbids_unknown_fields_and_invalid_type -v` passed immediately with `1 passed`.
- **Reclassification rationale:** This planned RED is already satisfied by existing behavior. `SearchEmployersRequest` already uses `ConfigDict(extra="forbid")`, so unexpected fields are rejected with `extra_forbidden`, and the existing `Literal["household", "business"] | None` field already rejects invalid values with `literal_error`.
- **Discipline note:** Per the merged plan's TDD rules, this node is reclassified to a GREEN regression rather than forcing a fake RED or weakening production behavior.
- **Next TDD step:** Continue to Task 2 cycle 7 with `tests/unit/api/test_employer_schemas.py::test_search_page_size_defaults_and_bounds`.

## 2026-08-05 — Task 2 cycle 7 RED observed
- **Observed RED:** After adding only `tests/unit/api/test_employer_schemas.py::test_search_page_size_defaults_and_bounds`, `env -u PYTHONPATH uv run pytest tests/unit/api/test_employer_schemas.py::test_search_page_size_defaults_and_bounds -v` failed because `SearchEmployersRequest` has no `page_size` attribute (`AttributeError: 'SearchEmployersRequest' object has no attribute 'page_size'`).
- **Interpretation:** This is the expected Task 2 cycle 7 RED from the merged plan: the bounded page-size field/default is not implemented yet.
- **Minimal GREEN checkpoint:** Add only `page_size=25` constrained to integer bounds 1..50 on `SearchEmployersRequest`.

## 2026-08-05 — Task 2 cycle 7 GREEN observed
- **Observed GREEN:** After adding only `page_size: int = Field(default=25, ge=1, le=50)` to `SearchEmployersRequest`, `env -u PYTHONPATH uv run pytest tests/unit/api/test_employer_schemas.py::test_search_page_size_defaults_and_bounds -v` passed with `1 passed`.
- **Scope check:** This cycle added only bounded page-size support. It did not yet add cursor support or the search response models.
- **Next TDD step:** Continue to Task 2 cycle 8 with `tests/unit/api/test_employer_schemas.py::test_search_rejects_cursor_over_512_characters`.

## 2026-08-05 — Task 2 cycle 8 RED observed
- **Observed RED:** After adding only `tests/unit/api/test_employer_schemas.py::test_search_rejects_cursor_over_512_characters`, `env -u PYTHONPATH uv run pytest tests/unit/api/test_employer_schemas.py::test_search_rejects_cursor_over_512_characters -v` failed with `extra_forbidden` because `SearchEmployersRequest` does not yet define a `cursor` field.
- **Interpretation:** This is the expected Task 2 cycle 8 RED from the merged plan: the optional cursor field/length bound is not implemented yet.
- **Minimal GREEN checkpoint:** Add only `cursor: str | None = Field(default=None, max_length=512)` to `SearchEmployersRequest`.

## 2026-08-05 — Task 2 cycle 8 GREEN observed
- **Observed GREEN:** After adding only `cursor: str | None = Field(default=None, max_length=512)` to `SearchEmployersRequest`, `env -u PYTHONPATH uv run pytest tests/unit/api/test_employer_schemas.py::test_search_rejects_cursor_over_512_characters -v` passed with `1 passed`.
- **Scope check:** This cycle added only the optional bounded cursor field. It did not yet add the search response models.
- **Next TDD step:** Continue to Task 2 cycle 9 with `tests/unit/api/test_employer_schemas.py::test_employer_read_responses_expose_exact_accepted_fields`.

## 2026-08-05 — Task 2 cycle 9 RED observed
- **Observed RED:** After adding only `tests/unit/api/test_employer_schemas.py::test_employer_read_responses_expose_exact_accepted_fields`, `env -u PYTHONPATH uv run pytest tests/unit/api/test_employer_schemas.py::test_employer_read_responses_expose_exact_accepted_fields -v` failed during collection with `ImportError: cannot import name 'EmployerDetailResponse' from 'golden_rose.api.staff.schemas'`.
- **Interpretation:** This is the expected Task 2 cycle 9 RED from the merged plan: the read/detail search response models do not yet exist.
- **Minimal GREEN checkpoint:** Add only the exact detail/item/page response models and fields described in Section 3.

## 2026-08-05 — Task 2 cycle 9 GREEN observed
- **Observed GREEN:** After adding only `EmployerDetailResponse`, `EmployerSearchItemResponse`, and `EmployerSearchPageResponse` with the exact accepted Section 3 fields, `env -u PYTHONPATH uv run pytest tests/unit/api/test_employer_schemas.py::test_employer_read_responses_expose_exact_accepted_fields -v` passed with `1 passed`.
- **Scope check:** This cycle added only the response schema models. It did not add routes, application queries, persistence reads, or cursor codec behavior.
- **Next TDD step:** Task 2 schema cycles are complete. Continue with the cursor-codec RED sequence at `tests/unit/application/test_employer_search_cursor.py::test_filter_fingerprint_is_deterministic_for_normalized_filters`.

## 2026-08-05 — Task 2 cursor cycle 1 RED observed
- **Observed RED:** After creating only `tests/unit/application/test_employer_search_cursor.py::test_filter_fingerprint_is_deterministic_for_normalized_filters`, `env -u PYTHONPATH uv run pytest tests/unit/application/test_employer_search_cursor.py::test_filter_fingerprint_is_deterministic_for_normalized_filters -v` failed during collection with `ModuleNotFoundError: No module named 'golden_rose.application.search_cursor'`.
- **Interpretation:** This is the expected first cursor-codec RED from the merged plan: the cursor helper module/import does not yet exist.
- **Minimal GREEN checkpoint:** Create only `src/golden_rose/application/search_cursor.py` with canonical filter JSON plus SHA-256 fingerprinting over normalized `display_name_query` and optional `employer_type`.

## 2026-08-05 — Task 2 cursor cycle 1 GREEN observed
- **Observed GREEN:** After creating only `src/golden_rose/application/search_cursor.py` with `compute_filter_fingerprint(...)` using canonical JSON (`sort_keys=True`, compact separators), UTF-8 encoding, and SHA-256 hex digest output over `display_name_query` plus optional `employer_type`, `env -u PYTHONPATH uv run pytest tests/unit/application/test_employer_search_cursor.py::test_filter_fingerprint_is_deterministic_for_normalized_filters -v` passed with `1 passed`.
- **Scope check:** This cycle added only deterministic filter fingerprinting. It did not yet add cursor transport encoding/decoding, payload validation, canonical transport checks, or filter-binding enforcement.
- **Next TDD step:** Continue to cursor cycle 2 with `tests/unit/application/test_employer_search_cursor.py::test_cursor_round_trips_without_transport_padding`.

## 2026-08-05 — Task 2 cursor cycle 2 RED observed
- **Observed RED:** After adding only `tests/unit/application/test_employer_search_cursor.py::test_cursor_round_trips_without_transport_padding`, `env -u PYTHONPATH uv run pytest tests/unit/application/test_employer_search_cursor.py::test_cursor_round_trips_without_transport_padding -v` failed during collection with `ImportError: cannot import name 'decode_search_cursor' from 'golden_rose.application.search_cursor'`.
- **Interpretation:** This is the expected second cursor-codec RED from the merged plan: transport encode/decode helpers do not yet exist.
- **Minimal GREEN checkpoint:** Add only unpadded URL-safe Base64 cursor encode/decode for version, canonical UTC timestamp, employer UUID, and filter fingerprint.

## 2026-08-05 — Task 2 cursor cycle 2 GREEN observed
- **Observed GREEN:** After adding only `encode_search_cursor(...)` and `decode_search_cursor(...)` to `src/golden_rose/application/search_cursor.py`, using canonical JSON, canonical UTC `%Y-%m-%dT%H:%M:%S.%fZ` timestamps, and unpadded URL-safe Base64 transport with internal padding restoration on decode, `env -u PYTHONPATH uv run pytest tests/unit/application/test_employer_search_cursor.py::test_cursor_round_trips_without_transport_padding -v` passed with `1 passed`.
- **Scope check:** This cycle added only cursor round-trip transport helpers. It did not yet add malformed-payload validation, non-canonical transport rejection, or filter-binding enforcement.
- **Next TDD step:** Continue to cursor cycle 3 with `tests/unit/application/test_employer_search_cursor.py::test_cursor_rejects_malformed_or_invalid_typed_payloads`.

## 2026-08-05 — Task 2 cursor cycle 3 RED observed
- **Observed RED:** After adding only `tests/unit/application/test_employer_search_cursor.py::test_cursor_rejects_malformed_or_invalid_typed_payloads`, `env -u PYTHONPATH uv run pytest tests/unit/application/test_employer_search_cursor.py::test_cursor_rejects_malformed_or_invalid_typed_payloads -v` failed with `Failed: DID NOT RAISE ValueError`.
- **Interpretation:** This is the expected third cursor-codec RED from the merged plan: at least one malformed or wrong-typed payload class currently decodes instead of failing safely.
- **Minimal GREEN checkpoint:** Add only strict exact-key/type/version/UUID/timestamp/fingerprint validation with one safe exception path.

## 2026-08-05 — Task 2 cursor cycle 3 GREEN observed
- **Observed GREEN:** After adding only strict decode-time validation for exact key set, version, field types, canonical timestamp parsing, UUID parsing, and 64-lowercase-hex fingerprint format — all mapped to one safe `ValueError("invalid search cursor")` path — `env -u PYTHONPATH uv run pytest tests/unit/application/test_employer_search_cursor.py::test_cursor_rejects_malformed_or_invalid_typed_payloads -v` passed with `1 passed`.
- **Scope check:** This cycle added only malformed/typed payload validation. It did not yet add non-canonical transport rejection or filter-binding enforcement.
- **Next TDD step:** Continue to cursor cycle 4 with `tests/unit/application/test_employer_search_cursor.py::test_cursor_rejects_noncanonical_transport_payload`.

## 2026-08-05 — Task 2 cursor cycle 4 RED observed
- **Observed RED:** After adding only `tests/unit/application/test_employer_search_cursor.py::test_cursor_rejects_noncanonical_transport_payload`, `env -u PYTHONPATH uv run pytest tests/unit/application/test_employer_search_cursor.py::test_cursor_rejects_noncanonical_transport_payload -v` failed with `Failed: DID NOT RAISE ValueError` when the transport payload was the canonical cursor plus a trailing `=` padding character.
- **Interpretation:** This is the expected fourth cursor-codec RED from the merged plan: non-canonical transport forms still decode instead of being rejected.
- **Minimal GREEN checkpoint:** Reject transport payloads whose submitted form differs from canonical re-encoding.

## 2026-08-05 — Task 2 cursor cycle 4 GREEN observed
- **Observed GREEN:** After adding only canonical re-encoding comparison inside `decode_search_cursor(...)`, `env -u PYTHONPATH uv run pytest tests/unit/application/test_employer_search_cursor.py::test_cursor_rejects_noncanonical_transport_payload -v` passed with `1 passed`.
- **Scope check:** This cycle added only non-canonical transport rejection. It did not yet add filter-binding enforcement.
- **Next TDD step:** Continue to cursor cycle 5 with `tests/unit/application/test_employer_search_cursor.py::test_cursor_rejects_different_normalized_filters`.

## 2026-08-05 — Task 2 cursor cycle 5 RED observed
- **Observed RED:** After adding only `tests/unit/application/test_employer_search_cursor.py::test_cursor_rejects_different_normalized_filters`, `env -u PYTHONPATH uv run pytest tests/unit/application/test_employer_search_cursor.py::test_cursor_rejects_different_normalized_filters -v` failed with `TypeError: decode_search_cursor() got an unexpected keyword argument 'expected_filter_fingerprint'`.
- **Interpretation:** This still opens the intended RED from the merged plan: filter-binding enforcement is absent, and the decoder has no way to compare the decoded fingerprint against the current normalized filters.
- **Minimal GREEN checkpoint:** Add only expected-fingerprint binding with constant-time compare between the decoded fingerprint and the caller-provided normalized-filter fingerprint.

## 2026-08-05 — Task 2 cursor cycle 5 GREEN observed
- **Observed GREEN:** After adding only optional `expected_filter_fingerprint` binding to `decode_search_cursor(...)` with `hmac.compare_digest(...)` against the decoded cursor fingerprint, `env -u PYTHONPATH uv run pytest tests/unit/application/test_employer_search_cursor.py::test_cursor_rejects_different_normalized_filters -v` passed with `1 passed`.
- **Scope check:** This cycle added only filter-fingerprint binding at the codec boundary. The final remaining cursor regression in the merged plan is the UTC canonicalization proof.
- **Next TDD step:** Continue to cursor cycle 6 with `tests/unit/application/test_employer_search_cursor.py::test_cursor_encoder_canonicalizes_aware_timestamp_to_utc`.

## 2026-08-05 — Task 2 cursor cycle 6 reclassified as GREEN regression
- **Observed result:** After adding `tests/unit/application/test_employer_search_cursor.py::test_cursor_encoder_canonicalizes_aware_timestamp_to_utc`, `env -u PYTHONPATH uv run pytest tests/unit/application/test_employer_search_cursor.py::test_cursor_encoder_canonicalizes_aware_timestamp_to_utc -v` passed immediately with `1 passed`.
- **Interpretation:** The planned RED did not materialize because the existing `encode_search_cursor(...)` implementation already canonicalizes aware timestamps with `astimezone(UTC)` and fixed `%Y-%m-%dT%H:%M:%S.%fZ` formatting before serialization.
- **Scope check:** Reclassified as a GREEN regression rather than fabricating a failure or weakening working behavior. Cursor codec unit cycles are now complete.

## 2026-08-05 — Task 4 cycle 1 RED observed
- **Observed RED:** After creating `tests/integration/application/test_get_employer.py::test_permitted_get_returns_current_minimized_employer`, `env -u PYTHONPATH uv run pytest tests/integration/application/test_get_employer.py::test_permitted_get_returns_current_minimized_employer -v` failed during collection with `ModuleNotFoundError: No module named 'golden_rose.application.get_employer'`.
- **Interpretation:** This is the expected first application-query RED from the merged plan: the authorized employer detail query module does not yet exist.
- **Minimal GREEN checkpoint:** Create only `src/golden_rose/application/get_employer.py` with one query function that checks `can_read_employer` first, calls the minimized persistence lookup, and returns the record.

## 2026-08-05 — Task 4 cycle 1 GREEN implementation landed, exact verification blocked by DB prerequisite
- **Implemented checkpoint:** Created only `src/golden_rose/application/get_employer.py` with `get_employer(...)` that checks `can_read_employer` first, calls the minimized persistence lookup, and returns the record.
- **Observed verification blocker:** Re-running `env -u PYTHONPATH uv run pytest tests/integration/application/test_get_employer.py::test_permitted_get_returns_current_minimized_employer -v` advanced past the missing-module RED but then failed in fixture setup with `sqlalchemy.exc.OperationalError` / `psycopg.OperationalError` because PostgreSQL at `127.0.0.1:55432` refused the connection.
- **Interpretation:** The planned product-level GREEN is implemented, but the exact integration node is not yet verifiable in this session because the required synthetic PostgreSQL service is unavailable and has not been explicitly approved for startup here.

## 2026-08-05 — PostgreSQL prerequisite restored and Task 4 cycle 1 verified GREEN
- **Service path:** After explicit approval, created ignored local `.env.test`, started `postgres-test` with `docker compose --env-file .env.test up -d postgres-test`, and confirmed the container reached `healthy` on loopback port `55432`.
- **Second RED (expected pre-migration):** With the service up and `GOLDEN_ROSE_DATABASE_URL=postgresql+psycopg://golden_rose_test:test@127.0.0.1:55432/golden_rose_test`, re-running `env -u PYTHONPATH uv run pytest tests/integration/application/test_get_employer.py::test_permitted_get_returns_current_minimized_employer -v` failed in fixture setup with `psycopg.errors.UndefinedTable` / `sqlalchemy.exc.ProgrammingError` because `audit_events`, `command_receipts`, and `employers` did not yet exist.
- **Migration step:** Ran `env -u PYTHONPATH uv run alembic upgrade head` against the same synthetic database URL.
- **Observed GREEN:** Re-running `env -u PYTHONPATH uv run pytest tests/integration/application/test_get_employer.py::test_permitted_get_returns_current_minimized_employer -v` then passed with `1 passed`.
- **Current runtime state:** Synthetic PostgreSQL remains running for the next integration-node cycles.

## 2026-08-05 — Task 4 cycle 2 RED observed
- **Observed RED:** After extending `tests/integration/application/test_get_employer.py::test_missing_get_raises_nonreflective_not_found`, `env -u PYTHONPATH uv run pytest tests/integration/application/test_get_employer.py::test_missing_get_raises_nonreflective_not_found -v` failed during collection with `ModuleNotFoundError: No module named 'golden_rose.application.errors'`.
- **Interpretation:** The planned not-found translation surface does not yet exist. This still serves as the next honest RED for cycle 2 because the shared application error module is missing, so the query cannot yet raise the intended nonreflective `EmployerNotFoundError`.
- **Minimal GREEN checkpoint:** Create the shared application error module and translate authorized missing lookups to constant-message `EmployerNotFoundError` only after the authorized read attempt.

## 2026-08-05 — Task 4 cycle 2 GREEN observed
- **Implemented checkpoint:** Created `src/golden_rose/application/errors.py` with `EmployerNotFoundError` and updated `src/golden_rose/application/get_employer.py` to translate authorized missing lookups from `NoResultFound` to `EmployerNotFoundError("employer not found")` after the permission gate.
- **Observed GREEN:** With the synthetic PostgreSQL service and migrated schema still available, `env -u PYTHONPATH uv run pytest tests/integration/application/test_get_employer.py::test_missing_get_raises_nonreflective_not_found -v` passed with `1 passed`.
- **Scope check:** This cycle added only the shared not-found error surface and constant-message translation for the employer detail query.

## 2026-08-05 — Task 4 cycle 3 RED observed
- **Observed RED:** After creating `tests/integration/application/test_search_employers.py::test_permitted_search_returns_page_and_next_cursor`, `env -u PYTHONPATH uv run pytest tests/integration/application/test_search_employers.py::test_permitted_search_returns_page_and_next_cursor -v` failed during collection with `ModuleNotFoundError: No module named 'golden_rose.application.search_employers'`.
- **Interpretation:** This matches the planned first RED for the authorized search application query: the search module does not yet exist.
- **Minimal GREEN checkpoint:** Create one authorization-first `search_employers(...)` function that normalizes through the validated request, binds/decodes the optional cursor, requests `page_size + 1`, and emits `next_cursor` only when an extra row is present.

## 2026-08-05 — Task 4 cycle 3 GREEN observed
- **Implemented checkpoint:** Created `src/golden_rose/application/search_employers.py` with authorization-first `search_employers(...)`, literal case-insensitive name filtering, optional type narrowing, optional filter-bound cursor decode, `page_size + 1` bounded reads, descending received-at/UUID ordering, and `next_cursor` emission only when an extra row is present.
- **Observed GREEN:** With the synthetic PostgreSQL service and migrated schema still available, `env -u PYTHONPATH uv run pytest tests/integration/application/test_search_employers.py::test_permitted_search_returns_page_and_next_cursor -v` passed with `1 passed`.
- **Scope check:** This cycle added only the first authorized search query surface needed for the page/cursor happy path.

## 2026-08-05 — Task 4 cycle 4 RED observed
- **Observed RED:** After extending `tests/integration/application/test_search_employers.py::test_persistence_failure_rolls_back_once_and_raises_safe_error`, `env -u PYTHONPATH uv run pytest tests/integration/application/test_search_employers.py::test_persistence_failure_rolls_back_once_and_raises_safe_error -v` failed during collection with `ImportError: cannot import name 'SafePersistenceError' from 'golden_rose.application.errors'`.
- **Interpretation:** The shared safe-persistence error has not yet been moved/reused in the common application error module, so the search query cannot yet raise the intended redacted failure type.
- **Minimal GREEN checkpoint:** Move/reuse `SafePersistenceError` in `src/golden_rose/application/errors.py`, update create/search imports to use it, and make the search query roll back once before raising the shared safe error on `SQLAlchemyError`.

## 2026-08-05 — Task 4 cycle 4 GREEN observed
- **Implemented checkpoint:** Moved/reused `SafePersistenceError` in `src/golden_rose/application/errors.py`, updated `src/golden_rose/application/create_draft_employer.py` to import the shared error, and updated `src/golden_rose/application/search_employers.py` to roll back once and raise `SafePersistenceError("persistence operation failed")` on `SQLAlchemyError`.
- **Observed GREEN:** With the synthetic PostgreSQL service and migrated schema still available, `env -u PYTHONPATH uv run pytest tests/integration/application/test_search_employers.py::test_persistence_failure_rolls_back_once_and_raises_safe_error -v` passed with `1 passed`.
- **Scope check:** This cycle added only the shared safe-persistence error reuse and single-rollback redacted failure path for the employer search query.

## 2026-08-05 — Task 4 regression 1 reclassified as GREEN regression
- **Observed result:** After extending `tests/integration/application/test_get_employer.py::test_denied_get_never_calls_persistence`, `env -u PYTHONPATH uv run pytest tests/integration/application/test_get_employer.py::test_denied_get_never_calls_persistence -v` passed immediately with `1 passed`.
- **Interpretation:** The planned RED did not materialize because `src/golden_rose/application/get_employer.py` already authorizes before the persistence lookup. The spy remained untouched, so denied detail reads execute no persistence path.
- **Scope check:** Reclassified as a GREEN regression rather than fabricating a failure; no production change was required.

## 2026-08-05 — Task 4 regression 2 reclassified as GREEN regression
- **Observed result:** After extending `tests/integration/application/test_search_employers.py::test_denied_search_never_decodes_fingerprints_or_queries`, the first run exposed a test-harness setup error (`AttributeError` on attaching a probe to bare `object()`), which was corrected without production changes. Re-running `env -u PYTHONPATH uv run pytest tests/integration/application/test_search_employers.py::test_denied_search_never_decodes_fingerprints_or_queries -v` then passed immediately with `1 passed`.
- **Interpretation:** The planned RED did not materialize because `src/golden_rose/application/search_employers.py` already authorizes before cursor decode and SQL execution. Both decode and query probes remained untouched for denied access.
- **Scope check:** Reclassified as a GREEN regression after fixing the test harness only; no production change was required.

## 2026-08-05 — Task 4 regression 3 reclassified as GREEN regression
- **Observed result:** After extending `tests/integration/application/test_search_employers.py::test_search_normalizes_decomposed_query_after_authorization`, `env -u PYTHONPATH uv run pytest tests/integration/application/test_search_employers.py::test_search_normalizes_decomposed_query_after_authorization -v` passed immediately with `1 passed`.
- **Interpretation:** The planned RED did not materialize because the validated `SearchEmployersRequest` already normalizes decomposed text through the shared normalizer before fingerprint construction and query execution. A decomposed `Cafe\u0301` search matched stored `Café Rose Staffing` without any new normalization path.
- **Scope check:** Reclassified as a GREEN regression rather than fabricating a failure; no production change was required.

## 2026-08-05 — Task 4 regression 4 reclassified as GREEN regression
- **Observed result:** After extending `tests/integration/application/test_search_employers.py::test_role_label_without_permission_remains_denied`, `env -u PYTHONPATH uv run pytest tests/integration/application/test_search_employers.py::test_role_label_without_permission_remains_denied -v` passed immediately with `1 passed`.
- **Interpretation:** The planned RED did not materialize because Task 1 permission checks already rely on exact permission membership rather than role labels. A `platform_administrator` role without `employer:read` remained denied, and the query probe was never reached.
- **Scope check:** Reclassified as a GREEN regression rather than fabricating a failure; no production change was required.

## 2026-08-05 — Task 4 regression 5 reclassified as GREEN regression
- **Observed result:** After extending `tests/integration/application/test_search_employers.py::test_successful_queries_perform_no_writes_or_transaction_control`, `env -u PYTHONPATH uv run pytest tests/integration/application/test_search_employers.py::test_successful_queries_perform_no_writes_or_transaction_control -v` passed immediately with `1 passed`.
- **Interpretation:** The planned RED did not materialize because successful `search_employers(...)` paths are already SELECT-only. With commit/flush/rollback rigged to fail, the query still succeeded and authoritative row counts for `employers`, `command_receipts`, and `audit_events` remained unchanged.
- **Scope check:** Reclassified as a GREEN regression rather than fabricating a failure; no production change was required.

## 2026-08-05 — Task 4 regression batch passed
- **Observed result:** Ran `env -u PYTHONPATH uv run pytest tests/integration/application/test_get_employer.py tests/integration/application/test_search_employers.py tests/integration/application/test_create_draft_employer.py tests/integration/api/test_staff_employers.py -v` against the migrated synthetic PostgreSQL database after sourcing `.env.test`. Result: `31 passed, 1 warning in 1.63s`.
- **Warning note:** The only warning was an upstream `StarletteDeprecationWarning` from `fastapi.testclient` about `httpx`/`starlette.testclient`; no slice-local failures or additional warnings appeared.
- **Scope check:** Task 4 application regressions and adjacent create/API preservation checks are green, so the branch is ready to proceed into Task 5 HTTP read-route RED cycles.

## 2026-08-05 — Task 5 cycle 1 RED observed
- **Observed RED:** Created `tests/integration/api/test_staff_employer_reads.py` and ran `env -u PYTHONPATH uv run pytest tests/integration/api/test_staff_employer_reads.py::test_search_returns_minimized_page_cursor_no_total_and_no_store -v` after fixing one test-harness seeding issue (shared identifier factory instance required for deterministic double-create setup). The honest product RED is `404 Not Found` on `POST /api/staff/v1/employers/search`.
- **Interpretation:** This matches the planned first RED for Task 5 cycle 1: the static search route is not declared yet, so the read-only HTTP slice does not exist.
- **Scope check:** No production change yet; only the new API integration test and a harness correction were added.

## 2026-08-05 — FastAPI route probe for static `/search` vs dynamic `/{employer_id}`
- **Observed probe:** Ran a disposable `env -u PYTHONPATH uv run python` FastAPI/TestClient probe with both `POST /api/staff/v1/employers/search` and `GET /api/staff/v1/employers/{employer_id}` declared. Observed routing: `POST /search` hit the static search route, `GET /search` was captured by the dynamic detail route with `employer_id='search'`, `GET /123` hit detail, and `POST /123` returned `405 Method Not Allowed`.
- **Implementation decision:** Declare the static `/search` route before any future dynamic `/{employer_id}` route exactly as planned.

## 2026-08-05 — Task 5 cycle 1 GREEN observed
- **Implemented checkpoint:** Added only static `POST /api/staff/v1/employers/search` in `src/golden_rose/api/staff/employers.py`, mapped `SearchEmployersRequest` to the existing `search_employers(...)` application query, converted items to the minimized `EmployerSearchPageResponse`, and set `Cache-Control: no-store` on success.
- **Observed GREEN:** Re-ran `env -u PYTHONPATH uv run pytest tests/integration/api/test_staff_employer_reads.py::test_search_returns_minimized_page_cursor_no_total_and_no_store -v` after sourcing `.env.test`; result was `1 passed, 1 warning`. The only warning was the existing upstream `StarletteDeprecationWarning` from `fastapi.testclient`.
- **Scope check:** This cycle added only the static POST search route and success-path `no-store` header; dynamic detail routing and extra error handling remain for later cycles.

## 2026-08-05 — Task 5 cycle 2 RED observed
- **Observed RED:** Extended `tests/integration/api/test_staff_employer_reads.py::test_authorized_invalid_search_inputs_return_nonreflective_no_store_422` and ran `env -u PYTHONPATH uv run pytest tests/integration/api/test_staff_employer_reads.py::test_authorized_invalid_search_inputs_return_nonreflective_no_store_422 -v` after sourcing `.env.test`. The exact failure was `500 Internal Server Error` for an authorized search request with `cursor="bad-cursor"`.
- **Interpretation:** This matches the planned next RED: cursor-originated validation is still unhandled at the API boundary, so invalid search cursors currently fall through to the generic 500 path instead of a safe 422 with `Cache-Control: no-store`.
- **Scope check:** No production change yet; only the new API integration node was added.

## 2026-08-05 — Task 5 cycle 2 GREEN observed
- **Implemented checkpoint:** Added `no_store_problem_response(...)` in `src/golden_rose/api/errors.py` and updated `src/golden_rose/api/staff/employers.py` so the search route catches safe cursor-decoder `ValueError` failures and returns the exact nonreflective 422 problem object with `Cache-Control: no-store`. The route return annotation was widened to allow the explicit problem response branch.
- **Observed GREEN:** Re-ran `env -u PYTHONPATH uv run pytest tests/integration/api/test_staff_employer_reads.py::test_authorized_invalid_search_inputs_return_nonreflective_no_store_422 -v` after sourcing `.env.test`; result was `1 passed, 1 warning`. The only remaining warning was the existing upstream `StarletteDeprecationWarning` from `fastapi.testclient`.
- **Scope check:** This cycle added only the safe 422 mapping and `no-store` problem response path for invalid search cursors; broader 503/500 route failure mapping remains for the next cycle.

## 2026-08-05 — Task 5 cycle 3 RED observed
- **Observed RED:** Extended `tests/integration/api/test_staff_employer_reads.py::test_search_failures_map_to_safe_redacted_503_and_500` and ran `env -u PYTHONPATH uv run pytest tests/integration/api/test_staff_employer_reads.py::test_search_failures_map_to_safe_redacted_503_and_500 -v` after sourcing `.env.test`. The exact failure was missing `Cache-Control` on the `503 Service Unavailable` response after monkeypatching `search_employers` to raise `SafePersistenceError`; the route still relied on generic exception handling for 503/500 paths.
- **Interpretation:** This matches the planned RED: search-route failure responses are not yet routed through a `no-store` response path for shared `503` and fallback `500` errors.
- **Scope check:** No production change yet; only the new API integration node was added.

## 2026-08-05 — Task 5 cycle 3 GREEN observed
- **Implemented checkpoint:** Updated `src/golden_rose/api/staff/employers.py` so the search route now catches `SafePersistenceError` and fallback `Exception` locally, returning exact redacted `503`/`500` problem objects via `no_store_problem_response(...)`. This preserved the shared problem shapes while adding route-local `Cache-Control: no-store` on failure responses.
- **Observed GREEN:** Re-ran `env -u PYTHONPATH uv run pytest tests/integration/api/test_staff_employer_reads.py::test_search_failures_map_to_safe_redacted_503_and_500 -v` after sourcing `.env.test`; result was `1 passed, 1 warning`. The only warning remained the upstream `StarletteDeprecationWarning` from `fastapi.testclient`.
- **Scope check:** This cycle added only search-route-local `no-store` mapping for safe `503` and fallback `500` failures; dynamic detail routing and 404 handling remain for later cycles.

## 2026-08-05 — Task 5 cycle 4 RED observed
- **Observed RED:** Extended `tests/integration/api/test_staff_employer_reads.py::test_get_existing_returns_exact_detail_with_no_store` and ran `env -u PYTHONPATH uv run pytest tests/integration/api/test_staff_employer_reads.py::test_get_existing_returns_exact_detail_with_no_store -v` after sourcing `.env.test`. The exact failure was `404 Not Found` on `GET /api/staff/v1/employers/81818181-8181-4181-8181-818181818181` after successfully seeding the employer through the existing POST command.
- **Interpretation:** This matches the planned RED for cycle 4: the dynamic detail route is absent, so authorized exact employer detail reads are not yet exposed over HTTP.
- **Scope check:** No production change yet; only the new API integration node was added.

## 2026-08-05 — Task 5 cycle 4 GREEN observed
- **Implemented checkpoint:** Added only `GET /api/staff/v1/employers/{employer_id}` in `src/golden_rose/api/staff/employers.py`, mapped it to the existing `get_employer(...)` application query, returned the exact `EmployerDetailResponse`, and set `Cache-Control: no-store` on success.
- **Observed GREEN:** Re-ran `env -u PYTHONPATH uv run pytest tests/integration/api/test_staff_employer_reads.py::test_get_existing_returns_exact_detail_with_no_store -v` after sourcing `.env.test`; result was `1 passed, 1 warning`. The only warning remained the upstream `StarletteDeprecationWarning` from `fastapi.testclient`.
- **Scope check:** This cycle added only the authorized detail GET route and success-path `no-store`; absent-detail 404 handling remains for the next cycle.

## 2026-08-05 — Task 5 cycle 5 RED observed
- **Observed RED:** Extended `tests/integration/api/test_staff_employer_reads.py::test_get_absent_returns_nonreflective_no_store_404` and ran `env -u PYTHONPATH uv run pytest tests/integration/api/test_staff_employer_reads.py::test_get_absent_returns_nonreflective_no_store_404 -v` after sourcing `.env.test`. The exact failure was `500 Internal Server Error` after monkeypatching the route-level `get_employer` import to raise `EmployerNotFoundError("employer not found")`.
- **Interpretation:** This matches the planned RED for cycle 5: application-level not-found errors are still unhandled at the API boundary, so absent detail reads fall through to the generic 500 path instead of the exact nonreflective 404 object with `Cache-Control: no-store`.
- **Scope check:** No production change yet; only the new API integration node was added.

## 2026-08-05 — Task 5 cycle 5 GREEN observed
- **Implemented checkpoint:** Updated `src/golden_rose/api/staff/employers.py` so the detail route now catches `EmployerNotFoundError` locally and returns the exact nonreflective `404 Not Found` problem object through `no_store_problem_response(...)`. The detail route return annotation was widened to allow the explicit problem-response branch.
- **Observed GREEN:** Re-ran `env -u PYTHONPATH uv run pytest tests/integration/api/test_staff_employer_reads.py::test_get_absent_returns_nonreflective_no_store_404 -v` after sourcing `.env.test`; result was `1 passed, 1 warning`. The only warning remained the upstream `StarletteDeprecationWarning` from `fastapi.testclient`.
- **Scope check:** This cycle added only absent-detail 404 mapping with `Cache-Control: no-store`; remaining API regressions are the planned authorization, cursor round-trip, write-silence, OpenAPI, and log-hygiene checks.

## 2026-08-05 — Task 5 regression 1 reclassified as GREEN regression
- **Observed result:** After extending `tests/integration/api/test_staff_employer_reads.py::test_denied_get_runs_no_sql_and_headers_cannot_elevate`, `env -u PYTHONPATH uv run pytest tests/integration/api/test_staff_employer_reads.py::test_denied_get_runs_no_sql_and_headers_cannot_elevate -v` passed immediately with `1 passed, 1 warning` after sourcing `.env.test`.
- **Interpretation:** The planned RED did not materialize because the detail HTTP route still depends on the Task 4 authorization-first `get_employer(...)` query and the principal dependency ignores authority-escalation headers. A denied GET returned the exact safe `403` object, forged `X-Actor-Id` / `X-Role-Name` / `X-Permissions` headers did not elevate access, and the SQL probe observed zero statements.
- **Scope check:** Reclassified as a GREEN regression rather than fabricating a failure; no production change was required.

## 2026-08-05 — Task 5 regression 2 reclassified as GREEN regression
- **Observed result:** After extending `tests/integration/api/test_staff_employer_reads.py::test_search_filters_and_cursor_round_trip_over_http`, `env -u PYTHONPATH uv run pytest tests/integration/api/test_staff_employer_reads.py::test_search_filters_and_cursor_round_trip_over_http -v` passed immediately with `1 passed, 1 warning` after sourcing `.env.test`.
- **Interpretation:** The planned RED did not materialize because the existing HTTP search route already delegates to the previously verified schema/application/persistence path. A bounded `business` search for `rose` returned the newest matching employer, emitted an opaque cursor, and the follow-up request with the same filters returned the next older matching employer with `next_cursor: null`; the `household` match stayed excluded and both responses preserved `Cache-Control: no-store`.
- **Scope check:** Reclassified as a GREEN regression rather than fabricating a failure; no production change was required.

## 2026-08-05 — Task 5 regression 3 RED observed
- **Observed RED:** After extending `tests/integration/api/test_staff_employer_reads.py::test_denied_search_precedes_cursor_and_sql_and_headers_cannot_elevate`, `env -u PYTHONPATH uv run pytest tests/integration/api/test_staff_employer_reads.py::test_denied_search_precedes_cursor_and_sql_and_headers_cannot_elevate -v` failed with `500 Internal Server Error` after sourcing `.env.test`.
- **Interpretation:** This exposed an honest API-boundary defect in the planned regression node: the search route's local fallback `except Exception` branch was swallowing `PermissionError`, so denied search requests fell through to the generic `500` path instead of returning a safe `403` before any cursor decode or SQL work.
- **Minimal GREEN checkpoint:** Add only a search-route-local `PermissionError` mapping to the exact `403 forbidden` problem object through `no_store_problem_response(...)`, preserving pre-authorization cursor/SQL silence and header non-elevation.

## 2026-08-05 — Task 5 regression 3 GREEN observed
- **Implemented checkpoint:** Updated `src/golden_rose/api/staff/employers.py` so `POST /api/staff/v1/employers/search` now catches `PermissionError` before its broader failure branches and returns the exact `403 forbidden` problem object through `no_store_problem_response(...)`.
- **Observed GREEN:** Re-ran `env -u PYTHONPATH uv run pytest tests/integration/api/test_staff_employer_reads.py::test_denied_search_precedes_cursor_and_sql_and_headers_cannot_elevate -v` after sourcing `.env.test`; result was `1 passed, 1 warning`. The test confirmed denied search returned the safe `403` object with `Cache-Control: no-store`, forged authority headers did not elevate access, the cursor-decode probe remained untouched, and the SQL probe observed zero statements.
- **Scope check:** This cycle added only search-route-local `403` mapping for denied reads so the search route no longer masks authorization failures as `500`; no new grant path, cursor behavior, or SQL behavior was introduced.

## 2026-08-05 — Task 5 regression 4 reclassified as GREEN regression
- **Observed result:** After extending `tests/integration/api/test_staff_employer_reads.py::test_detail_and_search_leave_authoritative_row_counts_unchanged`, `env -u PYTHONPATH uv run pytest tests/integration/api/test_staff_employer_reads.py::test_detail_and_search_leave_authoritative_row_counts_unchanged -v` passed immediately with `1 passed, 1 warning` after sourcing `.env.test`.
- **Interpretation:** The planned RED did not materialize because the existing detail/search HTTP routes already delegate to SELECT-only application queries. After seeding two fictional employers through the authoritative POST command, one detail GET and one search POST left `employers`, `command_receipts`, and `audit_events` row counts unchanged.
- **Scope check:** Reclassified as a GREEN regression rather than fabricating a failure; no production change was required.

## 2026-08-05 — Task 5 regression 5 reclassified as GREEN regression
- **Observed result:** After extending `tests/integration/api/test_staff_employer_reads.py::test_openapi_exposes_only_approved_staff_employer_routes`, `env -u PYTHONPATH uv run pytest tests/integration/api/test_staff_employer_reads.py::test_openapi_exposes_only_approved_staff_employer_routes -v` passed immediately with `1 passed, 1 warning` after sourcing `.env.test`.
- **Interpretation:** The planned RED did not materialize because the current OpenAPI surface is already limited to the approved staff-employer routes: `POST /api/staff/v1/employers`, `POST /api/staff/v1/employers/search`, and `GET /api/staff/v1/employers/{employer_id}`. No list-all, export, or public employer route appeared.
- **Scope check:** Reclassified as a GREEN regression rather than fabricating a failure; no production change was required.

## 2026-08-05 — Task 5 regression 6 reclassified as GREEN regression
- **Observed result:** After extending `tests/integration/api/test_staff_employer_reads.py::test_search_logs_do_not_include_body_cursor_filter_sql_url_actor_or_exception`, `env -u PYTHONPATH uv run pytest tests/integration/api/test_staff_employer_reads.py::test_search_logs_do_not_include_body_cursor_filter_sql_url_actor_or_exception -v` passed immediately with `1 passed, 1 warning` after sourcing `.env.test`.
- **Interpretation:** The planned RED did not materialize because the search path still emits no reflective logging. Even when the route-level `search_employers` import was monkeypatched to raise a runtime error containing synthetic filter/SQL/URL/actor/exception markers, the response stayed the safe `500` problem object with `Cache-Control: no-store` and `caplog` captured none of the submitted markers from the body, cursor, header, or exception text.
- **Scope check:** Reclassified as a GREEN regression rather than fabricating a failure; no production change was required.

## 2026-08-05 — Task 5 preservation regression 1 reclassified as GREEN regression
- **Observed result:** Re-ran `env -u PYTHONPATH uv run pytest tests/integration/api/test_staff_employers.py::test_post_staff_employers_returns_201_and_exact_body_for_permitted_request -v` after the read-route additions; result was `1 passed, 1 warning` after sourcing `.env.test`.
- **Interpretation:** The create route's core success contract remained stable. `POST /api/staff/v1/employers` still returned `201` with the exact draft-employer body and no retrieval `Location` header despite the added search/detail routes and route-local no-store problem handling.
- **Scope check:** Reclassified as a GREEN preservation regression; no production change was required.

## 2026-08-05 — Task 5 preservation regression 2 RED observed
- **Observed RED:** Re-ran `env -u PYTHONPATH uv run pytest tests/integration/api/test_staff_employers.py::test_openapi_exposes_only_intended_staff_route -v` after the read-route additions and the node failed because the legacy preservation assertion still expected `"/api/staff/v1/employers/{employer_id}" not in paths`.
- **Interpretation:** This was a test-surface drift failure, not a product defect: the create-route preservation assertion had not been updated to reflect the now-approved expanded OpenAPI surface that legitimately includes `POST /search` and `GET /{employer_id}`.
- **Minimal GREEN checkpoint:** Update only the preservation OpenAPI assertion so it preserves the create route while asserting the exact approved three-route staff-employer surface and methods.

## 2026-08-05 — Task 5 preservation regression 2 GREEN observed
- **Implemented checkpoint:** Updated `tests/integration/api/test_staff_employers.py::test_openapi_exposes_only_intended_staff_route` to assert the exact approved staff-employer OpenAPI path set and per-path methods: `POST /api/staff/v1/employers`, `POST /api/staff/v1/employers/search`, and `GET /api/staff/v1/employers/{employer_id}`.
- **Observed GREEN:** Re-ran `env -u PYTHONPATH uv run pytest tests/integration/api/test_staff_employers.py::test_openapi_exposes_only_intended_staff_route -v` after sourcing `.env.test`; result was `1 passed, 1 warning`.
- **Scope check:** This cycle updated only the preservation assertion to match the approved expanded route surface; no production code changed.

## 2026-08-05 — Task 5 focused API regression pass passed
- **Observed result:** Ran `env -u PYTHONPATH uv run pytest tests/integration/api/test_staff_employer_reads.py tests/integration/api/test_staff_employers.py -v` after sourcing `.env.test`. Result: `24 passed, 1 warning in 1.23s`.
- **Coverage of the pass:** The focused API pass included all read-route regressions in `test_staff_employer_reads.py` plus the preserved create-route/API assertions in `test_staff_employers.py`, including exact create-body behavior, idempotency handling, denied/header non-escalation, safe 400/403/409/422/503/500 mappings, approved OpenAPI surface, read-route no-write invariants, and search log-hygiene checks.
- **Warning note:** The only warning remained the existing upstream `StarletteDeprecationWarning` from `fastapi.testclient`; no slice-local warnings or failures appeared.

## 2026-08-05 — Task 6 quality/security verification pass
- **Runtime prerequisite:** `docker compose --env-file .env.test ps postgres-test` confirmed the synthetic PostgreSQL service was still `Up` and `healthy` on loopback `127.0.0.1:55432` before the gate run.
- **Observed first gate failure:** The first workflow-order pass stopped at `uv run ruff format --check .` because six files required formatting. After `uv run ruff format .`, the next pass stopped at `uv run ruff check .` with eight import-order findings auto-fixable by Ruff; `uv run ruff check . --fix` resolved them.
- **Observed second gate failure:** The next pass stopped at `uv run mypy src tests` with three stale imports still referencing `SafePersistenceError` from `golden_rose.application.create_draft_employer`. The fix was limited to import sites in `src/golden_rose/api/errors.py`, `tests/integration/application/test_create_draft_employer.py`, and `tests/integration/api/test_staff_employers.py`, switching them to the shared `golden_rose.application.errors` module already introduced by this slice.
- **Observed green gate sequence:** After those narrow fixes, the workflow-order pass completed successfully: Ruff format/check, mypy, Bandit, `alembic upgrade head`, full pytest with coverage, `alembic downgrade base`, `alembic upgrade head`, `pip-audit --skip-editable`, and CycloneDX SBOM generation.
- **Verification evidence:** `pytest --cov=golden_rose --cov-report=term-missing --cov-fail-under=95` reported `97 passed, 1 warning in 3.45s` with total coverage `96.67%`; the only warning remained the upstream `StarletteDeprecationWarning` from `fastapi.testclient`. `pip-audit --skip-editable` reported no known vulnerabilities. Local SBOM validation showed `build/backend-sbom.cdx.json` exists with `bomFormat='CycloneDX'` and `specVersion='1.6'`.
- **Range/hygiene evidence:** `git diff --check origin/develop...HEAD` passed with no output. `git diff --name-status origin/develop...HEAD` also produced no committed range delta, and `git rev-list --count origin/develop..HEAD` returned `0`, confirming the branch still has uncommitted working-tree changes rather than ahead commits. Exact-range Gitleaks over `origin/develop..HEAD` scanned `0 commits` / `0 bytes` and reported no leaks. `git status --short` still shows the active uncommitted slice surface. Content searches found no `SELECT *` usage and no Python `logging`/`logger` calls under `src/` for this slice.

## 2026-08-05 — Task 7 review handoff packet created
- **Artifact created:** Added `docs/review-handoffs/2026-08-05-phase-1-employer-read-search-review-handoff.md` for the independent code review/security review session that must inspect the local branch before any PR to `develop` is opened.
- **Recorded posture:** The packet states the review surface is the uncommitted `feat/staff-employer-read-search` working tree against merged planning base `bde9143`, with `git rev-list --count origin/develop..HEAD = 0`, so the reviewer must inspect the local diff rather than a pushed commit range.
- **Evidence summarized:** The handoff captures the approved scope/non-scope, key implementation paths, focused Task 5 regression result (`24 passed, 1 warning`), Task 6 verification result (`97 passed, 1 warning`, `96.67%` coverage, no known vulnerabilities, CycloneDX SBOM), range-hygiene caveat, and the exact High/Blocker stop boundary before PR opening.
- **Living-doc rebaseline:** `CURRENT_WORK.md` and `ROADMAP.md` now point to independent review/handoff as the immediate next step instead of ongoing RED → GREEN implementation.

## 2026-08-05 — Task 8 review-remediation pass for employer read/search tracer
- **Review verdict received:** Independent review returned **Changes requested / not PR-ready yet** on the uncommitted `feat/staff-employer-read-search` working tree, citing two High blockers and two Medium drifts. The actionable issues were: missing create-path NFC normalization before idempotency fingerprinting/insertion; missing `Cache-Control: no-store` on several detail-route problem responses; generic detail 404 problem type; and incomplete read-side data minimization behind the application boundary.
- **Implementation remediation applied:** `src/golden_rose/application/create_draft_employer.py` now normalizes `display_name` via `normalize_employer_text(...)` before fingerprinting and insert, while replay now reloads the authoritative create record through a new `get_authoritative_employer_by_id(...)`. `src/golden_rose/api/errors.py` now makes the installed `400/403/409/422/500/503` problem handlers emit `no_store_problem_response(...)`. `src/golden_rose/api/staff/employers.py` now returns the employer-specific 404 type `https://golden-rose.local/problems/employer-not-found`. `src/golden_rose/persistence/employers.py`, `src/golden_rose/application/get_employer.py`, and `src/golden_rose/application/search_employers.py` now separate authoritative create records from minimized read-side detail/search records so `created_by` and other extra create-only fields do not ride the read path.
- **New regression coverage:** Added/updated focused checks proving NFC normalization and composed/decomposed replay equivalence in `tests/integration/application/test_create_draft_employer.py`; proving minimized read-side shapes in `tests/integration/application/test_get_employer.py` and `tests/integration/application/test_search_employers.py`; and proving detail-route 403/404/422/503 responses all remain safe/no-store with the employer-specific 404 type in `tests/integration/api/test_staff_employer_reads.py`.
- **Focused remediation verification:** Ran exact rereview nodes for the reported findings and their blast radius: `uv run pytest` over 7 targeted nodes covering create normalization/replay, minimized detail/search shapes, absent/denied detail, and detail validation/safe-persistence mapping. Observed result: `7 passed, 1 warning in 0.68s` with only the pre-existing upstream `StarletteDeprecationWarning` from `fastapi.testclient`.
- **Broader rereview subset:** Ran `uv run ruff check` over the touched source/test files, `uv run mypy src tests`, and `uv run pytest tests/integration/application/test_create_draft_employer.py tests/integration/application/test_get_employer.py tests/integration/application/test_search_employers.py tests/integration/api/test_staff_employer_reads.py -v`. Observed results: Ruff clean, mypy clean (`Success: no issues found in 44 source files`), and targeted rereview suite `32 passed, 1 warning in 1.08s`.
- **Continuity/handoff update:** Refreshed `docs/review-handoffs/2026-08-05-phase-1-employer-read-search-review-handoff.md`, `CURRENT_WORK.md`, and `ROADMAP.md` so the next independent review session sees the reported blockers, exact remediations, green rereview evidence, and the unchanged stop boundary: no PR to `develop` until rereview clears the local working tree.

## 2026-08-06 — Independent rereview cleared; branch committed, pushed, and PR opened
- **Independent rereview result:** A separate rereview pass confirmed the reported High/Medium findings were closed. Fresh reruns of the 7 targeted rereview nodes passed with `7 passed, 1 warning`, and live detail-route probes confirmed denied/invalid-UUID/safe-persistence detail paths now all return safe no-store problem responses.
- **Commit/closeout:** Committed the remediated slice on `feat/staff-employer-read-search` as `2994a5c` (`feat: implement employer detail and bounded search tracer`).
- **Final-head verification on the committed range:** `git diff --check origin/develop...HEAD` passed clean; exact-range Gitleaks on `origin/develop..HEAD` scanned `1 commit` / about `152620 bytes` with no leaks; focused `uv run ruff check ...` passed; `uv run mypy src tests` passed; and `uv run pytest tests/integration/application/test_create_draft_employer.py tests/integration/application/test_get_employer.py tests/integration/application/test_search_employers.py tests/integration/api/test_staff_employer_reads.py -v` passed with `32 passed, 1 warning in 1.11s`.
- **Push/PR status:** Pushed `feat/staff-employer-read-search` to `origin` and opened PR #11 to protected `develop`: `https://github.com/b-mackenzie-alexander/golden_rose_project/pull/11`.
- **Current boundary:** PR #11 is limited to the approved ADR-0004 read/search tracer plus the review-remediation fixes and evidence updates. CI/review follow-up, if any, must stay in this slice and preserve the verified no-scope-expansion posture.

## Updating this file
Add a short dated entry after a material planning, implementation, test, security, or release event. Link detailed evidence rather than duplicating it. Record commands and results only when they were actually run.
