# Client-Owned GCP Package Runbook

This runbook describes the value-safe source package inputs needed before a
later client-owned Golden Rose deployment. This is not an approval to inspect or
mutate cloud resources, deploy production, admit live data, rotate credentials,
activate provider-side staff identity, or create shared runtime access.

## Boundary

- This repository currently contains the historical private synthetic develop
  infrastructure contract and production-shaped application code.
- A client-owned deployment requires a separate explicit approval packet,
  environment-specific variables, provider-side staff identity setup, and
  live-data gates.
- The example files under `deploy/gcp/templates/` are placeholders only. They
  are not secrets, not Terraform plans, not production values, and not complete
  authority to deploy.
- `deploy/gcp/templates/client-production-policy.example.json` is a source
  review manifest for later package checks. It is not a Terraform plan and does
  not authorize cloud execution.
- `deploy/gcp/templates/client-production-handoff.example.json` is a
  placeholder-only template for later value-safe handoff evidence. It is not a
  production evidence record and must not be filled with private URLs, staff
  identities, secret payloads, state details or command transcripts in source
  control.
- `deploy/gcp/templates/client-production-readiness-checklist.example.json` is a
  placeholder-only checklist for deciding whether the deployable package is
  reviewable. It is not a production activation checklist and must preserve the
  separate-approval boundary for deployment, live data and shared runtime.
- `deploy/gcp/templates/client-production-package-index.example.json` is a
  placeholder-only index of the source package artifacts and offline validators.
  It is not a production packet, release attestation, live evidence record or
  approval to execute cloud commands.
- Real project IDs, billing IDs, principals, service URLs, database URLs,
  identity-provider URLs, JWKS URLs, secret names, passwords, tokens, state
  buckets, support contacts, and owner emails must remain in approved private
  operator custody until a scoped production packet exists.

## Required Inputs

An operator must identify these inputs outside source control before any later
client-owned deployment packet can be considered:

- Client GCP project ID and region.
- Billing account and budget owner.
- Terraform state backend bucket or approved state lineage.
- Artifact Registry repository and immutable admitted image digest.
- Workload Identity Federation provider and repository subject restrictions.
- Runtime, migration, deployer, verifier, and artifact-reader service accounts.
- Cloud SQL instance posture, backup window, PITR choice, and restore owner.
- Secret Manager secret names for runtime database URL, migration database URL,
  staff OIDC issuer, audience, JWKS URL, and any future provider adapter
  material.
- Staff identity provider issuer, audience, JWKS URL, MFA claim semantics, and
  recovery/session-revocation provider runbook owner.
- Initial staff account list and authorized human who verifies provider
  subjects before activation.
- Monitoring, alerting, log-retention, incident, rollback, support, and
  acceptance owners.
- Signed image, SBOM and provenance admission records for the immutable digest
  that a client-owned environment would consume.

## Source Package Checks

Before a production packet is drafted, run the local package validator:

```bash
UV_CACHE_DIR=/private/tmp/golden-rose-uv-cache uv run python scripts/validate_deployable_package.py
```

The validator is intentionally static. It checks that placeholder-only package
templates remain present, that production app configuration uses staff OIDC
instead of synthetic/demo settings, and that the runbook keeps private
develop/demo values out of the client-owned package materials. It does not
authenticate to GCP, read Terraform state, inspect Cloud Run, create secrets,
or verify provider-side identity.

The package validator also requires the placeholder handoff evidence template.
When a later approved production packet has value-safe handoff evidence, keep
the filled JSON outside source control and validate it locally:

```bash
UV_CACHE_DIR=/private/tmp/golden-rose-uv-cache uv run python scripts/validate_client_handoff_evidence.py <operator-held-handoff.json>
```

The handoff evidence validator checks that source commit, migration revision,
immutable image digest, signed image/SBOM/provenance evidence, plan review,
database-authority receipt, smoke/readiness results, rollback or
forward-recovery note, operational owners and owner acceptance are present in a
value-safe shape. It does not authenticate to GCP, inspect cloud resources,
activate identity, run smoke probes, perform backup/restore, execute provider
recovery or revocation, deploy production, or admit live/client data.

When a later operator wants a single value-safe package readiness summary, keep
the filled checklist outside source control and validate it locally:

```bash
UV_CACHE_DIR=/private/tmp/golden-rose-uv-cache uv run python scripts/validate_client_readiness_checklist.py <operator-held-readiness.json>
```

The readiness checklist validator requires the package artifacts, staff
identity, Terraform plan review, artifact admission, handoff evidence and
operations-owner sections to be marked ready with value-safe evidence. It also
requires manual accessibility, fluent Spanish and staff workflow acceptance to
remain `separate-review-required`, and requires production deployment, live-data
admission and shared-runtime rollout to remain not executed without separate
approval.

When a later operator wants one value-safe index of the reviewed package source
artifacts and their offline validators, keep the filled package index outside
source control and validate it locally:

```bash
UV_CACHE_DIR=/private/tmp/golden-rose-uv-cache uv run python scripts/validate_client_package_index.py <operator-held-package-index.json>
```

The package index validator requires the runbooks, placeholder templates and
offline validator scripts to be marked reviewed with value-safe evidence. It
also requires the validator commands to remain offline/local, manual
accessibility, fluent Spanish and staff workflow acceptance to remain
`separate-review-required`, and production deployment, live-data admission and
shared-runtime rollout to remain not executed without separate approval.

## Later Plan Review Policy

A later approved production packet must review Terraform plan output against the
placeholder policy manifest before any apply authority is considered. The packet
must fail closed on delete/replace actions, public SQL exposure, broad IAM,
missing immutable image digest, missing staff identity configuration, demo access
or presentation seed configuration in production, and unqualified secret
payloads. The policy also requires signed image/SBOM/provenance evidence,
database-authority evidence, backup/restore ownership, and monitoring, incident
and support owners.

When an approved packet produces an operator-held Terraform plan, convert that
private plan to JSON outside source control and run the offline plan validator:

```bash
terraform show -json <operator-held-plan.tfplan> > <operator-held-plan.json>
UV_CACHE_DIR=/private/tmp/golden-rose-uv-cache uv run python scripts/validate_client_production_plan.py <operator-held-plan.json>
```

Do not commit the `.tfplan` file, plan JSON, private variable files, state files
or command transcripts. The validator reads only the local JSON file. It does
not authenticate to GCP, inspect Terraform state, create secrets, activate the
staff identity provider, execute provider-side recovery or revocation, apply
infrastructure, deploy production, or admit live/client data.

## Stop Conditions

Stop before drafting or executing any production deployment packet if any of
these are true:

- A template contains a concrete project ID, billing ID, service URL, email,
  private principal, credential, token, database URL, identity-provider URL, or
  JWKS URL.
- A production app template enables synthetic auth, demo access, presentation
  seed data, or an embedded staff actor.
- A runbook asks an operator to apply Terraform, create Secret Manager payloads,
  deploy Cloud Run, rotate credentials, activate live staff identity, or admit
  live/client data without a separate approval packet.
- A package policy omits delete/replace, public SQL, broad IAM, immutable
  digest, staff OIDC, demo-access, unqualified-secret, signed-artifact,
  database-authority, backup/restore or support-owner checks.
- Staff recovery or session-revocation wording implies Golden Rose performs
  provider-side factor reset, provider-side session revocation, token
  revocation, or forced logout.
- Required human operators and client-owned support contacts have not been
  named outside source control.

## Later Packet Evidence

A later approved production packet should produce value-safe handoff evidence:

- placeholder structure from
  `deploy/gcp/templates/client-production-handoff.example.json`,
- optional package-readiness summary structure from
  `deploy/gcp/templates/client-production-readiness-checklist.example.json`,
- optional package-source index structure from
  `deploy/gcp/templates/client-production-package-index.example.json`,
- source commit and immutable image digest,
- migration revision,
- state backend lineage identifier,
- database-authority receipt,
- staff identity readiness result,
- smoke/readiness results,
- rollback or forward-recovery note,
- owner acceptance checklist,
- support and incident-routing owner confirmation.

Do not place raw private URLs, secret payloads, staff emails, staff provider
subjects, client data, access tokens, plan files, state files, or command
transcripts in tracked source.
