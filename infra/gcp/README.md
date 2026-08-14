# GCP Terraform scaffold

This directory contains the repo-local Terraform scaffold for the Golden Rose private `develop` environment. PR #24 merged this validate-without-apply, local-validation, and static-policy surface into protected `develop` at `50451b3`.

Independent post-merge review did not clear this scaffold as a provisioning/deployment baseline. PR #25 merged that documentation-only disposition at `8dc1198`. ADR-0010 and `.hermes/plans/2026-08-14_164545-pr24-terraform-remediation-plan.md` now define a separate validate-without-apply remediation for required-CI governance, semantic static-policy validation, deterministic `uv`, Cloud Run/private-SQL connectivity, API ordering, Cloud SQL backups, and managed Artifact Registry image authority before bootstrap implementation, plan, or apply.

Terraform is executed from `infra/gcp`. The root module declares `module "develop"` in `develop.tf` and loads the intended resource scaffold from `infra/gcp/develop/`; nested files are not relied on through recursive file presence alone. Local review must prove `terraform -chdir=infra/gcp graph` includes the expected `module.develop.google_*` resource nodes.

## Boundary

- fictional synthetic-only data boundary
- local state only for this slice
- remote state must be approved before shared apply
- Secret metadata and IAM may be modeled later, but No secret payloads belong in Terraform source, state, plans, logs, artifacts, containers, or ordinary docs.
- Project IDs, billing IDs, domains, user emails, credentials, and cloud-specific input values must stay in ignored/operator-held inputs, not tracked source.

## Allowed local validation

```text
terraform fmt -check -recursive infra/gcp
terraform -chdir=infra/gcp init -backend=false
terraform -chdir=infra/gcp validate
# Equivalent from inside infra/gcp: terraform init -backend=false; terraform validate
python scripts/validate_terraform_static.py
```

The current `infrastructure-quality` pull-request workflow runs local Terraform
format/init-without-backend/validate before the Terraform hygiene tests so a clean CI
checkout initializes providers before the graph regression runs. It also runs
static validation through `scripts/validate_terraform_static.py` with read-only repository
permissions. The scanner is designed to catch forbidden public IAM, broad IAM,
service-account key, secret payload, public network, NAT/firewall, and mutable
image-tag patterns without cloud access. It covers Terraform native HCL (`*.tf`) and
Terraform JSON configuration (`*.tf.json`) under the scanned Terraform root, including
JSON-form backend, provider credentials, and Cloud Run environment/secret-injection
keys. It also scans every GitHub workflow file for forbidden cloud/deployment
authority and requires every workflow `uses:` action reference to be pinned to a full
40-character commit SHA; this is not limited to `infrastructure*` workflow filenames.
Independent final-head probes proved that the current implementation is still a
lexically bypassable policy boundary despite those checks. Do not treat it as
semantic or fail-closed until ADR-0010's parser and adversarial tests are
implemented and independently cleared.

## Explicit non-scope

- No terraform apply
- No Terraform plan
- No GCP authentication for this local scaffold branch
- No API enablement from this local scaffold branch
- No resource provisioning from this local scaffold branch
- No workflow secrets
- No project or billing linkage
- No service identity creation
- No image push
- No Cloud SQL use
- No deployment
- No public access
- No real identity
- No live/client data
- No production work

## Approval gates

Beatrice has accepted a durable bootstrap/state control plane separate from disposable `develop` workload teardown. The existing non-workload project is the candidate control-plane boundary pending read-only qualification; the dedicated deployment/testing project remains the workload target. A separate reviewed bootstrap/state/WIF packet is required before backend migration, Terraform plan/apply, cloud authentication, or provisioning. Named principals, alert recipients, billing scope, secret injection, migration execution, deployment, real identity, live/client data, public access, and production remain separate evidence and approval gates.
