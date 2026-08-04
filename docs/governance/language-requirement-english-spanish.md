# Language Requirement — English and Spanish Across the Application

**Status:** Confirmed product requirement
**Recorded:** 2026-07-28

## Requirement
English and Spanish are mandatory across the Golden Rose application. The primary end users are native Spanish speakers; the platform must also serve English-speaking clients and workers.

This is not limited to worker intake. It applies to the complete user-facing product experience for workers, employers, and agency staff, including:
- Account setup, authentication, recovery, onboarding, forms, validation, and error states
- Worker/employer portals, staff dashboard, job requests/descriptions, matching/review status, and document workflows
- Receipts, agreements, disclosures, acknowledgements, consent surfaces, and generated documents
- Messages, email/SMS/WhatsApp templates, notices, reminders, delivery/access status, and support/help content
- Settings, alerts, audit-facing status labels, download/export labels, and administrative operational workflows

## Implementation and governance controls
1. **Language selection:** explicit English/Spanish selection at entry and in settings; do not infer language from name, location, or other profile attributes. Persist a changeable preference with provenance.
2. **Functional parity:** both languages must provide equivalent workflow completion, required fields, validation/error handling, accessibility support, and material content. A translated shell around English-only flows is not sufficient.
3. **Controlled translations:** legal, compliance, fee, consent, contract, disclosure, and policy text requires a source, approved English and Spanish version, owner, approval state, effective date, and applicability. Do not use ad-hoc or machine-translated legal text as production content.
4. **Document execution/delivery:** select the approved language-specific document/template version deliberately, record the selected language/version, and retain it with the issued/delivered event. DocuSign routing must not substitute or auto-translate legal content.
5. **Operational content:** maintain versioned translation keys/content with review ownership; untranslated or stale material is a release blocker for the affected experience.
6. **Accessibility:** language metadata, readable layout, assistive-technology labels, and equivalent accessible content are required in both languages.
7. **Testing:** acceptance testing must cover both languages for each user journey and system-generated communication, including fallback behavior and character/formatting support.

## Boundary
This requirement establishes language availability and parity. It does not authorize translating or finalizing legal/business wording before counsel/client approval. Approved bilingual legal documents and the codified business plan remain the source of truth for governed content.
