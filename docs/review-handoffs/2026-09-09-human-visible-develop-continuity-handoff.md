# Human-visible `develop` continuity handoff

## Delivery lock — read this first

- **Staffing reality:** Beatrice is one independent developer. There is no standing human review team, CODEOWNER quorum, second administrator, or on-call security staff. Agent reviews are quality checks, not independent-human authorization.
- **Required outcome:** Deliver a durable GCP `develop` environment that Beatrice can open in a browser now and continue evolving toward production. Human visibility is mandatory, not optional or deferred.
- **Gate budget:** One 52-path amended source PR, then one exact eight-hour deployment approval packet covering precheck → quota role → image → migration plan/apply → secrets → migration execution → service plan/apply → access/readback → automated qualification. Ordinary internal steps do not receive separate approval days.
- **Exact next action:** Publish the reviewed 52-path source slice as one PR to protected `develop`, inspect required CI, and stop before merge. After protected merge, bind one separately approved eight-hour deployment packet to the exact final `develop` revision.
- **Do not regress:** Do not revive Gate E0, per-transaction signing/envelopes/runners, the immediate FinOps state split, four result attestors, HMAC result ledger, receipt v2, named-IAM-only tester gate, human quorum, production backup/restore, or command-by-command operational approvals before the human-visible synthetic target exists.

If another document appears to conflict, the newest accepted ADR-0016 addendum, its paired acceleration plan, `AGENTS.md`, and this handoff control the active lane. Historical plans remain evidence, not current execution authority.

## Branch topology

- Worktree: `/Users/genie/Desktop/golden_rose_human_visible_develop`
- Branch: `feat/human-visible-develop`
- Exact base: protected `develop@349a80b98b0b7637754befd9d2fe726d614d0e19` from merged PR #82.
- Surface: uncommitted source implementation; no source commit, push, PR, cloud operation, or committed-range evidence yet.
- Preserved dirty implementation evidence: `/Users/genie/Desktop/golden_rose_finops_signed_approval`; consult only, never merge/cherry-pick wholesale.

## Fixed managerial decisions

1. Use the existing governed workload project.
2. Keep the workload-owned budget for this deployment.
3. Before provisioner backend initialization, Beatrice's prechecked human identity proves complete workload-project ancestor-policy read visibility, creates or exact-readbacks custom role `goldenRoseProvisionerQuotaUser` and its sole provisioner binding, and verifies no direct/public/service-account-principal-set ancestor binding or unresolved group membership can expand provisioner authority; the provisioner then imports Terraform addresses `module.develop.google_project_iam_custom_role.provisioner_quota_user` and `module.develop.google_project_iam_member.provisioner_quota_user`, and the first full plan must show zero actions for both.
4. If the exact-source image is not already admitted, the packet binds source/workflow first and treats the verifier-admitted publication digest as an authorized packet output that becomes mandatory for both plans without reapproval.
5. Use temporary Cloud Run `allUsers` invocation protected by an application-enforced HTTP Basic gate.
6. Generate at least 32 random bytes for the password, keep it out of Git/chat/logs/argv, and expire it within seven days.
7. Keep `/health` and `/readiness` minimally public; protect every business/static/environment route.
8. Set Cloud Run min instances 0 and max instances 1; retain explicit compute/concurrency/time limits and budget alerts.
9. Keep Cloud SQL private and all data fictional synthetic.
10. Recovery for this stage is a non-mutating teardown/rebuild readiness check before handoff; an actual destructive drill occurs only after the browser walkthrough under separate destructive approval.
11. Retire `allUsers`, Basic access, synthetic auth, and revisit quota/FinOps ownership before live data or production.
12. Develop persisted mutations accept only bounded generated-fictional Employer/EmployerContact shapes before clocks, identifiers, receipts, domain rows, or audit writes; ordinary plausible names receive a no-store `422`.
13. Migration execution and service readiness require exact equality with the packet's verifier-admitted immutable image digest; digest syntax alone is insufficient.

## Planning source of truth

- `docs/adr/ADR-0016-signed-finops-approval-authority.md` — 2026-09-09 human-visible acceleration addendum.
- `.hermes/plans/2026-09-09_005924-finops-post-execution-result-authority-amendment-plan.md` — complete source and bundled deployment plan.
- `docs/planning/finops-result-authority-replay-disposition.md` — exact nine-file planning and 52-file amended source inventories.
- `AGENTS.md`, `CURRENT_WORK.md`, `ROADMAP.md`, `NOTES.md`, and `GIT_WORKFLOW.md` — continuity and delivery posture.

## Current-target stop conditions

Stop the bundled operation only for:

- any delete or replacement not explicitly accepted;
- public Cloud SQL or another public database/network path;
- any IAM permission beyond the exact allowlist or any extra principal;
- budget mutation or removal;
- source/image/state-generation mismatch;
- secret value in source, chat, argv, logs, plan, or public output;
- inability to enforce the Basic gate/expiry or one-instance cap;
- non-synthetic/client data admission;
- unknown mutation outcome that cannot be resolved by readback; or
- operation outside the eight-hour packet.

Production-only hardening findings are recorded with activation triggers and do not stop this target.

## Source completion definition

Before commit authorization, this branch must have: exact 52-path bidirectional scope; byte-identical `infra/gcp/develop/budgets.tf`; complete application/frontend/dependency/SBOM/Terraform/type/lint/static/live-verifier/diff/secret gates; one architecture/security agent review; one Terraform/deployment agent review; and no unresolved current-target Blocker/High defect. Passing source checks grants no cloud authority.

## Runtime completion definition

The lane is not complete at plan merge, source merge, Terraform apply, or health check alone. Completion requires:

- deployed Cloud Run service on the exact merged image;
- private Cloud SQL with migrated schema;
- temporary public URL protected by the expiring Basic credential;
- unauthenticated and wrong-credential denial;
- automated synthetic Employer/EmployerContact qualification;
- URL and owner-held credential-file location delivered to Beatrice without exposing the password;
- Beatrice opens and uses the browser workflow; and
- first human usability/accessibility evidence is recorded.

## Review discipline

Use only two review perspectives: architecture/security and Terraform/deployment executability. Review against the fictional-synthetic `develop` boundary. Block only concrete Blocker/High defects matching the current stop conditions. Do not require a human team, independent attestor, FinOps split, production identity, backup/restore, or another planning tranche.

Any substantive post-handoff edit to architecture, scope, gate shape, stop conditions, or source inventory invalidates prior review and needs one focused delta check—not another full production audit. Recording the returned verdict or owner acceptance status without changing those contracts does not invalidate it.

## Local validation already run

- Exact amended scope: `52` ledger paths and `52` changed/untracked paths; no missing or extra path.
- Focused qualification: `41 passed`; live-verifier: `108 passed`; Terraform hygiene: `298 passed`; final full unit suite after delayed review remediation: `709 passed` with one inherited Starlette deprecation warning.
- Frontend: lock validation, ESLint, TypeScript, `116` Vitest tests, `95.31%` line coverage, and production build passed.
- Python: Ruff format/lint, mypy over `87` source files, Bandit, `uv lock --check`, and `pip-audit` passed; pip-audit found no known vulnerabilities. The npm high-severity gate passed and reported three moderate Vitest development-tool advisories.
- Backend and frontend CycloneDX SBOM validation passed.
- Terraform 1.15.8 format, backend-free locked initialization, validation for root/bootstrap, and static validation passed. `infra/gcp/develop/budgets.tf` is byte-identical to the PR #82 merge base.
- Final working-tree Gitleaks scanned approximately `10.15 MB` with no leak; `git diff --check` passed.
- Docker was unavailable locally, so PostgreSQL-backed integration/coverage remains for required `application` CI as explicitly permitted by the plan. No service was started.

## Review status

- Planning architecture/security: `ACCEPT_WITH_ACCEPTED_SOLO_MAINTAINER_HIGH`.
- Planning Terraform/deployment review found four exact conflicts; all were remediated before PR #82 merged.
- Initial source architecture/security review: `HIGH_FINDINGS`; direct project IAM readback did not prove absence of inherited provisioner authority.
- Initial source Terraform/deployment review: `CHANGES_REQUIRED` for the same inherited-authority gap.
- Remediation: live collection now requires exactly one matching workload-project anchor, rejects empty/wrong/duplicate/malformed ancestry and member collections, reads every folder/organization IAM policy, and rejects direct/public/service-account-principal-set inherited provisioner authority plus unresolved group membership.
- First focused architecture/security rereview: `APPROVE_CURRENT_TARGET` for inherited-authority remediation only.
- First focused Terraform/deployment rereview found and then closed the unanchored-ancestry variant.
- Delayed complete initial-review output exposed three additional Highs not included in those focused rereviews: arbitrary develop data admission, stale migration-job image execution, and quota-role description drift. All three are remediated locally; final comprehensive architecture/security and Terraform/deployment rereviews are pending.
- The comprehensive rereviews closed those four original findings, then exposed three further current-target Highs: suffix-based project service-agent admission, public uptime collected/expected shape mismatch, and service-stage success evidence never being written. All three are remediated under TDD with exact Google-managed role/member pairs, absent-auth normalization, and a success write only after Ready plus exact-image verification. Final focused delta rereviews are pending.
- Final focused architecture/security delta rereview: `PASS`; all three last Highs closed and no current-target Blocker/High remains.
- Final focused Terraform/deployment delta rereview: `PASS`; all three last Highs closed and no current-target Blocker/High remains. Lower-severity and production/cloud qualification items remain separate deferred scope.
- Source implementation authority: granted; local implementation and verification are active.
- Source commit/push/PR: authorized by Beatrice. Merge and bundled deployment execution remain unauthorized.

## Authority boundary

This handoff grants no commit, push, PR, cloud authentication, IAM mutation, image publication, Terraform plan/apply/import, backend/state operation, secret write, database action, migration, service activation, access delivery, live-data admission, or production action. The completed local source surface and later bundled deployment packet each require their next explicit owner authorization.
