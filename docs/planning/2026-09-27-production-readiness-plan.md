# Production-readiness and staff identity plan — 2026-09-27

## Delivery position

- **Staffing:** One independent developer; automated checks, fresh agent review and protected PR gates provide quality evidence, not independent-human authorization.
- **Human-visible outcome:** Demo day is complete. PR #116 merged the PR #115 deployment closeout into protected `develop` at `4d4a0dc8c726efee8b9f5db1aa2b8b701b04d6da`; PR #117 merged the Worker/Employer `New intake` visibility repair into protected `develop` at `9c9a09d2c5ffb9128a28195a333f7f208d98bca6`. The private fictional-synthetic develop service has workflow evidence through PR #115, but no fresh runtime readback occurred in this planning branch.
- **Gate budget:** This is a docs-only production-readiness plan. It authorizes no source implementation, cloud mutation, production deployment, live/client data, new identity provider activation, persistent synthetic writes, credential rotation, billing transfer or default permission activation.
- **Next executable action after this docs PR merges:** Fetch the merged protected `origin/develop`, create a fresh implementation branch from that exact tip, and begin the staff identity/account lifecycle tranche. Do not start production implementation from this docs branch.
- **Do not regress:** Human staff decision boundaries; no automatic matching/ranking/eligibility/referral/placement; private fictional-synthetic data limits until live-data gates are explicitly opened; immutable intake history and exact retries; restricted-address and field permissions; bilingual/accessibility parity; separate public/staff identity planes; deployable-package portability for the client's later GCP environment.

## Objective

Move Golden Rose from a successful private demo surface toward a deployable package the client can later run in her own GCP environment. The immediate production blocker is staff identity and personal staff accounts. The broader goal is a package with clear environment separation, portable infrastructure/runbooks, accountable staff access, authoritative dashboard data, operational support evidence and truthful production gates.

This plan intentionally separates:

- **Source readiness:** code, tests, docs and runbooks merged into `develop`.
- **Deployable package readiness:** a repository and operator procedure that can be configured for the client's GCP project without hidden Beatrice-only assumptions.
- **Production activation:** an explicit later approval to deploy with live data, real staff accounts, production secrets and client-owned support paths.

## Current assessment

### Strong foundations

- Staff intake, review, finalization, canonical corrections and current-facts review are implemented in source and protected by existing command, receipt, audit, field-permission and retry contracts.
- The dashboard shell, search/queue routing, intake cards, seeded fictional presentation data and recent `New intake` repair are in place for staff review.
- The private fictional-synthetic develop target has prior service-only deployment evidence, signed-image verification and read-only smoke evidence through the PR #115 rollout.
- The repository already contains accepted policy contracts for staff permission roles, MFA/recovery/support ownership, correction/audit behavior, request/shift state, queues, calendar semantics, service zones and NYC map boundaries.

### Production blockers

1. **Real staff identity is absent.** `Settings.auth_mode` is still synthetic-only, staff principals are injected from configuration, and `StaffDirectory` is a trusted local/test helper rather than a production account system.
2. **Personal account lifecycle is not implemented.** There is no durable staff account table, invitation/activation flow, MFA enrollment enforcement, suspension/deprovisioning, recovery workflow, access review record, session revocation model or role/delegation administration workflow.
3. **The dashboard is not fully authoritative.** Some cards and links derive from current draft-intake summaries, but request/shift demand, calendar coverage, map/reporting aggregates and queue aging still need backend records and explicit permissions.
4. **The deployable GCP package needs portability hardening.** Source and runbooks must distinguish client-owned production variables from the historical private develop project, avoid embedded private IDs/secrets, document bootstrap order, and prove the exact artifact can be rebuilt/admitted outside Beatrice's project.
5. **Production operations are not qualified.** Backup/restore, monitoring/alert ownership, incident/support handoff, log retention, dependency/action lifecycle, cost guardrails, release rollback/forward-recovery and break-glass procedures need implementation evidence.
6. **Live-data and human acceptance gates remain open.** Manual accessibility, fluent Spanish review, staff workflow acceptance, legal/business copy, data classification, retention/export/disclosure rules and initial staff training are not complete.

## Implementation sequence

### Tranche 1 — Staff identity and account lifecycle

Implement the minimum production-capable staff identity foundation before further dashboard production work. This tranche should be its own source PR series after this docs PR merges.

Required outcomes:

- Add a provider-neutral staff authentication boundary that can validate a real identity provider token/session for production while preserving local/test synthetic principals for development and automated tests.
- Introduce durable staff account records with immutable actor identity, display name, active/suspended state, provider subject binding, role assignments, named permission grants, optional record/field scopes and audit-safe metadata.
- Implement account activation, suspension, reactivation and deprovisioning commands. Historical actor attribution must remain stable after deprovisioning.
- Implement role/delegation grant and revoke commands aligned to `phase-1-staff-permission-matrix.md`. Role labels alone must not grant authority.
- Implement MFA/readiness enforcement at the application boundary using provider claims or an approved provider-specific adapter. Production access must fail closed when MFA/session requirements are not met.
- Implement assisted recovery and session-revocation evidence at the application contract level, even if the first provider adapter delegates factor reset mechanics to the identity provider.
- Update `get_staff_principal` and `get_staff_directory` so production never creates a synthetic operational principal and local/test fixtures cannot leak into production settings.
- Add unit and integration tests for valid staff login, missing/invalid provider subject, missing MFA, suspended user, removed permission, expired delegation, self-escalation denial, Platform Administrator operational-data denial, account recovery evidence and session revocation hooks.
- Add frontend states for sign-in failure, suspended/unavailable account, insufficient permission and safe sign-out without exposing restricted operational data.

Non-goals for tranche 1:

- No public worker/employer identity.
- No live data.
- No production deployment.
- No automatic role import from cloud IAM or identity-provider groups unless separately approved.
- No broad admin bypass for Platform Administrator.

Exit criteria:

- Production configuration can no longer start with synthetic staff auth.
- A named staff actor is required for every staff API command/read in production mode.
- Account, role, delegation, recovery and deprovisioning actions create safe attributable evidence.
- Existing intake/dashboard flows still pass with test/local principals.
- The next source branch starts from the protected merge commit of this docs PR, not from historical demo branches.

### Tranche 2 — Deployable GCP package portability

Harden the repository so the client can later deploy into her own GCP environment without reverse-engineering Beatrice's private develop setup.

Required outcomes:

- Produce an operator runbook that starts from an empty or client-owned GCP project and names every prerequisite: billing, APIs, service accounts, Workload Identity Federation, Artifact Registry, Cloud SQL, Cloud Run, Secret Manager, state backend and required human approvals.
- Split private develop defaults from production/client variables. Private project IDs, principals, billing IDs, service URLs, passwords and secret payloads stay out of source-controlled docs.
- Add example configuration templates using placeholders only.
- Verify Terraform plans fail closed on deletes/replacements, public SQL exposure, broad IAM, missing immutable image digest, missing staff identity configuration, demo-access configuration in production, and unqualified secrets.
- Preserve the existing signed image/SBOM/provenance admission path and document how the client-owned environment consumes the admitted artifact.
- Define handoff artifacts: build digest, migration revision, database-authority receipt, smoke evidence, rollback/forward-recovery notes and owner acceptance checklist.

Exit criteria:

- A qualified operator can identify all required inputs without private chat/Obsidian material.
- The package can be reviewed without exposing credentials or private URLs.
- The plan distinguishes "deployable package" from "production activated with live data."

### Tranche 3 — Authoritative dashboard operations

Move dashboard modules from demo-safe staff surface toward operational truth.

Required outcomes:

- Implement governed `StaffingRequest` to `ShiftNeed` progression so finalized employer intake can become reviewable demand only through explicit staff action.
- Implement request/shift lifecycle transitions from the accepted request/shift state model with expected versions, permissions and audit evidence.
- Derive work queues from authoritative request, shift, review, follow-up and ownership records; no hardcoded queue rows or separate editable queue status.
- Derive calendar and coverage views from authoritative timed shifts and milestones; personal browser-local calendar notes remain visibly separate or are removed from production surfaces.
- Keep map/reporting aggregates broad and authorized. Exact address stays restricted and never becomes a proximity, ranking, referral or eligibility signal.
- Add visible staleness/failure states for dashboard projections instead of false zeros.

Exit criteria:

- Dashboard counts, queues, links and calendar items can be traced to source records and permissions.
- Static demo fallbacks are absent from production mode.
- No workflow performs automatic matching, ranking, assignment, referral, placement or eligibility decisions.

### Tranche 4 — Production operations, data and support readiness

Close operational gates required before live use.

Required outcomes:

- Backup and restore rehearsal evidence for the production-shaped database.
- Monitoring, alerting, log-retention and incident-routing configuration with named client owners.
- Dependency/action runtime lifecycle review, including GitHub Actions runner/image deprecation tracking.
- Production data classification, retention/deletion/export/disclosure rules and restricted-history recipients.
- Legal/business-controlled copy inventory and approval workflow.
- Manual accessibility, keyboard, screen-reader and fluent Spanish review on the production candidate.
- Staff training, support escalation and acceptance checklist.

Exit criteria:

- The client has named operational owners and successor technical contacts.
- Recovery and deprovisioning procedures are rehearsed.
- Live-data admission can be considered as a separate explicit approval with evidence, not as a side effect of source merge.

## Documentation and PR rules

This plan is its own docs PR. It must not include product code, migrations, Terraform applies, cloud inspection/mutation or credentials.

After this docs PR merges:

1. Fetch and verify current `origin/develop`.
2. Create a fresh implementation branch from the exact protected tip.
3. Start tranche 1 only.
4. Keep each implementation PR reviewable and independently qualified.
5. Update `CURRENT_WORK.md`, `ROADMAP.md`, `NOTES.md`, `SECURITY.md` and `TECHNICAL_REQUIREMENTS.md` after material implementation milestones.

Return to planning before any material change to identity provider choice, production cloud authority, live-data admission, public identity, uploads/documents, payment, messaging, exports, geocoding provider, automated matching/comparison logic or destructive recovery/state editing.

## Verification for this docs PR

Required before publishing:

- `git diff --check`
- Redacted secret scan over the docs-only outgoing range
- PR readback confirming the base is `develop`, the head is the docs branch and required checks are reported truthfully

No runtime, browser, database, Cloud Run or production qualification is claimed by this plan.
