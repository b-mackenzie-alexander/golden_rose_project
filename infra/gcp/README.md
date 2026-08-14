# GCP Terraform scaffold

This directory contains the repo-local Terraform scaffold for the Golden Rose private `develop` environment. The current branch is a validate-without-apply, local-validation, and static-policy implementation surface only.

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

The `infrastructure-quality` pull-request workflow runs local Terraform
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

Beatrice has approved moving into cloud implementation/testing after this scaffold branch is review-qualified, using the dedicated GCP deployment/testing project and fictional synthetic data only. Provisioning, remote state, named principals, alert recipients, billing scope, secret injection, migration execution, deployment, and production promotion remain evidence-bearing steps; real identity, live/client data, public access, and production remain separate approval gates.
