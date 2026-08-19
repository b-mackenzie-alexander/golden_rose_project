# GCP Terraform scaffold

This directory contains the repo-local Terraform scaffold for the Golden Rose private `develop` environment. PR #24 merged this validate-without-apply, local-validation, and static-policy surface into protected `develop` at `50451b3`.

PR #29 merged semantic static-policy validation, deterministic `uv`, Cloud Run/private-SQL declaration, API ordering, Cloud SQL backup enablement, and managed Artifact Registry image authority into protected `develop` at `08fe305`. No independent reviewer/CODEOWNER exists; the same-repository-CI High therefore remains open accepted residual risk. Accepted ADR-0012 adopted the permanent solo-maintainer posture and authorized one consolidated source-controlled pre-deployment implementation lane. That local implementation now extends through Task 15 clean-room qualification on `feat/consolidated-predeployment-foundation` and is awaiting independent review handoff before commit/push/PR closeout. Read-only cloud qualification, Terraform plan, foundation apply, first private synthetic deployment, and qualification remain separate explicit Beatrice-owned gates.

Terraform is executed from `infra/gcp` for the disposable workload root and from `infra/gcp/bootstrap` for the lifecycle-independent state bootstrap root. The workload root declares `module "develop"` in `develop.tf` and loads the intended resource scaffold from `infra/gcp/develop/`; nested files are not relied on through recursive file presence alone. The bootstrap root is separate from the disposable workload root and exists only to define the durable remote-state bucket plus its one-time operator ceremony. Local review must prove `terraform -chdir=infra/gcp graph` includes the expected `module.develop.google_*` resource nodes and must keep bootstrap resources out of the disposable workload graph.

## Boundary

- fictional synthetic-only data boundary
- local state only for this slice
- remote state must be approved before shared apply
- `infra/gcp/backend.tf` is partial backend configuration only; operator-held values must be supplied out of band and are never committed in source.
- Bootstrap state uses operator-supplied project, location, bucket, and principal values with no committed defaults.
- Bootstrap WIF trust is exact and keyless: only the reviewed `b-mackenzie-alexander/golden_rose_project` `develop` branch plus the named `develop` deployment environment may impersonate bootstrap-reviewed automation identities; pull-request subjects, wildcard claims, broad principal sets, and service-account keys are forbidden.
- Workload IAM is least-privilege and value-safe: runtime and migration identities receive only the reviewed Cloud SQL, logging, metrics, and exact secret-access bindings; the image-publisher and deployer principals are operator-held inputs; private invocation is explicit and never public.
- The serialized migration boundary is explicit: `infra/gcp/develop/migration_job.tf` is the only reviewed Cloud Run job path, it must use the same immutable managed application digest as the web service, it runs as the separate migration identity over Direct VPC/private ranges only, and it may not commit secret payloads or runtime-startup migration behavior.
- Application migration execution is fail-closed and source-controlled: `golden-rose-migrate` must hold one PostgreSQL advisory lock for the full Alembic upgrade and exit non-successfully on lock contention before any service rollout gate proceeds.
- Database authority remains separate from workload runtime: the reviewed schema-owner role is non-login, runtime privileges stay bounded to explicit DML/readiness needs, migration authority is reviewed separately, and `scripts/verify_database_authority.py` must fail closed on drift before later deployment qualification.
- Cloud SQL metadata remains value-safe and recovery-gated: the scaffold may model one reviewed private PostgreSQL 16 instance plus one application database and non-secret role identifiers, but passwords and user creation stay out of Terraform, and backup/PITR/retention inputs remain explicit operator-held values with the marker `gate-2-evidence-required` until later recovery evidence is accepted.
- Task 8 cost and observability controls are source-controlled but still no-cloud only: `infra/gcp/develop/budgets.tf` fixes the reviewed $50/$75/$100 thresholds, routes alerts only through operator-held notification inputs, and keeps alerts explicitly non-cap. `infra/gcp/develop/observability.tf` adds reviewed notification-channel, alert-policy, log-retention, and value-safe viewer/access contracts without creating any export sink or logging request bodies/SQL values.
- Workload startup is intentionally gated on reviewed cost/observability resources: `infra/gcp/develop/cloud_run.tf` and `infra/gcp/develop/migration_job.tf` both depend on the reviewed budget/alert/log-retention contract so later deployment work cannot claim readiness before those prerequisites exist.
- Task 9 immutable-build authority is source-controlled and still no-cloud only: `.github/workflows/build-image.yml` keeps pull requests limited to local build/SBOM/provenance validation with read-only repository permissions, reserves WIF-backed publication for the named `develop` environment on a separate workflow-dispatch path, uploads only value-safe evidence artifacts, and captures the immutable Artifact Registry digest so later deployment work can refuse mutable tags. `scripts/verify_image_provenance.py` fail-closes on missing digest, reviewed base-image pins, absent provenance metadata, or missing SBOM evidence.
- Task 10 deploy authority is source-controlled and still no-cloud only: `.github/workflows/deploy-develop.yml` accepts only an immutable digest input, requires the exact protected `develop` ref plus named `develop` environment, uses only the reviewed deployer WIF path, serializes `run-migrations` before `staff-tracer` rollout under workflow concurrency, and emits only value-safe forward-only compatibility/readiness evidence while leaving synthetic qualification to a later separate tool/gate.
- Task 11 live-foundation qualification tooling is source-controlled but still read-only and separately gated: `scripts/verify_gcp_foundation.py` checks live labels, API inventory, private invoker posture, private Cloud SQL posture, no service-account keys, exact project/service-account IAM, state bucket recovery controls, reviewed budget/alert route presence, and bounded logging posture without adding any mutation mode; `deploy/gcp/evidence-template.md` records the value-safe evidence shape for that later read-only qualification gate.
- Task 12 private-synthetic deployment qualification tooling is source-controlled but still separate from deployment itself: `scripts/qualify_develop_deployment.py` requires authenticated private access, keeps `/health` and `/readiness` as non-mutating probes, exercises only bounded Employer and EmployerContact create/read/search/revision/replay flows with newly generated fictional values, emits minimized evidence that redacts submitted identifiers/cursors/tokens/DSNs/raw bodies, and records cleanup as teardown/rebuild disposition rather than inventing delete semantics.
- Task 13 operator procedures are source-controlled but still no-cloud only: `deploy/gcp/first-deployment-runbook.md` defines the out-of-band secret custody/injection ceremony and `deploy/gcp/private-tester-access.md` defines named private tester access while synthetic auth remains. Both procedures keep payloads, tester identities, and private endpoints out of Terraform, chat, repo artifacts, and ordinary docs.
- Secret metadata and IAM may be modeled later, but No secret payloads belong in Terraform source, state, plans, logs, artifacts, containers, or ordinary docs.
- Private tester access must remain named and service-level only; `allUsers`, `allAuthenticatedUsers`, and project-wide convenience bindings are forbidden.
- Project IDs, billing IDs, domains, user emails, credentials, and cloud-specific input values must stay in ignored/operator-held inputs, not tracked source.
- The approved ceremony remains explicit: local bootstrap → remote state migration → WIF handoff → bootstrap-authority retirement. State access, emergency recovery, client handoff, and teardown exclusions remain runbook-controlled and value-safe.

## Allowed local validation

```text
terraform fmt -check -recursive infra/gcp
terraform -chdir=infra/gcp init -backend=false
terraform -chdir=infra/gcp validate
terraform -chdir=infra/gcp/bootstrap init -backend=false
terraform -chdir=infra/gcp/bootstrap validate
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
authority, requires every workflow `uses:` action reference to be pinned to a full
40-character commit SHA, and now permits only the reviewed `build-image.yml` WIF/id-token
publish path plus the reviewed `deploy-develop.yml` deployer path while keeping the
pull-request path cloud-blind; this is not limited to `infrastructure*` workflow
filenames.
The manifest also records `scripts/verify_gcp_foundation.py` as an approved
read-only verification entrypoint so later Gate 2 qualification can use a
reviewed source-controlled tool instead of ad-hoc cloud inspection notes.
Independent final-head probes on the earlier PR #24 surface proved the original
implementation was still a lexically bypassable policy boundary. The ADR-0011
solo-maintainer remediation sequence merged through PR #29. Those
controls remain quality evidence rather than independent authorization, and
they do not clear the open same-repository-CI High or grant cloud authority by
themselves. Accepted ADR-0012 now governs the consolidated local implementation boundary and later gate-evidence closeout.

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

Beatrice has accepted a durable bootstrap/state control plane separate from disposable `develop` workload teardown. The existing non-workload project is the candidate control-plane boundary pending separately approved read-only qualification; the dedicated deployment/testing project remains the workload target. Accepted ADR-0012's consolidated implementation lane now contains the bootstrap/state/WIF and remaining source-controlled pre-deployment contract. Even with local implementation complete through Task 15, read-only qualification, backend migration, Terraform plan, apply, out-of-band secret injection, named private tester access, migration execution, deployment, real identity, live/client data, public access, and production remain separate evidence and approval gates.
