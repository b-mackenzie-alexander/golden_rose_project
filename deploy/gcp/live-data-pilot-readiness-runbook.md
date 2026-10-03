# Controlled Live-Data Staff Pilot Readiness Runbook

This runbook defines the source-controlled, value-safe evidence shape for a
later controlled staff working environment where staff may enter real worker and
employer intake records. It is not a cloud execution approval and it is not a
production-completion claim.

## Boundary

- The next working environment is a controlled live-data staff pilot, not a
  presentation environment and not a public self-service launch.
- Real worker and employer intake records may be entered only after an
  operator-held readiness record explicitly approves that scope.
- The runtime must use named staff accounts through `staff_oidc`. Shared access
  gates, presentation seeds and static operational examples must be disabled for
  this pilot.
- The pilot remains staff-only. Public worker/employer accounts, public
  portals, uploads, automated matching, ranking, eligibility, referral,
  assignment and placement remain out of scope.
- Records entered during the pilot must be treated as durable operational
  records. Teardown, destructive cleanup, export/import, current-environment
  migration and client-owned environment transition require separate approval.
- Golden Rose records recovery and session-revocation evidence only. Provider
  factor reset, token revocation, session revocation and forced logout remain
  provider-side procedures outside the application.
- Value-safe evidence in tracked source must not contain raw staff names, worker
  or employer details, private URLs, email addresses, provider subjects,
  credentials, database identifiers, plan files, state details or command
  transcripts.

## Required Evidence

Use `deploy/gcp/templates/live-data-pilot-readiness.example.json` as the
placeholder-only source template. Keep the filled JSON outside source control.
The operator-held readiness record must cover:

- the operating boundary for a controlled staff pilot
- the exact live-data scope, initially worker and employer intake records only
- staff OIDC identity readiness, named staff account readiness and MFA posture
- no-store/auth-sensitive handling
- disabled presentation seed, disabled shared gate and disabled static examples
- backup/restore posture and rollback or closeout owner
- migration/disposition posture for records created in the current environment
- data-governance basics for access, correction, retention and restricted fields
- support/escalation ownership for daily staff use
- staff working instructions and known-limit acknowledgement
- manual dashboard review acceptance before opening the pilot

Validate the filled operator-held JSON locally:

```bash
UV_CACHE_DIR=/private/tmp/golden-rose-uv-cache uv run python scripts/validate_live_data_pilot_readiness.py <operator-held-live-data-pilot-readiness.json>
```

The validator allows explicit controlled live-data admission for the staff pilot
scope. It still rejects value-unsafe evidence, private URLs, email-like values,
secret terms, presentation or example-data framing, product-completion claims,
public portal activation, automated matching/ranking/referral/placement,
provider-side recovery or revocation completion claims, data export/import,
current-environment migration, client-owned transition, repository transfer,
account creation, destructive cleanup and shared-runtime rollout claims.

## Cloud Packet Preparation

A later cloud packet should bind to the protected source commit being deployed
and should include, outside source control:

- source commit and immutable image digest
- migration revision, currently expected by application readiness
- database-authority and migration execution evidence
- staff OIDC issuer/audience/JWKS values in approved secret custody
- pre-service evidence that `staff-oidc-issuer`, `staff-oidc-audience` and
  `staff-oidc-jwks-url` Secret Manager containers already exist with enabled
  `latest` versions prepared outside Terraform; the service-stage plan must not
  be the action that creates or populates those staff identity-provider secrets
- initial named staff-account list and activation owner
- backup/restore posture and forward-recovery note
- smoke/readiness results after deployment
- staff pilot opening receipt and closeout owner

No cloud inspection, Terraform plan/apply, migration execution, service update,
runtime access change, credential rotation or live-data admission follows from
this source runbook alone.

## Stop Conditions

Stop before opening the live-data pilot if any of these are true:

- staff access is shared, anonymous or not attributable to named accounts
- staff OIDC issuer, audience, JWKS or MFA claim semantics are missing
- demo access, presentation seed data or static operational examples would be
  visible in the pilot
- staff do not have concise working instructions and an escalation path
- backup/restore, rollback/closeout or migration-disposition posture is unknown
- data-governance basics for access, correction, retention or restricted fields
  are undefined
- the pilot is being described as product completion, public launch, production
  handoff, client-owned transition or automated placement/referral authority
