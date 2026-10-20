# Staff Google binding and onboarding repair

Status: Accepted source contract on October 20, 2026. Implementation candidate is locally qualified with combined full-run/focused-rerun evidence recorded in `NOTES.md`; protected CI, merge and deployment remain separate stages. The bounded owner-present account recovery is complete.

## Delivery lock

- **Staffing:** One independent developer. Fresh agent/session review and automated checks supply quality evidence, not independent-human authorization.
- **Human-visible outcome:** On October 20, the user authorized recovery of one existing staff owner account. The administrator observed a manually supplied role label in its sign-in binding, restarted onboarding using existing application commands, observed verified Google binding, and restored activation with previously confirmed MFA evidence. The user confirmed that the owner could open her account and workspace. The existing staff ID, history and 49 permissions were retained; no account was deleted. This is evidence for that account, not general pilot or production completion.
- **Gate budget:** Approved source implementation, disposable fictional local qualification and publication to `develop`. Image admission, live schema migration, service deployment, additional account changes and provider-side actions remain separate stages. The one-account recovery authorization is consumed and does not authorize further live-account changes.
- **Next executable action:** Publish the qualified source repair to protected `develop`, then read final-head CI. Do not alter the separately maintained urgent-alert/catalog work.
- **Do not regress:** Stable staff actor IDs and historical attribution; named permission enforcement; independent public/staff identity planes; Google signature/issuer/audience/expiry verification; account-level MFA policy; no-store responses; English/Spanish and accessibility parity; no raw subjects, tokens, email addresses or private URLs in source evidence; no automatic active-account linking by email; no provider reset/revocation claims; no automatic matching, ranking, eligibility, referral or placement.

## Observed incident and source evidence

The failed account page displayed `authentication_failed` while the browser reported that a Google credential was present. Administration showed active lifecycle state, MFA evidence and a recorded binding. The account's complete displayed version sequence showed creation, email addition, activation and two administrator corrections, without the automatic verified-email-binding event.

Historical source at `bae8e01` required an administrator-supplied provider subject at creation. Email onboarding was added in `6036b6b`; the email-management path in `2c15d73` preserved a nonpending subject when adding an existing account's missing email. The incident record was consistent with that legacy path.

Implementation baseline: protected `develop@f8b9ee8` includes merged PR #188. The branch was fetched and rebased before implementation qualification. That merge says nothing about a subsequent runtime deployment. Planning uses its isolated checkout and does not modify the other session's branch.

Incident baseline source (superseded by this implementation):

- `src/golden_rose/application/staff_account_lifecycle.py`: accepts nonblank subject text; preserves a legacy subject when first adding email; bundles identity with access correction; binds only an exact verified email on a suspended pending account.
- `src/golden_rose/persistence/staff_accounts.py`: stores exact subjects and performs the restricted pending-email lookup; access correction rewrites subject/email alongside role and MFA.
- `src/golden_rose/auth/staff_oidc.py`: verifies the signed Google credential before extracting subject and verified email.
- `apps/web/src/staffAccounts/StaffAccountAdmin.tsx`: labels any subject without the pending prefix as a recorded binding; form initialization and correction submission round-trip the subject.
- `src/golden_rose/api/staff/schemas.py` and `apps/web/src/api/staffAccountClient.ts`: account responses expose subjects and correction requests submit them.
- `migrations/versions/0010_staff_accounts.py`, `0016_staff_google_email.py`, `0017_staff_signin_email_mgmt.py`, `0018_staff_account_correction_authority.py`: uniqueness, lifecycle/MFA constraints, audit-event shapes and runtime column authority must remain coherent.

## Failure mechanism

An arbitrary nonblank identifier can pass validation, avoid the pending-prefix activation check, and receive a binding label without Google proof. Adding a correct email and allocating permissions does not repair that identifier. A later verified credential whose subject differs will not find the account, and the pending-email fallback deliberately excludes an already active/bound account. The generic authentication error then hides the distinction between token failure and account lookup failure.

The live recovery confirmed that replacing the manual placeholder with the ordinary verified Google binding restored access. It did not establish that every authentication error has this cause.

## Accepted contracts

### 1. Ordinary account creation accepts email, never a manual subject

Normal staff-admin creation requires the intended Google sign-in email and creates a suspended pending account. The server derives pending storage values. Remove the subject field from ordinary UI and API requests; reject an attempted subject injection rather than silently accepting it. Normalize case/outer whitespace only; do not invent alias or mailbox equivalences.

The operator-controlled first-owner bootstrap remains a separate, explicitly authorized path. It must not become a normal account-management override or a way to assert Google verification.

### 2. Separate access administration from sign-in administration

Introduce an access-only request/service that accepts display name, role, named permissions, expected version and reason. It never accepts or rewrites subject, sign-in email, binding evidence or MFA state. Reject forbidden identity fields. The normal permission form uses only this contract.

Close the corresponding legacy correction path for identity mutation. Keeping an old endpoint that can write arbitrary subjects would leave the design gap open even after removing the UI field. Route any retained compatibility behavior through the same invariants; old requests must fail safely when they attempt unsupported identity changes.

### 3. Record binding provenance explicitly

Add durable binding state and a nullable verification timestamp through a new additive migration after the actual Alembic head. The states are `pending`, `legacy_unverified` and `google_verified`; final names can follow repository conventions.

- Only the server path that has verified the credential's signature, issuer, audience, expiry and subject may set `google_verified` and its timestamp.
- A manual value, an MFA checkbox, successful activation, an administrator reason or a nonpending prefix is not verification evidence.
- Existing pending records migrate to `pending`; other existing records migrate to `legacy_unverified`, never automatically to `google_verified`. Do not infer proof from free-text history or identifier appearance.
- Preserve existing active accounts' exact-subject plus MFA session behavior during transition. A valid credential that exactly matches the current subject of an active or suspended, nondeprovisioned legacy account can transactionally record verified provenance. Recording proof does not change lifecycle, MFA or permissions: suspended accounts still receive no staff session, but can subsequently complete authorized activation. This avoids both mass owner lockout and a circular verification/activation requirement for suspended legacy accounts.
- For provenance promotion, lock and re-read the current row before comparing the verified subject, state and version. Atomically write proof, the new version and the audit event. A concurrent restart, subject change or deprovisioning invalidates the earlier lookup; never promote a stale binding or resurrect a deprovisioned account.
- A legacy record cannot receive a new ordinary activation solely because its identifier is nonpending. It needs verified binding or the separately controlled bootstrap procedure. Do not expand access to an active legacy record based on email alone.
- Database constraints, service invariants and all API serializers must agree about pending state, subject representation and verification timestamps. A marker string alone is not the authority.

The API returns safe binding status and verification metadata for routine administration; it no longer exposes raw subjects in ordinary account list/detail/session responses. Update strict frontend parsers and the API contract together.

### 4. Provide an explicit restart-Google-onboarding command

Proposed action: `Restart Google sign-in` on an existing account, backed by a dedicated audited command. It preserves staff ID, operational attribution, existing permission grants and historical evidence while atomically clearing prior binding proof, setting the email's pending identity, suspending access and clearing MFA confirmation for deliberate reactivation.

Require a dedicated named permission, expected version, required reason and immutable command identity. Reject self-reset and deprovisioned targets. Do not grant the new permission automatically to all existing accounts in a migration; make its availability and explicit provisioning part of the owner access profile and rollout packet. An ordinary access editor must not be able to grant this recovery permission to themselves or another account unless they hold the authority to grant it; enforce that in the service, not only in preset visibility. Establish the first authorized recovery grant through the separately approved operator/bootstrap provisioning path, without silently distributing it to existing accounts. The same solo maintainer may use an already authorized separate admin account; no fictional second-human quorum is required.

Apply that grant guard to account creation, access-only correction, retained legacy correction, role/profile expansion and temporary delegation. Adding recovery authority requires the grantor to hold that authority and the applicable account-management grants; a target's `owner` role label is insufficient. Denied grants roll back account, permission and audit writes together. The current self-escalation guard alone is insufficient because it does not prevent provisioning a more powerful second account.

Support resetting the existing correct email. Do not require a fake temporary email or deletion/recreation to work around the current unchanged-email rejection. Email changes use this same guarded reset semantics; permission changes never do.

The reset command needs transactional replay protection: identical command/actor/target/payload retries return the original result without resetting a newly rebound account, while changed-payload command reuse is rejected. Introduce an appropriate durable receipt/fingerprint and uniqueness constraint if current lifecycle-event storage cannot provide that guarantee. It must not store raw credential material. Serialize reset and first-binding operations with row locks and expected versions.

Do not label this as provider sign-out, token revocation, password reset or a guaranteed fresh Google authentication. A still-valid Google credential can establish a pending binding; clearing Golden Rose browser state does not force Google to reauthenticate.

### 5. Make onboarding and diagnostics understandable

Display distinct bilingual states: waiting for Google sign-in; Google identity verified and awaiting activation; active with verified binding; and legacy binding requiring verification. Avoid claiming successful application sign-in merely because a browser token exists. Confirm the staff-session endpoint before showing application access as established.

Preserve minimized unauthenticated errors. Do not disclose whether a named email has an account. Offer an authenticated account-manager diagnostic that reports safe state and binding-provenance facts, and, where a controlled verified-credential comparison is available, a match/no-match result. Never expose the subject or token in a support screen, log, screenshot or source artifact.

Audit explicit event types for binding restarted, binding verified and access updated. Do not overload a free-text `Account corrected` event as the only evidence of identity verification. Update event-type/version constraints and safe history labels together.

## Delivery and acceptance

The bilingual [staff onboarding and diagnostics guide](../security/staff-google-onboarding.md) describes the intended manager/person workflow and uncertain-result handling. It becomes operational guidance only after the separately approved rollout.

Treat the coherent repair as one accepted outcome, with internal test-first implementation steps. Split PRs only if schema/API/UI compatibility requires it; do not deploy a half-migrated boundary. Existing applied migrations remain byte-for-byte unchanged.

Required regression evidence:

1. A role label/email/manual subject cannot be installed by ordinary creation or either current/legacy correction endpoint.
2. Permission/display-name updates preserve subject, email, binding provenance and MFA; forged identity fields fail without partial grants or audit writes.
3. A pending exact verified-email sign-in records Google provenance and stays suspended until authorized activation; unrelated email, missing verified email and invalid tokens cannot bind.
4. Activation requires verified provenance plus confirmed account-level MFA; absent Google `amr` does not reinstate the superseded token-level MFA requirement.
5. Existing active legitimate accounts retain exact-subject access through migration. Suspended legitimate legacy accounts can acquire exact-subject verified evidence while remaining denied a session, then complete authorized activation. Wrong subjects still fail even when an email matches. Proof promotion cannot overwrite a concurrent reset/deprovisioning or use an old row version.
6. Same-email onboarding restart preserves staff ID, history, grants and operational references; denies self/deprovisioned/unauthorized/stale requests; exact retries do not reset a subsequently rebound account. Access editors lacking recovery-grant authority cannot manufacture it through self-correction, another account, a preset, or temporary delegation.
7. Concurrent sign-in/reset/email-change attempts cannot bind the wrong account, bypass suspension or leave partial receipts/evidence. No subject or email collision admits an unintended account.
8. Migration tests preserve populated historical data, cover required runtime DB authority and constraints, and define downgrade refusal when new evidence cannot be represented safely.
9. Strict API/client tests reject raw-subject responses and forbidden identity inputs. English/Spanish UI tests cover the full onboarding/recovery sequence, accessible status/errors and uncertainty/retry handling.
10. Synthetic local integration/browser evidence covers creation, binding, activation, access edit, recovery and reload. Provider-side factor/reset/session-revocation behavior is not claimed.

Use the repository's focused lifecycle/API/persistence/migration tests first, then applicable backend quality gates and `npm --prefix apps/web run verify`, fresh agent review, `git diff --check` and redacted secret scans. Broader CI and protected merge remain publication stages. A later operator-held deployment packet must separately authorize schema/image/service changes and include continuity for existing named staff accounts plus bounded post-deploy acceptance.

## Current completion boundary

- Complete: one explicitly authorized owner-present recovery with preserved account/history/grants and user-confirmed workspace access.
- Complete: source-backed failure analysis, fresh design review and user acceptance of this identity/schema contract.
- Implemented candidate: email-only normal creation; access-only correction; explicit pending/legacy/verified provenance; safe diagnostics; same-email restart with immutable receipt replay; durable recovery-grant controls; restricted migration and downgrade behavior.
- Qualified: focused regressions, combined backend coverage, full frontend verification, final fresh source reviews and fictional production-build browser checks. `NOTES.md` records exact results and local test-harness limitations; protected CI is separate.
- Pending: protected merge and separately authorized migration/image/service rollout with existing-account continuity and bounded staff acceptance.
- No account purge, new live staff account, cloud mutation, provider-side mutation or broad live-data action accompanies this source repair.
