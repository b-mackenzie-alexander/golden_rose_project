# Current Worker Receipt — Evidence Review and Delivery Requirement Candidate

**Status:** Client-supplied evidence plus proposed operational requirement; not a finalized legal template or approved business policy
**Reviewed:** 2026-07-28
**Source:** `IMG_9423.HEIC`
**Source SHA-256:** `434743074224a2f01b38c5574af6166d737a47f5c6dd0f4e8325b4d5ed686247`
**Review copy:** `artifacts/source-materials/golden-rose-current-worker-receipt/photos/IMG_9423.png`

## Observed receipt
**Title:** `Receipt`
**Preprinted number:** `No. 011597`

### Printed agency information
- Name of Employment Agency: **Golden Rose Employment Agency Inc**
- DCWP License Number: **2032912**
- Address: **381 TROY AVENUE, BROOKLYN, NY, 11213**
- Telephone: **347.350.9660**
- Fields also present: agency staff/salesperson; email address if available.

### Printed transaction / placement fields
**Applicant Information**
- Name of Applicant
- Name of Employer (if known)
- Address of Employer
- Email Address, if available
- Telephone
- Job Title
- Salary
- Employment Class
- Amount of Fee
- Purpose of Fee
- Date

**Execution / acknowledgement fields**
- Applicant Signature / Date
- Employment Agency Representative Signature
- Print Title of Representative / Date
- Printed statement: “I confirm that any and all fees the Employment Agency requires applicants to pay are consistent with the law.”

### Printed applicant-fee notice
The form carries this all-caps notice, transcribed as legibly visible:

> AN EMPLOYMENT AGENCY MAY NOT CHARGE YOU, THE JOB APPLICANT, A FEE BEFORE REFERRING YOU TO A JOB THAT YOU ACCEPT. IF YOU PAY A FEE THAT OTHERWISE VIOLATES THE LAW, YOU MAY DEMAND A REFUND, WHICH SHALL BE REPAID WITHIN SEVEN DAYS. IF YOU HAVE A COMPLAINT OR NEED MORE INFORMATION, CALL 3-1-1.

### Completion state
- The submitted sample is blank apart from the preprinted agency details, receipt number, and notice.
- No handwritten transaction values, signatures, or dates are visible.

## Interpretation boundary
**Strong inference, not confirmed fact:** This is an applicant/worker-facing employment-agency fee receipt. It records agency, applicant, employer/job context, fee amount/purpose, and an applicant acknowledgement. It does **not** show an employer signature, employer acknowledgement, or an explicit three-party reconciliation section.

It may support tracking between agency, worker, and employer operationally, but the photograph alone does not prove current delivery practice or legal duties owed to each party.

## Proposed operational requirement — pending codified business plan and legal review
The user identified a desired control: receipts should be digitized, tracked, and delivered to both the worker and employer for record.

Record this as a **candidate dual-recipient delivery requirement**, with these guardrails:
1. Generate a unique immutable receipt event from the approved fee/placement case; do not allow post-issuance edits.
2. Store the rendered issued copy, template/legal-rule version, receipt identifier, payment/fee-event linkage, issuing actor, timestamps, and delivery evidence.
3. Deliver the worker/applicant copy through a recorded channel and retain delivery/access evidence appropriate to the approved legal workflow.
4. **Confirmed privacy design constraint:** do not automatically deliver an identical worker receipt to the employer. Use a **role-scoped rendering** or separate employer record, because the worker receipt contains applicant identity and applicant-fee information. The official business plan/legal review must still approve the exact recipient, content, delivery, and retention policy.
5. Preserve failed, bounced, declined, reissued, voided, corrected, refunded, and superseded states as linked append-only events—not edits to the issued receipt.
6. Provide agency staff with a reconciliation view that links employer/job order, applicant, placement/referral, approved fee rule, receipt(s), payment(s), delivery status, and refund/adjustment events.

## Candidate receipt data model
- **Issuer:** agency entity, license, staff/representative, source/template version.
- **Receipt identity:** receipt number, issuance timestamp, event version/state.
- **Parties:** applicant/worker; employer/job order; authorized contact; role-scoped display rules.
- **Placement context:** job title, worksite/job-order reference, employment class, compensation context.
- **Financial context:** payer, fee purpose, amount/currency, payment method/reference, approved legal/business rule version, installment/refund relationship.
- **Execution/delivery:** signer/acknowledgement (where required), rendered document hash/reference, delivery recipient/channel/time/status, accessibility/download evidence where applicable.
- **Corrections:** void/refund/correction/supersession reason, actor, timestamp, linkage to original issuance.

## Validation questions
1. Does Golden Rose issue this receipt whenever it records any applicant fee/payment, or also for employer-paid placement fees and non-fee events?
2. Who receives it today: applicant only, employer only, both, or agency file only? Which channel is used?
3. What information may the employer receive about an applicant fee, and should the employer copy be redacted or differently rendered?
4. Is the receipt number sequence controlled, and must historical paper numbering be migrated/reconciled?
5. Is applicant signature currently required in practice, and can approved electronic acknowledgement satisfy the applicable workflow?
6. What does “Purpose of Fee” mean operationally, and who may select it under the future official business plan?

## Governance reminder
Do not digitize the current wording or treat the sample as legally current. Legal wording, fields, delivery duties, and retention rules must come from approved legal documents; payer/delivery policy must come from the client’s codified official business plan.
