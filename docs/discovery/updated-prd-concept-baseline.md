# Updated PRD Concept — Compliance-First Builder Brief

**Status:** Client-supplied discovery evidence; not yet an approved legal or technical specification
**Reviewed:** 2026-07-28
**Source:** Two photographed pages supplied 2026-07-28 (`IMG_9409.HEIC`, `IMG_9410.HEIC`)
**Source SHA-256:** `e294c97914516145d9c6f0c3275e4356596bc5fd029ee8e25d70d431e3244327` (IMG_9409); `2eb06fc5fedc41f9cb318dc0c41db5de31a5b8e3931d18d434b953f9b7d8f364` (IMG_9410)

## Material change from the initial mini PRD
The revised concept reframes V1 from an AI recruiting-efficiency tool to an internal, compliance-first operating platform for a New York City employment agency placing domestic workers and household employees. AI-assisted recruiting is now an operations-supporting concern; the stated core is preventing non-compliant actions through the system’s architecture.

## Stated operating context
- The agency is licensed in New York City and operates under New York employment-agency regulation cited in the brief as Article 11 of the New York General Business Law and Department of Consumer and Worker Protection (DCWP) oversight.
- The brief says applicant intake, placements, and licensing operations continue while the platform is built.
- It identifies a repeated fee-receipt-template formatting error—stated as 678 occurrences—as the motivating compliance incident and says each occurrence may be treated as a separate regulatory violation.

## Stated Version 1 requirements

### Compliance layer
1. Generate legally compliant fee receipts with exact, hardcoded, uneditable GBL §181(4) language.
2. Capture applicant name, agency information, date, amount, purpose, and signature.
3. Prevent recording applicant payments before a confirmed placement.
4. Automatically calculate stated legal fee caps: 10%, 12%, 14%, or 18%.
5. Prevent fees above the statutory maximum.
6. Enforce payment schedules of no more than ten equal weekly installments.
7. Mark employer fees as due when employment begins.
8. Generate a Register and Refund Log; retain records for three years, log every refund, and support one-click export.
9. Prevent completion of the Employee Rights and Job Description Form before placement.

### Operations layer
- Digital intake forms, secure document uploads, electronic signatures, automatic job-match notifications, and a unified placement-specialist dashboard.
- System-generated bilingual communications.
- Centralized applicant and employer tracking.
- Compliance reporting and Register export in Version 1.

## Stated scope and delivery outcomes
- This is an internal Golden Rose platform, not a commercial product for other agencies.
- It should nevertheless keep each agency’s records separate from the start to preserve future flexibility.
- Desired outcomes are: agreement on the revised problem statement; a data model for applicants, employers, placements, fees, receipts, and disclosures; and a working prototype that creates a placement, automatically writes a legally compliant receipt, and automatically writes to the register.
- The brief asks for clarification of software and intellectual-property ownership for work created through the program.

## Critical validation gates before implementation
| Gate | Why it must be validated |
|---|---|
| Legal-source verification | The exact statutory language, fee-cap conditions, payment-schedule rule, trigger definitions, and record-retention rule must be verified against authoritative current sources and client/legal counsel—not inferred from a builder brief. |
| Human authority and exception process | The system must define who can create/confirm/void a placement, approve corrections, issue refunds, and amend an immutable receipt or register record. |
| Auditability and record integrity | “Hardcoded/uneditable” needs a compliant correction model: append-only history, actor/time/source evidence, versioned templates/rules, and export/reconciliation behavior. |
| Personal-data protection | Applicant, employer, placement, payment, and signature data requires defined role access, encryption, retention/disposal, access review, logging, and incident handling. |
| Rules coverage | Fee caps and required forms likely depend on facts not enumerated in the concept. The data inputs, precedence, effective dates, ambiguity handling, and test fixtures must be specified. |
| Product boundary | “Separate records per agency” could become multi-tenancy. Confirm whether this is only a data-model isolation requirement or a future product commitment. |

## Immediate planning posture
Treat the document as a strong revised product direction, but do not represent the prototype’s receipt/register output as legally compliant until legal rules, source documents, and acceptance tests are validated.

**Research update (2026-07-28):** Phase 1 research identifies a candidate GBL §181(4) applicant-fee/refund receipt notice requirement in the non-theatrical setting. Its exact current wording, triggers, delivery method, and interaction with Golden Rose’s actual fee model remain counsel-approval items; see `docs/compliance/phase-1-compliance-matrix.md`.

## Artifact provenance
- Converted review copies: `artifacts/source-materials/golden-rose-updated-prd-concept/photos/`.
- Original HEIC images remain in Downloads and were not copied into the workspace, avoiding unnecessary duplication of client-source material.
