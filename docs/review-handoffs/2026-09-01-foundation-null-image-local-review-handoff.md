# Foundation null-image local review handoff

## Review surface

- **Branch:** `docs/e2-closeout-workload-state-prep`
- **Base:** `develop@0d13ebcbb565a4a887fc5c0d42558f4595872526`
- **Surface:** committed local branch, one commit ahead of `develop` (`git rev-parse HEAD` is the authoritative exact head).
- **PR target:** `develop`

## Scope

A bounded source correction makes the `foundation` stage evaluable when `container_image_digest = null`. During the separately approved workload-state import, Terraform failed before any address entered state because `infra/gcp/develop/locals.tf` interpolated that nullable value into `managed_container_image`, even though Cloud Run and migration resources have zero instances in `foundation`.

The change:

1. guards `managed_container_image` so it is `null` when the digest is `null`;
2. extends the existing foundation-stage regression to require that guard; and
3. records the exact E2/E3 state outcome and the paused workload-import boundary in the active living docs.

## Complete intended file inventory

- `infra/gcp/develop/locals.tf` — guarded nullable image local.
- `tests/unit/test_terraform_hygiene.py` — regression for the foundation null-image local.
- `CURRENT_WORK.md` — current E3 state/import status.
- `ROADMAP.md` — E3 preparation completion and source-correction/rebind sequence.
- `NOTES.md` — dated observed import stop, readback, RED→GREEN evidence.
- `README.md` — current state-establishment sequence.
- `infra/gcp/README.md` — Terraform-scaffold status.
- `docs/review-handoffs/2026-09-01-foundation-null-image-local-review-handoff.md` — this handoff.

## Observed verification

- Focused RED: `env -u PYTHONPATH uv run pytest tests/unit/test_terraform_hygiene.py::test_foundation_stage_does_not_require_or_resolve_container_image_digest -q` failed because the guard was absent.
- Focused GREEN: the same selector passed after the guarded local was added.
- `env -u PYTHONPATH uv run pytest tests/unit/test_terraform_hygiene.py -q` — `268 passed`.
- `env -u PYTHONPATH uv run python scripts/validate_terraform_static.py` — passed.
- `terraform fmt -check -recursive infra/gcp` — passed.
- `git diff --check` — passed.

## Operational boundary

The first E3 state operation initialized a distinct private workload lineage but failed before any Terraform address entered state. A private post-failure readback confirmed zero addresses plus lineage/serial. No state repair, Terraform plan/apply, cloud resource/IAM/API mutation, authority retirement, deployment, tester access, live/client data, or production action occurred.

The private command allowlist must be rebound only after this correction is independently reviewed and merged. Do not resume workload imports from this working tree.

## Reviewer focus

1. Confirm the conditional local preserves immutable-digest behavior for `migration` and `service` while avoiding null interpolation in `foundation`.
2. Confirm the regression detects the observed failure class rather than only reiterating nullable variable declarations.
3. Confirm no source change broadens cloud authority, relaxes stage gating, or authorizes plan/apply.
4. Confirm the living-doc status is truthful and value-safe.

## Independent review and remediation

- **Initial review:** two Medium findings were returned against the local working tree: the regression could be satisfied by a non-active literal, and `README.md` / `infra/gcp/README.md` incorrectly described workload state as merely next despite the initialized empty lineage.
- **Remediation:** the test now selects the unique `managed_container_image` assignment and asserts its expression begins with the null guard. The two active status summaries now describe E3 preparation, initialized empty lineage, bounded source correction, and paused import resumption.
- **Post-remediation verification:** focused regression passed; Terraform hygiene passed with `268 passed`; static validation, Terraform formatting, tracked diff hygiene, and untracked-handoff whitespace hygiene passed.
- **Fresh rereview finding:** one Medium found stale `CURRENT_WORK.md` immediate-next-step text that still directed PR #62/E2 work. It was replaced with the correction-review/rebind → approved E3 import-resumption → A5/foundation-plan sequence.
- **Final rereview finding:** one Medium found stale `CURRENT_WORK.md` active-objective text that still treated the bootstrap IAM reconciliation as current and E2/E3 as future. It now records merged PR #62, completed E2, E3's empty lineage/import stop, the source correction/review/rebind sequence, and the later-plan disposition for four absent IAM addresses.
- **Closeout rereview finding:** one Medium found that nullable digest coverage did not assert `default = null`. The test now requires that default in both root and module variable blocks; it passed immediately because the reviewed source already has the required defaults (a documented GREEN regression). Focused and full Terraform verification were rerun successfully.
- **Final closeout rereview finding:** one Medium found `infra/gcp/README.md` approval-gate wording that still placed workload state wholly in the future. It now distinguishes completed E2, E3 preparation plus empty-lineage initialization, and paused import resumption. The parallel active `TECHNICAL_REQUIREMENTS.md` state summary was reconciled in the same sweep.
- **Final closeout rereview required:** inspect this refreshed full working-tree surface before any commit, push, or workload-import resumption.

- **CI remediation:** PR #63 Application quality failed only because Ruff required the test's `read_text(...)` call on one line. Ruff format/check and mypy now pass locally; no Terraform/cloud behavior changed. The amended head must be reread by CI before merge.

## Closeout boundary

Review and remediate the entire committed surface first. The exact-head local verification and exact-range Gitleaks scan passed for `develop@0d13ebc..HEAD`. Push this branch, then open the PR; no workload-import resumption follows from publication.
