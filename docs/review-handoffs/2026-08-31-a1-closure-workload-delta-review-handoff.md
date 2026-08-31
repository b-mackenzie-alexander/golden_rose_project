# A1-closure workload-scope-delta review handoff

**Date:** 2026-08-31
**Branch:** `docs/a1-closure-workload-delta`
**PR base:** `develop`
**Exact base:** `origin/develop@a8e091aa19de3d0a9d2c9118cfbbd1e8c07740ef` (PR #58 merge)
**Review surface:** uncommitted local working tree

## Purpose

Review the delivery-pivot amendment after PR #58. It preserves PR #57 as the closed A1 record, replaces the unexecuted full-A1-recollection wording with a separately approved bounded workload-scope delta, and records that the stakeholder-feedback target must use production-shaped application/container/PostgreSQL/migration paths with only bounded attributable technical debt.

## Changed surface

- `.hermes/plans/2026-08-31_161200-workload-project-binding-a1-scope-delta-decision-plan.md` (renamed from the PR #58 packet)
- `AGENTS.md`
- `ARCHITECTURE.md`
- `CURRENT_WORK.md`
- `NOTES.md`
- `README.md`
- `ROADMAP.md`
- `SECURITY.md`
- `TECHNICAL_REQUIREMENTS.md`
- `TECHNOLOGY_DECISIONS.md`
- `deploy/gcp/bootstrap-state-runbook.md`
- `deploy/gcp/staged-plan-approval.md`
- `infra/gcp/README.md`
- this handoff

## Contract under review

1. WP-2 remains a separately approved no-mutation binding/readback.
2. WP-3 is separately approved but may run immediately after a successful WP-2 readback in the same operator session.
3. WP-3 collects only new workload-target facts and necessary cross-project custody references; PR #57 control-plane evidence and dispositions are reused, not repeated.
4. A2 remains a separate bootstrap provenance/import decision; A3/A4/A5, plans/applies, publication, migration, service, tester access, and production remain separate.
5. A private synthetic stakeholder-feedback environment must reuse production-shaped application/container/PostgreSQL/migration paths. No public access, client/live data, toy persistence path, or embedded secrets are allowed.
6. Temporary technical debt is allowed only when bounded, attributable, removable without redesign, and retired before production/handoff.

## Observed verification

- `env -u PYTHONPATH uv run pytest tests/unit/test_terraform_hygiene.py -q` — `264 passed`
- `env -u PYTHONPATH uv run python scripts/validate_terraform_static.py` — passed
- `terraform fmt -check -recursive infra/gcp` — passed
- `git diff --check` — passed

## Review focus

- No active document reopens PR #57 A1 or requires a full recollection.
- WP-2/WP-3 remain separately approved and no mutation authority is introduced.
- The production-shaped demo posture does not create public, live-data, or production authority.
- Historical notes and the PR #58 handoff retain their historical wording rather than being misrepresented as current authority.
- No private identifiers, billing values, principals, credentials, raw evidence, state, or plans appear.

## Stop boundary

This is documentation-only. No cloud command, state/backend operation, Terraform plan/apply, deployment, tester access, or production action is authorized. After independent review clearance, stage only the listed source files, commit, run exact-head checks and exact-range Gitleaks, push, and open a documentation-only PR to `develop`.
