# Qualification status contract

Status: v28 automated qualification and initial browser handoff ran. The current exact final status is `not_qualified` because the production Spanish toggle failed and required manual browser/accessibility/fluent-language rows remain unrun; Wave 1 is the bounded remediation path.

The human-visible fictional-synthetic `develop` tranche ends with exactly one final status. Existing machine-readable labels retain `private_develop` for compatibility, but the transport is intentionally public behind the temporary shared Basic gate; the URL, credential, and raw evidence stay operator-held.

## Exact statuses

### `qualified_private_develop_for_human_feedback`

All automated, shared-access, browser, manual accessibility, fluent English/Spanish, monitoring, non-mutating recovery-readiness, and feedback-blocker criteria pass.

This status remains non-production and synthetic-only. It is not staff-pilot identity and does not authorize live/client data or production.

### `operational_private_develop_technical_feedback_only`

Service, security/automated qualification, and every required browser/manual-accessibility row pass, but the specifically named fluent-language content-quality review remains `not_evidenced`.

No other missing/failed row qualifies for this status. Do not call this fully qualified, bilingual-approved, not client-accepted, or production-ready.

This status does not authorize live/client data or production.

### `not_qualified`

A core automated, security, privacy, migration, service, browser, accessibility, language, monitoring, recovery, cleanup, or feedback criterion fails or remains unrun outside the narrow technical-feedback exception.

Record blockers and stop/cleanup disposition in value-safe tracked docs and keep raw evidence operator-held.

This status does not authorize live/client data or production.

### `torn_down_after_failed_activation`

Activation cannot be safely retained, and the approved workload cleanup/rebuild disposition has been executed while preserving the control-plane/state evidence required by the approved recovery policy.

This status does not authorize live/client data or production.

## Overclaiming boundary

- Exactly one final status may be selected.
- Passing automated qualification alone is not human browser qualification; human visibility is mandatory before this final status may be selected.
- An unexpired shared credential is temporary access, not production identity.
- Passing browser/manual accessibility rows alone is not fluent-language approval.
- Human technical feedback is not client acceptance.
- None of these statuses authorizes live/client data or production.
- Tracked docs may record only value-safe status, blocker category, and approved evidence references/digests.
