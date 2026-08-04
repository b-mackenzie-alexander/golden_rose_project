# Phase 1 Operational Discovery Register

**Status:** Active implementation and pilot-discovery register
**Opened:** 2026-08-04
**Owners:** Golden Rose client for operational policy and acceptance; Beatrice for technical delivery and evidence capture; counsel for legal conclusions and legal/policy content
**Scope:** Questions expected to be answered through implementation, synthetic testing, staff walkthroughs, pilot preparation, and separately approved legal review

## Purpose

The Phase 1 structural, map, and role models are accepted by the client. Their acceptance does not imply that every label, threshold, named assignment, provider, retention period, or exception is already known. This register keeps those operational discoveries visible without turning them all into blockers for bounded local development.

Every discovery must be classified as Observed, Reported, Proposed, or Validated. Record the evidence, decision owner, affected contract, and whether the result changes code, configuration, training, production readiness, or legal review. Do not silently convert a pilot observation or public-source research result into production policy.

## Gate classes

- **Before affected implementation:** needed before a slice can safely define schema nullability, state guards, authorization, or other durable behavior.
- **Discover during implementation:** may be explored with synthetic data and reversible/configurable behavior; it does not block unrelated slices.
- **Before live-data admission:** required before production or client data enters the affected workflow.
- **Before public/legal feature release:** requires approved source/version, client owner, and counsel validation before legal text, fees, receipts, agreements, retention rules, or compliance claims become executable behavior.

## Active discovery items

| Area | Current accepted boundary | Discovery to capture | Gate | Evidence / owner |
|---|---|---|---|---|
| First implementation slice | ADR-0002 accepts one synthetic/local draft-Employer plus atomic `employer.created` tracer | Review/merge exact TDD tasks, PostgreSQL service approval, CI/recovery evidence, and independent-review handoff | Before affected implementation | Beatrice; `.hermes/plans/2026-08-04_phase-1-first-slice-plan.md` |
| Field requiredness | First tracer accepts only client-supplied `employer_type` and bounded `display_name`; server controls draft/source/actor/IDs/timestamps/version | Required/optional fields for later review, open, closure, cancellation, correction, contact, worksite, request, and shift slices | Before each affected later implementation | Client terminology/workflow walkthrough; technical contract update |
| Client terminology | Stable identifiers and neutral canonical concepts are accepted | Staff-facing names, reason labels, translations, help text, and legacy aliases | Discover during implementation | Client walkthroughs; English/Spanish review |
| Household/general-labor extensions | One canonical workflow; no duplicate stores | Which typed extension fields are needed and at which workflow stages | Before affected extension implementation | Client examples and approved field-purpose update |
| Role assignments | Owner, delegated Manager, Operations Staff, and bounded Platform Administrator model is client-accepted | Named users, delegated capabilities, review owner, dormant-account threshold, support contacts, break-glass approvers | Before live-data admission | Client access roster and reviewed delegation record |
| Exact-address use | Exact worksite address is separately restricted | Collection timing/purpose, named recipients, reveal workflow, correction, and disposal | Before live-data admission | Client operational validation; privacy/security review |
| Queue operation | Separate clocks, shared ownership, deterministic lanes, and configurable triggers are accepted | Business calendar, threshold values, escalation owner, contact attempts, no-response terminology and exceptions | Discover during implementation; validate before production policy | Client staff walkthrough/pilot evidence |
| Calendar operation | Derived request milestones and explicit shift occurrences are accepted | Display terminology, rescheduling exceptions, correction reasons, and staff workflow ergonomics | Discover during implementation | Client walkthroughs and accessibility testing |
| Service zones | Adaptive client-managed zones over pinned CDTAs are accepted | Zone names/descriptions/translations, overlap conventions, delegation, outside-area policy | Discover during implementation | Client map/catalog walkthroughs |
| NYC demand map | Authorized-staff job-demand/coverage map is client-accepted | Usability, default measures, accessible table behavior, out-of-area handling, renderer/tile presentation | Discover during implementation | Client walkthroughs; accessibility evidence |
| Map/geocoder providers | Provider-neutral boundary; coordinates transient and discarded by default | Vendor privacy/security terms, data flow, regional processing, failure behavior, renderer/tile/geocoder selection | Before live provider or live-address use | Security/vendor review and client approval |
| CDTA dataset | Pinned/checksummed official DCP release and provenance are required | Exact release/checksum, normalization/import evidence, upgrade review process | Before affected map implementation | Public dataset verification; Beatrice approval |
| Identity and recovery | Individual MFA identities, controlled recovery, revocation, review, and separated support are accepted | Provider qualification, named approver/executor, rehearsal evidence, client successor | Before live-data admission | Security qualification and client roster |
| Audit history | Current domain rows plus append-only material `AuditEvent` history are accepted | Client reason terminology, restricted-history recipients, deletion/anonymization handling | Before live-data admission where sensitive history is retained | Client/counsel/privacy decision |
| Legal and public content | Public-source research supplies suggested candidate controls only | Counsel-approved applicability, authoritative source/version, exact wording, fees, schedules, receipts, agreements, retention and update ownership | Before public/legal feature release | Counsel documentation plus client acceptance |
| Data classification | Data minimization and synthetic development boundary are accepted | Field/environment classifications, approved fixture procedure, production admission checklist | Before live-data admission; slice-specific classification before affected implementation | Security review and release acceptance owner |
| Legacy data | No automatic import and no protected/proxy default filters | Excluded fields, controlled extensions, neutral treatment, source preservation, migration mapping and correction | Before any legacy import/migration | Client/counsel/security review |
| Retention and disposal | No hardcoded legal retention; ordinary hard delete prohibited for active authority | Approved periods, disposal mechanics, legal holds, audit-envelope treatment, deletion/anonymization policy | Before live-data admission | Counsel/client/privacy approval |
| Office constraints | Browser-based staff workspace is required | Supported devices/browsers, performance budget, network limitations, printing and accessibility needs | Discover during implementation | Observed office environment and staff testing |
| Support and training | Each increment requires support/incident and training impact | Hours, escalation paths, runbooks, staff training, acceptance evidence | Discover during implementation; complete before production activation | Client and Beatrice |

## Recording rule

Add dated findings to `NOTES.md` and update the controlling contract when a discovery changes an accepted behavior. Configuration discoveries may remain configurable; architecture, authorization, data-purpose, legal, or trust-boundary changes require reviewed document/ADR updates before implementation proceeds. Production/live-use gates remain hard stops even when adjacent synthetic implementation is allowed.
