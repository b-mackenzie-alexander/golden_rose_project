# Foundation project-representation source-only review handoff

## Review surface

- **Base:** `develop@6c45664db55b3b56efe8426769df0610a1b1bf7c`.
- **Branch:** `fix/foundation-project-representation`.
- **Purpose:** remove source-side false replacement churn from one logging bucket configuration and four metadata-only Secrets after the accepted plan's bounded private comparison and owner same-project disposition.
- **Boundary:** source-only. No Terraform plan/apply, backend/state operation, import, cloud mutation, Secret version, database, image, service, tester, live-data, or production action occurred or is authorized.

## Complete intended file inventory

- `infra/gcp/develop/observability.tf` — derive canonical project-name and project-number forms from the existing exact project data source; apply the name form only to the logging bucket configuration.
- `infra/gcp/develop/secrets.tf` — apply the canonical project-number form only to metadata-only Secret parents.
- `tests/unit/test_terraform_hygiene.py` — source contracts for the resource-family parent shapes and a whole-root local/output deferred-reference sweep.
- `CURRENT_WORK.md` — active correction and withheld fresh-plan boundary.
- `ROADMAP.md` — current ownership-alignment checkpoint.
- `NOTES.md` — dated bounded-comparison, owner-disposition, RED→GREEN, and non-event evidence.
- `SECURITY.md` — current security-gate/Secret-IAM disposition.
- `TECHNICAL_REQUIREMENTS.md` — current Terraform stage requirement.
- `infra/gcp/README.md` — canonical-parent/rebind requirement.
- `deploy/gcp/staged-plan-approval.md` — fresh-plan prerequisite.
- `docs/review-handoffs/2026-09-02-foundation-project-representation-review-handoff.md` — this review artifact.

## Observed evidence

- The prior private foundation plan had zero Cloud Run service/job changes and five `project`-forced replacements.
- Bounded read-only comparison plus owner disposition classify all five as same-project representation drift.
- Four known Secret-access IAM rows remain expected absent desired creates with no duplicate Terraform owner.
- The parent-shape regression was a true RED before the source correction; focused GREEN passed afterward.
- Initial independent review found one Medium: the root sweep allowed one assignment's guard to mask another assignment's unguarded deferred reference. The remediation scopes checks per assignment and adds a mixed guarded/unguarded-local regression.
- Focused rereview found one additional Medium: an inverted service conditional could still treat a foundation-eager dereference as guarded. The second remediation requires each reference to occur in the service-only arm or after an explicit foundation-null arm, with an adversarial regression.
- Final rereview found one additional Medium: four-space local indentation bypassed assignment splitting. The third remediation derives top-level local indentation and adds an adversarial regression.
- The owner-approved final focused rereview returned CLEAN: it confirmed sibling isolation, inverted-conditional rejection, and four-space indentation coverage.
- Local verification passed: focused parent/deferred-reference tests (`5 passed`), full Terraform hygiene (`273 passed`), static validator, and Terraform format check.

## Reviewer focus

1. Confirm canonical parent selection is limited to the two affected resource families and does not broaden project/identity authority.
2. Confirm the deferred-reference test rejects unguarded local/output dereferences of stage-counted resources while preserving current stage guards.
3. Confirm all status text remains value-safe and does not treat source correction as fresh plan, apply, or cloud authority.
4. Confirm no forbidden state-repair, lifecycle suppression, destructive replacement, or deferred workload change is present.

## Required closeout checks

- `env -u PYTHONPATH uv run pytest tests/unit/test_terraform_hygiene.py -q`
- `env -u PYTHONPATH uv run python scripts/validate_terraform_static.py`
- `terraform fmt -check -recursive infra/gcp`
- `git diff --check`
- exact-range Gitleaks after the closeout commit

## Next boundary

After review and protected merge only: rebind the private source/lock/input/backend/state/recovery artifacts to the exact merged `develop` tip, then request separate foundation plan-generation approval. The prior withheld plan must not be applied or reused.
