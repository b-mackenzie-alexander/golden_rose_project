# Staff Feedback Readiness Runbook

This runbook defines the source-controlled, value-safe evidence shape for a
later bounded staff-feedback use window in the current working environment. It
does not approve cloud inspection, cloud mutation, production deployment,
live/client data admission, support-channel activation, credential rotation,
current-environment data migration, client-owned environment transfer, or
business repository transfer.

## Boundary

- A staff-feedback use window is a learning and acceptance mechanism, not a
  declaration that Golden Rose is complete.
- Staff daily use must have an explicit data-entry scope before it starts. If
  live/client data is proposed, that is a separate approval and evidence packet,
  not a side effect of this source artifact.
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
value-safe review of the staff-feedback readiness materials, feedback triage
materials, transition-planning materials and human-feedback templates. Validate
that operator-held package
index locally:

```bash
UV_CACHE_DIR=/private/tmp/golden-rose-uv-cache uv run python scripts/validate_staff_feedback_package_index.py <operator-held-staff-feedback-package-index.json>
```

The validator checks that readiness statuses are marked ready with value-safe
evidence and that approval boundaries remain explicit. It does not authenticate
to GCP, inspect runtime state, grant staff access, rotate credentials, activate
support channels, migrate records, create GitHub accounts, transfer
repositories, deploy production, roll out a shared runtime, admit live/client
data, or prove provider-side recovery or session revocation.

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
