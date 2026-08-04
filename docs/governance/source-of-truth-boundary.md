# Governance Boundary — Source of Truth for Legal and Business Rules

**Status:** Week 1 decision; active for all Golden Rose planning and implementation
**Recorded:** 2026-07-28

## Decision
Client-provided forms, packets, photos, PRDs, business-model canvases, and field observations are **discovery evidence**. They may inform workflows, candidate data fields, migration questions, and validation requests. They are not copied unchanged into the product and are not the source of truth for legal wording, legal rules, fee calculations, retention rules, or approved commercial policy.

Two pending authoritative inputs control the corresponding product behavior:
1. **Legal advice and approved legal documents** provide the applicable wording, form, disclosure, legal-rule, execution, and retention guidance.
2. **The client’s codified official business plan** provides the approved pricing, packages, payer model, service scope, business policies, ownership, and operating decisions.

## Engineering consequences
- No hardcoded legal text, statutory rate, receipt language, fee ceiling, payment schedule, or policy exception from discovery artifacts.
- Legal/business configuration enters only through a named owner, authoritative source, approval state, effective date, version, and applicability scope.
- Product behavior remains blocked or uses a non-production discovery state until required governing inputs are approved.
- Issued compliance/financial/document events remain immutable; corrections, voids, refunds, and amendments are new attributable linked events.
- The platform must retain provenance for the approved rule/template used at the time of each event.
- A vendor’s e-signature capability does not replace an approved legal template or governance decision.

## Release gate
No production claim of compliance, no production fee collection, and no legal-template automation until the applicable legal and official-business-plan inputs have been reviewed, recorded, and approved by the designated client/counsel authority.
