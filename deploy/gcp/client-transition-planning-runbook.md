# Client Environment Transition Planning Runbook

This runbook defines a value-safe planning evidence shape for the future move
from the current working environment to a client-owned operating environment.
It is source guidance only. It does not approve cloud inspection, cloud
mutation, production deployment, live/client data admission, data export,
data import, destructive cleanup, support-channel activation, credential
rotation, GitHub account creation, business repository transfer, or client-owned
environment activation.

## Boundary

- The current working environment may collect staff feedback before Golden Rose
  is complete. Records created there may later need a planned disposition.
- A migration plan is not migration execution. Export/import commands, database
  copies, destructive cleanup and live-data decisions require separate approval.
- A repository stewardship plan is not a GitHub account or repository transfer.
  Business account setup, owner invitations, token changes and repository moves
  remain private, separately approved actions.
- A management model review is not production handoff. The client-owned
  environment still needs named owners, support paths and successor technical
  contacts before activation.
- Tracked source must contain only value-safe planning records and references.
  Raw staff identities, client records, private URLs, database names, account
  identifiers, screenshots with sensitive values, credentials and command
  transcripts stay operator-held.

## Required Evidence

Use `deploy/gcp/templates/client-transition-planning.example.json` as the
placeholder-only source template. A later operator-held transition-planning
record should cover:

- management model and successor technical ownership
- current-environment record inventory at the class/category level
- data classification and live-data boundary for candidate records
- migration candidate scope and records that should not migrate
- export/import strategy and validation approach
- identity/access transition expectations
- repository stewardship and business-account decision tracking
- support ownership after the transition
- rollback, abandonment or retain-current-environment disposition
- known limitations and next-review owner

Validate the filled operator-held JSON locally:

```bash
UV_CACHE_DIR=/private/tmp/golden-rose-uv-cache uv run python scripts/validate_client_transition_planning.py <operator-held-client-transition-planning.json>
```

The validator checks that planning statuses are marked ready with value-safe
evidence and that execution boundaries remain explicit. It does not authenticate
to GCP, inspect runtime state, export data, import data, mutate databases, clean
up records, create GitHub or business accounts, transfer repositories, rotate
credentials, activate support channels, deploy production, roll out a shared
runtime, admit live/client data, or prove provider-side recovery or session
revocation.

## Stop Conditions

Stop before client-owned transition work if any of these remain unresolved:

- management and successor technical ownership are unclear
- current-environment records have no migration/disposition classification
- live-data boundaries are ambiguous
- export/import validation is undefined
- identity/access transition is not reviewed
- repository stewardship or business-account ownership is unknown
- support ownership after transition is missing
- migration, repository transfer or production authority is being inferred from
  this source-only planning artifact
