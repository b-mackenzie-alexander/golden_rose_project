# ADR-0011: PR #24 solo-maintainer remediation boundary

- **Status:** Proposed planning boundary; no implementation authorization
- **Date:** 2026-08-14
- **Owner:** Beatrice Alexander (engagement owner and sole repository maintainer)
- **Supersedes on acceptance:** ADR-0010's independent-review execution prerequisite and its seven-node execution plan
- **Related:** ADR-0001, ADR-0009, ADR-0010, `.hermes/plans/2026-08-14_174830-pr24-solo-maintainer-remediation-amendment-plan.md`

## Context and evidence posture

PR #26 merged ADR-0010 and its seven-node PR #24 remediation planning packet into protected `develop` at `c5a1380`. The repository is a private personal repository with one collaborator/administrator: Beatrice. No independently controlled GitHub reviewer, CODEOWNER, organization-level required workflow, ruleset, GitHub environment, or external status producer is available.

ADR-0010 correctly identified that a same-repository workflow is editable by the pull request that emits its status. Its required independent reviewer/CODEOWNER prerequisite cannot be satisfied in this operating model. Leaving the implementation lane phrased as waiting for a reviewer would misstate the actual delivery constraint; silently removing the control would misstate the security posture.

The remaining six findings are still valid and can be improved through local, backend-free, validate-without-apply engineering work: semantic static-policy enforcement, deterministic `uv`, Direct VPC/private-SQL declaration, API activation ordering, Cloud SQL automated backups, and managed Artifact Registry digest authority.

## Decision

### 1. Retain the required-CI finding as an open High residual risk

The self-authorizing same-repository CI finding remains **High, open, and explicitly accepted as residual risk**. No required-context name, PR-local workflow, author-controlled alternate account, delegated agent, self-review, or documentation can close it. Do not describe any solo-maintainer check as independent authorization, CODEOWNER enforcement, approval-after-latest-push, or immutable CI authority.

The original ADR-0010 Task 1 is retired for execution once this ADR and its successor plan are accepted. ADR-0010 remains historical evidence of the stronger control that would be required if an eligible external authority becomes available.

### 2. Use a truthful solo-maintainer quality protocol

The repository retains PR-only protected branches, required owned checks, strict update-before-merge, stale-review dismissal, required conversation resolution, administrator enforcement, force-push/deletion prevention, clean branch topology, exact-head local qualification, exact-range secret scanning, and documented owner merge rationale.

`required_approving_review_count` remains `0`; `require_code_owner_reviews` and `require_last_push_approval` remain `false` while no eligible independent actor exists. This is not a weaker implementation of independent review: it is a separate, transparent operating model that avoids review/CODEOWNER theater or a permanent deadlock.

`Terraform static validation` may become a required status context only after its unconditional producer is qualified on the exact implementation PR and, after merge, the committed policy is separately authorized for application and read back from protected `develop`. It is required quality evidence, not an independent authorization boundary.

### 3. Permit only the six static remediation tasks after successor-plan acceptance

A successor implementation plan may execute the six static tasks in this required order:

1. semantic HCL/JSON/YAML parsing and fail-closed structural policy enforcement;
2. deterministic reviewed `uv` selection;
3. Direct VPC private Cloud Run-to-Cloud SQL declaration;
4. exact API activation dependencies;
5. Cloud SQL automated-backup baseline only;
6. managed regional Artifact Registry digest authority.

Each task requires exact RED → GREEN evidence, separate-session/delegated review evidence that is not described as independent GitHub approval, exact-head qualification, and an honest dated record. The original technical decisions in ADR-0010 for all six tasks remain unchanged.

### 4. Preserve the cloud and deployment stop boundary

The open High blocks bootstrap/state/WIF implementation, cloud authentication or inspection, Terraform plan/apply, API enablement, provisioning, IAM mutation, remote-state migration, image push, Cloud SQL use, service start, deployment, public access, real identity, live/client data, and production work.

A later organization-level required workflow/ruleset, independently controlled GitHub App, or real external reviewer may be considered only through a separately accepted decision. That decision may reconsider whether and how the High can be remediated; this ADR does not pre-approve it.

## Consequences and constraints

- The repository can improve static safety and reproducibility without claiming its CI is independently authoritative.
- The High remains visible in every planning, implementation, review, and handoff artifact; static task completion cannot be reported as full PR #24 remediation closure.
- The six-task implementation remains validate-without-apply. Static Terraform declarations do not prove cloud connectivity, backup execution, recovery, artifact publication, or deployment behavior.
- Live GitHub policy mutation remains separately authorized and must be applied from merged `develop`, then read back; source files alone are not operational proof.
- Bootstrap/state/WIF and all cloud-mutating/deployment lanes remain blocked until independent authority is actually available and a later decision clears that specific gate.

## Alternatives considered

### Wait for an independent human reviewer

Not selected for the current delivery window. No candidate exists, and waiting would leave the remaining static defects unaddressed.

### Pretend a required same-repository status closes the High

Rejected. A pull request can modify the workflow producer while preserving its status name.

### Create CODEOWNERS or require approvals without an independent actor

Rejected. It would either create a deadlock or a bypass-theater control without independent authority.

### Use author-controlled alternate accounts or delegated-agent review as independent approval

Rejected. These share the owner's authority. They remain useful evidence only when accurately labeled.

### Migrate now to an organization-level required workflow/ruleset or independently controlled GitHub App

Deferred. It may provide a stronger future control but is broader than this planning-only amendment and unavailable in the current personal-repository setup.

## Approval, evidence, and revisit triggers

This ADR is proposed for a planning-only PR. It authorizes no implementation until its successor plan is accepted and merged. The planning PR must state that no independent GitHub authority exists and that the High remains open.

Revisit this ADR if:

- a real independent reviewer becomes available;
- an organization-level required workflow/ruleset or independently controlled GitHub App becomes available;
- the repository moves to an organization with an independently administered governance boundary;
- a later bootstrap/state/WIF or cloud/deployment decision needs an authority model beyond this solo-maintainer protocol.
