# Initial PRD Baseline — Golden Rose Employment Agency

**Status:** Discovery evidence; not an approved specification
**Reviewed:** 2026-07-28
**Source:** `/Users/genie/Downloads/Pursuit x HF SMB PRDs 071326.pdf` (2-page scanned PDF)
**SHA-256:** `37b9cd686e5c87167757745c929c3ab1bb997353f2ab723e7216854484e18ce2`

## Evidence captured from the initial PRD

### Stated problem and users
- Recruitment specialists manually screen candidates, match them to openings, and respond to inquiries across WhatsApp, phone, email, and spreadsheets.
- Primary users: recruitment specialists.
- Secondary users: agency owners overseeing operations and placements.

### Stated product idea
A web-based “AI Recruiting Assistant” intended to organize recruitment work, analyze candidate information, recommend matches, generate bilingual communications, answer FAQs, and track follow-ups. The PRD says it should assist—not replace—recruiters.

### Stated Version 1 requirements
1. Candidate digital intake for personal, employment, and contact information.
2. Secure document upload portal.
3. Electronic signatures for contracts, disclosures, and authorization forms.
4. Automatic notification when an opportunity fits a candidate’s qualifications.
5. Centralized recruiter platform for candidate review and recruitment-process management.

### Explicitly out of scope for Version 1
- Video interviews and a live-support AI chatbot.
- Dedicated mobile application.
- Third-party integrations (including QuickBooks, Airtable, payroll, and external CRMs).
- Advanced AI (predictive recommendations, resume optimization, career coaching).
- Advanced analytics/custom reports, employer self-service, and multi-office/multi-agency management.

### Success measures
No measurable acceptance criteria, baseline metrics, targets, owners, or launch criteria are stated. The PRD asserts desired outcomes (reduced operational cost, saved staff time, faster matching/communication), but these are not measurable requirements.

## Discovery findings — clarification required

| Area | Evidence / ambiguity | Why it matters |
|---|---|---|
| AI scope | The PRD calls for candidate analysis and “best” match recommendations, while excluding predictive job recommendations. | Define whether V1 is rules-based search, assisted ranking, or an ML/LLM feature; set human review and evaluation boundaries. |
| High-stakes hiring safeguards | Employment matching is central, but no human-approval, explanation, fairness, bias-testing, or audit requirements are stated. | Automated or opaque employment recommendations create material fairness, legal, and trust risk. |
| Data protection | Intake and document uploads will hold personal/employment information; “securely” is not defined. | Establish data classification, authorization roles, encryption, retention/deletion, audit logging, incident handling, and access-review expectations. |
| E-signature workflow | Contracts, disclosures, and authorization forms are in scope, but authority, templates, signers, evidence, and legal provider requirements are unspecified. | The implementation must preserve enforceability and an audit trail. |
| Workflow model | Intake, matching, notifications, and “entire recruiting process” are named, but job-opening creation, candidate stages, recruiter handoffs, exceptions, and ownership are not. | A workflow/state model is needed before building the centralized system. |
| Communications | The context names WhatsApp, phone, and email; the product proposes bilingual generated communications and notifications. Channels, languages, consent, templates, review, delivery, and opt-out rules are absent. | Messaging cannot be safely scoped or tested without these decisions. |
| Roles and access | Candidate, recruiter, and owner needs are mentioned, but permissions and approval boundaries are not. | Role-based access is foundational to the portal and operational workflows. |
| Integration/migration | Third-party integration is excluded, but current spreadsheets and multi-platform work are central to the problem. | Clarify V1 import/export, data cleanup, coexistence, and migration strategy. |

## Recommended Week 1 decisions
1. Confirm the V1 user roles and end-to-end happy path, including recruiter approval points.
2. Define the permitted meaning of “AI” for V1 and explicitly prohibit autonomous employment decisions.
3. Establish a data inventory and baseline privacy/security requirements before collecting real candidate records.
4. Select or constrain e-signature, document-storage, notification, and identity/access approaches.
5. Turn the requirements into testable acceptance criteria, prioritized scope, and seven-week milestones.

## Artifact provenance
- Rendered review copies are stored locally under `artifacts/source-materials/golden-rose-prd-initial/rendered-pages/`.
- The original PDF remains in Downloads; it was not copied into the product workspace to avoid unnecessary duplication of client-source material.
