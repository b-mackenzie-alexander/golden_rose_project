# ADR-0018 — Staff Google binding provenance and guarded recovery

- **Status:** Accepted for source implementation, October 20, 2026.
- **Staffing:** One independent developer; fresh agent/session review and automated checks provide quality evidence, not independent-human authorization.
- **Human-visible outcome:** One separately authorized owner-present recovery restored the existing account; the user confirmed workspace access. The permanent repair is a source candidate.
- **Gate budget:** Source, disposable fictional local validation and a PR to `develop`. No live migration, deployment, additional account action, bootstrap provisioning or provider mutation follows.
- **Next executable action:** Complete source qualification and protected PR review; prepare a separate rollout packet after merge.
- **Do not regress:** Named permissions, stable staff IDs/history, verified credentials, account-level MFA, separate identity planes, no-store safe responses, bilingual/accessibility parity and human staff decisions.

## Context

An existing account held a manually supplied role label as its external subject. The administration UI called that a recorded binding, and activation accepted it without evidence that Google had verified the identity. Later adding the correct email and updating permissions retained the invalid subject. Exact-subject sign-in then failed safely, while generic diagnostics concealed the onboarding problem.

The accepted [repair contract](../planning/2026-10-20-staff-google-binding-repair.md) closes this source gap without deleting durable accounts or automatically linking active accounts by email.

## Decision

1. Ordinary creation requires the intended Google email and creates suspended pending onboarding. The server derives its pending marker. Ordinary requests cannot supply a subject.
2. Access editing accepts display name, role, named grants, version and reason. It never writes sign-in email, subject, provenance or MFA. Retained aliases enforce the same strict contract.
3. Persist `pending`, `legacy_unverified` or `google_verified` plus a verification timestamp. Only verified credential resolution writes Google proof. Historical nonpending subjects migrate to unverified; legitimate exact-subject access continues and records proof under a lock. Suspended accounts can acquire proof but remain denied access until activation. An active/pending anomaly stops migration before DDL for reviewed recovery.
4. Explicit onboarding restart supports the current email or a corrected email. It requires account-management and recovery permissions, expected version, reason and command ID. Reject self-reset and deprovisioned targets. Suspend access, clear binding/MFA proof and preserve staff ID, history, durable grants and operational references.
5. Store a fingerprint and minimized immutable result receipt in the same transaction as restart and its audit event. Exact retries return the original snapshot even after later binding/access edits; changed-payload reuse fails. Serialize identity changes with row locks.
6. Adding durable recovery authority requires the grantor's own durable recovery authority. Temporary holders cannot manufacture a permanent grant through account creation/access editing or redelegate recovery. Migration distributes no new permission; initial provisioning remains an explicitly authorized operator path.
7. Authenticated diagnostics show safe provenance/lifecycle/MFA facts, actionable bilingual guidance and current recovery/activation capabilities. Ordinary API responses contain no raw subjects. A received Google credential does not establish Golden Rose application access.

## Consequences and rollout

The additive `0021_staff_google_binding` migration follows the actual `0020_contact_email_fields` head; applied migrations remain unchanged. Runtime authority includes only the required account columns and receipt SELECT/INSERT. Downgrade refuses before DDL if it would discard new proof, events or receipts.

The API contract intentionally rejects old clients attempting identity mutation through access editing. Schema, backend and frontend must be qualified and deployed together in a later approved packet. That packet must include existing-account continuity, active/pending preflight, explicit recovery-permission provisioning, immutable image/schema identity and bounded staff acceptance.

The application does not reset Google factors, force Google reauthentication, revoke provider sessions or delete accounts. The solo-maintainer concentration remains an accepted residual risk; review and automated checks do not create a second-human authorization claim.
