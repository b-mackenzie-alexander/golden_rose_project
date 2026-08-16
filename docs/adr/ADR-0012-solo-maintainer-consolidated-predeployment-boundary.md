# ADR-0012: Solo-maintainer consolidated pre-deployment boundary

- **Status:** Proposed
- **Date:** 2026-08-15
- **Owner:** Beatrice Alexander (engagement owner and sole repository maintainer)
- **Supersedes on acceptance:** ADR-0011's permanent block on bootstrap/state/WIF and cloud progression; ADR-0011 remains historical authority for the completed six-task static remediation
- **Related:** ADR-0009, ADR-0010, ADR-0011, `.hermes/plans/2026-08-15_210257-consolidated-predeployment-foundation-plan.md`

## Context and evidence posture

PR #29 merged the six authorized Terraform/static remediations into protected `develop` at `08fe3056e1637d3cab4d1f82ad3081a8a324948e`. Its required `application`, `enforce`, `check`, and `Terraform static validation` checks passed. The merged tree has semantic fail-closed Terraform/workflow policy parsing, deterministic `uv`, Direct VPC/private-SQL declarations, exact API activation ordering, an enabled Cloud SQL backup baseline, and managed-registry digest authority. Local post-merge verification also passed Terraform static validation, 134 Terraform hygiene tests, Terraform format/validate, 273 Python unit tests, Python format/lint/type checks, and the frontend verification/build.

The repository is a private personal repository with one collaborator/administrator: Beatrice. No second human reviewer, independent CODEOWNER, or separately administered repository authority is available. This is a durable operating constraint, not a temporary prerequisite. Repeatedly requiring an unavailable reviewer would create a false or permanent delivery deadlock.

The same-repository CI limitation remains real: a pull request can change workflows and policy code that produce its required statuses. Required checks and agent/separate-session reviews therefore provide quality and adversarial evidence, not independent authorization. The limitation must remain visible as accepted residual risk without pretending that another human or independently controlled account exists.

The current Terraform module is still a scaffold rather than a deployment-complete foundation. It does not yet define the durable state/bootstrap contract, GitHub OIDC/WIF trust, deploy and image-publisher authority, migration job, private invoker IAM, per-secret IAM, budget/alert routing, logging/monitoring controls, PostgreSQL role lifecycle, or deployment workflows. Those remaining source-controlled pre-deployment tasks are interdependent. Splitting each into another planning PR would add delay without improving the authority model.

## Decision

### 1. Adopt a truthful permanent solo-maintainer governance posture

Golden Rose will not require a second human reviewer, independent CODEOWNER, alternate owner-controlled account, or fictional approval boundary. Beatrice is the accountable owner and final approver for planning, merge, cloud-operation, deployment, and residual-risk decisions.

The same-repository-CI finding remains documented as **High/open accepted residual risk**. Acceptance means the project may progress under compensating controls; it does not reclassify the finding as fixed or describe CI as independent.

Agent and separate-session review may be used for architecture, security, Terraform, workflow, database, and documentation challenge. Their findings must be remediated or explicitly dispositioned, but their output is quality evidence rather than independent human approval.

### 2. Use explicit owner-controlled gates instead of an unavailable reviewer gate

The following gates remain separate, evidence-bearing decisions:

1. **Planning acceptance:** accept this ADR and its paired plan, then merge the documentation-only packet.
2. **Pre-deployment implementation:** one larger source-controlled PR implements all remaining pre-deployment definitions and tests. It performs no cloud authentication, Terraform plan/apply, backend migration, provisioning, image push, secret injection, Cloud SQL use, or service start.
3. **Read-only GCP qualification:** after the implementation merges, Beatrice separately authorizes read-only inspection of the organization, candidate control-plane project, workload project, billing attachment, inherited IAM, service availability, quotas, and non-overlapping network inputs. No mutation is permitted.
4. **Terraform plan:** Beatrice separately approves backend initialization/migration and a non-secret reviewed plan against the named non-production boundary. Plan output is treated as potentially sensitive and is not committed or broadly logged.
5. **Foundation apply:** Beatrice separately approves only the reviewed bootstrap/state/WIF and non-production foundation resources. Apply evidence must include effective IAM, budget routing, state controls, cost exposure, and teardown authority.
6. **First private synthetic deployment:** Beatrice separately approves image push, out-of-band secret injection, migration execution, and Cloud Run rollout by digest.
7. **Qualification:** synthetic workflow, log minimization, role/grant drift, backup/restore or teardown/rebuild, rollback/forward recovery, accessibility, browser, and English/Spanish evidence determine whether the shared target is qualified.

Passing one gate never silently grants the next.

### 3. Consolidate all remaining source-controlled pre-deployment work

The paired plan places the following in one implementation plan and, after planning acceptance, one larger implementation PR:

- post-PR #29 status reconciliation;
- bootstrap/state/WIF Terraform structure and operator ceremony;
- exact GitHub repository/ref/environment OIDC trust;
- distinct provisioner, image publisher, deployer, migration, runtime, and private invoker authority;
- Cloud Run migration job and database-level serialization contract;
- PostgreSQL schema-owner/migration/runtime role lifecycle and drift tests;
- per-secret IAM with metadata-only Terraform ownership;
- budgets, alert routing inputs, monitoring, and logging/minimization controls;
- private Cloud Run invoker IAM and effective-IAM verification tooling;
- build/provenance, push, migrate, and deploy workflow definitions;
- immutable digest, SBOM, vulnerability, migration-compatibility, and rollback evidence;
- backup/restore and intentional teardown/rebuild runbooks;
- value-safe gate evidence templates and living-document alignment.

The larger PR is accepted as an efficiency tradeoff. It must stay internally reviewable through ordered TDD nodes, bounded commits, exact file manifests, and component-focused agent reviews.

### 4. Preserve non-production and data boundaries

All work remains limited to the private, fictional-synthetic-only GCP `develop` environment described by ADR-0009. Public invocation, real staff identity, live/client-derived data, production resources, production promotion, uploads, mapping/geocoding, messaging, payment, signatures, screening, and automated decisions remain outside this decision.

Project IDs, billing IDs, domains, user emails, principal identifiers, backend configuration values, credentials, secret payloads, database passwords, generated plans, and Terraform state remain outside tracked source and ordinary documentation. Operator-held values must use ignored files or protected runtime/environment configuration.

### 5. Compensating controls are mandatory quality controls

The solo-maintainer implementation protocol requires:

- a fresh branch from exact protected `origin/develop`;
- test-first RED → GREEN nodes for executable policy and infrastructure contracts;
- fail-closed semantic validation for Terraform and workflow authority;
- immutable action, tool, provider, base-image, and deployment-artifact selection;
- locked dependency and SBOM validation;
- least-privilege, exact-scope IAM and WIF claims;
- no long-lived service-account keys;
- exact-head local qualification and protected required checks;
- exact-range Gitleaks and diff hygiene;
- component-focused agent/separate-session review with honest provenance;
- owner disposition of every Blocker/High finding before merge;
- no claim that same-repository CI or agent review is independent authorization;
- value-safe evidence and explicit records of actions that did and did not occur.

A substantiated Blocker or High technical/security defect still blocks the affected gate unless Beatrice explicitly accepts that specific residual risk with scope and mitigation. This does not recreate an unavailable reviewer prerequisite.

## Consequences and constraints

### Positive

- The project can progress without recurring governance deadlocks or review theater.
- Security limitations remain visible rather than being falsely declared remediated.
- One consolidated implementation surface reduces planning/PR overhead across tightly coupled infrastructure authorities.
- Separate operational gates preserve control over cloud cost, mutation, secret handling, and deployment.
- The larger PR remains auditable through ordered nodes, exact evidence, and component reviews.

### Costs and risks

- Beatrice remains a concentration of repository, cloud, billing, and approval authority.
- Same-repository workflow tampering cannot be independently prevented by the current hosting model.
- A larger PR increases review load and the chance of cross-component defects.
- Read-only qualification or provider schemas may invalidate planned values and require a bounded amendment before plan/apply.
- State/bootstrap mistakes can have durable consequences even in non-production.

Mitigations are defense in depth, not claims of independent authorization. The project should revisit independently administered controls if they become practical, but their absence does not itself halt this accepted solo-maintainer lane.

## Alternatives considered

### Continue blocking until a second human reviewer exists

Rejected. Beatrice has repeatedly established that no such reviewer is available. Keeping this prerequisite would be a permanent deadlock and would misrepresent the operating model.

### Treat same-repository CI or an agent as independent approval

Rejected. Both remain under the owner's repository or execution authority. They provide useful quality evidence only.

### Split every remaining pre-deployment component into separate planning and implementation PRs

Rejected for the current schedule. Bootstrap/state/WIF, IAM, migration, budgets, observability, and deployment workflows form one coupled pre-deployment contract. Internal task gates and bounded commits provide more value than repeated planning publication overhead.

### Combine plan, apply, and deployment into one authorization

Rejected. Source review, cloud mutation, cost exposure, secret handling, and runtime qualification carry materially different risks and require separate explicit owner decisions.

### Lower finding severity because the repository is solo-maintained

Rejected. The self-authorization risk remains High/open; this ADR accepts and contains it rather than relabeling it.

## Approval, evidence, and revisit triggers

Beatrice directed the consolidated-plan and permanent solo-maintainer posture on 2026-08-15. This ADR remains **Proposed** until Beatrice reviews and explicitly accepts the completed packet. Acceptance and merge authorize only the paired pre-deployment implementation plan; they do not authorize cloud authentication, inspection, backend migration, Terraform plan/apply, provisioning, image push, secret injection, service start, deployment, live/client data, or production.

Revisit this decision if:

- repository ownership or staffing changes;
- an independently administered organization rule, GitHub App, or external status producer becomes practical;
- the project admits real identity, live/client data, public access, or production;
- cloud/billing/state ownership transfers to the client;
- a gate requires authority outside Beatrice's accepted risk envelope;
- the consolidated PR becomes too broad to preserve exact component evidence.
