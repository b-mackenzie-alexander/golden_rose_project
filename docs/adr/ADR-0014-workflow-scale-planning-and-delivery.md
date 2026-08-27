# ADR-0014: Workflow-scale planning and multi-PR delivery governance

- **Status:** Accepted
- **Date:** 2026-08-27
- **Owner:** Beatrice Alexander (engagement owner and sole repository maintainer)
- **Applies to:** Golden Rose planning, coding, review, PR, deployment, and qualification lanes
- **Related:** ADR-0012, ADR-0013, `GIT_WORKFLOW.md`, `AGENTS.md`

## Context and evidence posture

Golden Rose's plan-first, test-first, independently rereviewed workflow has protected security, privacy, infrastructure, and data boundaries. It has also repeatedly made one planning cycle approximately equal to one small implementation correction or RED → GREEN node.

The repeated fixed sequence—plan, review, planning PR, merge, rebaseline, implementation, rereview, implementation PR, merge, and another rebaseline—has delayed the first shared `develop` environment where humans can exercise the product. Roughly three weeks into development, current product behavior remains local/synthetic despite merged deployment source contracts and privately recorded partial foundation work. Beatrice reports that the schedule is approximately three days behind and that workflow granularity, rather than the engineering content itself, is the dominant cause.

Evidence is classified as follows:

- **Observed:** PR #48 merged at `develop@5f265d8`; the repository has accepted source contracts, automated local/CI evidence, and a partial non-executable foundation, but no running shared application or completed human browser/accessibility/language qualification.
- **Observed:** Several recent plans and PRs closed one narrow source contradiction or part of one roadmap item while incurring the full planning/publication/rebaseline workflow.
- **Reported by engagement owner:** The project is approximately three days behind schedule because planning/review ceremony has been repeated at micro-implementation scale.
- **Accepted:** Beatrice directed that this become general software-engineering methodology and that Golden Rose adopt it immediately.
- **Not changed:** Security, privacy, data, migration, cloud, runtime, and production approval boundaries remain explicit and evidence-bearing.

## Decision

### 1. Plan at outcome scale

An implementation plan must normally authorize a meaningful user-observable, operational, or risk-bounded outcome spanning multiple roadmap/checklist items. It must not authorize only one routine test node or part of one checklist item unless that part independently closes a material trust-boundary risk.

The plan must state:

- target outcome and definition of done;
- included roadmap items;
- ordered PR sequence and dependencies;
- cross-PR integration/qualification evidence;
- security, privacy, data, migration, and recovery boundaries;
- explicit operational go/no-go checkpoints;
- human validation or other observable completion evidence;
- material replanning triggers;
- stop boundaries and deferred work.

### 2. Allow one accepted plan to authorize several implementation PRs

A reviewed, accepted, and merged master plan may authorize several ordered implementation PRs. Each PR remains a coherent, independently reviewable surface and must start from the current approved base or an explicitly documented stack.

No new planning PR is required between predeclared implementation PRs merely because the previous PR merged.

### 3. Keep TDD small inside implementation

RED → GREEN nodes remain small and test-first. Test granularity does not control plan granularity.

A routine failing test, fixture/harness correction, helper extraction, review remediation, or internal implementation-detail change stays within the accepted plan when it does not alter the plan's contracts or authority.

### 4. Preserve explicit hazardous-operation approvals

Applicable actions still require separate explicit owner approval and readback evidence:

- cloud authentication or private source/live inventory;
- backend/state adoption or migration;
- each Terraform plan and apply;
- artifact publication;
- secret or database preparation;
- migration execution;
- service activation or exposure;
- tester access;
- qualification involving controlled runtime access;
- live/client data admission;
- production promotion.

Passing one gate never grants the next. These checkpoints may execute steps already defined in one master plan and do not each require a separate planning document.

### 5. Replan only for material change

Replanning is required when evidence materially changes:

- architecture or trust boundaries;
- sensitive-data classification or public exposure;
- identity, authorization, vendor, or external-integration authority;
- schema or cloud authority outside the accepted plan;
- a security assumption invalidated by a Blocker/High finding;
- feasibility of the planned PR decomposition;
- the target workflow because of user/client feedback.

Splitting a predeclared PR for reviewability does not itself require replanning if scope, contracts, dependencies, and completion evidence remain unchanged.

### 6. Require observable tranche completion

A tranche is complete only when it produces the declared observable result and qualification evidence. Merged source alone is insufficient when the planned outcome is a shared environment, human workflow, migration, deployment, or feedback loop.

Golden Rose's immediate next plan must cover the complete private fictional-synthetic `develop` activation and human-feedback outcome across several PRs while retaining all ADR-0013 operational gates.

## Consequences and constraints

### Positive

- Planning and review ceremony becomes proportional to risk and blast radius.
- TDD precision and PR reviewability remain intact.
- Integrated environments and human feedback arrive earlier.
- One master plan preserves cross-PR architecture and completion criteria.
- Operational approvals stay explicit without generating redundant planning packets.

### Costs and risks

- Master plans require stronger up-front cross-PR dependency and integration analysis.
- Larger authorized tranches can drift if living docs and PR handoffs do not identify the controlling plan and remaining sequence.
- Reviewers must distinguish authorized implementation variation from a material replanning trigger.
- Scope pressure could misuse consolidation to hide unrelated work; each PR must still be coherent and traceable.

### Hard constraints

- This ADR does not authorize cloud actions, runtime startup, live/client data, public access, or production.
- Blocker/High findings still block progression until remediated or explicitly accepted by the owner.
- Planning, coding, and review/PR lanes remain separate.
- Exact-head verification, exact-range secret scanning, protected CI, and truthful living-document closeout remain required.
- Operator-held identifiers, credentials, plans, state, raw outputs, and secret payloads remain outside tracked source and ordinary evidence.

## Alternatives considered

### Continue one micro-plan per implementation node

Rejected. It maximizes local ceremony while delaying integrated product evidence and human feedback.

### Collapse planning, implementation, and hazardous operations into one PR/approval

Rejected. It improves apparent speed by removing controls rather than correcting granularity.

### Use one giant implementation PR

Rejected as the default. The accepted model is one outcome-scale plan with several reviewable PRs, not one unreviewable code surface.

## Approval and revisit trigger

Beatrice accepted this methodology on 2026-08-27 and directed immediate Golden Rose adoption.

Revisit if multi-maintainer authority, release automation, regulatory obligations, incident evidence, or measured delivery outcomes show that different plan/PR boundaries would materially improve safety or throughput.
