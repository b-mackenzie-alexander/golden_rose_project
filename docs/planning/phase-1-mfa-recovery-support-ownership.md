# Phase 1 MFA, Account Recovery, and Support Ownership Contract

**Status:** Accepted production security and operating baseline
**Accepted:** 2026-08-03
**Decision owner:** Beatrice, technical delivery owner
**Scope:** Phase 1 staff-plane authentication, account lifecycle, recovery, session controls, access review, and support ownership

## Decision

Every Phase 1 staff-plane and Platform Administrator account requires individual attributable identity, mandatory MFA, controlled recovery, prompt suspension/deprovisioning, and named support ownership before access to live data. Authentication establishes identity only; application authority remains controlled by `docs/planning/phase-1-staff-permission-matrix.md`.

This baseline is approved for production policy and implementation. Production use still requires named personnel, identity-provider qualification, configured and tested controls, initial data-classification approval, rehearsed recovery/support procedures, and the separate production-data and promotion gates. This contract does not itself authorize cloud provisioning, production deployment, live-data admission, or vendor selection.

## Identity and account rules

1. Every human receives an individual account. Shared staff, Owner, support, recovery, and emergency accounts are prohibited.
2. Staff-plane identities remain separate from future worker/employer public identities and use a distinct identity client, session/token audience, endpoint/credential boundary, and authorization path.
3. A person performing Platform Administrator work uses a separate privileged identity from any ordinary staff account they also hold.
4. Identity-provider or cloud roles never silently create Owner, Manager, Operations Staff, exact-address, or other business authority.
5. Account activation requires:
   - attributable Owner approval;
   - an assigned application role and named permissions;
   - completed MFA enrollment;
   - a confirmed recovery method;
   - acceptance of applicable access expectations; and
   - successful identity/security audit evidence.
6. Accounts are suspended promptly after departure, loss of authorized need, or suspected compromise. Historical records and actor attribution are preserved; operational identities are not destructively deleted merely to remove access.
7. Account creation, role assignment, recovery, suspension, reactivation, and deprovisioning are distinct attributable operations.

## MFA policy

MFA is mandatory before every staff-plane or Platform Administrator account can access live data or a production privileged path.

### Accepted factor order

1. **Passkey or hardware security key:** preferred. Every Owner, delegated Manager with recovery/access-administration authority, recovery approver, and Platform Administrator must enroll at least one phishing-resistant factor.
2. **Authenticator-app TOTP:** acceptable fallback when a supported passkey/security key is unavailable.
3. **Single-use recovery codes:** recovery only; never an ordinary login factor.
4. **SMS, voice, or email codes:** not accepted as the ordinary primary MFA method. Any vendor-specific emergency fallback requires a separate documented risk acceptance, bounded use, monitoring, and review.
5. **Knowledge-based security questions:** prohibited.

### Enrollment and factor lifecycle

- Each person must enroll two independent recovery-capable methods before production activation.
- Recovery codes are generated once, displayed only to the account holder, stored outside the application and ordinary email/chat, and invalidated after use or regeneration.
- MFA secrets, enrollment QR material, recovery codes, authentication tokens, and complete factor identifiers must not appear in application logs, audit-event reason text, tickets, chat, or source control.
- Adding, removing, replacing, or resetting a factor revokes existing sessions and produces attributable security evidence.
- A lost, stolen, or potentially copied factor triggers prompt factor revocation and compromise review; it is not merely renamed or left active as a fallback.

## Step-up authentication

Recent MFA reauthentication is required for:

- adding, removing, replacing, or resetting MFA factors;
- account recovery and recovery-code regeneration;
- granting, changing, or revoking roles and delegated permissions;
- changing Owner or Platform Administrator entitlement;
- activating break-glass access;
- changing identity/security configuration; and
- future privileged actions expressly designated by an approved security contract.

Ordinary employer-demand work should not repeatedly prompt for MFA after a valid staff session. Exact-address access remains separately permission-controlled and attributable, but it does not require MFA for every reveal unless pilot evidence and a later approved control require it.

## Session baseline

Initial production policy values are configurable and must be verified against the selected provider and pilot usability:

| Path | Inactivity timeout | Absolute session limit |
|---|---:|---:|
| Ordinary staff application | 30 minutes | 12 hours |
| Privileged Platform Administrator path | 15 minutes | 4 hours |

Password/factor changes, assisted recovery, account suspension, confirmed/suspected compromise, role removal, and deprovisioning revoke affected sessions and tokens promptly. Refresh/session-token behavior must not silently extend access beyond the applicable absolute limit.

## Recovery authority matrix

| Recovery case | Required approval | Technical execution | Prohibition |
|---|---|---|---|
| Operations Staff locked out | Owner or explicitly delegated Manager | Authorized identity-support operator | A Manager cannot approve their own recovery. |
| Manager locked out | Owner | Authorized identity-support operator | Another Manager cannot restore or broaden the role without Owner authority. |
| Owner locked out | Designated backup Owner/recovery approver plus independent technical executor | Platform Administrator or approved identity-support operator | The locked-out Owner cannot be the sole approver of their own recovery. |
| Platform Administrator locked out | Designated technical recovery approver with Owner notification/review | Separate authorized technical executor or qualified provider recovery process | The affected Platform Administrator cannot approve and execute their own recovery alone. |
| Suspected compromise | Owner/security owner authorizes containment; immediate technical suspension may occur when delay is unsafe | Platform Administrator | Recovery cannot restore prior sessions or unreviewed permissions automatically. |
| Lost factor while another valid factor remains | Recent step-up authentication; privileged-role changes also notify the applicable recovery owner | Account holder through controlled self-service | Self-service cannot bypass privileged-role review. |

Recovery verifies the person using pre-registered approved evidence. The following are insufficient by themselves:

- a request from the same email account being recovered;
- caller-ID or possession of a known phone number;
- personal trivia or security questions;
- recognition by a technical administrator;
- an informal email/chat message; or
- possession of an expired session.

## Assisted recovery workflow

Every assisted recovery must:

1. Create a recovery request recording requester, affected account, reason, and time.
2. Suspend or restrict the account immediately if compromise is suspected.
3. Verify the requester through approved pre-registered evidence.
4. Obtain the independent approval required by the recovery matrix.
5. Reset only affected authentication factors; do not alter operational records or invent business permissions.
6. Reconfirm the expected role, named permissions, and unexpired delegations against the authoritative access record.
7. Revoke existing sessions, tokens, pending recovery links, and old recovery codes.
8. Require fresh MFA enrollment before ordinary access resumes.
9. Notify the account holder and applicable Owner through an independent approved channel.
10. Record requester, verifier, approver, executor, timestamps, factor category changed, session revocation, result, and follow-up review under `docs/planning/phase-1-correction-audit-event-contract.md`.
11. Never record factor secrets, recovery codes, identity-document contents, or unnecessary personal data in audit evidence.

Recovery does not automatically restore expired delegations, precise-worksite access, break-glass access, or previously removed permissions.

## Support ownership

| Area | Primary owner | Backup/escalation | Boundary |
|---|---|---|---|
| Workflow questions and ordinary staff assistance | Owner or delegated Manager | Named backup Manager/Owner | May explain workflow and approve ordinary account requests; no infrastructure access. |
| Role, permission, onboarding, and offboarding decisions | Owner | Designated backup Owner | Business authority; a technical executor cannot invent or broaden access. |
| MFA enrollment and routine recovery approval | Owner or delegated Manager within the recovery matrix | Backup Owner | No person approves their own assisted recovery. |
| Identity-provider configuration and technical recovery execution | Platform Administrator | Named independent technical backup/provider support | Executes approved changes; no business-role authority. |
| Application availability, deployment health, jobs, and monitoring | Platform Administrator | Beatrice/project technical lead during the engagement, then named client successor | No standing operational-record access. |
| Operational-data correctness and workflow-impact decisions | Owner | Delegated Manager | Platform Administrator may diagnose technical behavior but cannot decide business meaning. |
| Security incident coordination during the engagement | Beatrice/project technical lead | Named technical backup; client Owner controls business-impact decisions | Legal/regulatory notifications remain governed by separately approved client/counsel policy. |
| Break-glass operational-data approval and review | Owner; delegated Manager only where expressly authorized | Backup Owner | Platform Administrator cannot self-authorize. |
| Vendor escalation | Platform Administrator | Project technical lead/client successor | Disclose only minimum approved diagnostic information. |
| Post-engagement support | Named client technical/support owner | Documented vendor or successor | Transfer through the final-payment and continuity handoff. |

No 24/7 support, response-time SLA, or continuous on-call service is promised by this contract. The initial pilot uses documented business-hours support plus an approved urgent-incident path. Exact support hours, contact channel, escalation targets, and response expectations must be recorded before production use.

## Access-review cadence

- During the pilot, review staff accounts, roles, delegations, precise-worksite permissions, recovery events, Platform Administrator access, and break-glass events monthly.
- After stabilization, review them quarterly unless incident/risk evidence requires greater frequency.
- Perform an immediate review after:
  - staff departure or role change;
  - suspected compromise;
  - assisted recovery of an Owner, Manager, or Platform Administrator;
  - break-glass activation;
  - client ownership/support transfer;
  - material identity-provider configuration change; or
  - unexplained privileged activity or authorization-denial pattern.
- Dormant accounts are suspended rather than retained indefinitely. The inactivity threshold remains a named client operational-policy value before production activation.
- Each review records reviewer, scope, findings, removals/corrections, unresolved exceptions, and completion time.

## Incident and support handling boundaries

1. The Owner controls business-workflow, account-authority, data-meaning, and service-acceptance decisions.
2. The Platform Administrator controls approved technical diagnosis, containment, recovery execution, and provider escalation within the permission and break-glass boundaries.
3. Beatrice/project technical lead coordinates security incidents during the engagement; a named client successor must accept this responsibility at handoff.
4. Immediate technical containment may suspend accounts/sessions or disable a vulnerable path when delay is unsafe. It does not authorize deletion, broad extraction, business-state changes, or unapproved notification statements.
5. Support artifacts use minimum necessary data and must not contain credentials, MFA material, raw secrets, unrestricted record dumps, or unnecessary precise location/personal data.
6. Formal breach, legal, regulator, worker, or employer notification obligations are not defined here and require separately approved client/counsel policy.

## Provider qualification boundary

This contract is provider-neutral. GCP Identity Platform remains a candidate, not an accepted vendor selection. Before selection, a documented technical evaluation must verify that the exact configuration supports:

- required passkey/security-key and fallback factors;
- staff-only identity separation;
- session and token revocation;
- the accepted inactivity/absolute session controls or an approved compensating design;
- controlled assisted recovery and recovery-code behavior;
- attributable identity events and safe log contents;
- administrative and business-authority separation;
- provider-side emergency recovery;
- export/handoff continuity;
- pricing, availability, and support expectations; and
- prevention of public-to-staff role promotion.

A provider limitation must be recorded and reviewed; implementation must not silently weaken this accepted baseline.

## Implementation and production-readiness verification

Before production activation, tests and rehearsals must demonstrate:

- mandatory MFA and required factor enrollment for every staff/privileged role;
- phishing-resistant factor enforcement for privileged/recovery roles;
- prohibited-factor and shared-account rejection;
- staff/public identity and token-audience separation;
- step-up authentication for every listed privileged action;
- inactivity and absolute session expiry;
- revocation after factor change, recovery, suspension, compromise, role removal, and deprovisioning;
- each recovery-matrix path, including self-approval denial and independent Owner/Platform Administrator recovery;
- no automatic restoration of expired or removed permissions;
- safe audit evidence without secrets/recovery material;
- monthly pilot access-review procedure;
- ordinary and urgent support routing;
- Platform Administrator denial of standing operational-data/business-role access; and
- provider/export/handoff continuity adequate to avoid single-person dependency.

## Named production-readiness gates

Before production activation, record:

- primary agency Owner;
- backup Owner/recovery approver;
- Managers allowed to approve Operations Staff recovery;
- technical recovery executor and independent technical backup;
- precise-worksite permission recipients under the permission matrix;
- supported business hours and urgent support contact path;
- post-engagement client technical/support successor;
- dormant-account suspension threshold;
- selected and qualified identity provider/configuration;
- initial staff cohort and approved data classification; and
- evidence that recovery, deprovisioning, session revocation, access review, and support escalation were rehearsed.

## Revisit triggers

Revisit this contract before adding public identities, passwordless-only operation, biometric policy, SMS/email emergency fallback, federation with a client identity system, mobile/offline access, 24/7 or SLA-backed support, external helpdesk access, additional privileged roles, production handoff, or any identity-provider limitation that cannot meet the accepted controls.