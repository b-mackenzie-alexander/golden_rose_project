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
- `deploy/gcp/templates/client-production-backup-restore.example.json` is a
  placeholder-only template for later backup/restore rehearsal evidence. It is
  not a backup receipt, not a restore receipt, not proof of recovery execution,
  and not approval to run destructive recovery or use live/client data.
- `deploy/gcp/templates/client-production-operations-readiness.example.json` is
  a placeholder-only template for later monitoring, alerting, log-retention,
  incident-routing and support-routing evidence. It is not an alerting
  configuration, not an incident contact list, not proof that contact channels
  have been activated, and not approval to mutate cloud monitoring resources.
- `deploy/gcp/templates/client-production-runtime-lifecycle.example.json` is a
  placeholder-only template for later dependency, GitHub Actions runtime,
  runner-image, language-runtime and container-base-image lifecycle review
  evidence. It is not a dependency update, not a runner or image rollout, not a
  production runtime change, and not approval to mutate CI or deployment
  resources.
- `deploy/gcp/templates/client-production-data-governance.example.json` is a
  placeholder-only template for later data classification, retention, deletion,
  export, disclosure and restricted-history-recipient governance evidence. It
  is not live-data admission, not a data export, not a disclosure approval, not
  destructive deletion execution and not approval to mutate client records.
- `deploy/gcp/templates/client-production-copy-approval.example.json` is a
  placeholder-only template for later legal/business-controlled copy inventory,
  legal review, business review, translation review and controlled-copy owner
  evidence. It is not legal approval completion, not production copy
  activation, not public publishing and not approval to change production text.
- `deploy/gcp/templates/client-production-manual-review.example.json` is a
  placeholder-only template for later manual keyboard, screen-reader, reflow,
  contrast, fluent-Spanish and bilingual-parity review evidence. It is not a
  public accessibility claim, not a certification, not a translation
  certification, not production deployment and not approval to publish.
- `deploy/gcp/templates/client-production-training-acceptance.example.json` is
  a placeholder-only template for later staff training, support escalation,
  staff workflow acceptance, management-model review, working-environment
  feedback, data-migration planning, repository-stewardship and known-limits
  evidence. It is not support-channel activation, not live-data admission, not
  current-environment migration execution, not business repository transfer,
  not GitHub account creation, not production deployment and not a declaration
  that the product is complete.
- `deploy/gcp/templates/live-data-pilot-readiness.example.json` is a
  placeholder-only template for a controlled staff working environment where
  staff may enter real worker and employer intake records after explicit
  operator-held approval. It is not client-owned environment transition, not
  export/import execution, not support-channel activation, not production
  completion and not public portal activation.
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
- Controlled live-data staff pilot readiness evidence if staff have started or
  will start entering real worker and employer intake records before a
  client-owned environment transition.

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
identity, Terraform plan review, artifact admission, handoff evidence,
backup/restore rehearsal, operations readiness and operations-owner sections to
be marked ready with value-safe evidence. It also requires runtime lifecycle
review and data governance review to be marked ready with value-safe evidence,
copy approval review, manual accessibility/language review and training or
workflow acceptance review to be marked ready with value-safe evidence. Its
remaining manual-acceptance boundary must be empty once that validator-backed
training evidence exists, and production deployment, live-data admission and
shared-runtime rollout must remain not executed without separate approval.

When a later operator wants one value-safe index of the reviewed package source
artifacts and their offline validators, keep the filled package index outside
source control and validate it locally:

```bash
UV_CACHE_DIR=/private/tmp/golden-rose-uv-cache uv run python scripts/validate_client_package_index.py <operator-held-package-index.json>
```

The package index validator requires the runbooks, placeholder templates and
offline validator scripts to be marked reviewed with value-safe evidence. It
also requires the validator commands to remain offline/local, its remaining
manual-acceptance boundary to be empty once training acceptance evidence is
validator-backed, and production deployment, live-data admission and
shared-runtime rollout to remain not executed without separate approval.

When a later approved production packet records value-safe backup/restore
rehearsal evidence, keep the filled JSON outside source control and validate it
locally:

```bash
UV_CACHE_DIR=/private/tmp/golden-rose-uv-cache uv run python scripts/validate_client_backup_restore_evidence.py <operator-held-backup-restore.json>
```

The backup/restore evidence validator checks the source commit, migration
revision, passed backup and restore rehearsal status, approved isolated restore
target, no live data in source, database-authority receipt, rollback or
forward-recovery note, and backup/restore owner. It does not authenticate to
GCP, inspect resources, execute backups, execute restores, run destructive
recovery, deploy production, roll out a shared runtime, admit live/client data,
or prove provider-side recovery or session revocation.

When a later approved production packet records value-safe operations readiness
evidence, keep the filled JSON outside source control and validate it locally:

```bash
UV_CACHE_DIR=/private/tmp/golden-rose-uv-cache uv run python scripts/validate_client_operations_readiness_evidence.py <operator-held-operations-readiness.json>
```

The operations readiness evidence validator checks the source commit, migration
revision, ready monitoring, alerting, log-retention, incident-routing and
support-routing statuses, value-safe receipts, and named monitoring, incident
and support owners. It does not authenticate to GCP, inspect resources, create
alert policies, create notification channels, activate incident contacts, page
operators, deploy production, roll out a shared runtime, admit live/client data,
or prove provider-side recovery or session revocation.

When a later approved production packet records value-safe runtime lifecycle
review evidence, keep the filled JSON outside source control and validate it
locally:

```bash
UV_CACHE_DIR=/private/tmp/golden-rose-uv-cache uv run python scripts/validate_client_runtime_lifecycle_evidence.py <operator-held-runtime-lifecycle.json>
```

The runtime lifecycle evidence validator checks the source commit, migration
revision, ready GitHub Actions runtime, runner-image, Node, Python, dependency
audit and container-base-image lifecycle statuses, value-safe receipts, runtime
review owner and next-review note. It does not authenticate to GCP, inspect
resources, update dependencies, change CI runners, push container images,
deploy production, roll out a shared runtime, admit live/client data, or prove
provider-side recovery or session revocation.

When a later approved production packet records value-safe data governance
review evidence, keep the filled JSON outside source control and validate it
locally:

```bash
UV_CACHE_DIR=/private/tmp/golden-rose-uv-cache uv run python scripts/validate_client_data_governance_evidence.py <operator-held-data-governance.json>
```

The data governance evidence validator checks the source commit, migration
revision, ready classification, retention, deletion, export, disclosure and
restricted-history-recipient statuses, value-safe receipts, governance owner and
next-review note. It does not authenticate to GCP, inspect resources, admit live
data, export records, approve disclosures, perform destructive deletion, deploy
production, roll out a shared runtime, or prove provider-side recovery or
session revocation.

When a later approved production packet records value-safe legal/business copy
approval review evidence, keep the filled JSON outside source control and
validate it locally:

```bash
UV_CACHE_DIR=/private/tmp/golden-rose-uv-cache uv run python scripts/validate_client_copy_approval_evidence.py <operator-held-copy-approval.json>
```

The copy approval evidence validator checks the source commit, migration
revision, ready copy inventory, legal review, business review, translation
review and controlled-copy owner statuses, value-safe receipts, owner and
next-review note. It does not authenticate to GCP, inspect resources, complete
legal approval, activate production copy, publish public content, deploy
production, roll out a shared runtime, admit live/client data, or prove
provider-side recovery or session revocation.

When a later approved production packet records value-safe manual accessibility
and language review evidence, keep the filled JSON outside source control and
validate it locally:

```bash
UV_CACHE_DIR=/private/tmp/golden-rose-uv-cache uv run python scripts/validate_client_manual_review_evidence.py <operator-held-manual-review.json>
```

The manual review evidence validator checks the source commit, migration
revision, ready keyboard navigation, screen-reader, reflow, contrast,
fluent-Spanish and bilingual-parity statuses, value-safe receipts, owner and
next-review note. It does not authenticate to GCP, inspect resources, make a
public accessibility claim, certify accessibility, certify translations, deploy
production, roll out a shared runtime, admit live/client data, or prove
provider-side recovery or session revocation.

When a later approved production packet records value-safe staff training,
support escalation, workflow acceptance and management-transition evidence,
keep the filled JSON outside source control and validate it locally:

```bash
UV_CACHE_DIR=/private/tmp/golden-rose-uv-cache uv run python scripts/validate_client_training_acceptance_evidence.py <operator-held-training-acceptance.json>
```

The training acceptance evidence validator checks the source commit, migration
revision, ready staff training, support escalation, staff workflow acceptance,
management-model review, working-environment feedback, data-migration planning,
repository-stewardship and known-limit statuses, value-safe receipts, acceptance
owner and next-review note. It is intended to capture the reality that a working
environment may be used by staff to gather daily-use feedback before the product
is complete. It does not authenticate to GCP, inspect resources, activate
support channels, create business accounts, transfer repositories, migrate
current-environment records, deploy production, roll out a shared runtime,
admit live/client data, activate provider-side identity, or prove provider-side
recovery or session revocation.

When a controlled staff working environment is opened for real worker and
employer intake records before client-owned transition, keep the filled JSON
outside source control and validate it locally:

```bash
UV_CACHE_DIR=/private/tmp/golden-rose-uv-cache uv run python scripts/validate_live_data_pilot_readiness.py <operator-held-live-data-pilot-readiness.json>
```

The live-data pilot readiness validator checks named staff access, staff OIDC,
disabled presentation/seed/static example posture, worker/employer intake
scope, backup/restore posture, data-governance basics, support escalation,
staff training, manual acceptance, rollback/closeout and
migration-disposition evidence. It does not authenticate to GCP, execute
deployment, activate support channels, create business accounts, transfer
repositories, migrate current-environment records, export or import data,
activate a public portal, perform automated matching/ranking/referral/placement,
or declare the product complete.

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
- Operations readiness evidence includes real staff emails, private contact
  URLs, alert channel payloads, command transcripts, or claims that incident
  contacts were activated without a separate approval packet.
- Staff recovery or session-revocation wording implies Golden Rose performs
  provider-side factor reset, provider-side session revocation, token
  revocation, or forced logout.
- Required human operators and client-owned support contacts have not been
  named outside source control.
- A real-data staff working environment is being opened without a validated
  controlled live-data staff pilot readiness record.

## Later Packet Evidence

A later approved production packet should produce value-safe handoff evidence:

- placeholder structure from
  `deploy/gcp/templates/client-production-handoff.example.json`,
- optional package-readiness summary structure from
  `deploy/gcp/templates/client-production-readiness-checklist.example.json`,
- optional package-source index structure from
  `deploy/gcp/templates/client-production-package-index.example.json`,
- optional backup/restore rehearsal structure from
  `deploy/gcp/templates/client-production-backup-restore.example.json`,
- optional operations readiness structure from
  `deploy/gcp/templates/client-production-operations-readiness.example.json`,
- optional runtime lifecycle review structure from
  `deploy/gcp/templates/client-production-runtime-lifecycle.example.json`,
- optional data governance review structure from
  `deploy/gcp/templates/client-production-data-governance.example.json`,
- optional legal/business copy approval review structure from
  `deploy/gcp/templates/client-production-copy-approval.example.json`,
- optional manual accessibility and language review structure from
  `deploy/gcp/templates/client-production-manual-review.example.json`,
- optional controlled live-data staff pilot readiness structure from
  `deploy/gcp/templates/live-data-pilot-readiness.example.json`,
- source commit and immutable image digest,
- migration revision,
- state backend lineage identifier,
- database-authority receipt,
- backup and restore rehearsal receipts,
- monitoring, alerting, log-retention, incident-routing and support-routing
  receipts,
- GitHub Actions runtime, runner-image, language-runtime, dependency-audit and
  container-base-image lifecycle receipts,
- classification, retention, deletion, export, disclosure and restricted-history
  recipient governance receipts,
- copy inventory, legal review, business review, translation review and
  controlled-copy owner receipts,
- keyboard navigation, screen-reader, reflow, contrast, fluent-Spanish and
  bilingual-parity review receipts,
- staff identity readiness result,
- smoke/readiness results,
- rollback or forward-recovery note,
- owner acceptance checklist,
- support and incident-routing owner confirmation.

Do not place raw private URLs, secret payloads, staff emails, staff provider
subjects, client data, access tokens, plan files, state files, or command
transcripts in tracked source.
