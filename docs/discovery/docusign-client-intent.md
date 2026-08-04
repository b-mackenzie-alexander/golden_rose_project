# DocuSign Interest — Client-Reported Discovery Evidence

**Status:** Client-reported preference; not an approved vendor selection, executed agreement, integration authorization, or legal determination
**Recorded:** 2026-07-28

## Observed statement
The client specifically said she wants the business to begin using DocuSign.

## What this establishes
- A desired electronic-signature/document workflow exists.
- DocuSign is a named vendor candidate for that workflow.
- The product needs an integration decision point rather than a custom signature implementation assumed by default.

## What it does not establish
- That Golden Rose already has a DocuSign account, which entity owns it, which plan/API features are licensed, or who administers it.
- Approval to create an account, purchase a plan, configure DocuSign, upload client documents, share personal data, or connect an API.
- That every agency contract, disclosure, receipt, notice, or statutory form can be delivered/signed electronically in the proposed workflow.
- Any specific signer-authentication, identity-verification, retention, data-residency, privacy, accessibility, language, or e-notary requirement.

## Product-direction implication
Treat DocuSign as an external document-execution system candidate. If adopted, Golden Rose’s platform should retain its own authoritative business/compliance lifecycle events and store controlled references/evidence for the executed document, not treat a vendor envelope ID as the entire audit record.

Candidate evidence per executed document:
- Approved template/version and source/approval reference.
- Document hash or immutable final-copy reference, recipient role, envelope/reference ID, send/complete/decline/void event timestamps, and actor/system source.
- Delivered completed document and vendor completion/certificate evidence, subject to approved retention and access policy.
- Append-only linkage for replacement, correction, void, refund, or superseding business events. Do not mutate an issued record.

## Discovery questions before any integration
1. Which documents should use DocuSign: agency–employer agreements, applicant agreements, placement terms, disclosures, receipts, wage/payroll forms, or internal approvals?
2. For each document, is electronic execution/delivery allowed and does any New York agency-form or consumer-disclosure rule impose a different method, wording, form, or retention requirement?
3. Who is account owner, administrator, billing owner, and template approver? What plan/API/webhook capability and sandbox access exist?
4. What signer assurance is proportionate for each document: email link, access code, SMS/phone verification, ID verification, or an in-person process? Do not assume a DocuSign workflow alone verifies identity.
5. What data fields/documents will be sent to DocuSign? What DPA, security review, retention/deletion, export, subprocessor, incident-notification, and access controls are required?
6. Which recipients are legal “consumers” receiving required written disclosures electronically, such that E-SIGN §7001(c) consent/access evidence is required?
7. What is the failed/declined/expired/voided-envelope path, and how does the agency preserve a complete non-destructive history?

## Current guardrails
- No DocuSign account, template, integration, webhooks, or credentials will be created/used in discovery without explicit client and project approval.
- Do not upload client forms or personal information to a vendor sandbox during discovery.
- DocuSign does not itself establish compliance with Article 11, Fair Chance, E-SIGN consumer-disclosure rules, record-retention duties, or a particular form’s required wording.

## Related research
- `docs/compliance/phase-1-compliance-matrix.md` — E-SIGN and Article 11 candidate controls.
- `docs/compliance/phase-2-nyc-employment-and-data-matrix.md` — data/vendor trigger controls.
