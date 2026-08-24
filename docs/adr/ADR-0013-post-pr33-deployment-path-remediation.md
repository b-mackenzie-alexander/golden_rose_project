# ADR-0013: Post-PR33 staged deployment-path remediation

- **Status:** Accepted
- **Date:** 2026-08-20
- **Owner:** Beatrice Alexander (engagement owner and sole repository maintainer)
- **Amends:** ADR-0009 and ADR-0012 for post-PR33 deployment staging, automation authority, tester ingress, WIF identity, provenance, and availability evidence
- **Related:** `.hermes/plans/2026-08-20_002931-post-pr33-deployment-path-remediation-plan.md`, PR #33 merge `3c0118abb8b84472141992d2238033b1312d5af2`

> **Publication status:** The initial accepted ADR-0013 packet merged as PR #34 at `develop@63caa4088da44d5f98663bfc2578a0f93444a0fc`. The proof-node clarifications below are a separate, currently unmerged documentation-only amendment on `docs/post-pr34-planning-review-remediation`. They authorize no remediation implementation, cloud action, or later gate until they pass independent review and merge through protected `develop`.

## Context and evidence posture

PR #33 merged the consolidated source-controlled pre-deployment implementation into protected `develop` at `3c0118abb8b84472141992d2238033b1312d5af2`. Its local and protected-check evidence established substantial no-cloud source contracts, but a post-merge audit found deployment-path defects that prevent truthful Terraform planning, foundation apply, workload activation, or qualification.

The confirmed findings include four Blockers: missing executable runtime/migration configuration and secret references; a foundation gate that conflicts with unconditional Cloud Run job/service creation; insufficient deploy-execution authority under the prior workflow design; and an internal-only ingress posture with no viable named-human tester path. Additional High and Medium findings cover API dependencies, WIF workflow separation, verifier response shapes, bootstrap validation, Cloud SQL input bounds, logging, no-traffic availability, Terraform cardinality, failure evidence, image provenance/SBOM binding, partial workflow mutation, and stale living documents.

Evidence is classified as follows:

- **Observed:** PR #33 is merged; the current Terraform root unconditionally creates executable Cloud Run resources; runtime/migration configuration is absent from executable deployment paths; repository-level WIF principal-set bindings can reach multiple automation identities; the deploy workflow imperatively updates Cloud Run configuration; request-derived 5xx alerts do not detect a silent target.
- **Validated:** current official GitHub documentation defines `workflow_ref` for direct workflows and `job_workflow_ref` for reusable workflows; current Cloud Run roles provide narrow viewer and existing-job execution capabilities; Cloud Monitoring supports authenticated HTTPS uptime checks against Cloud Run using its service agent.
- **Accepted:** the seven owner decisions below and the digest-bound Sigstore provenance posture were explicitly accepted by Beatrice on 2026-08-20.
- **Not yet validated live:** organization/project/IAM/API/quota facts, provider behavior against operator-held inputs, registry/signing interoperability in the target project, effective roles, alert delivery, and actual Cloud Run access. Those remain later gate evidence.

The same-repository-CI finding remains **High/open accepted residual risk**. Exact workflow identity and signed provenance narrow runtime authority but do not turn owner-controlled repository automation into independent authorization.

## Decision

### 1. Use one required staged workload root

The workload root will require a no-default `deployment_stage` with exactly three values:

1. `foundation` creates control-plane-independent workload foundations but no executable Cloud Run job or service.
2. `migration` retains foundation resources and adds the configured migration job, but does not execute it or create the staff service.
3. `service` retains the migration job and adds the configured staff service plus its exact named invocation boundary only after successful migration evidence.

Each transition requires a separately reviewed saved Terraform plan and explicit approval. Static policy and graph tests must reject invalid stages, broad boolean shortcuts, arbitrary resource expansion, and stage/resource mismatches. Reverse transitions require an explicit destruction review and never serve as automatic schema rollback.

The no-cloud remediation must prove the stage contract with a narrow local evaluator for the only approved stage expressions; a plain configuration graph is not sufficient evidence of evaluated instance absence. At Gate 3+ each saved plan must yield a value-safe receipt containing the stage, source revision, Terraform plan hash, provider-lock digest, non-secret-input digest, evaluated inventory, approval reference, and—where a workload exists—the authorized immutable image digest. `foundation` must neither require nor resolve an image digest; `migration` and `service` must require it. The migration/service executor must reject a missing, wrong-stage, wrong-source, wrong-plan-hash, wrong-lock, or wrong-digest receipt. No workflow success or publication artifact substitutes for this transition evidence.

### 2. Keep Terraform as sole configuration authority

For the first private fictional-synthetic target, Terraform alone creates and configures Cloud Run resources, including image digest, environment values, secret references, identities, ingress, IAM, network attachment, scaling, timeout, and retry settings.

The build workflow publishes the immutable image and its signed evidence. The deploy workflow may:

- verify existing Terraform-managed configuration;
- execute the already configured migration job without overrides;
- inspect typed Cloud Run readiness and the ready revision/digest; and
- produce bounded failure-safe evidence.

The deploy workflow may not create resources, mutate configuration, repair drift, change IAM, or replace a reviewed Terraform plan with imperative `gcloud ... update` behavior. A later automated-plan or signed-release-controller model requires a separate ADR.

### 3. Use IAM-private, internet-reachable tester ingress for develop

The first fictional-synthetic staff service will use `INGRESS_TRAFFIC_ALL` at the network layer while retaining the Cloud Run IAM invoker check. Exact service-level named tester principals receive invocation authority. `allUsers`, `allAuthenticatedUsers`, disabled invoker checks, and broad project-level invocation are prohibited.

Approved technical testers use individual Google identities through a loopback Cloud Run proxy or a bounded identity-token qualification procedure. This must be described as **IAM-private and internet-reachable**, not internal-network-only. It is a technical develop-test perimeter and does not satisfy production staff identity, MFA, session, recovery, or business authorization.

The first target uses an operator-held, review-bound set of exact individual tester identities. Terraform, verification, and Gate 5C/6 evidence must reject substituted, additional, empty, group, domain, principal-set, or public invokers. A later group-based access model requires a separate ADR amendment with membership-governance controls.

### 4. Narrow deploy-executor authority to existing-resource operations

The deploy workflow identity receives only:

- `roles/run.jobsExecutor` on the exact migration job; and
- `roles/run.viewer` on the exact migration job and staff service.

It does not receive `roles/run.developer`, `roles/run.admin`, `roles/run.jobsExecutorWithOverrides`, service-account impersonation, IAM mutation, secret access, image publication, Terraform provisioning, database credentials, or application invocation authority. Unexpected live permission requirements are stop-and-review events, not justification for automatic broadening.

Cancellation of a timed-out migration execution does not prove database rollback. A cancelled or unknown execution requires schema/database-authority inspection before retry or service activation.

### 5. Enforce direct-workflow WIF separation with `workflow_ref`

The GitHub WIF provider will map and enforce the signed direct-workflow `workflow_ref` claim alongside exact repository, owner, protected `develop` ref, named `develop` environment, and `workflow_dispatch` event conditions.

- Only `b-mackenzie-alexander/golden_rose_project/.github/workflows/build-image.yml@refs/heads/develop` may impersonate the image-publisher service account.
- Only `b-mackenzie-alexander/golden_rose_project/.github/workflows/deploy-develop.yml@refs/heads/develop` may impersonate the deploy-executor service account.
- The provisioner service account has no GitHub WIF impersonation binding until a separately accepted Terraform-apply workflow exists.

Repository-level shared impersonation and unnecessary `roles/iam.serviceAccountTokenCreator` bindings are prohibited. `job_workflow_ref` is not used because the accepted workflows are direct rather than reusable workflows.

### 6. Require digest-bound OCI/Sigstore provenance and SBOM evidence

The protected publication workflow will produce keyless Cosign signatures and signed in-toto attestations bound to the exact Artifact Registry image digest. Verification must require:

- the exact protected build-workflow certificate identity;
- GitHub Actions OIDC issuer;
- Sigstore transparency-log inclusion;
- SLSA v1 provenance tied to the exact repository commit and reviewed builder;
- an image-level SBOM covering final container contents; and
- checksum-bound, schema-validated backend and frontend CycloneDX SBOMs.

Publication and deployment independently verify the signature and attestations before migration or service activation. Tags, ordinary BuildKit metadata, workflow success, artifact names, and unsigned files are not sufficient authority.

Verification is required for every evidence class, not provenance alone: image-SBOM and application-SBOM checksum attestations must independently reject missing signature, wrong subject/predicate/media type, wrong certificate identity, wrong OIDC issuer, absent transparency proof, and digest mismatch. The image-level SBOM must be schema-valid, identify the same `linux/amd64` immutable image, and contain a nonempty final-image component inventory.

The limited public Sigstore transparency metadata is accepted. Secret payloads, credentials, application content, and operator-held environment identifiers must not enter signing, provenance, SBOM, logs, chat, or ordinary evidence.

This evidence proves signing identity, subject digest, source/build claims, and attached evidence integrity. It does not prove vulnerability freedom, independent review, deployment correctness, or production readiness.

### 7. Add authenticated no-traffic availability evidence

Cloud Monitoring will perform an authenticated HTTPS uptime check against the exact IAM-private staff service `/readiness` endpoint using Service Agent Authentication. The Monitoring service agent receives only exact service-level invocation authority through `roles/run.servicesInvoker` or the current narrow equivalent containing `run.routes.invoke`.

The check sends no business record, request body, synthetic staff identity, query data, or application secret. It validates a stable readiness response and records success/failure and latency. Repeated failure routes to an operator-held notification channel using provisional develop triggers that are not an SLA.

The uptime-check resource, its alert, and the Monitoring service-agent invocation binding exist only in `service`; they must be absent from `foundation` and `migration`. Gate 6 qualification also writes a minimized failure result before the first request and updates it atomically on a handled failure without retaining URLs, tokens, generated identities, identifiers, request/response bodies, or raw exception text.

Request-derived 5xx alerts remain complementary. Private Service Directory checks, a separate synthetic-monitor function, and unauthenticated health access are not required for the first target.

### 8. Preserve the revised gate model

The deployment path remains owner-controlled and sequential:

1. Accepted planning amendment and merged documentation-only packet.
2. No-cloud remediation implementation and merge after exact-head evidence and owner disposition of Blocker/High findings.
3. Separately approved read-only GCP qualification.
4. Separately approved bootstrap/backend ceremony and reviewed `foundation` plan.
5. Exact `foundation` apply and foundation-mode verification.
6. Separately approved immutable publication plus out-of-band secret/database preparation.
7. Reviewed `migration` plan/apply, configuration verification, authorized migration execution, and schema evidence.
8. Reviewed `service` plan/apply, exact named invocation, digest, and typed readiness verification.
9. Gate 6 foundation/database/application/access/log/alert/cost/recovery/browser/accessibility/English/Spanish qualification.

Passing one gate never grants the next.

### 9. Amendment A — independently verifiable transition and tester authorities

This amendment was accepted by Beatrice on 2026-08-21 after independent review of the first remediation implementation found that the stage-receipt and named-tester contracts were described but not executable.

1. A reviewed stage-plan receipt is an **operator-held signed blob**, never an artifact authored by the image-publication workflow. Its detached Sigstore bundle, the receipt bytes, and its declared SHA-256 are supplied only at manual dispatch from the protected `develop` environment. The deploy workflow must independently run `cosign verify-blob` against the configured, operator-held receipt certificate identity and GitHub OIDC issuer before parsing any receipt field. The receipt itself binds the stage, source SHA, plan/lock/non-secret-input digests, reviewed inventory, approval reference, and required workload digest. It is not uploaded by `build-image.yml` and must not be substituted by publication success or an unsigned GitHub artifact.
2. Deploy dispatch must select exactly one transition: `migration` or `service`. A migration transition verifies only its migration receipt and exact Terraform-owned migration-job projection, then executes the existing job without overrides. A service transition verifies a distinct service receipt, a separately signed successful migration-execution receipt bound to the migration receipt SHA-256 and image digest, and the exact Terraform-owned service projection before readiness inspection. Neither transition creates or mutates Cloud Run configuration.
3. The operator-held tester-authority receipt is also a signed blob. Before a Terraform plan/apply, the approved local ceremony verifies its detached Sigstore bundle and derives one exact `user:` principal plus a receipt SHA-256. Terraform receives only that derived principal and its immutable authority digest; the root and module reject missing/non-hex authority digests and the verifier independently repeats receipt verification before comparing live service IAM. A caller-supplied principal, digest, or syntactically valid substitute is never sufficient.
4. The deploy environment holds the non-secret expected certificate identities for stage and tester receipts as protected configuration, not tracked Terraform values. Receipt content, bundles, named identities, endpoints, plans, and approval records remain operator-held and must not enter logs, source, state, or ordinary evidence.
5. Deploy-time image authority must be established by fresh Cosign verification directly against the immutable OCI image. The workflow preserves raw `cosign verify` and `cosign verify-attestation` output only as bounded ephemeral execution input, verifies the signature, SLSA provenance, image-SBOM attestation, and application-SBOM-checksum attestation with the reviewed certificate identity/issuer, and parses their actual signed subjects/predicates. Workflow-authored JSON assertions and hand-constructed image SBOMs are prohibited. Before selecting the final-image SBOM generator, predicate, or Cosign v3 command shape, a separately approved isolated-registry compatibility spike must demonstrate the exact `linux/amd64` final-image SBOM subject, signed-attestation retrieval, and parser schema; no inferred attachment contract is authorized.

This amendment authorizes only the corresponding no-cloud source, test, and documentation remediation. It does not authorize receipt signing, cloud authentication, Terraform planning/apply, publication, deployment, tester access, or live verification.

## Consequences and constraints

### Positive

- Foundation apply becomes mechanically free of executable workload resources.
- Terraform remains the single desired-state authority.
- Migration execution and service activation are independently reviewable.
- Technical testers can reach the synthetic target without public invocation.
- Publisher, deploy executor, and dormant provisioner authority are materially separated at cloud trust.
- Image source, digest, provenance, and SBOM evidence become cryptographically bound.
- A silent or unreachable service can alert without waiting for agency traffic.

### Costs and risks

- The first deployment requires multiple plans, approvals, and evidence handoffs.
- IAM-private internet reachability still exposes the managed endpoint to network traffic that IAM must reject.
- Sigstore and OCI evidence add tool, registry, and transparency-log dependencies.
- The Monitoring service agent becomes another exact invoker that must be inventoried and reviewed.
- The same-repository-CI High remains open because trusted workflow files remain owner-controlled.
- Provider/live API behavior may require a bounded amendment, but may not be handled by broadening permissions or bypassing gates in place.

### Hard constraints

This ADR does not authorize GCP authentication, read-only inspection, backend migration, Terraform plan/apply, API enablement, provisioning, image publication, secret-version creation, database-login creation, migration execution, service activation, tester access, live qualification, real identity, live/client-derived data, public unauthenticated access, or production.

Project IDs, billing IDs, user emails, domains, principal values, backend values, plans, state, endpoints, credentials, secret payloads, and live evidence remain outside tracked source and ordinary documentation.

## Alternatives considered

### Separate Terraform roots/states for foundation, migration, and service

Rejected for the first target. It increases cross-state dependencies and duplicates authority. One required stage enum with exact graph/static tests preserves one workload-state authority.

### Let the deploy workflow update Cloud Run configuration

Rejected. It would create dual configuration authority and drift relative to Terraform.

### Keep internal-only ingress

Rejected for the first target because no approved local named-tester path exists. It would require an in-project runner, VPN, load balancer/IAP, or another separately costed access architecture.

### Grant Cloud Run Developer to the deploy workflow

Rejected after accepting Terraform-only configuration ownership. Viewer plus exact existing-job execution is the narrower supported shape.

### Use repository-level WIF principal sets or `job_workflow_ref`

Rejected. Repository-level bindings do not separate workflows, and `job_workflow_ref` applies to reusable workflows rather than the direct workflows used here.

### Accept checksum/workflow-run provenance as a Medium residual risk

Rejected. Digest-bound keyless signature and signed provenance/SBOM attestations are required now because retrofitting supply-chain authority becomes harder after promotion begins.

### Rely only on 5xx request metrics

Rejected. They cannot detect a silent or unreachable target without traffic.

## Approval, evidence, and revisit triggers

Beatrice explicitly accepted all seven decisions and the detailed Sigstore/transparency posture on 2026-08-20. This acceptance authorizes only publication of the planning amendment through the protected documentation workflow. It does not activate implementation until this ADR and its paired plan merge into protected `develop`.

Revisit this ADR if:

- direct workflows become reusable workflows;
- an independently administered release authority becomes available;
- Terraform application moves into CI;
- Cloud Run ingress changes to IAP, VPN, load balancer, or internal-only access;
- production staff identity or live data is admitted;
- Sigstore/Artifact Registry interoperability or transparency requirements materially change;
- monitoring moves from provisional develop triggers to approved production SLOs;
- multiple environments, regions, controllers, repositories, or maintainers become active constraints.
