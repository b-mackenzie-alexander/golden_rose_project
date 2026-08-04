# Security — Golden Rose Operations Platform

**Status:** Planning baseline. This document records security posture and open controls; it does not claim production compliance or completed implementation.

## Security objectives
- Protect worker, employer, household/worksite, document, and operational data using least privilege and data minimization.
- Preserve attributable, reviewable operational history without making originals silently editable.
- Keep public workflow traffic materially separate from higher-trust agency administration.
- Make security controls testable before real data or production use.

## Trust boundaries
1. **Public plane:** eventual worker/employer browser/API flows. Public accounts never gain staff access by role selection or token reuse.
2. **Staff plane:** agency-member administration, operational search, data entry, review, and reporting. Requires separate identity client/session/token audience, endpoints, credentials, authorization checks, MFA, and account lifecycle.
3. **Controlled crossing:** narrow, authorized, audited staff actions on public-workflow records.
4. **Data stores:** transactional records, documents, logs, backups, exports, and secrets have distinct access and retention controls.

## Baseline controls required before live data
- Server-enforced, role/record/field authorization; no UI-only authorization.
- Staff MFA, least-privilege roles, attributable privileged actions, controlled access recovery, session revocation, prompt deprovisioning, access review, and separated support ownership under `docs/planning/phase-1-mfa-recovery-support-ownership.md`.
- A server-enforced staff permission matrix under `docs/planning/phase-1-staff-permission-matrix.md` that distinguishes Owner, delegated Manager, Operations Staff, and Platform Administrator. Platform Administrator access must use a separate privileged identity/path and must not create standing access to operational personal data, document contents, raw database records, or business-role management.
- TLS/HTTPS in transit; encryption at rest; secrets outside source code and client-facing builds.
- Separate development/test and production accounts, databases, buckets, identity clients, and credentials.
- Structured append-only application audit events separated from operational logs under `docs/planning/phase-1-correction-audit-event-contract.md`; domain/event writes are atomic, sensitive historical payloads remain field-authorized, and secrets or unnecessary personal data are excluded from events and logs.
- Backup/restore evidence, forward-recovery plans, and incident/support ownership.
- Dependency, secret, static-analysis, migration, authorization, and deployment review gates in CI/CD.

## Data-protection rules
- Treat precise household/worksite address, proximity, household composition, worker contact data, résumés, and free-text notes as sensitive operational data.
- Use least-precise location for routine worker-facing/public views; disclose precise location only in approved need-to-know workflows.
- Do not make protected traits, nationality/religion/community labels, language inference, disability/health proxies, caregiving preferences, or legacy free-text requirements default filters, comparison signals, or decisions.
- Do not expose worker/home locations or exact household/worksite addresses through routine dashboards, maps, exports, or public surfaces. Use approved broad service zones for routine operational/reporting views; any point-level location use requires separate approval.
- Employer assertions about conditions, pay, safety, language, physical demands, transportation, and supervision require agency review; they do not automatically become worker-facing facts.
- Treat all legal text, consents, notices, communication preferences, retention rules, and fee/payment behavior as versioned, approved content—not hardcoded form copy.

## Document ingestion: blocked until qualified
If worker résumé upload is approved, the system must establish:
- authenticated/authorized initiation;
- strict PDF-first allowlisting, signature/content validation, bounded sizes, and rate limits;
- isolated, non-executable private quarantine storage;
- malware scanning before release to staff or downstream processing;
- safe preview/download behavior and authorization checks;
- audit events, failure/retry process, retention/deletion, and user-visible outcomes.

Unscanned/rejected artifacts must not be served, rendered, indexed, or available to staff/public users.

## Security workflow
1. Classify the observation as Observed, Reported, Proposed, or Validated.
2. Record risk, affected boundary/data, owner, mitigation, evidence, and approval state.
3. Treat High/Blocker security findings as release blockers until resolved or explicitly accepted by the authorized owner.
4. Require security review escalation for auth, public/staff boundaries, data access, documents, payments, exports, logging/audit, dependencies, infrastructure, and database migrations.
5. Record correction/exception paths under the accepted correction/audit-event contract; do not erase operational history to correct it.

Current domain rows and append-only audit history have separate authority. Audit events are not ordinary logs or full-row snapshots, and Phase 1 does not claim full event sourcing, cryptographic immutability, legal WORM storage, or perpetual retention. The application runtime may append approved events but must not update/delete them. Every required domain/event change is atomic, expected-version checked, idempotent, and field-authorized; correction-of-correction appends a linked event. Exact-address/restricted historical values use a protected payload and are never routine search/filter/log content.

Phase 1 request/shift transitions are guarded authoritative operations defined in `docs/planning/phase-1-request-shift-state-model.md`. Implementations must reject stale/forbidden transitions, keep coverage count consistent with shift state, append prior/new state and coverage evidence, and prevent ordinary staff from reopening terminal records. No-show and coverage-loss events are operational evidence, not automatic worker discipline, eligibility, comparison, or ranking inputs.

Phase 1 queue timing and follow-up behavior is defined in `docs/planning/phase-1-work-queue-aging-follow-up-model.md`. Authorization must be applied before queue search, counts, lanes, filters, and exports. Shared ownership must not create private hidden queues; escalation must not broaden record/field access. Follow-up attempts, deadline changes, reassignment, acknowledgments, and threshold versions remain attributable. No queue trigger authorizes automatic contact, closure, reassignment, staff discipline, or employment decision-making.

Phase 1 calendar behavior is defined in `docs/planning/phase-1-calendar-coverage-semantics.md`. Authorization applies before item rendering, counts, filtering, detail previews, and exact-address reveal. Service zone is the default; exact address may be revealed only in authorized day/week operational views and is excluded from month/aggregate/external surfaces. Calendar commands require expected-version checks and audit evidence. Active-shift rescheduling must be an atomic linked replacement that does not inherit coverage. The calendar must not infer worker conflicts, availability, travel feasibility, suitability, placement, or payment.

Phase 1 service-zone behavior is defined in `docs/planning/phase-1-service-zone-taxonomy.md`. Zone catalog/composition authority, CDTA assignment, worksite membership, request/shift operational attribution, and exact-address access are separate permissions. The Owner may group pinned CDTAs and assign zones later; unassigned records remain visible/countable. Secondary memberships do not duplicate counts. Geography must not become a proximity, suitability, eligibility, referral, or worker-ranking signal.

Phase 1 NYC map behavior is defined in `docs/planning/phase-1-nyc-job-demand-map-contract.md`. Authorization applies before aggregation and drill-down. Exact addresses are sent only through an approved server-side geocoder using minimum fields; employer/contact/request/worker content is excluded. Provider/result metadata and match quality are attributable, ordinary logs redact payloads/points, and precise coordinates are discarded by default after local point-in-polygon classification against a pinned CDTA release. Basemap/tile requests receive no operational record payload. Failed/ambiguous/outside results require visible review. No worker map layer ships before its privacy/availability/suppression contract.

## Current open security decisions
- Named staff-role assignments/delegations, recovery approvers/executors, support contacts/hours, client technical successor, dormant-account threshold, and qualified identity-provider configuration under the accepted MFA/recovery/support contract; including precise-worksite permission recipients and separate Platform Administrator/break-glass approvers.
- Owner map/zone delegation, out-of-area policy, exact-address reveal permissions, demand-map aggregation/export rules, geocoder/renderer/tile provider review, API-key/data-processing/retention terms, and later worker-layer suppression. Exact zone names may emerge through pilot use.
- Production data classification, retention/deletion/export rules, restricted audit-history recipients, and any stronger legal-record archival requirement under the accepted correction/audit contract; migration governance remains separately gated.
- Identity, messaging, signature, payment, screening, and other vendor selection/data processing.
- Backup RTO/RPO, test cadence, key-management details, security-edge/WAF needs, and monitoring/alert ownership.
- Upload scope and secure-ingestion implementation acceptance criteria.

## Incident handling baseline
Do not improvise with client records. Preserve minimum necessary evidence, protect access, notify the designated client/security owner through the approved path, assess containment and recovery, and document attributable remediation. Formal incident notification obligations require approved legal/business policy.
