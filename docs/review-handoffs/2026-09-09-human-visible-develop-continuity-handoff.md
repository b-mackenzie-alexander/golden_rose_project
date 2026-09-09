# Human-visible `develop` continuity handoff

## Delivery lock — read this first

- **Staffing reality:** Beatrice is one independent developer. There is no standing human review team, CODEOWNER quorum, second administrator, or on-call security staff. Agent reviews are quality checks, not independent-human authorization.
- **Required outcome:** Deliver a durable GCP `develop` environment that Beatrice can open in a browser now and continue evolving toward production. Human visibility is mandatory, not optional or deferred.
- **Gate budget:** One source PR, then one exact eight-hour deployment approval packet covering precheck → quota role → image → migration plan/apply → secrets → migration execution → service plan/apply → access/readback → automated qualification. Ordinary internal steps do not receive separate approval days.
- **Exact next action:** Finish the proportional two-perspective review of the current planning packet, obtain owner acceptance, publish/merge planning, then implement the single 40-path source PR from the exact merge tip.
- **Do not regress:** Do not revive Gate E0, per-transaction signing/envelopes/runners, the immediate FinOps state split, four result attestors, HMAC result ledger, receipt v2, named-IAM-only tester gate, human quorum, production backup/restore, or command-by-command operational approvals before the human-visible synthetic target exists.

If another document appears to conflict, the newest accepted ADR-0016 addendum, its paired acceleration plan, `AGENTS.md`, and this handoff control the active lane. Historical plans remain evidence, not current execution authority.

## Branch topology

- Worktree: `/Users/genie/Desktop/golden_rose_finops_result_authority_plan`
- Branch: `docs/finops-post-execution-result-authority`
- Base/HEAD before planning commit: `develop@3dca8101141e31e3d5b22739dabeaa4bc61dd15f`
- Surface: uncommitted planning working tree; no PR/commit/range evidence yet.
- Preserved dirty implementation evidence: `/Users/genie/Desktop/golden_rose_finops_signed_approval`; consult only, never merge/cherry-pick wholesale.

## Fixed managerial decisions

1. Use the existing governed workload project.
2. Keep the workload-owned budget for this deployment.
3. Before provisioner backend initialization, Beatrice's prechecked human identity creates or exact-readbacks custom role `goldenRoseProvisionerQuotaUser` and its sole provisioner binding; the provisioner then imports Terraform addresses `module.develop.google_project_iam_custom_role.provisioner_quota_user` and `module.develop.google_project_iam_member.provisioner_quota_user`, and the first full plan must show zero actions for both.
4. If the exact-source image is not already admitted, the packet binds source/workflow first and treats the verifier-admitted publication digest as an authorized packet output that becomes mandatory for both plans without reapproval.
5. Use temporary Cloud Run `allUsers` invocation protected by an application-enforced HTTP Basic gate.
6. Generate at least 32 random bytes for the password, keep it out of Git/chat/logs/argv, and expire it within seven days.
7. Keep `/health` and `/readiness` minimally public; protect every business/static/environment route.
8. Set Cloud Run min instances 0 and max instances 1; retain explicit compute/concurrency/time limits and budget alerts.
9. Keep Cloud SQL private and all data fictional synthetic.
10. Recovery for this stage is a non-mutating teardown/rebuild readiness check before handoff; an actual destructive drill occurs only after the browser walkthrough under separate destructive approval.
11. Retire `allUsers`, Basic access, synthetic auth, and revisit quota/FinOps ownership before live data or production.

## Planning source of truth

- `docs/adr/ADR-0016-signed-finops-approval-authority.md` — 2026-09-09 human-visible acceleration addendum.
- `.hermes/plans/2026-09-09_005924-finops-post-execution-result-authority-amendment-plan.md` — complete source and bundled deployment plan.
- `docs/planning/finops-result-authority-replay-disposition.md` — exact nine-file planning and 40-file source inventories.
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

## Completion definition

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

## Review status

- Architecture/security: `ACCEPT_WITH_ACCEPTED_SOLO_MAINTAINER_HIGH`.
- Terraform/deployment review found four exact conflicts; all were remediated.
- Focused delta rereview `deleg_568dd146`: `ACCEPT_WITH_ACCEPTED_SOLO_MAINTAINER_HIGH`.
- Owner acceptance: granted for the exact nine-file planning packet.
- Publication authority: staging, commit, final-range checks, push, and PR creation to `develop` are authorized.
- Merge, source implementation, and bundled deployment execution remain separately unauthorized.

## Authority boundary

This handoff grants no commit, push, PR, cloud authentication, IAM mutation, image publication, Terraform plan/apply, state operation, secret write, database action, migration, service activation, access grant, live-data admission, or production action. Planning publication, source implementation, and the bundled deployment packet each require their next explicit owner authorization.
