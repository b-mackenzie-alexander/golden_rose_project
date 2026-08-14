# PR #24 remediation planning-packet review handoff

**Date:** 2026-08-14
**Branch:** `docs/pr24-remediation-plan`
**Base:** exact `origin/develop` at `8dc1198c0eb571ca39e9f4814bb3af5e33079890`
**Scope:** planning and source-of-truth documentation only
**Target:** protected `develop`

## Purpose

Review the bounded implementation plan and architecture decision that follow PR #25's documentation-only closeout of PR #24. This branch must not change workflow YAML, repository policy JSON/scripts, Python dependencies/lockfile, validator code/tests, Terraform, or cloud state.

Primary packet:

- `.hermes/plans/2026-08-14_164545-pr24-terraform-remediation-plan.md`
- `docs/adr/ADR-0010-pr24-terraform-remediation-boundary.md`

The plan must cover all final-head findings in this exact order:

1. required-CI authority — High;
2. semantic static-policy enforcement — High;
3. deterministic `uv` — Medium;
4. private Cloud Run → Cloud SQL path — Medium;
5. API activation ordering — Medium;
6. Cloud SQL automated backups — Medium;
7. managed Artifact Registry image authority — Medium.

## Planning decisions to challenge

### Independent CI authority

The packet rejects a new same-repository status name as insufficient. It requires a genuinely independent GitHub collaborator/CODEOWNER, one approval, stale-review dismissal, last-push approval, and critical-path ownership before implementation begins. The implementation PR is a bootstrap case that itself requires the independent review; post-merge policy apply/read-back is separately authorized.

Reviewers should determine whether this honestly closes self-authorization, whether the protected path list is sufficient, whether the required Terraform context runs on every protected-branch PR, and whether any text falsely implies current repository settings already provide this control. The staged bootstrap must not require CODEOWNERS or merge-event evidence before merge: pre-branch account evidence, pre-merge exact-head approval/checks/eligibility, post-merge exact-head/no-bypass and `develop` CODEOWNERS proof, and separately authorized both-branch policy read-back are distinct. `main` receives non-author/last-push approval immediately but no claimed CODEOWNER resolution until the file reaches that base. If any required evidence or independent reviewer is unavailable, the High remains open for the affected branch/stage.

### Semantic validator

The packet selects `python-hcl2==8.1.2`, duplicate-rejecting JSON decoding, and `ruamel.yaml==0.19.1` YAML 1.2 safe parsing with duplicate-key rejection. Protected `infra/policy/static-validation-manifest.json` covers exact Terraform files/types/labels/cardinality/paths/guarded values and complete workflow/job/step semantics, including action inputs, environment values, shell, working directory, conditions, runner, permissions, and unknown fields. Adversarial coverage includes Unicode/duplicate JSON keys, alternate/duplicate YAML forms, renamed or unknown workflows, local/reusable workflows, mutable actions/containers/inputs, execution-field changes, destructive commands, extra allowed-type instances, unapproved APIs, dynamic guarded values, secret-safe diagnostics, malformed documents, and required-job body replacement. The validator executes through locked `uv`; Tasks 3–7 must first show the prior manifest rejects each new structure before exact source/manifest updates.

Reviewers should look for representational gaps, unsafe parser behavior, alias/duplicate-key ambiguities, structural allowlist gaps, local/reusable-action gaps, command construction bypasses, secret-value disclosure, and tests that merely assert source strings rather than semantic outcomes. A parsed command denylist alone is not acceptable.

### Direct VPC egress

The packet selects Cloud Run v2 Direct VPC egress through an explicit regional `/26`-or-broader RFC1918 subnet with `PRIVATE_RANGES_ONLY`, while preserving private Cloud SQL and no public invoker IAM. The CIDR remains a required non-secret input with no committed environment value.

Reviewers should validate provider v6.50.0 schema compatibility, subnet sizing, resource/API graph, private SQL reachability, and absence of accidental all-traffic egress, connector/NAT/public-edge scope, or cloud-runtime claims.

### Backup and artifact limits

The packet enables only automated backups, not PITR/retention/RTO/RPO claims. It changes image input authority to digest-only and derives the host/project/region/repository/image path from managed Terraform values.

Reviewers should ensure these boundaries close the findings without inventing recovery evidence or leaving caller-controlled registry provenance.

## No-side-effect boundary

This planning branch authorizes no:

- GCP authentication, API query, credential/secret handling, or account qualification;
- Terraform backend, plan, apply, migration, API enablement, or provisioning;
- GitHub repository-policy mutation or collaborator invitation;
- dependency/lockfile change, workflow change, validator/test change, or Terraform implementation;
- image build/push, database migration, service start, deployment, public access, real identity, live/client data, or production work.

Read-only local Git/GitHub inspection and public documentation/package metadata lookup were used to ground the plan. No cloud operation occurred.

## Evidence posture

- **Validated:** PR #25 merged to protected `develop` at `8dc1198`; its source branch was deleted and checks passed.
- **Observed:** repository is private/personal, has one administrator, classic branch protection, no rulesets/environments, and no independent status producer.
- **Validated:** PR #24 final-head review found two High and five Medium defects; PR #25 recorded but did not fix them.
- **Proposed/accepted planning boundary:** exact implementation and test sequence in ADR-0010 and the paired plan.
- **Not validated:** independent reviewer availability, live future policy, semantic implementation, Terraform runtime graph after remediation, cloud connectivity, backups/restores, registry push/provenance, provisioning, deployment, or runtime readiness.

## Executed preliminary qualification

Executed locally on the uncommitted planning working tree:

- documentation-only status inspection: 18 Markdown files, no non-Markdown path;
- `git diff --check` — passed;
- `terraform fmt -check -recursive infra/gcp` — passed;
- `terraform -chdir=infra/gcp init -backend=false -input=false` — reused locked `hashicorp/google v6.50.0` and passed;
- `terraform -chdir=infra/gcp validate` — passed;
- `terraform -chdir=infra/gcp graph` — passed, 22 output lines;
- `python scripts/validate_terraform_static.py` — passed for the unchanged current implementation, without claiming the known lexical bypass is fixed;
- `env -u PYTHONPATH uv run pytest tests/unit/test_terraform_hygiene.py -q` — `100 passed in 2.57s`;
- `gitleaks dir --no-banner --redact .` — scanned approximately 7.45 MB with no leaks found.

These checks prove only that the documentation branch did not disturb the current backend-free scaffold. They do not qualify any planned remediation or cloud/runtime behavior.

## Required review result

Return one of:

- `ACCEPT` — no Blocker, High, or Medium planning/documentation finding remains; or
- `CHANGES REQUESTED` — list each finding with severity, exact file/section, failure mode, and minimum correction.

A Blocker, High, or Medium finding blocks commit/publication. Low editorial findings may be recorded but do not block unless they cause ambiguity in authority, evidence, sequencing, or stop boundaries.

## First independent review and remediation

The first three-way review returned `CHANGES REQUESTED` with two High and six Medium findings. The packet was corrected to require:

- an unconditional required Terraform context on every protected-branch PR;
- exact collaborator/CODEOWNERS/review-head/latest-pusher/no-bypass/live-policy evidence;
- executable staged bootstrap sequencing that does not claim pre-merge or absent-`main` CODEOWNERS authority;
- locked-environment validator execution in CI and local qualification;
- a Terraform manifest covering files, labels/cardinality, guarded values, and unknown/dynamic instances;
- duplicate-name rejection for JSON as well as YAML;
- canary-backed redaction tests for parser and policy diagnostics;
- semantically tested `uv --version` ordering before dependency operations;
- removal of the false current immutable-tag-posture claim.

The remediated exact working tree received focused rereview; findings were not considered cleared merely because text changed.

The first focused rereview accepted the Terraform/documentation lane but found two further High and one Medium contract defects. Governance bootstrap evidence had been ordered before the CODEOWNERS file could exist and implied `main` path ownership before promotion. Semantic policy did not bind all execution-affecting workflow fields, and later tasks would have changed exact structures without their own manifest RED → GREEN updates. The packet now uses staged pre-branch/pre-merge/post-merge/post-activation governance evidence, distinguishes `develop` CODEOWNERS from `main`'s immediate non-author approval control, protects one explicit static-validation manifest, binds complete workflow execution semantics, and requires Tasks 3–7 to prove rejection before source/manifest updates. The second semantic rereview returned `ACCEPT`; governance found one remaining temporal contradiction because pre-merge Stage B required a completed merge. That proof now occurs only in post-merge Stage C. The final governance-only rereview returned `ACCEPT` with no remaining Medium-or-higher findings. The Terraform/documentation, semantic-manifest, and staged-governance lanes are independently accepted for planning publication.

## Reviewer checklist

- all seven defects present exactly once and in required order;
- required-CI solution is genuinely independent and does not use an author-controlled alternate account;
- governance bootstrap and post-merge apply/read-back sequencing are explicit;
- scanner design is semantic, fail-closed, and adversarially tested;
- exact `uv` version/checksum contract is consistent in both workflows;
- exact `uv --version` evidence precedes both workflows' first dependency operation;
- Direct VPC architecture retains private SQL/no public ingress;
- API dependencies are exact rather than sleeps/provisioners;
- backup configuration does not claim restore qualification;
- image input cannot select another registry/project/region/repository/name/tag;
- living docs distinguish planned, implemented, and validated states;
- planning diff contains documentation only;
- cloud/backend/plan/apply/deployment bootstrap work remains prohibited.
