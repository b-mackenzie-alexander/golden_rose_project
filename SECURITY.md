# Security — Golden Rose Operations Platform

**Status:** Planning baseline with active no-cloud remediation implementation on `fix/post-pr33-deployment-path-remediation`. This document records security posture and open controls; it does not claim production compliance, merged remediation closeout, or completed cloud qualification.

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
- Dependency, secret, static-analysis, migration, authorization, deployment, and schema-validated SBOM review gates in CI/CD.

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

## Synthetic Employer authorization boundaries
ADR-0002 permits the implemented local/test-only create tracer before a real identity provider exists. The synthetic principal is supplied by validated configuration/dependency injection, never by a request header or body. The create command requires the named `employer:draft:create` permission, must be rejected when the environment is production, and must authorize before idempotency lookup or any database read/write. Tests must prove that denial produces no employer/audit row and that a different actor cannot reuse another actor's idempotency key to replay or discover the prior result. Only fictional synthetic names are allowed, and validation/error/log output must not echo submitted names, database URLs, SQL parameters, or raw exception details.

ADR-0004 adds `employer:read` to the implemented synthetic local/test principal for exact detail and bounded filtered search only. Authorization runs before Employer lookup, search, pagination, or result derivation; role labels and request headers cannot grant access. Search uses a validated POST body so household/person-identifying name fragments do not enter URLs, and names/cursors/filter fingerprints remain excluded from logs and safe errors. Literal wildcard escaping, filter-required keyset pagination, minimized no-store responses, no total/unfiltered list/export, and no read-side Employer/receipt/audit writes are mandatory. The cursor grants no authority.

ADR-0005 accepts a local/synthetic Employer workspace frontend boundary over those implemented staff contracts after one test-first cache hardening: fresh and replayed create successes must add `Cache-Control: no-store` without changing their existing `201` status, body, authority, idempotency, or persistence behavior. Employer names/types, search values, cursors, command IDs, problem bodies, and payloads remain out of browser navigation URLs, browser persistence, console output, analytics, and third-party runtime recipients. Employer-name inputs disable autocomplete, spellcheck, autocorrect, and autocapitalization, subject to separate managed-browser validation before live use. A selected Employer UUID appears only in the required exact-detail staff API request path. The client uses relative same-origin no-store requests with same-origin mode/credentials, redirect refusal, and no-referrer policy, plus narrow response guards, stale-request cancellation, and one browser-generated idempotency UUID retained for retry of unchanged input after a network failure, retryable 500/503, an unexpected 2xx status, or an unreadable/invalid `201` create body. Because that UUID is deliberately tab-memory-only, reload/crash recovery is not solved; synthetic staff are directed to search before another create, and live use requires a separately approved durable design. UI visibility never grants authority. PR #13 merged that bounded workspace.

ADR-0006 governed the closeout merged by PR #15. ADR-0007 governed draft-Employer revision merged by PR #17 and remediated by PR #18. PR #20 merged ADR-0008's independently reviewed EmployerContact authority implementation at `6eb05d5`. PR #22 merged ADR-0009 Slice B's local runtime/container contract, and PR #33 merged ADR-0012's consolidated source-controlled pre-deployment implementation at `3c0118a`. Post-merge audit F1-F17 means that source is not deployment-ready. Accepted ADR-0013 now requires staged Terraform authority, Terraform-only configuration mutation, exact-job/view deploy execution, direct-workflow WIF separation, mandatory digest-bound Sigstore provenance/SBOM, IAM-private named-tester access, and authenticated no-traffic readiness monitoring before any cloud progression. Cloud Run IAM remains an outer test perimeter, not application business authorization. Terraform plan/apply, backend migration, cloud authentication, provisioning, image publication, deployment, service start, real identity, live/client data, and production remain separately gated.

PR #29 merged semantic Terraform/workflow policy, deterministic `uv`, an explicit Cloud Run-to-private-SQL network path, API-enablement dependency ordering, Cloud SQL backup enablement, and authoritative managed-registry digest binding. The self-authorizing same-repository-CI High remains open accepted residual risk because the sole maintainer controls the repository and its required workflows. Accepted ADR-0012 does not claim that risk is fixed; it replaces the unavailable-reviewer deadlock with explicit Beatrice-owned implementation, read-only qualification, plan, apply, deployment, and qualification gates plus mandatory defense-in-depth evidence.

PR #26 merged ADR-0010's original required-CI authority plan, but live repository evidence confirms no independently controlled reviewer/CODEOWNER exists. PR #27 merged ADR-0011's truthful solo-maintainer static-remediation protocol, and PR #29 completed that bounded work. Accepted ADR-0012 now treats solo maintenance as permanent: required checks and delegated/separate-session review remain quality evidence, no fake approval control is claimed, Beatrice dispositions Blocker/High findings, and the High/open CI-authority risk remains explicit. The accepted successor consolidates all remaining source-controlled pre-deployment controls but grants no cloud authority from planning or merge alone.

Current direct dependency purpose/license/deprecation review evidence is recorded in `docs/security/dependency-purpose-license-review.md`. Frontend and backend CycloneDX SBOMs must be schema-validated against their expected Golden Rose application identity before CI treats them as qualifying evidence; raw SBOM inventories are artifacts, not log output.

The accepted frontend supply-chain gate must validate lockfile version 3, exact manifest/root-lock dependency agreement, exact-version dependency specs, canonical `https://registry.npmjs.org` tarball provenance, and SHA-512 integrity for every fetched package before any dependency install; ranges/tags/aliases/protocols, local, link, git, alternate-host, weak-integrity, and wildcard exception paths fail closed. Installs keep lifecycle scripts disabled, and dependency-tree, audit, license, SBOM, immutable-action, and exact-final-head evidence remain mandatory. The required workflow uses a job-level PostgreSQL service that exists before job steps; local parity therefore starts and health-checks the disposable service first, then runs the same lock/frontend/backend/migration/audit/SBOM sequence and tears it down deterministically.

## Current open security decisions
- Complete GCP billing/Terraform-state ownership, named cloud administrators and alert recipients, Cloud SQL recovery, log retention, and first-provisioning inputs under accepted ADR-0009/ADR-0013. The durable control plane must survive workload teardown; the existing non-workload project remains only a candidate pending read-only qualification. The develop region is accepted as `us-east4`; database sizing and $50/$75/$100 alerts remain planning inputs rather than production guarantees.
- Implement and merge ADR-0013's F1-F17 remediation before cloud progression. Secret payloads and database passwords stay out of Terraform source/state; exact workflow WIF authority, Sigstore/OCI compatibility, Monitoring service-agent invocation, and provider-valid recovery inputs require source tests and later live verification.
- Named staff-role assignments/delegations, recovery approvers/executors, support contacts/hours, client technical successor, dormant-account threshold, and qualified identity-provider configuration under the accepted MFA/recovery/support contract; including precise-worksite permission recipients and separate Platform Administrator/break-glass approvers.
- Owner map/zone delegation, out-of-area policy, exact-address reveal permissions, demand-map aggregation/export rules, geocoder/renderer/tile provider review, API-key/data-processing/retention terms, and later worker-layer suppression. Exact zone names may emerge through pilot use.
- Production data classification, retention/deletion/export rules, restricted audit-history recipients, and any stronger legal-record archival requirement under the accepted correction/audit contract; migration governance remains separately gated.
- Identity, messaging, signature, payment, screening, and other vendor selection/data processing.
- Backup RTO/RPO, test cadence, key-management details, security-edge/WAF needs, and monitoring/alert ownership.
- Upload scope and secure-ingestion implementation acceptance criteria.

## Incident handling baseline
Do not improvise with client records. Preserve minimum necessary evidence, protect access, notify the designated client/security owner through the approved path, assess containment and recovery, and document attributable remediation. Formal incident notification obligations require approved legal/business policy.
