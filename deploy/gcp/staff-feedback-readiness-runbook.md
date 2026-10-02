# Staff Feedback Readiness Runbook

This runbook defines the source-controlled, value-safe evidence shape for a
bounded staff-feedback use window that does not admit real worker or employer
records. It does not approve cloud inspection, cloud mutation, production
deployment, live/client data admission, support-channel activation, credential
rotation, current-environment data migration, client-owned environment transfer,
or business repository transfer.

If staff will enter real worker or employer data, use
`deploy/gcp/live-data-pilot-readiness-runbook.md` instead. That controlled
live-data staff pilot packet supersedes this feedback-only packet for the next
working environment.

## Boundary

- A staff-feedback use window is a learning and acceptance mechanism, not a
  declaration that Golden Rose is complete.
- Staff daily use must have an explicit data-entry scope before it starts. If
  live/client data is proposed, use the controlled live-data staff pilot packet,
  not this feedback-only artifact.
- The current working environment may later need migration into a client-owned
  environment. This runbook records planning evidence only; it does not execute
  exports, imports, database copies or destructive cleanup.
- Management of a client-owned environment, including successor technical
  contacts and repository ownership, remains an explicit review item. A future
  business GitHub account or repository transfer requires separate approval and
  private account setup outside source control.
- Feedback evidence in tracked source must stay value-safe. Raw staff names,
  client records, private URLs, credentials, screenshots with sensitive values,
  database identifiers and command transcripts stay operator-held.

## Required Evidence

Use `deploy/gcp/templates/staff-feedback-readiness.example.json` as the
placeholder-only source template. A later operator-held readiness record should
cover:

- current environment scope and expiration/closeout owner
- staff identity/access posture for the feedback window
- no-store/auth-sensitive handling posture
- staff training and known-limit acknowledgement
- support/escalation handling for staff-reported blockers
- data-entry scope, including whether the window is synthetic-only or depends
  on a separately approved live-data packet
- feedback triage and defect disposition ownership
- migration-disposition planning for records created in the current environment
- repository stewardship and business-account decision tracking
- rollback, closeout or access-removal posture

Use `deploy/gcp/templates/staff-feedback-triage.example.json` after a bounded
feedback window to summarize value-safe staff-reported issue counts,
accessibility/privacy/security impact review, disposition and retest posture.
Validate that operator-held triage record locally:

```bash
UV_CACHE_DIR=/private/tmp/golden-rose-uv-cache uv run python scripts/validate_staff_feedback_triage.py <operator-held-staff-feedback-triage.json>
```

The triage record is not client acceptance, product completion, production
qualification, support activation, live-data admission or authority to migrate
current-environment records.

Before any bounded feedback window is activated, use
`deploy/gcp/templates/staff-feedback-activation-approval.example.json` to record
the value-safe approval decision and unresolved execution boundaries. Validate
that operator-held approval record locally:

```bash
UV_CACHE_DIR=/private/tmp/golden-rose-uv-cache uv run python scripts/validate_staff_feedback_activation_approval.py <operator-held-staff-feedback-activation-approval.json>
```

The approval record is still not cloud execution, runtime access mutation,
support activation, live-data admission, production deployment, export/import
execution, current-environment migration, account creation, repository transfer
or shared-runtime rollout.

After a separately approved bounded feedback window is opened, use
`deploy/gcp/templates/staff-feedback-activation-receipt.example.json` to record a
value-safe receipt for the operator-held action and retained boundaries.
Validate that operator-held receipt locally:

```bash
UV_CACHE_DIR=/private/tmp/golden-rose-uv-cache uv run python scripts/validate_staff_feedback_activation_receipt.py <operator-held-staff-feedback-activation-receipt.json>
```

The receipt record is evidence only. It is not production deployment,
live-data admission, support activation, export/import execution,
current-environment migration, client-owned transition, account creation,
repository transfer, shared-runtime rollout or a product-completion claim.

When the bounded feedback window is closed or access removal/expiration posture
is recorded, use
`deploy/gcp/templates/staff-feedback-closeout-receipt.example.json` to record a
value-safe closeout receipt and retained boundaries. Validate that operator-held
receipt locally:

```bash
UV_CACHE_DIR=/private/tmp/golden-rose-uv-cache uv run python scripts/validate_staff_feedback_closeout_receipt.py <operator-held-staff-feedback-closeout-receipt.json>
```

The closeout receipt is not destructive cleanup, data deletion, export/import
execution, current-environment migration, production deployment, live-data
admission, account creation, repository transfer, shared-runtime rollout or a
product-completion claim.

For deeper planning on eventual data disposition, client-owned management,
business account decisions and repository stewardship, use
`deploy/gcp/client-transition-planning-runbook.md` and validate the
operator-held planning record with
`scripts/validate_client_transition_planning.py`. That planning evidence is
still not export/import execution, account creation, repository transfer,
production deployment or live-data admission.

Validate the filled operator-held JSON locally:

```bash
UV_CACHE_DIR=/private/tmp/golden-rose-uv-cache uv run python scripts/validate_staff_feedback_readiness.py <operator-held-staff-feedback-readiness.json>
```

If the feedback window is being assembled as an operator packet, use
`deploy/gcp/templates/staff-feedback-package-index.example.json` to record the
value-safe review of the staff-feedback readiness materials, activation-approval
materials, activation-receipt materials, closeout-receipt materials, feedback
triage materials, transition-planning materials and human-feedback templates.
Validate that
operator-held package index locally:

```bash
UV_CACHE_DIR=/private/tmp/golden-rose-uv-cache uv run python scripts/validate_staff_feedback_package_index.py <operator-held-staff-feedback-package-index.json>
```

The validator checks that readiness statuses are marked ready with value-safe
evidence and that approval boundaries remain explicit. It does not authenticate
to GCP, inspect runtime state, grant staff access, rotate credentials, activate
support channels, migrate records, create GitHub accounts, transfer
repositories, deploy production, roll out a shared runtime, admit live/client
data, or prove provider-side recovery or session revocation.

For the controlled live-data staff pilot, validate the operator-held readiness
record with:

```bash
UV_CACHE_DIR=/private/tmp/golden-rose-uv-cache uv run python scripts/validate_live_data_pilot_readiness.py <operator-held-live-data-pilot-readiness.json>
```

## Stop Conditions

Stop before staff feedback use if any of these remain unresolved:

- staff access cannot be bounded to the intended users
- data-entry scope is unclear
- support/escalation ownership is missing
- known limitations are not acknowledged by the feedback owner
- feedback triage has no accountable owner
- migration disposition for current-environment records is not documented
- repository stewardship or business-account ownership is unknown
- production, live data, cloud mutation or migration authority is being inferred
  from this source-only readiness artifact
