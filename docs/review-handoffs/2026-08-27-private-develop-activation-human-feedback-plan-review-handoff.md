# Planning review handoff — private develop activation and human feedback

**Date:** 2026-08-27
**Branch:** `docs/post-pr48-truthful-state-rebaseline`
**PR base:** protected `develop`
**Exact base:** `origin/develop@5f265d8d1c1044915638d1399d8ba62c159b70c9` (PR #48 merge)
**Review surface:** accepted candidate prepared for closeout commit; review evidence was collected against the uncommitted working tree before final-head qualification
**Plan status:** Historical: Beatrice accepted the plan on 2026-08-27 after final CLEAN rereview, and PR #49 later merged the packet into protected `develop@fa8334c`. This handoff preserves planning-review evidence; current authority is `CURRENT_WORK.md`, `ROADMAP.md`, the accepted master plan, and separately approved operational-gate records.

## Objective

Review the first ADR-0014 workflow-scale master plan. The packet changes planning granularity without weakening security, review, evidence, or cloud/data/runtime approval boundaries. Its target outcome is a private fictional-synthetic shared `develop` environment where approved humans can exercise the current Employer/EmployerContact product and record structured feedback.

## Source of truth

- `docs/adr/ADR-0014-workflow-scale-planning-and-delivery.md`
- `.hermes/plans/2026-08-27_124046-private-develop-activation-human-feedback-plan.md`
- `docs/adr/ADR-0013-post-pr33-deployment-path-remediation.md`
- `.hermes/plans/2026-08-26_210433-gate3-source-live-adoption-ceremony-plan.md`
- `AGENTS.md`
- `CURRENT_WORK.md`
- `ROADMAP.md`
- `GIT_WORKFLOW.md`

## Methodology decision under review

- Plans target a meaningful user-observable, operational, or risk-bounded outcome spanning multiple checklist items.
- One accepted plan may authorize several ordered implementation PRs.
- RED → GREEN nodes remain small inside implementation and do not each reopen planning.
- Material architecture/trust/data/identity/vendor/schema/cloud-authority changes trigger replanning.
- Cloud inventory, state adoption, each Terraform plan/apply, publication, secret/database preparation, migration, service activation, tester access, qualification, live-data admission, and production retain separate explicit approvals.
- Completion requires the declared observable integration/qualification result, not merely merged source.

## Proposed master-plan decomposition

1. Planning PR P — this governance, truthful-state, and proposed master-plan packet.
2. Implementation PR 0 — bootstrap partial-backend and remote-state adoption readiness.
3. Implementation PR A — real Buildx/Cosign/registry artifact and stage-transition authority interoperability, including proposed separate artifact-verifier identity and migration-success receipt production.
4. Implementation PR B — automated qualification plus human browser/accessibility/language/feedback evidence contracts.
5. Conditional implementation PR C — contract-preserving remediation only if evidence finds implementation defects; material changes replan and every bound downstream artifact follows the invalidation/replay matrix.
6. Closeout PR D — value-safe qualification and feedback disposition.

Operational gates remain outside implicit PR authority: private inventory; bootstrap adoption; workload adoption; foundation plan/apply; publication; secret preparation; migration plan/apply; database login preparation; migration execution; service plan/apply; tester authority; automated qualification; human feedback; cleanup.

## Initial independent-review findings incorporated

The first component reviews returned **CHANGES REQUIRED**. The current remediated packet now includes:

- a bootstrap-root partial backend PR because `infra/gcp/bootstrap` had no backend declaration for the planned remote-state migration;
- an explicit source-readiness gate requiring PR 0/PR A merge before approval-bound inventory/adoption, so no state ceremony races a stale source revision;
- a proposed ADR-0013 Amendment B for a separate exact-repository read-only artifact-verifier identity, preserving the deployer's Cloud Run-only role set;
- a distinct bootstrap-root augmentation saved-plan/apply gate to create the accepted artifact-verifier identity/WIF before the workload foundation plan grants its exact repository reader binding;
- explicit production/signing of migration-success authority only after successful waited execution, with no success receipt on failure/cancellation/unknown outcome;
- actual-shaped OCI index/child/platform/SLSA/media/subject negative coverage;
- distinct unauthenticated and authenticated-but-unapproved denial probes with separate non-argv token custody;
- fail-closed `Cache-Control: no-store` qualification across approved success/error surfaces;
- browser/OS/device-or-viewport/assistive-technology/network matrix requirements;
- database-authority manifest/main-path/integration coverage;
- corrected secret-version → migration apply → database-login preparation → migration execution ordering in both plan and roadmap;
- a mandatory post-remediation invalidation/replay matrix;
- an explicit separately approved reverse/destroy/recovery gate;
- an ADR-0007 planning-granularity clarification under ADR-0014.

These remediations received fresh independent rereview. Beatrice accepted Amendment B and the master plan, and PR #49 later merged the packet into protected `develop@fa8334c`. The merged source tranche did not grant identity/IAM/WIF operations; each such gate remained separately approval-bound.

The first fresh rereview then found three remaining Medium consistency/executability issues: roadmap omission of source-readiness/bootstrap augmentation, ambiguity from the historical Gate 3 one-plan-per-action sentence, and insufficiently exact no-store/manual-matrix/four-status rules. After remediation, the final focused cross-lane rereview returned **CLEAN** with no remaining Medium-or-higher finding. Beatrice accepted Amendment B and the master plan on 2026-08-27, and PR #49 later merged the packet. The acceptance delta changed status/governance only; protected merge authorized the predeclared source work, never an implicit operational gate.

## Critical sequencing details

- Source implementation and private approval/custody preparation may proceed in parallel only after this plan is accepted and merged; approval-bound inventory/adoption waits until PR 0, PR A, and PR B merge and the exact source tip is rebaselined.
- Both tracks join before foundation-plan generation.
- If Amendment B is accepted, bootstrap adoption is followed by its own exact bootstrap augmentation plan/apply and readback before the workload foundation plan grants the artifact verifier repository access.
- Foundation is workload-free and Cloud-SQL-free.
- Secret versions may be prepared before migration planning, but database login roles and live database-authority verification occur only after migration-stage Cloud SQL exists and before migration execution.
- Tester authority is separately approved, signed, verified, and derived before the service plan.
- Deployment readiness is not Gate 6 qualification.
- A non-fluent tester cannot close fluent English/Spanish review; technical-feedback evidence must remain separately labeled.

## Primary review questions

### State/adoption and Terraform authority

1. Does the packet retain every detailed inventory, provenance, backend-fingerprint, root-separation, state-readback, and mismatch stop from the prior Gate 3 plan?
2. Is replacing the redundant future plan document requirement narrowly bounded while preserving exact plan-generation and apply approvals?
3. Are foundation, migration, and service resource/stage dependencies sequenced correctly?
4. Can source Track A and operator Track B safely proceed in parallel without implied authority?

### IAM, database, and deployment authority

5. Are publisher, deployer, provisioner, migration, runtime, tester, monitoring, and human authority still distinct?
6. Are secret-version preparation, database existence, login-role preparation, authority verification, and migration execution ordered correctly?
7. Does any step broaden invocation, project IAM, service-account impersonation, secret access, or imperative Cloud Run mutation?

### OCI/Sigstore and supply chain

8. Does PR A correctly require an isolated compatibility spike before claiming actual Buildx/Cosign/SBOM interoperability?
9. Does the proposed separate artifact-verifier identity close private OCI read authority without broadening publisher or deployer authority, and is credential replacement testable?
10. Does it reject workflow-authored placeholder SBOM/provenance and require actual-shaped signed evidence bound to the exact digest/source/workflow identity?
11. Is migration-success authority actually produced and signed only after successful waited execution, with database/schema/authority readback still required before service approval?
12. Are publication and deploy verification independently fail-closed?

### Qualification, accessibility, language, and feedback

13. Does PR B independently prove unauthenticated denial, authenticated-but-unapproved denial, and approved access with separate token custody?
14. Does PR B separate readiness, synthetic write qualification, cache policy, manual browser/accessibility, fluent-language, monitoring/recovery, feedback, and cleanup evidence?
15. Can the final status contract avoid overclaiming full qualification when fluent-language or other human evidence is missing?
16. Are current product limitations—especially no EmployerContact browser UI and synthetic application auth—represented honestly?
17. Are feedback artifacts value-safe and actionable without recording private identities/endpoints or submitted fictional values in tracked evidence?

### Executability and schedule

18. Is each implementation PR large enough to advance the outcome while still independently reviewable?
19. Are all named files, tests, commands, joins, stop conditions, invalidation rules, recovery gates, and replanning triggers executable from current source?
20. Does the plan remove redundant planning loops without collapsing hazardous-operation approvals?
21. Is there any avoidable sequential dependency that can safely move into the parallel tracks?

## Requested finding format

For each finding provide:

1. severity: Blocker / High / Medium / Low;
2. exact file and section;
3. violated authority, safety, or executability contract;
4. concrete failure scenario;
5. minimal remediation direction.

A Blocker/High finding blocks plan acceptance. Medium findings require remediation or explicit owner disposition before publication.

## Current observed verification

Before this master-plan draft, merged-source checks passed locally:

- foundation verifier and Terraform hygiene: `275 passed`;
- Terraform static validation: passed;
- Terraform format: passed;
- backend-free locked init/validate for workload and bootstrap roots: passed;
- `git diff --check`: passed;
- working-tree Gitleaks scan: no leaks.

After the governance and plan edits, path validation confirmed every plan path marked existing exists and every planned new qualification artifact is absent and explicitly marked `Create`. A fresh final diff/path/secret check is still required after review remediation.

## Hard stop

Review and refine this documentation-only surface. Do not run GCP commands, registry/Sigstore spikes, backend/state/import operations, Terraform plan/apply, image publication, secret/database actions, migration, service activation, tester access, qualification, live/client data, or production operations.
