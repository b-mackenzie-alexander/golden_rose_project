# Gate 2 Qualification and Foundation Transition Plan

> **For Hermes:** Use subagent-driven-development skill only for repository/documentation tasks. All GCP actions remain owner-operated, separately authorized gates.

**Goal:** Convert the merged PR #37 remediation into a safe, concise sequence for the remaining August 23 Gate 2 work and the August 24 bootstrap-to-foundation work, without inferring cloud authority from planning, merge, or prior-stage success.

**Architecture:** Keep the durable control-plane/state boundary independent from the disposable workload root. Gate 2 gathers value-safe, read-only facts; Gate 3 performs the separately approved bootstrap/backend ceremony and prepares one saved `foundation` plan; Gate 4 applies only that exact approved plan and verifies foundation mode. `foundation` must contain no Cloud Run job or service, requires no image digest, and stops before secret payloads, database logins, migration, service activation, or tester access.

**Tech Stack:** Terraform 1.15.8; Google provider 6.50.0; GCP CLI/API read-only inspection; `scripts/verify_gcp_foundation.py`; signed tester-authority receipt verification; GitHub OIDC/WIF; private operator-held deployment records.

**Decision relationship:** This plan operationalizes accepted ADR-0013; it does not amend or supersede that ADR and creates no additional cloud authority.

---

## Current rebaseline evidence

- PR #37 merged into protected `develop` at `caf96a72df87cd98114025627ad9f467f846f3a9` on 2026-08-24.
- `origin/fix/post-pr33-deployment-path-remediation` was deleted after merge; the local branch was patch-equivalent to `origin/develop` and has been retired.
- Local `develop` equals `origin/develop` at `caf96a7`; the sole worktree began clean and is now on `docs/gate2-foundation-plan`, created from that exact tip, with only this uncommitted planning artifact.
- ADR-0013 and the PR #37 source contract remain authoritative. The same-repository-CI High is still open and accepted; no review or CI result is independent cloud authorization.

## Immutable boundaries

- Do not authenticate to GCP, inspect GCP, run Terraform plan/apply, bootstrap state, publish an image, inject secrets, create database logins, execute a migration, start a service, grant tester access, or run live qualification until the specific task below has Beatrice’s explicit approval.
- Do not store project IDs, billing IDs, domains, user emails, principal values, backend values, plans, state, endpoints, credentials, secret payloads, raw command output, or operator-record contents in Git, chat, or ordinary evidence.
- Gate completion does not authorize the next gate. A failure, unknown result, permission gap, collision, quota issue, or unexpected provider behavior is a stop-and-record event, not a reason to broaden IAM or improvise configuration.

## Task 1: Publish this planning-only rebaseline and status correction

**Objective:** Make the repository truthfully describe PR #37 as merged and identify Gate 2 as the next requested authorization, without performing any cloud action.

**Files:**
- Create: `.hermes/plans/2026-08-24_165125-gate2-foundation-execution-plan.md`
- Modify: `CURRENT_WORK.md`
- Modify: `ROADMAP.md`
- Modify: `NOTES.md` (append a dated 2026-08-24 entry)
- Modify as needed for stale PR #37 wording only: `GIT_WORKFLOW.md`, `ARCHITECTURE.md`, `README.md`, `infra/gcp/README.md`, `docs/adr/README.md`, `deploy/gcp/*.md`

**Steps:**
1. Replace stale statements that PR #37 is open, uncommitted, or pending merge with its observed merge truth.
2. Mark the August 23 rebaseline item complete only after recording the exact merged tip and clean worktree evidence.
3. Leave Gate 2, Gate 3, and Gate 4 unchecked. State that the next action is an owner approval request for explicitly named Gate 2 projects and read-only commands.
4. Run repository Markdown/reference checks, `git diff --check`, and exact-range secret scanning.
5. Independently review the documentation-only diff and merge it through protected `develop` before treating the plan as repository baseline.

**Acceptance:** The repository contains no claim that PR #37 itself authorized cloud activity, and no private cloud values enter the diff.

## Task 2: Obtain explicit Gate 2 read-only authorization

**Objective:** Obtain a written, bounded approval for the candidate control-plane project, reported disposable workload project, billing scope, and the exact read-only inspection commands/tools.

**Operator-held approval bundle:**
- named control-plane and workload project identifiers;
- billing account scope, if its inspection is approved;
- authenticated operator identity and intended read-only role/path;
- exact command list and declared read-only API methods;
- approved local, ignored evidence directory and private deployment-record location;
- expected region `us-east4`, candidate RFC1918 CIDR scope, and collision-check scope;
- tester-authority receipt/bundle/certificate-identity handling, if the foundation verifier will run;
- explicit prohibition on API enablement, IAM modification, resource creation, Terraform plan/apply, and secret/database access.

**Stop condition:** No Gate 2 command runs without this specific approval. Missing identifiers, unavailable permissions, or a request to expand scope produces a blocked result and a revised approval request rather than an ad hoc command.

## Task 3: Execute Gate 2 read-only qualification and record value-safe results

**Objective:** Gather the facts needed to prepare—but not generate—the `foundation` plan.

**Files:**
- Private operator-held record only: source identifiers, exact commands, raw/redacted outputs, timestamps, and operator identity.
- Repository evidence after review: only a dated value-safe disposition in `NOTES.md` and roadmap/checklist status; never private values or raw output.

**Steps:**
1. Confirm the active source revision is the merged/reviewed `develop` tip and record it in the private operator record.
2. Run only the approved read-only project, billing, IAM, Service Usage/API, quota, region, VPC/subnet CIDR, and resource-name collision inspection commands.
3. Run the reviewed foundation verifier in `foundation` mode only when all required operator-held verifier inputs and tester-authority receipt material are available. Preserve its output only in the approved private evidence location.
4. Classify every observation as **Observed**, **Validated**, **Blocked**, or **Unknown**. Record each Gate 2 blocker and each operator-held Gate 3 input without copying the underlying sensitive value into tracked files.
5. Confirm that expected `foundation` prerequisites are feasible: separate control-plane/workload boundary, state-bucket placement/recovery posture, least-privilege IAM/WIF feasibility, allowed APIs/quotas, non-overlapping network candidate, private SQL feasibility, budget/alert routing ownership, and no name collision requiring a design amendment.
6. Stop. Do not run `terraform init` with a backend, `terraform plan`, `terraform apply`, API enablement, resource creation, or secret/database operation.

**Acceptance:** Gate 2 yields either (a) a value-safe sufficient-input disposition for Gate 3 preparation, or (b) a truthful blocker list and no mutation.

## Task 4: Obtain Gate 3 bootstrap/backend and foundation-plan preparation approval

**Objective:** Authorize the one-time ceremony and plan preparation only after Gate 2 evidence is sufficient.

**Operator-held approval bundle:**
- reviewed Gate 2 disposition and all unresolved blockers;
- exact bootstrap root and workload root source SHA;
- non-secret input inventory and digest, including values retained outside Git;
- remote-state backend custody, recovery, and client-handoff responsibilities;
- bootstrap operator authority, required retirement point, and emergency-access constraints;
- exact plan/evidence storage locations and access ownership;
- explicit execution scope: local bootstrap → remote-state migration → WIF handoff → bootstrap-authority retirement, then one `foundation` saved plan only;
- explicit exclusions: image publication/digest, secret payloads, database logins, migration job, service, tester access, and qualification.

**Stop condition:** Do not begin the ceremony if the approved input digest, source SHA, state ownership, recovery posture, or bootstrap-retirement authority differs from the reviewed bundle.

## Task 5: Perform the approved bootstrap/backend ceremony and generate one foundation plan

**Objective:** Establish reviewed remote state and create a reviewable saved `foundation` plan without applying it.

**Files:**
- Private operator-held record: backend values, state location, plan artifact, JSON inventory, digests, approval reference, and command output.
- Repository evidence after review: only value-safe plan-exists/plan-not-approved status and any sanitized blocker disposition.

**Steps:**
1. Execute the approved bootstrap root procedure with operator-held values; verify state-bucket recovery/lifecycle controls and authorized access using the approved checks.
2. Migrate the approved Terraform root to remote state using the partial backend and operator-held backend values.
3. Complete the reviewed WIF handoff and bootstrap-authority retirement; verify the temporary bootstrap path no longer remains standing authority.
4. Generate exactly one saved Terraform plan for `deployment_stage=foundation` from the reviewed source and non-secret input set. Do not use an image digest for foundation.
5. Export a JSON inventory from the same saved plan. Calculate and preserve the plan-file hash, provider-lock digest, source SHA, non-secret-input digest, and inventory reference in the private operator record.
6. Prove the inventory contains only foundation-authorized resources and no Cloud Run job, Cloud Run service, workload invoker IAM, or readiness uptime check.
7. Produce the value-safe foundation stage receipt/approval bundle required by `deploy/gcp/staged-plan-approval.md`; do not apply.

**Acceptance:** A single saved foundation plan is reviewable and mechanically shown to have no executable workload. Gate 3 completion is not Gate 4 apply authorization.

## Task 6: Review the exact foundation plan and obtain Gate 4 approval

**Objective:** Make an explicit go/no-go decision for one immutable saved plan.

**Review checklist:**
- plan/source/lock/non-secret-input digests match the private record;
- JSON inventory is from the exact saved plan and contains no executable workload;
- reviewed resources cover only approved APIs, state controls, IAM/WIF, private network/SQL foundations, secret metadata only, budgets/alerts/logging/recovery controls, and deliberate labels;
- all destructive/replacement actions, monthly-cost assumptions, alert-recipient ownership, effective IAM, and teardown implications are understood;
- plan carries no secret payload or unreviewed input;
- approval record expressly permits only the exact foundation plan and requires immediate foundation-mode verification.

**Stop condition:** A changed source SHA, plan hash, provider lock, input digest, inventory, or approval reference invalidates the approval. Regenerate and re-review; never apply a near-match.

## Task 7: Apply only the approved foundation plan and verify foundation mode

**Objective:** Apply the exact approved plan and establish only the non-executable foundation.

**Steps:**
1. Apply only the saved, approved `foundation` plan.
2. Run the reviewed foundation-mode verification using the approved private evidence location and record its pass/fail result in the private operator-held record.
3. Verify effective IAM, no public invoker/database path, no service-account keys, remote-state controls, APIs, budgets/alert routing, logging posture, labels, recovery/deletion protection, and teardown inventory.
4. Record a value-safe repository disposition: foundation verification passed/failed, any blockers, and explicit confirmation that no image was published, no payload was injected, no database login was created, no migration/service/tester action occurred.
5. Stop. A later publication or migration/service activity requires a new Gate 5 approval and its own exact artifact/receipt chain.

**Acceptance:** The foundation exists only if exact post-apply verification passes with no unresolved foundation Blocker/High. Otherwise record failure and perform only separately approved recovery/teardown work.

## Validation and review matrix

| Stage | Required evidence | Prohibited outcome |
| --- | --- | --- |
| Planning | Protected documentation PR, clean diff, secret scan, truthful status | Implicit cloud authorization |
| Gate 2 | Explicit read-only authorization, private evidence, value-safe disposition | Mutation or sensitive data in Git |
| Gate 3 | Explicit ceremony/plan-prep approval and a saved plan receipt | Applying or creating workload |
| Gate 4 | Exact plan review + approval, exact saved-plan apply, foundation verifier | Job/service/image/secrets/migration/tester access |

## Risks and decision points

- Existing documents contain stale pre-merge statements; Task 1 must correct them before Gate 2 work is represented as current.
- Gate 2 may reveal project, IAM, API, quota, billing, CIDR, or collision blockers. These are expected decision inputs, not defects to bypass.
- The foundation verifier has required operator-held inputs, including verified tester-authority receipt material, even though `foundation` must contain no service. If unavailable, document the blocker and do not weaken its contract.
- Cost/alert routing, support/emergency access, recovery objectives, and final handoff remain open decisions; a foundation plan may not invent them.

## Final stop boundary

This plan ends immediately after successful or failed foundation-mode verification. It does not authorize or schedule August 25 publication, secret/database preparation, migration, service activation, private tester access, Gate 6 qualification, live/client data, staff identity, or production.
