# Golden Rose Operations Platform — Roadmap

**Status:** Living checklist. Discovery evidence and approved decisions control scope; unchecked items are not authorized merely because they appear below.

## Phase 0 — Discovery and planning baseline
- [x] Record source-material ledger and evidence notes for received client artifacts.
- [x] Identify fragmented paper, spreadsheet, calendar, Trello, messaging, and hosted-form workflows.
- [x] Establish the source-of-truth boundary: client artifacts are discovery evidence, not production legal/business content.
- [x] Establish English/Spanish functional-parity requirement.
- [x] Record the proposed public-plane / staff-plane security boundary.
- [x] Create repository living-document baseline.
- [ ] Complete client validation of current workflow, owners, source records, and exceptions.
- [ ] Obtain approved business model, legal statements, and production content/rule owners.
- [ ] Reconcile the client-provided DCWP checklist against current authoritative sources and counsel/client validation.
- [ ] Approve the preliminary PRD and seven-week delivery plan.

## Phase 1 — Staff pilot foundation: employer demand workflow
**Goal:** Give authorized agency staff a reliable, browser-based place to create and find employer staffing requests without duplicating response stores.

- [ ] Approve staff roles, account lifecycle, MFA, and initial data classification.
- [ ] Approve canonical employer, contact, worksite, staffing-request, and shift-need field inventory and purpose.
- [ ] Define request states, agency review/correction path, and immutable/auditable event requirements.
- [ ] Define household and general-labor request extensions without creating separate workflows or data stores.
- [ ] Create synthetic/de-identified fixtures only; do not import live legacy data.
- [ ] Implement staff authentication and authorization boundary.
- [ ] Implement employer/contact/worksite/request/shift persistence with migration-managed schema.
- [ ] Implement staff request entry, detail, correction, and authorized search/work queue.
- [ ] Implement attributable audit events and safe operational logging.
- [ ] Test accessibility and English/Spanish behavior for the released staff workflow.
- [ ] Complete staff-pilot acceptance, support, rollback/forward-recovery, and training evidence.

## Phase 2 — Staff dashboard and governed comparison aid
**Goal:** Replace manual statistics collection with an agency-only dashboard derived from authoritative workflow records, then support transparent staff comparison.

- [ ] Approve staff roles, decision questions, KPIs, source records, calculation definitions, and refresh/export rules.
- [ ] Implement role-scoped operational dashboard projections; no extra metric-entry forms.
- [ ] Validate graph totals and empty/error states against source records.
- [ ] Approve job-relevant worker/employer comparison criteria, display language, and human-review process.
- [ ] Implement explainable comparison aid that shows supported signals, missing data, and staff notes.
- [ ] Block automated ranking, eligibility, hiring, or referral decisions.
- [ ] Test authorization, aggregation/redaction, accessibility, and auditability.

## Phase 3 — Worker profile and controlled documents
**Goal:** Add a staged, inclusive worker profile for agency review and controlled referral preparation.

- [ ] Approve worker field inventory, field purpose, visibility, retention, and correction process.
- [ ] Implement staged worker onboarding with agency review; do not imply automatic eligibility or employment.
- [ ] Achieve English/Spanish functional and accessibility parity across the workflow.
- [ ] Approve document-upload scope, consent, retention, and staff-access rules.
- [ ] Implement and qualify a PDF-first secure document-ingestion boundary before enabling uploads.
- [ ] Implement agency-controlled worker profile management and referral-readiness state.

## Phase 4 — Controlled referral, delivery, and operational records
- [ ] Approve legal/business templates, receipt/agreement rules, and role-scoped delivery views.
- [ ] Implement agency-reviewed referral/placement workflow and immutable referral snapshot.
- [ ] Implement attributable corrections, cancellations, replacements, and delivery events.
- [ ] Validate record retrieval, audit, retention, and export requirements with client/counsel.

## Phase 5 — Production qualification and rollout
- [ ] Approve client-owned accounts, billing, domain/DNS, support, and recovery ownership.
- [ ] Qualify isolated environments, secrets, backups/restore, monitoring, and incident response.
- [ ] Complete security/privacy review and production-data gate for each rollout increment.
- [ ] Promote the qualified immutable release artifact through recorded approval.
- [ ] Capture client acceptance and post-release follow-up.

## Explicitly deferred unless separately approved
- AI-assisted ranking, screening, or decision-making.
- Public job publication, mapping/heat maps, and precise-location features.
- Payment, e-signature, background/identity/credit screening, messaging, and calendar vendors.
- Legacy-response migration or unrestricted production-data collection.
