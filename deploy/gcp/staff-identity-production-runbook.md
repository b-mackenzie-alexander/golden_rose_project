# Staff Identity Production Readiness Runbook

This runbook is an operator checklist for preparing Golden Rose staff personal
accounts and staff OIDC configuration before any production or live-data
admission. It is source guidance only. It does not authorize cloud mutation,
provider changes, credential rotation, production deployment, live data intake,
or a shared-runtime rollout.

## Required boundary

- Production staff sessions must use `GOLDEN_ROSE_AUTH_MODE=staff_oidc`.
- Production must not set `GOLDEN_ROSE_SYNTHETIC_STAFF_ID`.
- Production must not enable demo access or presentation seed data.
- Staff account records must exist in Golden Rose before live staff use.
- Staff MFA evidence comes from the configured identity-provider claims and is
  recorded/displayed by Golden Rose; factor reset remains a provider-side
  operation outside the application.
- Recovery and session-revocation actions in Golden Rose record evidence only.
  They do not perform provider-side account recovery, factor reset, token
  revocation, session revocation, or logout.

## Required application settings

Use approved secret/configuration delivery for actual values. Do not commit
provider URLs, client identifiers, database URLs, credentials, or project IDs.

```text
GOLDEN_ROSE_ENVIRONMENT=production
GOLDEN_ROSE_AUTH_MODE=staff_oidc
GOLDEN_ROSE_DATABASE_URL=<delivered from approved production secret>
GOLDEN_ROSE_STAFF_OIDC_ISSUER=<https issuer from approved staff identity provider>
GOLDEN_ROSE_STAFF_OIDC_AUDIENCE=<approved staff API audience>
GOLDEN_ROSE_STAFF_OIDC_JWKS_URL=<https JWKS URL from approved staff identity provider>
GOLDEN_ROSE_SYNTHETIC_STAFF_ID=<unset>
GOLDEN_ROSE_DEMO_ACCESS_ENABLED=false
GOLDEN_ROSE_DEMO_ACCESS_PASSWORD=<unset>
GOLDEN_ROSE_DEMO_ACCESS_EXPIRES_AT=<unset>
GOLDEN_ROSE_PRESENTATION_DEMO_SEED_ENABLED=false
```

## Pre-live operator checklist

1. Confirm the approved staff identity provider exposes a stable HTTPS issuer
   and JWKS endpoint.
2. Confirm the application audience value is provider-approved and environment
   specific.
3. Confirm MFA claim semantics with the provider owner before admitting live
   staff sessions.
4. Create the initial Golden Rose staff accounts while they remain suspended.
5. Activate only accounts whose provider subject and MFA evidence have been
   verified by an authorized human operator.
6. Record the provider-side recovery and session-revocation procedure in the
   operational handoff materials before production use.
7. Verify `/api/staff/v1/staff-identity-readiness` returns
   `production_staff_auth_ready: true`, `synthetic_staff_runtime_allowed: false`
   and `recovery_and_session_revocation_evidence_only: true` under the
   production OIDC configuration.

## What Golden Rose should show

The staff personal-account page should show a production OIDC identity boundary,
the current account lifecycle state, MFA evidence, active permissions and active
temporary delegations. The account administration surface should continue to
show lifecycle history and evidence entries without implying provider-side
activation, reset or revocation.

## Stop conditions

Stop before live use if any of these are true:

- Synthetic auth is configured in production.
- Demo access or presentation seeding is enabled in production.
- OIDC issuer, audience or JWKS settings are missing or unapproved.
- The MFA claim mapping has not been confirmed.
- No authorized human operator has verified the initial staff account subjects.
- Recovery/session-revocation provider procedures have not been recorded.
- The readiness endpoint reports a synthetic identity boundary.
