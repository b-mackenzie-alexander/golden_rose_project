# Technical Requirements — Golden Rose Operations Platform

## 2026-09-29 — Client-owned package policy manifest guard

The active Tranche 2 portability slice extends the deployable package source guard with `deploy/gcp/templates/client-production-policy.example.json`. The manifest is a placeholder-only review contract for a later approved production packet. It records separate-approval boundaries for cloud execution, Terraform plan, production deployment, live-data admission and provider-side identity activation; production app posture requiring staff OIDC; forbidden production demo/synthetic posture; plan-review fail-closed checks for delete/replace, public SQL, broad IAM, immutable digest, staff identity, secret payloads and operational owner evidence; and value-safe artifact/handoff evidence placeholders.

`scripts/validate_deployable_package.py` now requires the policy manifest alongside the existing runbook, app configuration template and client-owned input inventory. It rejects synthetic/develop/demo policy drift, missing fail-closed plan checks, missing owner/artifact evidence placeholders and concrete package values. This remains local static validation only; it does not replace future Terraform plan validation, image admission verification, migration qualification, backup/restore rehearsal, staff acceptance or live-data approval.

## 2026-09-29 — Client-owned deployable package source guard

The active Tranche 2 portability slice adds source-controlled, placeholder-only package artifacts for a later client-owned GCP environment: `deploy/gcp/client-owned-production-package-runbook.md`, `deploy/gcp/templates/client-production.env.example`, and `deploy/gcp/templates/client-owned-gcp-inputs.example.json`. These artifacts are technical input inventories and stop-condition guides, not executable Terraform variables, plans, cloud credentials, runtime secrets, or production deployment authority.

`scripts/validate_deployable_package.py` is the local static gate for these package artifacts. It requires production app posture to use `GOLDEN_ROSE_ENVIRONMENT=production` and `GOLDEN_ROSE_AUTH_MODE=staff_oidc`, keeps synthetic staff IDs/demo access/presentation seed disabled or unset, requires OIDC/database values to remain placeholders, requires client-owned GCP identity/state/artifact/secret/operations owners, and rejects concrete URLs and known private develop/demo fragments. This gate does not replace future Terraform plan validation, image admission, migration qualification, backup/restore rehearsal, staff acceptance or live-data approval.

## 2026-09-16 — Current develop stakeholder-review surface

PR #108 is merged at protected `develop@dd6697871986fa5677e722b2805a21a8a7776b64` and deployed to the existing private fictional-synthetic `develop` service for stakeholder review. The current service includes the PR #107 dashboard shell/artwork plus PR #108's Activity by area NYC map, static calendar module and static work queues module. This updates the human-visible review surface, but it does not complete the authoritative backend contracts for map/calendar/queues/search and does not admit live/client data, production promotion, new access model, credential rotation or default permission activation.

Near-term product feedback should focus on whether the dashboard helps stakeholders reason about staff work despite the static modules. Implementation follow-up still needs governed backend wiring from authoritative records for map areas, calendar coverage, work queues and dashboard search, with the existing authorization, exact-address, location-privacy, audit, and non-automation constraints preserved.

## 2026-09-15 — PR D canonical correction source candidate

PR #104 merged PR C at `develop@50f2ac86621329f12680e706bd8d224e76833c22`. PR D proceeds on `feat/staff-intake-corrections` under accepted ADR-0017. The source adds nine explicit section correction commands with current field permissions, expected versions, required reasons, immutable retries, same-target correction references, and protected before/after evidence. Separate current-facts review binds the original output identities/dispositions to current row versions; original intake reviews and finalizations remain immutable.

Migrations `0009_canonical_corrections` and `0009a_canonical_reviews` retain applied predecessors, narrow runtime column grants, invoker-only guards, exact typed receipt/result/audit authority and downgrade refusal with protected history. Current-purpose address and structured schedule/availability checks apply in both application and SQL authority. Browser buffers retain later edits and exact unknown retries, serialize shared-row commands, and block router history traversal while unresolved; the router's optional transition cache uses inert storage. No default permission activation, cloud inspection/mutation, deployment, live/client data or production authority follows. See [the intake contract](docs/planning/staff-intake-contract.md) and [the PR D handoff](docs/review-handoffs/2026-09-15-staff-intake-pr-d-handoff.md) for qualification and publication status.


## 2026-09-14 — PR B source implementation

PR #102 merged durable intake drafts at `develop@2783415dd19027428bf2036730b6c0d83f23ab3c`. The owner completed the bounded local browser-verification step and authorized PR B on `feat/staff-intake-review`. Review/follow-up, protected history and governed bilingual work interests are now implemented in the source candidate. Fresh specification/quality and final integration reviews approved source publication; local qualification passed 1,253 backend tests (95.64% coverage) and 202 frontend tests. Required CI and protected merge remain; this is not deployed functionality. The browser evidence remains separately preserved in `ee82615` on `test/staff-intake-browser-ux`, and the requested minor-polish note is reserved for the next docs PR.

Migration `0007_intake_review_follow_up` extends exact receipt/result/audit authority and append-only protected payloads. Review binds the saved content/catalog versions; follow-up changes aggregate version without changing reviewed facts. Owner choices come only from an injected trusted directory; no user administration or develop permission grant is introduced. Contract §6 clarifies the bounded owner query and structured protected follow-up context. PR C linking/finalization and PR D corrections remain later work under the accepted plan. No cloud inspection/mutation, deployment, live/client data or production authority follows. The historical v28 packet remains consumed and its formal status remains `not_qualified`.

See the [PR B handoff](docs/review-handoffs/2026-09-14-staff-intake-pr-b-handoff.md) for the current evidence and next action. Older PR A-only and planning-only activation statements below are historical.

## 2026-09-14 — PR A source activation

PR #100 merged this intake planning contract at `ce38fb0`; PR #101 merged the Wave 1 UX predecessor at `9a6b66735f7261ca705f7e8ba5b7c2afcd815f92`. The owner subsequently authorized PR A implementation and disposable local PostgreSQL tests. The active branch is `feat/staff-intake-drafts` from that exact integration tip. Older docs-only/unmerged-predecessor statements below describe the planning snapshot and are superseded for this source lane. Browser UX verification is deferred until PR A is finished at the owner's request.

PR A adds only durable candidate drafts, separately authorized address sections, bounded shared recovery and typed atomic receipt/result/audit authority. Review/follow-up, links, canonical finalization and corrections remain PRs B–D. The v28 runtime is historical and remains `not_qualified`; no deployment, cloud inspection/mutation, live data or production is authorized or claimed.


**Status:** Documentation-only staff-intake planning. The new contract is proposed implementation scope, not implemented or deployed. Preserve and merge the improved-UI predecessor before coding; docs-only publication is independent, and both planning and UI merges gate coding. V28 remains historical evidence with last recorded status `not_qualified`; no live check occurred in this audit.

## 2026-09-14 — Staff intake planning boundary

Accepted conversational direction is durable shared worker/employer intake with explicit save/resume, version-bound review and follow-up, restricted addresses, deliberate existing-party links without overwrite, and atomic finalization only after complete current review. Technical details remain proposed source contracts, not deployed functionality or new client/counsel policy. See [Staff intake contract](docs/planning/staff-intake-contract.md), [outcome-scale plan](.hermes/plans/2026-09-14-staff-intake-workflows-plan.md), and proposed [ADR-0017](docs/adr/ADR-0017-staff-intake-workflows.md).

The improved Wave 1 UI is the preserved uncommitted predecessor in `/Users/genie/Desktop/golden_rose_project` on `feat/staff-intake-workflows`; do not reset, stash, copy over, or mix it into this docs-only planning worktree. Complete and merge that predecessor and the accepted planning packet before intake coding. V28 deployment/browser evidence is historical and its packet consumed; this audit did not recheck runtime availability or access expiry. The last recorded formal status remains `not_qualified`. No cloud, live-data, public-plane, implementation, or service-start authority is granted here.

## Product outcome
Provide agency staff a reliable browser-based operations workspace that replaces fragmented paper/form/spreadsheet employer-demand handling, supports governed operational reporting, and later supports transparent staff review of worker-to-employer/job compatibility.

## Priority delivery scope
### First release: agency-staff employer demand
- Authorized staff can create, view, correct, and find employers, employer contacts, worksites, staffing requests, and one or more shift needs.
- The system provides an authorized demand work queue/search, rather than separate monthly files or manual row tracking. `docs/planning/phase-1-work-queue-aging-follow-up-model.md` controls separate record/review/follow-up/coverage clocks, shared accountable ownership, provisional triggers, and deterministic queue lanes. Client validation is required before provisional thresholds become production policy.
- The system provides an authorization-scoped calendar derived from distinct request milestones and timed shift occurrences under `docs/planning/phase-1-calendar-coverage-semantics.md`; it must not become a separate manual calendar store. Worker assignments/availability remain future authorities.
- The system records who performed material actions and preserves attributable history/corrections under `docs/planning/phase-1-correction-audit-event-contract.md`; current domain rows and append-only material history remain distinct authorities.
- The system supports household and general-labor request details as governed extensions of one canonical workflow.

### Follow-on release: dashboard and comparison aid
- Agency-only dashboard derives approved KPIs from authoritative workflow records; staff do not re-enter information solely to create metrics.
- Charts and aggregate service-area demand/coverage visualizations may be included only after KPI definition, calculation, audience, aggregation/redaction, refresh, export, and location-privacy rules are approved. The client-accepted Phase 1 authorized-staff job-demand map is not optional; optional follow-on mapping refers to worker-supply, comparison, or additional dashboard layers, all of which require separate contracts.
- Comparison aid exposes only approved, job-relevant, explainable signals and missing information for staff review.
- The aid must not rank people, make eligibility/hiring/referral decisions, or use unapproved protected-trait/proxy fields.

### Near-term exception: staff-operated worker/employer intake
- Ordered PRs A–D include bounded canonical correction and current-facts re-review under contract §9, not a post-finalization correction deferral. Correct worker phone/residence/preferences/availability, current employer contact/address, worksite and request descriptions with reason/version/permission/audit/retry controls; immutable original intake/review/output links are never overwritten.
- Save controls are section-local with immutable command keys, independent status and preserved dirty buffers. Aggregate saved is forbidden while another section is dirty/pending/failed/unknown; exact success-then-unknown-and-later-edits integration/browser tests are required.
- `docs/planning/staff-intake-contract.md` defines shared partial drafts, explicit save/resume, validation of supplied values without invented names/contact data, version-bound review, accountable due-instant follow-up, and explicit linking/finalization.
- Save, completeness, current review, and finalization are distinct states. The same authorized staff member may review and finalize; permissions remain separate.
- Review/finalize require complete current facts and restricted-field access. Finalization creates the exact canonical outputs atomically and does not open demand or create ShiftNeed, worker assignment, referral, placement, or agreed pay.
- This is a bounded exception to worker-profile deferral and predecessor-only backend exclusions; the broader worker/public release remains deferred.

### Follow-on release: broader worker profile
- Worker records use staged, inclusive, bilingual onboarding and explicit agency review.
- Self-reported skills/preferences remain unverified unless a separately governed verification procedure establishes otherwise.
- Employer visibility and referral content are controlled and snapshot-capable.

## Functional requirements
- Web UI works on constrained office hardware and common modern browsers. Future worker/employer public workflows must be mobile-first, resilient to constrained networks, and measured against an approved responsiveness/performance budget before release.
- English/Spanish functional and accessibility parity across all affected flows, validation/errors, notices, notification paths, documents, and staff interfaces.
- Staff search honors record/field authorization before showing results.
- The implemented Employer read/search slice uses one server-enforced `employer:read` permission before exact lookup, filtered query, or pagination. Potentially household-identifying name fragments use a validated POST body rather than URL query parameters, remain excluded from logs, and are matched literally with bounded deterministic keyset pagination. It adds no unfiltered list, total count, export, ranking, read-side audit event, schema/index, or separate search store; ADR-0004 controls the exact contract.
- The accepted first-frontend boundary uses one `/employers` route and the existing Employer create/search/detail status/body/schema/authority contracts after one prerequisite test-first `Cache-Control: no-store` header is added to fresh and replayed create successes. Employer names/types, search values, cursors, command IDs, and problems stay out of browser navigation URLs, browser persistence, logs, analytics, and third-party runtime calls; the selected UUID appears only in the required detail API path. English/Spanish parity, accessibility, idempotent unknown-outcome retry, frontend quality/audit/SBOM gates, and synthetic/local-only use are mandatory; ADR-0005 controls the exact boundary and PR #13 merged the first implementation.
- ADR-0006 deferred human browser/manual accessibility/fluent-language qualification until a shared deployed `develop` target existed. ADR-0007's revision and PR #18 remediation remain implemented; PR #69 later merged the bounded delayed receipt-visibility race remediation. PR #20 merged ADR-0008's backend-only EmployerContact create/query/exact-read and typed authority generalization. PR #22 merged ADR-0009 Slice B's local runtime/container contract; later ADR-0013 source/operator work and v28 completed state establishment, ownership alignment, exact foundation apply, immutable publication, Secret versions, private database authority, migration, service activation, automated qualification, and browser handoff. The browser exposed a production Spanish-toggle defect and incomplete manual accessibility/fluent-language evidence. Real identity, live data, and production remain separate.
- Staff authorization uses the server-enforced permission matrix in `docs/planning/phase-1-staff-permission-matrix.md`. Accepted roles are Owner, delegated Manager, interchangeable Operations Staff, and separately bounded Platform Administrator; role labels do not grant broad data access by themselves.
- Dates/times are stored once with time zone where relevant; calendar/month views are derived, not separate storage silos.
- Routine operational/reporting location uses the adaptive Owner-managed taxonomy in `docs/planning/phase-1-service-zone-taxonomy.md`: worksites may have overlapping memberships with one primary/default, while requests/shifts may be assigned later and remain visibly unassigned until then. Exact names/conventions are configuration discovered through use, not implementation prerequisites. Exact worksite/household address remains separately restricted.
- Phase 1 includes the authorized-staff NYC demand map defined by `docs/planning/phase-1-nyc-job-demand-map-contract.md`. It pins official DCP 2020 CDTAs, derives worksite CDTA server-side through a provider-neutral geocoder boundary, discards precise coordinates by default, and shows named request/shift/coverage measures with a synchronized accessible table. Worker supply is deferred to its own authoritative contract.
- Core workflow supports correction, cancellation, and replacement as atomic attributable events under the accepted correction/audit contract. Referral/delivery history remains follow-on scope.
- Policy/legal/business-controlled copy is versioned, owned, and approved before production use. Public-source legal research supplies suggested candidate controls only; legal behavior becomes validated software only after counsel documentation is translated into approved versioned requirements and acceptance tests.

## Accepted employer-demand baseline and proposed follow-on domain model
```text
Employer → EmployerContact
         → Worksite → WorksiteZoneMembership → ServiceZone
                    → WorksiteMapAreaAssignment → MapArea
         → StaffingRequest → ShiftNeed
                           → RequestRequirement (approved typed values + restricted source text)
MapAreaDatasetVersion → MapArea
ServiceZone → ServiceZoneComposition → MapArea
Worker → WorkerProfile / governed preferences
WorkerAssignment → ReferralOrDeliveryEvent
All Phase 1 material actions → AuditEvent
```

The Phase 1 employer-demand structure and field purposes are accepted in `docs/planning/phase-1-canonical-field-purpose-inventory.md`. `Employer` is the neutral household/business hiring-party record; employer type controls approved extensions without separate stores. Worksite-to-zone and worksite-to-map-area relationships are explicit versioned association records, not a direct `Worksite.service_zone_id` shortcut. `MapAreaDatasetVersion`, `MapArea`, `ServiceZoneComposition`, and `WorksiteMapAreaAssignment` preserve pinned public-geography provenance and evolving client-managed zones. Workflow-state requiredness, retention, named role assignments, and client terminology remain tracked operational discoveries. The bounded staff-intake contract now proposes Worker/contact/residence/preferences outputs; broader worker management, assignment, referral, and delivery remain follow-on proposals.

Request and shift lifecycle is controlled by `docs/planning/phase-1-request-shift-state-model.md`. Shift coverage is part of the active shift state and may reverse when coverage changes or a no-show occurs. Terminal shift outcomes are `completed`, `unfulfilled`, and `cancelled`; request `closed` never erases or replaces those outcomes. No state transition implies automated matching, referral, placement, payment, or worker discipline.

Queue indicators are derived from authoritative states, timestamps, ownership, follow-up events, versioned business-calendar configuration, and versioned review-trigger configuration. They do not form a separate editable queue status and never change lifecycle state, ownership, contact behavior, or outcomes automatically.

The calendar shows pending, active, terminal, and cancelled records with distinct request/shift semantics, timezone-aware intervals, and approved aggregate coverage. Phase 1 materializes every shift occurrence explicitly. Permission-gated day/week address reveal is separate from broad-zone defaults. Audited drag-and-drop invokes authoritative correction/replacement commands; active shifts are replaced atomically and do not carry coverage to a new interval.

Zone classification is optional during intake and active work. Unassigned, review-required, outside-area, and map-area derivation exceptions remain visible rather than disappearing from map/list totals. Owner-led late assignment and reclassification preserve versions/history and never alter lifecycle/coverage or perform eligibility, matching, or proximity decisions.

## Non-functional requirements
- Separate staff and public security planes; public traffic must not have staff credentials, endpoints, tokens, or data access.
- Server-enforced authorization and the accepted individual-account, MFA, recovery, session, access-review, and support controls in `docs/planning/phase-1-mfa-recovery-support-ownership.md`; append-only application events and atomic correction semantics in `docs/planning/phase-1-correction-audit-event-contract.md`; encryption in transit/at rest, secret management, isolated environments, backups, and recovery qualification remain required before real data.
- Migration-managed schema evolution: expand → backfill/map → switch reads/writes → retire. Do not rewrite authoritative/audited history to fit a new schema.
- Accessible, responsive, and understandable error/recovery states.
- Observability without logging secrets or unnecessary personal data.
- Primary hosting-region selection must prioritize the East-US/NYC-area user population and exact service availability. The accepted `develop` location is `us-east4` / Northern Virginia for Cloud Run, Cloud SQL, and Artifact Registry. Central/western US comparisons may inform production cost/recovery choices; EU primary, active-secondary, or default-backup data placement requires a separately approved need.
- CI validation for tests, lint/type checks, migrations, secret/dependency/SAST scanning, and relevant configuration/IaC checks.
- The proposed first cloud target requires a cheap database-independent liveness endpoint, bounded database/schema readiness, and a separate synthetic qualification workflow; health probes must not mutate domain state.
- The proposed runtime database role must be non-owner and unable to perform routine DDL, `TRUNCATE`, trigger management, or append-only authority update/delete; migrations use a separate serialized identity and role.
- Terraform/IaC remains reviewable before cloud execution. The current source adds the exact one-permission quota bootstrap role/binding, preserves the existing budget byte-for-byte, and admits public service invocation only when the Basic gate, strict bounded expiry, fictional-synthetic marker, private Cloud SQL, immutable image, and zero-to-one scaling all match.
- ADR-0013 requires a no-default `deployment_stage` (`foundation`, `migration`, `service`), Terraform-only resource/configuration mutation, exact-job migration execution without overrides, exact direct-workflow WIF separation, and independently verified keyless Cosign signature plus SLSA v1/image-SBOM/checksum-bound application-SBOM attestations on the exact digest.
- The fictional-synthetic develop service uses temporary exact `allUsers` transport access behind an application-enforced Basic boundary. `/health` and `/readiness` remain unauthenticated and minimized; every other route and static asset is protected. Passwords are canonical unpadded base64url with at least 32 decoded random bytes, represented as `SecretStr`, compared with `hmac.compare_digest`, held outside argv/state/logs, and expired within seven days of revision creation. Production forbids the configuration.
- Automated qualification must run public probes, fixed missing/wrong credential denials, the complete Employer/EmployerContact workflow with correct credentials through a non-argv handoff, then an exact bounded post-request Cloud Run log query that fails on credential, Authorization, or generated fictional-value leakage.
- Every develop Employer create/revision and EmployerContact create command must reject values outside the bounded generated-fictional patterns before clock/identifier/persistence access and return a value-safe no-store `422`. The exact migration job and service images must equal the packet's verifier-admitted immutable digest; digest syntax alone is insufficient.

## Out of scope without separate approval
- Public portals, public job posting, public or individual-level precise mapping, AI ranking/screening, and automatic decisions. The accepted aggregate authorized-staff Phase 1 demand map remains in scope.
- Live data migration/import, résumé upload, e-signature, payment, messaging, calendar, screening, and identity-verification integrations.
- Hardcoded legal requirements, legal copy, fees, retention periods, or commercial policy.

## Acceptance gates per release
Each increment must name: users/access boundary; feature scope/non-scope; data classification; acceptance owner; support/incident path; monitoring/audit signals; rollback/forward-recovery plan; training/documentation impact; and client/counsel dependencies.
