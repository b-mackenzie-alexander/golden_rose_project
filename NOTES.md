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

## 2026-08-03 — NYC job-demand map accepted
- **Required capability:** Phase 1 includes an authorized-staff NYC map. Official DCP 2020 Community District Tabulation Areas are pinned/checksummed base cells; the Owner groups cells into adaptive zones. Boroughs provide context only.
- **Derivation boundary:** Worksite addresses are geocoded server-side through a provider-neutral interface, then classified locally into the pinned CDTA geometry. Exact coordinates are transient/discarded by default; ambiguous/failed/outside results remain visible for Owner correction. A live provider remains separately gated.
- **Measures:** The map exposes named open-request, upcoming-shift, requested-worker, confirmed-coverage, remaining-gap, and classification-exception measures with accessible list parity—never an opaque heat/match score.
- **Worker boundary:** Phase 1 maps job demand only. Worker supply follows an approved worker-location/availability/privacy/suppression contract; geographic overlap does not establish suitability, referral, assignment, or commute feasibility.
- **Source of truth:** `docs/planning/phase-1-nyc-job-demand-map-contract.md`.

## 2026-08-03 — Staff permission matrix accepted
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

## Updating this file
Add a short dated entry after a material planning, implementation, test, security, or release event. Link detailed evidence rather than duplicating it. Record commands and results only when they were actually run.
