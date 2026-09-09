# Human-Visible Develop Deployment Acceleration Plan

> **For Hermes:** After this packet is accepted and merged, implement one source PR, then request one bounded deployment approval covering the exact sequence below. Do not split ordinary steps into separate gate days.

**Goal:** Put the current Golden Rose staff workflow into a durable GCP `develop` environment that Beatrice can open in a browser, test with fictional synthetic data, and continue evolving toward production.

**Architecture:** Keep the existing governed workload project, Terraform roots, private Cloud SQL, staged migration/service model, immutable image publication, and synthetic application identity. Replace the blocked FinOps state split with one narrowly scoped `serviceusage.services.use` custom-role exception for the workload provisioner. Expose Cloud Run temporarily through public ingress, but protect every business/static route with high-entropy HTTP Basic access, cap Cloud Run at one instance, expire the shared credential, and prohibit live/client data.

**Operating model:** One solo developer; agent reviews are quality checks, not human approvals. One source PR and one time-bounded operational approval packet. Production/live-data promotion remains separate.

---

## 1. Accepted managerial decisions

1. Use the existing governed GCP `develop` project rather than creating a throwaway project.
2. `develop` must remain production-shaped and incrementally promotable; it is not a one-off demo.
3. Human visibility is required now. Target creation precedes human browser/accessibility/language/usability evidence.
4. Gate administration may not consume multiple days. One explicit approval may cover the complete bounded private-synthetic deployment transaction.
5. Grant the workload provisioner exactly `serviceusage.services.use` in the workload project so Terraform quota attribution works without the FinOps state split.
6. Use temporary public Cloud Run ingress with a high-entropy shared access gate, one-instance cost bound, credential expiry, and mandatory retirement before live data.
7. Treat the synthetic database as disposable; teardown/rebuild is required, while backup/restore qualification is deferred until live-data or production admission.
8. Keep the inherited solo-maintainer High explicit but non-blocking.

## 2. Source PR — deployable human-visible `develop`

Create one fresh branch from the exact protected planning-merge tip. Implement only the exact paths in `docs/planning/finops-result-authority-replay-disposition.md`.

### 2.1 Temporary shared access gate

Add `src/golden_rose/demo_access.py` and install it in `create_app()` before application routers/static fallback.

- HTTP Basic username is fixed `golden-rose-demo`.
- Password is at least 32 random bytes encoded as canonical base64url without padding, stored as a Pydantic `SecretStr`, compared with `hmac.compare_digest`, never logged or rendered.
- `GOLDEN_ROSE_DEMO_ACCESS_PASSWORD` and `GOLDEN_ROSE_DEMO_ACCESS_EXPIRES_AT` are mandatory only for `environment=develop`, forbidden for production, and excluded from repr/errors.
- Expiry is exact UTC RFC 3339 and no more than seven days after service revision creation. Expired credentials fail closed until rotated under a new bounded approval.
- `/health` and `/readiness` remain unauthenticated and value-safe for platform probes. Every other route—including `/`, static assets, `/api/environment`, and staff APIs—requires valid Basic credentials.
- Missing/malformed/wrong credentials return fixed `401`, `WWW-Authenticate: Basic realm="Golden Rose synthetic develop", charset="UTF-8"`, `Cache-Control: no-store`, and no application body or credential reflection.
- Expired configuration returns fixed no-store `503` without revealing timestamps.
- Middleware does not persist sessions, cookies, usernames, passwords, authorization headers, or source IPs.

Tests cover startup validation, production rejection, health/readiness bypass, root/static/API protection, correct access, constant-time comparison seam, malformed encodings, wrong credentials, expiry, no-store headers, and no secret reflection.

### 2.2 Terraform access and cost boundary

Modify the existing workload Terraform source:

- add `module.develop.google_project_iam_custom_role.provisioner_quota_user` with role ID `goldenRoseProvisionerQuotaUser` and exactly `serviceusage.services.use`;
- add `module.develop.google_project_iam_member.provisioner_quota_user` bound only to `golden-rose-provisioner@<control-plane-project>.iam.gserviceaccount.com`;
- reject every additional permission, member, inherited broad role, and user-managed key in static/live verification;
- retain the existing budget in the workload root; defer ADR-0015's FinOps state split until production/handoff or a concrete billing-ownership need;
- keep Cloud SQL private with no public IP;
- keep Cloud Run `INGRESS_TRAFFIC_ALL` and add exact `allUsers` `roles/run.invoker` only at `deployment_stage=service`;
- replace the named-tester receipt input for this synthetic stage with a fixed temporary-public-access marker; do not retain both invoker models;
- add Secret Manager metadata `demo-access-password` and runtime-only accessor binding;
- inject the demo password and expiry into the service from Secret Manager/config without putting values in Terraform state, argv, workflow inputs, logs, or Git;
- set Cloud Run `min_instance_count=0`, `max_instance_count=1`, bounded concurrency, CPU/memory, and request timeout;
- retain deletion protection during operation but document exact teardown sequencing;
- update foundation/service verification so `allUsers` is accepted only when the temporary shared-access gate, synthetic-only label, one-instance cap, expiry, and no-live-data marker all match.

The temporary public invoker and shared gate must be removed before live/client data, production, or any non-synthetic authentication mode.

### 2.3 Qualification updates

Update the qualification harness to:

1. call `/health` and `/readiness` without credentials and require only minimized value-safe responses;
2. prove an unauthenticated business/API request returns fixed `401` without business content;
3. prove wrong Basic credentials return the same fixed denial;
4. use the approved Basic credential through a non-argv private handoff for browser/API qualification;
5. run the current bounded fictional Employer/EmployerContact flows;
6. verify the ready revision/image digest, private database, one-instance cap, budget alerts, synthetic label, and credential expiry;
7. scan logs for authorization/password/client-data leakage; and
8. emit one minimized qualification result.

## 3. Source verification and merge

Use exact TDD on the access middleware, Terraform/static policy, and qualification changes. Then run the existing complete application, unit, Terraform 1.15.8, Ruff, mypy, dependency/SBOM, Gitleaks, and diff gates. A local Docker outage may defer PostgreSQL execution to required CI; it does not create another planning lane.

One architecture/security agent review and one Terraform/deployment agent review are sufficient. Fix only concrete Blocker/High findings for this synthetic-develop boundary. Production-only Mediums are deferred with triggers. Merge through normal protected CI; do not require human PR reviewers.

## 4. One bounded deployment approval packet

After source merge, prepare one private packet bound to exact protected source SHA, publication workflow identity, repository, Terraform 1.15.8/provider locks, immutable inputs, current state generations, expected resource-action allowlists, and one transaction ID. If an immutable image already admitted for that exact source exists, bind it at approval. Otherwise the verifier-admitted digest emitted by the exact publication workflow is a designated packet output and becomes the mandatory immutable input to both Terraform plans and every later check without a second approval. One explicit user approval authorizes this ordered sequence for up to eight hours:

1. read-only repository/GCP/state/IAM/resource precheck, including proof that Beatrice's selected human identity currently has exactly the custom-role creation/read and project IAM policy get/set authority needed for the bootstrap;
2. before provisioner backend initialization, Beatrice creates—or reads back if already present—exact project custom role `goldenRoseProvisionerQuotaUser` containing only `serviceusage.services.use` and its sole binding to the workload provisioner. Any role/binding collision, extra permission/member, wrong stage/title, or missing human authority stops;
3. after the permission is effective, initialize the workload backend as the provisioner and import exact addresses `module.develop.google_project_iam_custom_role.provisioner_quota_user` and `module.develop.google_project_iam_member.provisioner_quota_user` using the exact project/role/member import IDs. Read both state objects back and require the first full migration plan to show zero actions for them;
4. publish and verify the exact merged image when no admitted digest exists; bind its verifier-admitted digest as the packet output described above;
5. generate and inspect the `migration` Terraform plan;
6. stop automatically on any delete, replacement, public Cloud SQL/network database path, broad IAM, budget mutation, extra principal, or action outside the allowlist;
7. apply the admitted migration plan and read back network, Cloud SQL, migration job, IAM, and state;
8. create runtime/migration database roles and database URL Secret versions through non-echoing private handoffs;
9. generate the high-entropy demo password and seven-day expiry, write only the Secret version/config, and save the credential in an owner-held `0600` file outside Git/chat;
10. execute the migration job once and verify schema/database authority;
11. generate and inspect the `service` Terraform plan under the same stop conditions;
12. apply the admitted service plan and verify image, readiness, public invoker, Basic gate, expiry, max-instances, private database, IAM, budget, and logs;
13. run automated synthetic qualification plus a **non-mutating** teardown/rebuild readiness check that validates source, runbook, deletion order, state/recovery bindings, and rebuild prerequisites without destroying the target; and
14. return the URL plus access-file location to Beatrice, never the password in chat.

Ordinary readbacks, plans, applies, secret writes, migration execution, service activation, and qualification inside this exact packet do not require new approvals. A transient retry is allowed within the eight-hour window only when source/inputs/state generation and admitted action set remain unchanged. Unknown mutation outcome requires readback before retry. Any stop condition, scope change, destructive action, or expired packet requires a new decision.

## 5. Human-visible completion

The deployment outcome is complete only when:

- Beatrice can open the URL in a normal browser using the private Basic credential;
- the non-production fictional-synthetic banner is visible;
- create/search/detail/revision/contact flows work against Cloud SQL;
- unauthenticated and wrong-credential requests are denied;
- automated qualification passes;
- the first human browser/accessibility/usability walkthrough is recorded; and
- any Spanish fluent-language gap is labeled honestly without taking the environment offline for technical feedback.

The environment may remain available for continued `develop` builds while synthetic-only access, credential expiry/rotation, max-instances, cost alerts, and teardown controls remain effective.

## 6. Promotion and retirement triggers

Before live/client data or production:

- remove `allUsers` invoker;
- remove the shared Basic gate and credential;
- implement real staff identity/MFA/session authorization;
- revisit the provisioner quota exception and ADR-0015 FinOps separation;
- qualify backup/restore, production recovery/support, retention/legal rules, and client ownership;
- complete production security/accessibility/language acceptance.

These are promotion gates, not blockers for the human-visible synthetic `develop` environment.

## 7. Handoff invariants

Every planning, implementation, review, and operational handoff for this lane must begin with the delivery-lock block from `docs/review-handoffs/2026-09-09-human-visible-develop-continuity-handoff.md`. It must state:

- one solo developer and no assumed human review team;
- durable human-visible `develop` as the current required outcome;
- one 40-path source PR and one eight-hour deployment approval packet;
- the exact access/quota/database/cost decisions;
- the current-target stop conditions;
- the exact next executable action; and
- the production-only controls that are deferred.

A receiving session must not convert a production recommendation into a current blocker unless it maps to a named stop condition. It must not revive the FinOps split, result-attestor design, named-IAM-only tester gate, backup/restore qualification, or command-by-command approvals before the target exists. Any handoff missing this block is incomplete and must be repaired before execution continues.

## 8. Stop boundaries

This planning packet itself performs no cloud authentication, state operation, Terraform plan/apply, secret write, image publication, migration, service activation, or data admission. Implementation starts only after planning merge and explicit source authorization. The one bundled operational packet requires a separate explicit approval after source merge.
