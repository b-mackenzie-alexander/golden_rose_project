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

## Updating this file
Add a short dated entry after a material planning, implementation, test, security, or release event. Link detailed evidence rather than duplicating it. Record commands and results only when they were actually run.
