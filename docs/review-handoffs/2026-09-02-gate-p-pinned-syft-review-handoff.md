# Gate P pinned-Syft source-only review handoff

> **Historical closeout:** This artifact records the pre-merge PR #69 review surface. PR #69 subsequently passed protected checks and merged into `develop@64f4ae5` on 2026-09-03. Its former branch and pre-merge next steps are not continuation authority; current work is controlled by `CURRENT_WORK.md` and requires fresh Gate P publication approval.

## Review surface

- **Base:** `develop@a431b3c6a35f16ae014dbe21c091d5739ed52dbf`.
- **Branch:** `fix/gate-p-pinned-syft-sbom`.
- **Purpose:** replace unavailable runner-provided Docker SBOM/Scout interfaces with one immutable-pinned Syft acquisition path that generates SPDX JSON for the already-published immutable image before existing Cosign attestation and verification.
- **Boundary:** source-only. No publication retry, Terraform plan/apply, backend/state operation, import, cloud mutation, Secret version, database, migration, service, tester, live-data, or production action occurred or is authorized.

## Complete intended file inventory

- `.github/workflows/build-image.yml` — add the immutable Anchore Syft action pin, pin the Syft version, and invoke its exact output to emit SPDX JSON for the immutable image.
- `infra/policy/predeployment-authority-manifest.json` — bind the reviewed publish-job step inventory/order to the added Syft step.
- `scripts/validate_terraform_static.py` — bind the allowed action SHA, step input/id, ordered inventory, and reviewed signing-step executable SHA to the workflow contract.
- `tests/unit/test_terraform_hygiene.py` — assert the action pin, exact Syft version/output command, SBOM ordering, and removal of runner-provided Docker Scout reliance.
- `CURRENT_WORK.md` — state Gate F completion and the current Gate P source-only remediation boundary.
- `ROADMAP.md` — record Gate F completion and Gate P's current blocked source correction.
- `NOTES.md` — append dated RED→GREEN and non-action evidence.
- `docs/review-handoffs/2026-09-02-gate-p-pinned-syft-review-handoff.md` — this review artifact.
- `src/golden_rose/application/revise_draft_employer.py` — bounded post-reservation receipt-visibility retry after the required `application` CI exposed an unrelated revision race.
- `tests/unit/application/test_revise_draft_employer_concurrency.py` — delayed concurrent-winner receipt-visibility regression.

## CI remediation review surface

- **Pre-remediation branch tip:** `dc14cc888256a87de1e0090b48df0a71db486cf8` against the stated `develop` base.
- **Committed/pushed remediation:** the two revision receipt-race files above plus this handoff and required living-document closeout updates were amended into PR #69, which later merged at `develop@64f4ae5`.
- **CI finding:** `test_concurrent_same_key_changed_actor_or_payload_has_one_success_and_one_conflict` observed `SafePersistenceError("persistence operation failed")` for a same-key changed actor/payload loser rather than `RuntimeError("idempotency conflict")`; the pinned-Syft change did not cause it.
- **Minimal remediation:** after failed receipt reservation, `_get_revision_receipt_after_conflict()` performs up to three fresh receipt lookups, rolling back after each absent read. It preserves fail-closed `SafePersistenceError` exhaustion and existing replay validation.
- **Observed verification:** the new regression was first RED, then focused unit coverage passed (`3 passed`); the exact PostgreSQL selector passed once and 30 consecutive repetitions. Local CI-equivalent application quality passed with frontend `116 passed`, Python `767 passed`, and `95.94%` Python coverage. The disposable loopback PostgreSQL service was removed after verification.
- **Secret-scanning status:** the exact six-file working-tree candidate scan reported `0` Gitleaks findings; after amendment, the exact committed PR range also reported `0` findings.
- **Rereview status:** independent review was CLEAN with no Blocker, High, Medium, or Low findings; it verified the retry/rollback/fail-closed semantics and handoff scope. Protected CI later passed and PR #69 merged at `develop@64f4ae5`; any publication retry still requires fresh approval.

## Observed evidence

- The latest approved Gate P dispatch built and pushed an immutable image, then failed before attestation because `docker scout sbom --format spdx` resolved to base Docker and rejected `--format`.
- The first focused regression run was a true RED: the reviewed workflow lacked the pinned Anchore Syft action and its output-driven SPDX command.
- The minimal correction uses `anchore/sbom-action/download-syft@fbfd9c6c189226748411491745178e0c2017392d` with `syft-version: "1.37.0"` and emits `spdx-json=build/image-sbom.spdx.json` for the immutable `MANAGED_IMAGE`.
- The existing explicit Cosign SPDX attestation and verification path remains required; no evidence fallback is introduced.
- Focused workflow regressions and the static validator passed after policy parity updates.

## Reviewer focus

1. Confirm the added third-party action is pinned to the stated full commit SHA and the allowed version/input/id contract is exact.
2. Confirm Syft scans the immutable digest-bound image, produces SPDX JSON, and occurs before the existing SPDX Cosign attestation/verification.
3. Confirm the workflow does not retain `docker scout sbom`, mutable action tags, broad credentials, or a new deployment/data authority path.
4. Confirm manifest, static validator, test, and living-document status agree with the exact workflow step inventory and executable script hash.

## Required closeout checks

- `env -u PYTHONPATH uv run pytest tests/unit/test_terraform_hygiene.py -q`
- `env -u PYTHONPATH uv run python scripts/validate_terraform_static.py`
- `env -u PYTHONPATH uv run ruff format --check .`
- `env -u PYTHONPATH uv run ruff check .`
- `terraform fmt -check -recursive infra/gcp`
- `git diff --check`
- exact-range Gitleaks after the closeout commit

## Next boundary

After independent review and protected merge only: obtain one fresh approval tied to the exact merged `develop` revision before retrying Gate P publication. A successful publication still stops before every Secret, database, migration, service, tester, qualification, live-data, or production gate.
