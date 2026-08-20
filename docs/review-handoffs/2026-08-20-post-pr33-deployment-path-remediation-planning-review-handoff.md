# Planning review handoff — post-PR33 deployment-path remediation

**Date:** 2026-08-20
**Review base:** protected `develop@3c0118abb8b84472141992d2238033b1312d5af2`
**Current branch at initial review:** `develop`
**Packet status:** historical initial planning review surface; PR #34 merged it into `develop` at `63caa4088da44d5f98663bfc2578a0f93444a0fc`
**Cloud status:** no cloud action authorized or performed

## Objective

Review accepted ADR-0013 and its paired F1-F17 remediation plan before publication through a protected documentation-only PR. This review must verify that the seven accepted owner decisions are internally consistent, implementable under exact-node TDD, least-privilege, and aligned across living documents.

## Source of truth

- `docs/adr/ADR-0013-post-pr33-deployment-path-remediation.md`
- `.hermes/plans/2026-08-20_002931-post-pr33-deployment-path-remediation-plan.md`
- `CURRENT_WORK.md`
- `ROADMAP.md`
- `SECURITY.md`
- `TECHNICAL_REQUIREMENTS.md`
- `TECHNOLOGY_DECISIONS.md`
- `ARCHITECTURE.md`
- `GIT_WORKFLOW.md`
- `AGENTS.md`

ADR-0009 remains the private fictional-synthetic GCP develop boundary. ADR-0012 remains the permanent solo-maintainer and separate-gate boundary. ADR-0013 amends their deployment-path details after PR #33.

## Observed baseline

- PR #33 merged at `3c0118abb8b84472141992d2238033b1312d5af2`.
- Local `develop` and `origin/develop` matched that merge before this packet was written.
- The post-merge audit records F1-F17, including four Blockers.
- The same-repository-CI High remains open accepted residual risk.
- The only pre-existing worktree item was the untracked candidate remediation plan.

## Accepted decisions to review

1. One required no-default `deployment_stage`: `foundation`, `migration`, `service`.
2. Terraform is sole configuration authority; deploy automation verifies/executes existing resources without mutation.
3. The first tester path is IAM-private and internet-reachable using exact named invocation and loopback proxy/token access.
4. Deploy executor receives exact-job `roles/run.jobsExecutor` and exact job/service `roles/run.viewer`, with no Cloud Run mutation or service-account impersonation.
5. WIF maps direct-workflow `workflow_ref`; publisher and deploy executor have different exact workflow bindings; provisioner has no GitHub WIF authority yet.
6. Publication requires keyless digest-bound Cosign signature plus signed SLSA v1, image-SBOM, and checksum-bound backend/frontend SBOM evidence with accepted transparency metadata.
7. Availability requires an authenticated Cloud Monitoring `/readiness` check with exact Monitoring service-agent invocation and repeated-failure routing.

## Primary review focus

### Terraform and gate authority

- Foundation graph has no Cloud Run job/service.
- Migration adds the configured job without service or execution.
- Service adds the staff service only after migration evidence.
- Every stage change requires a reviewed saved plan; reverse transitions are destruction reviews, not rollback automation.
- Terraform remains the only configuration mutation authority.

### IAM and WIF

- The deploy role model is compatible with the non-mutating workflow.
- No execution override, service-account-user/token-creator, secret, publication, provisioning, or application invocation leaks into deploy authority.
- `workflow_ref`, not reusable-only `job_workflow_ref`, controls direct workflow identity.
- Exact workflow principal-set representation is implementable and fail-closed under the pinned provider.
- Same-repository CI is not overclaimed as independent authorization.

### Supply chain

- The plan requires exact-digest signature and attestation verification at publication and deployment.
- Certificate identity, issuer, transparency inclusion, source commit, builder, SLSA predicate, image SBOM, and application SBOM checksums are all mandatory.
- No checksum/workflow-success fallback remains.
- Signing/provenance content cannot leak secrets or operator-held environment identifiers.

### Tester access and monitoring

- `INGRESS_TRAFFIC_ALL` is described honestly as internet-reachable.
- IAM remains mandatory and broad/public invokers remain prohibited.
- Technical proxy/token access is not described as production staff identity.
- The Monitoring service agent receives only exact service invocation.
- `/readiness` checks send no business or synthetic-user payload and provisional alert timing is not an SLA.

### Documentation and delivery

- PR #33 is consistently merged/historical rather than open.
- F1-F17 remediation is blocked until this packet merges.
- Agency-facing staff workflow polish is prioritized; public-facing features may be deferred before security/governance controls.
- August 25 is a private fictional-synthetic develop target, not a production claim.
- Read-only qualification, backend/bootstrap, each plan/apply, publication, migration, service activation, and qualification remain separate approvals.

## Hard stop

This planning packet authorizes no GCP authentication or inspection, backend migration, Terraform plan/apply, API enablement, provisioning, image publication, secret/database action, migration execution, service activation, tester access, qualification, real identity, live/client data, public unauthenticated access, or production action.

## Review completion criteria

- No undispositioned planning Blocker/High finding.
- All seven accepted decisions are internally consistent across ADR, plan, and living docs.
- Every F1-F17 finding has an exact remediation node or explicit accepted residual-risk disposition.
- No unavailable second-human prerequisite is introduced.
- No environment-specific or secret material appears in the packet.
- Review outcome is recorded as quality evidence, not independent authorization.

## Post-PR34 independent-review addendum

The initial packet merged before the independent component reviews completed. Those reviews found plan-executability gaps, not new cloud facts and not a claim that F1-F17 are remediated: evaluated stage inventory cannot be proven by a configuration graph alone; foundation image input and per-secret runtime/migration IAM lack exact nodes; every transition lacks a review-bound saved-plan receipt; tester authority is caller-supplied and permits groups despite the individual-identity ADR; WIF lacks literal event-negative tests; the deploy path lacks exact receipt/attestation matrices; monitoring resources are not explicitly `service`-stage-only; qualification failure lacks minimized durable evidence; and living docs retained pre-merge wording.

`docs/post-pr34-planning-review-remediation` is the follow-up documentation-only branch. Its required outcome is an amended ADR/plan/handoff/living-doc packet with all Blocker/High findings remediated or explicitly accepted, followed by fresh independent rereview. This addendum grants no remediation implementation, cloud, Terraform, secret, publication, migration, service, tester-access, qualification, or production authority.

The amended packet passed fresh independent component and status rereviews with no new Blocker/High/Medium finding. PR #35 merged the amendment into protected `develop` at `db1f2936d4cc2b352d302893fe4665f072f8a003`. The same-repository-CI High remains explicitly accepted residual risk. This handoff is historical context; a fresh `fix/post-pr33-deployment-path-remediation` branch from that exact merge tip is the next possible implementation lane and still authorizes no cloud action.
