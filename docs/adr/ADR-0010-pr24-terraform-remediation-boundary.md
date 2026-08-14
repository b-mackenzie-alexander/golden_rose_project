# ADR-0010: PR #24 Terraform remediation boundary

- **Status:** Accepted historical planning boundary; execution supersession proposed in ADR-0011
- **Date:** 2026-08-14
- **Owners:** Beatrice Alexander (engagement owner)
- **Related:** ADR-0001, ADR-0009, ADR-0011, `.hermes/plans/2026-08-14_164545-pr24-terraform-remediation-plan.md`, `.hermes/plans/2026-08-14_174830-pr24-solo-maintainer-remediation-amendment-plan.md`

## Context and evidence posture

PR #24 merged a backend-free Terraform validation scaffold into protected `develop` at `50451b3`. Its configured checks passed, but independent final-head review found two High and five Medium defects. PR #25 merged the documentation-only disposition into `develop` at `8dc1198`, and PR #26 merged this original planning packet at `c5a1380`; neither event remediated implementation or granted cloud authority. Live evidence then established that no independently controlled reviewer/CODEOWNER exists in this single-maintainer repository. ADR-0011 proposes the successor execution boundary.

Validated findings:

1. required GitHub Actions checks are emitted by PR-editable same-repository workflows and are therefore self-authorizing without independent review ownership;
2. the Terraform/workflow policy validator relies on lexical matching and accepted semantically privileged alternate representations;
3. required workflows did not select an exact reviewed `uv` binary artifact;
4. Cloud Run had no declared path to private Cloud SQL;
5. dependent resources were not ordered after API activation;
6. Cloud SQL omitted the accepted automated-backup baseline;
7. callers could provide a digest-qualified image from outside the managed regional Artifact Registry.

Observed repository governance at planning time is a private personal repository with one administrator, classic branch protection, zero required approvals, no CODEOWNERS, no rulesets, no environments, and no independent status producer. A new same-repository job name cannot eliminate the first High because the pull request can edit the job that emits it.

Provider and tool documentation supports Cloud Run v2 Direct VPC egress through an explicit subnetwork, Cloud SQL `settings.backup_configuration.enabled`, exact setup-uv `version` and `checksum` inputs, HCL2 parsing through a dedicated parser, and YAML 1.2 safe parsing with duplicate-key rejection.

## Decision

### 1. Independent required-CI authority

The repository will move from the documented solo-maintainer residual-risk protocol to a real non-author review boundary before remediation implementation begins.

Beatrice must nominate another accountable person with an independently controlled GitHub account and grant that person repository write/CODEOWNER responsibility. The reviewer cannot be the author, last pusher, Beatrice's alternate account, or an agent using Beatrice's credentials. With only one independent reviewer, the author must push requested corrections; a reviewer who becomes the latest pusher requires a second eligible approver. Protected `develop` and `main` will require one approval, stale-review dismissal, CODEOWNER review, approval after the latest push, and the required `enforce`, `check`, `application`, and `Terraform static validation` contexts.

Critical authority paths include workflows, CODEOWNERS itself, repository policy/apply/verify code, the semantic validator and its policy tests, and dependency lock surfaces. The implementation PR receives the independent bootstrap review. `Terraform static validation` must run unconditionally on every protected-branch pull request before it becomes required. After merge and separate authorization, policy is applied from protected `develop` and read back. Source declarations alone do not close the High.

Bootstrap is staged because the current base has no CODEOWNERS file. Before implementation, evidence proves only collaborator permission and actor separation. Before bootstrap merge, it proves independent approval bound to the exact final head after the latest author push, latest-pusher separation, exact-head checks, and merge eligibility under the then-live policy. After merge, it proves the exact reviewed head merged without administrator bypass and verifies effective CODEOWNERS resolution on `develop`; only then may separately authorized policy application/read-back occur. Both branches immediately require one non-author approval and last-push approval. `main` does not receive claimed path-specific CODEOWNER enforcement until the reviewed file reaches that base branch through a later protected promotion. Missing or ambiguous evidence leaves the High open for the affected branch/stage.

If no eligible reviewer is nominated and verified, the High remains open and remediation implementation stops. An independently controlled GitHub App may replace the human reviewer only through a separately reviewed amendment.

### 2. Semantic policy boundary

Terraform HCL will be parsed with locked `python-hcl2==8.1.2`; `.tf.json` with standard JSON parsing plus duplicate-name rejection; and workflows with locked `ruamel.yaml==0.19.1` YAML 1.2 safe parsing with duplicate-key rejection. Parse errors fail closed. Protected `infra/policy/static-validation-manifest.json` binds Terraform files, block kinds, types, labels/cardinality, paths, and guarded values, rejecting unknown instances and dynamic guarded values. It also binds the complete semantic workflow/job/step object, including action inputs, environment values, shell, working directory, conditions, runner, permissions, and every other accepted execution-affecting field; unknown fields and dynamic values fail closed.

Adversarial tests cover Unicode-escaped and duplicate JSON keys, YAML alternate/duplicate forms, renamed/unknown workflows, mutable actions/containers and action inputs, local/reusable workflow calls, execution-field mutations, write permissions, destructive or newly constructed commands, malformed documents, extra instances of allowed Terraform types, unapproved APIs, dynamic guarded values, secret-safe diagnostics, and required-job-name body replacement. The validator runs through the locked `uv` environment. Each later task must first prove the current manifest rejects its new structure, then update exact source and manifest objects together; future authority is never pre-authorized. Lexical checks may remain only as defense-in-depth.

### 3. Deterministic uv

Both required workflows will retain the reviewed `setup-uv` action commit and select `uv 0.12.5` with the official Linux x86-64 archive SHA-256 `68a509da24b06b4223a1c0175fb5eb5bc79342b76cbeff0cfe51ac3f5b17b6b2`. They will emit `uv --version` before use. Upgrades require one reviewed change to both workflows, checksum evidence, tests, and lock qualification.

### 4. Private Cloud Run-to-SQL path

Use Cloud Run v2 Direct VPC egress with one explicit regional `/26`-or-broader RFC1918 subnet in the dedicated workload VPC and `PRIVATE_RANGES_ONLY` egress. The CIDR is a required non-secret input with no committed environment value until later read-only qualification proves it non-overlapping. Keep Cloud SQL private and Cloud Run without public invoker IAM. Do not add a connector, NAT, external address, broad route, or public database path.

### 5. API activation ordering

Every dependent Terraform resource will use exact `depends_on` references to the relevant `google_project_service.approved` instances. Resource references continue to establish resource ordering. Sleeps, provisioners, local-exec, and blanket dependency shortcuts are rejected.

### 6. Cloud SQL backup baseline

Add only `settings.backup_configuration { enabled = true }`. This is static automated-backup configuration, not restore evidence. Start time, retention, PITR, transaction-log retention, RTO/RPO, restore cadence, and production policy remain unresolved and must not be inferred.

### 7. Managed Artifact Registry image authority

Callers provide only `sha256:` plus 64 lowercase hexadecimal characters. Terraform derives the complete image reference from `var.region`, `var.project_id`, the managed `google_artifact_registry_repository.application_images.repository_id`, fixed image name `staff-tracer`, and the digest. Callers cannot select another host, project, region, repository, image name, or tag.

## Consequences and constraints

- Independent review becomes an operational dependency and may slow delivery; that cost is accepted because same-repository CI cannot independently authorize itself.
- The current owner-only repository cannot implement this ADR until an eligible reviewer is supplied.
- Parser dependencies enlarge the reviewed development supply chain but replace an invalid lexical security boundary.
- Direct VPC egress avoids connector resources/cost but requires a dedicated subnet and later non-overlap qualification.
- Explicit API dependencies make the Terraform graph more accurate without proving cloud readiness.
- Enabling backups can create storage cost only if later applied; this ADR authorizes no apply and makes no recovery guarantee.
- Digest-only input narrows caller flexibility intentionally and preserves one managed repository as image authority.
- Bootstrap/state/WIF architecture remains lifecycle-independent from disposable workload resources and is not implemented here.
- No GCP authentication, backend migration, Terraform plan/apply, provisioning, image push, deployment, service start, real identity, live/client data, or production work is authorized.

## Alternatives considered

### Another required same-repository workflow

Rejected. A PR can alter the workflow and retain the expected status name; renaming the check does not create independent authority.

### Solo delegated-agent review only

Rejected as closure for the High. It remains valuable review evidence but uses the repository owner's authority and cannot satisfy a non-author protected-branch approval.

### Alternate account controlled by the author

Rejected. It creates the appearance rather than substance of independent approval.

### Organization required-workflow/ruleset migration or external GitHub App

Potentially strong, but not currently available/configured in this personal repository and materially broader than this bounded remediation. It remains a revisit option.

### Serverless VPC Access connector

Rejected for this baseline. Direct VPC egress supplies the private path with fewer managed components; a connector may be reconsidered if later runtime evidence proves Direct VPC unsuitable.

### Full image reference input with regex validation

Rejected. Regex validation would duplicate managed repository identity and still leave more caller-controlled provenance surface than a digest-only input.

### Enable PITR and define retention/RTO/RPO now

Rejected. Those decisions require recovery ownership and evidence not present in this planning slice. Only the already accepted automated-backup baseline is encoded.

## Approval, evidence, and revisit triggers

Beatrice authorized creation and publication of this bounded planning packet on 2026-08-14. The exact implementation remains separately authorized and cannot start until the independent reviewer identity is provided and verified.

Revisit this ADR if:

- an organization-level required-workflow facility or independently controlled GitHub App becomes available;
- Direct VPC egress cannot meet private connectivity, cost, or runtime evidence requirements;
- Cloud SQL recovery ownership establishes approved PITR/retention/RTO/RPO;
- managed image naming or promotion requires more than the fixed `staff-tracer` repository path;
- semantic parser limitations prevent fail-closed evaluation of supported repository syntax.
