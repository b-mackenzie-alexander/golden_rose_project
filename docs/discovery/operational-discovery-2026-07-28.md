# Operational Discovery — Office Workflow, Portal Need, and Runtime Constraints

**Status:** Beatrice-reported office observations and proposed direction; validation pending
**Recorded:** 2026-07-28

## Observed / reported operating constraints

### Office environment
- Four people work in the office, including the client-facing agency representative.
- Staff use aging HP all-in-one desktops that reportedly freeze even under light use.
- The product therefore cannot rely on office devices for bulk processing or long-running local work.

### Current intake and assignment workflow
- Workers visit the agency, complete paper forms, and staff manually re-enter those forms into Trello.
- Hiring parties contact the agency through phone, WhatsApp, email, and sometimes outside normal office hours.
- Job requests are placed in Google Calendar to track date-specific availability.
- Staff use separate workbooks on different computers; no centralized, shared operational system is established.
- Workers may wait in the office while staff sort assignments, then receive paper contracts and receipts before being dispatched—even when a job is close to the worker’s home.
- Staff use Google Maps to identify proximity between workers and hiring locations.

## Product direction proposed by Beatrice

### Employer portal
Allow a hiring party to register, authenticate, establish and verify an account, submit business/request details, request workers, and view agency-account status, expected worker hours, and payment information.

### Worker portal
Allow a worker to register, authenticate, submit required details, and complete an identity-verification process appropriate to the validated business and legal requirements.

### Agency workspace
Provide a role-controlled agency dashboard to review verified accounts, manage requests and availability, create/confirm assignments, generate applicable documents, and make worker–job matches.

### Mapping / proximity capability
A possible final-build heat map could assist placement decisions. It must be separately scoped: location precision, purpose, consent, retention, visibility, and security controls are not yet defined. Defaulting to least-precise data necessary is important because worker/home locations are sensitive.

## Architecture implications
- Favor a cloud-hosted, browser-based system with server-side processing and asynchronous/background work; the office hardware should need only a modern browser.
- Set a low-end-device usability/performance budget and test on constrained hardware/network conditions.
- Centralize authoritative operational data rather than treating Trello, Google Calendar, or individual workbooks as the system of record.
- Design distinct employer, worker, and agency-staff workflows over a shared, access-controlled data model.

## Security clarification and baseline
- Require TLS/HTTPS for data in transit and encryption at rest for sensitive stored data, backed by managed keys, access controls, logging, backups, and recovery procedures.
- Do not casually claim “end-to-end encryption”: true E2EE normally prevents the application server from reading protected content and may conflict with centralized matching, document generation, compliance checks, and audit workflows. Determine the actual threat model first.
- Establish role-based, least-privilege access; account verification, identity-proofing, sensitive-document access, staff actions, and exports require explicit authorization and audit trails.
- Identity verification is a high-risk integration and data-handling decision. Define purpose, verification method/vendor, consent, evidence retained, retention/deletion, failure handling, and manual-review path before collecting identity documents.

## Validation backlog — Week 1
1. Map the current worker intake, employer request, assignment, payment, document, and exception workflows end to end.
2. Inventory Trello, Google Calendar, workbooks, paper forms, and Google Maps usage; identify ownership, data fields, data quality, and migration/export feasibility.
3. Confirm the roles, account-verification requirement, identity-proofing need, and permissions for workers, hiring parties, staff, and owners.
4. Define the minimum assignment-matching inputs, including whether a map is necessary for V1.
5. Capture device/browser/network constraints and decide what client-side capability is safe to require.
6. Produce a data inventory and threat model before choosing cloud, identity, mapping, notification, or document-storage vendors.

## Evidence posture
These are reported field observations and a proposed architecture, not yet validated requirements or an approved design. No direct assessment of Trello’s configuration, current hardware specifications, data contents, Google Calendar/workbook structure, or mapping practices has been performed.
