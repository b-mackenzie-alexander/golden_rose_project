# GCP Terraform scaffold

This directory contains the repo-local Terraform scaffold for the Golden Rose private `develop` environment. PR #24 merged this validate-without-apply, local-validation, and static-policy surface into protected `develop` at `50451b3`.

Foundation/state work, Gate P, bounded Gate S, both named-human bootstrap authority transitions, exact apply/readback, and provisioner-owned workload-backend proof are complete. ADR-0015 merged through PR #79 at `develop@e7bab147` to resolve the later quota-authority conflict through a billing-authorized FinOps root with a separately IAM-isolated state bucket, signed receipt admission, and import-before-remove transfer. Only Implementation PR A source work is authorized next; no IAM/state, Terraform plan/apply, migration, service, tester, or qualification operational action is authorized. The workload provisioner retains no project-level role or FinOps-state access.

Terraform is executed from `infra/gcp` for the disposable workload root and from `infra/gcp/bootstrap` for the lifecycle-independent state bootstrap root. The workload root declares `module "develop"` in `develop.tf` and loads the intended resource scaffold from `infra/gcp/develop/`; nested files are not relied on through recursive file presence alone. The bootstrap root is separate from the disposable workload root and exists only to define the durable remote-state bucket plus its one-time operator ceremony. Local review must prove `terraform -chdir=infra/gcp graph` includes the expected `module.develop.google_*` resource nodes and must keep bootstrap resources out of the disposable workload graph.

## Original scaffold boundary and current authority

- fictional synthetic-only data boundary
- the original validate-without-apply slice used local state only and granted no remote-state authority
- separately approved E2/E3 operations later established and verified distinct remote bootstrap/workload state lineages; those completed operations do not authorize another backend/state action
- `infra/gcp/backend.tf` is partial backend configuration only; operator-held values must be supplied out of band and are never committed in source.
- Bootstrap state uses operator-supplied project, location, bucket, and principal values with no committed defaults.
- Accepted remediation requires WIF trust to map direct-workflow `workflow_ref`: exact `build-image.yml@refs/heads/develop` may impersonate only the publisher, exact `deploy-develop.yml@refs/heads/develop` only the deploy executor, and the provisioner has no GitHub WIF binding until a separately accepted apply workflow exists. Pull-request subjects, wildcard claims, shared repository principal sets, unnecessary Token Creator bindings, and service-account keys are forbidden.
- Workload IAM remains least-privilege and value-safe. The deploy executor receives exact-job `roles/run.jobsExecutor` plus exact job/service `roles/run.viewer`, not Cloud Run Developer/Admin, overrides, service-account impersonation, secret access, publication, or provisioning authority. Tester invocation is exact service-level IAM over an internet-reachable endpoint and is never public/broad invocation.
- The serialized migration boundary is explicit: `infra/gcp/develop/migration_job.tf` is the only reviewed Cloud Run job path, it must use the same immutable managed application digest as the web service, it runs as the separate migration identity over Direct VPC/private ranges only, and it may not commit secret payloads or runtime-startup migration behavior.
- Application migration execution is fail-closed and source-controlled: `golden-rose-migrate` must hold one PostgreSQL advisory lock for the full Alembic upgrade and exit non-successfully on lock contention before any service rollout gate proceeds.
- Database authority remains separate from workload runtime: the reviewed schema-owner role is non-login, runtime privileges stay bounded to explicit DML/readiness needs, migration authority is reviewed separately, and `scripts/verify_database_authority.py` must fail closed on drift before later deployment qualification.
- Cloud SQL metadata remains value-safe and recovery-gated: the scaffold may model one reviewed private PostgreSQL 16 instance plus one application database and non-secret role identifiers, but passwords and user creation stay out of Terraform, and backup/PITR/retention inputs remain explicit operator-held values with the marker `gate-2-evidence-required` until later recovery evidence is accepted.
- Foundation cost and observability controls are present and verified. The existing `infra/gcp/develop/budgets.tf` remains the sole desired/state owner until Implementation PR A merges and the accepted state-transfer/PR-B sequence completes under continuous freeze. The accepted plan preserves the exact $50/$75/$100 non-cap posture and routes alerts only through operator-held notification inputs while separating billing API/quota authority from the workload provisioner.
- Workload startup remains gated on the reviewed cost/observability contract. Until ADR-0015's implementation/state sequence completes, that is the direct Terraform budget dependency. PR B may replace it only with a freshly signed, exact FinOps receipt admission after single state ownership is proven; no caller assertion or stale receipt is sufficient.
- Task 9 immutable-build authority is source-controlled and Gate P is complete. PR #74 merged canonical Cosign v3 signature admission at `develop@92b104e`; run `33882394981` completed immutable publication, keyless signing, all attestations, certificate/transparency verification, final repository semantic admission, and verifier-approved immutable-reference emission. `scripts/verify_image_provenance.py` and deployment admission remain fail-closed on identity/digest/provenance/SBOM evidence.
- Task 10 deploy authority is source-controlled and still no-cloud only: `.github/workflows/deploy-develop.yml` accepts only an immutable digest input, requires the exact protected `develop` ref plus named `develop` environment, uses only the reviewed deployer WIF path, serializes `run-migrations` before `staff-tracer` rollout under workflow concurrency, and emits only value-safe forward-only compatibility/readiness evidence while leaving synthetic qualification to a later separate tool/gate.
- Task 11 live-foundation qualification tooling remains read-only and separately gated by stage: `scripts/verify_gcp_foundation.py` verifies the named-human Token Creator member only on the provisioner service account, rejects WIF/project-wide alternatives, and now also requires that provisioner independently in the exact state-bucket Object Admin set even when human state/recovery authorities differ. The verifier can complete the amended contract only after a separately approved bootstrap apply and exact readback. Later stages remain responsible for private invoker and private Cloud SQL checks when those resources enter scope. `deploy/gcp/evidence-template.md` records the value-safe evidence shape.
- Task 12 private-synthetic deployment qualification tooling is source-controlled but still separate from deployment itself: `scripts/qualify_develop_deployment.py` requires authenticated private access, keeps `/health` and `/readiness` as non-mutating probes, exercises only bounded Employer and EmployerContact create/read/search/revision/replay flows with newly generated fictional values, emits minimized evidence that redacts submitted identifiers/cursors/tokens/DSNs/raw bodies, and records cleanup as teardown/rebuild disposition rather than inventing delete semantics.
- Task 13 operator procedures are source-controlled but still no-cloud only: `deploy/gcp/first-deployment-runbook.md` defines the out-of-band secret custody/injection ceremony and `deploy/gcp/private-tester-access.md` defines named private tester access while synthetic auth remains. Both procedures keep payloads, tester identities, and private endpoints out of Terraform, chat, repo artifacts, and ordinary docs.
- Secret metadata and IAM may be modeled later, but No secret payloads belong in Terraform source, state, plans, logs, artifacts, containers, or ordinary docs.
- Private tester access must remain named and service-level only; `allUsers`, `allAuthenticatedUsers`, and project-wide convenience bindings are forbidden.
- Project IDs, billing IDs, domains, user emails, credentials, and cloud-specific input values must stay in ignored/operator-held inputs, not tracked source.
- The foundation ceremony and Gate P are complete. Gate S has one validated bounded result at protected source `develop@375038e`: the sole `synthetic-staff-id` version exists and passed metadata-only readback. Runtime/migration database-URL versions remain deferred until real migration-stage database/login material exists. Migration plan/apply/execution, service, tester, qualification, recovery/handoff, and teardown remain separately approved.

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
The manifest records the currently approved read-only verification entrypoints. Both bootstrap authority transitions and workload-backend proof completed under consumed approvals. ADR-0015 merged through PR #79 and now governs the FinOps separation direction; no historical packet or approval is reusable. Only Implementation PR A source work is next, and every later IAM/state/migration/service gate remains separately approved.
Independent final-head probes on the earlier PR #24 surface proved the original
implementation was still a lexically bypassable policy boundary. The ADR-0011
solo-maintainer remediation sequence merged through PR #29. Those
controls remain quality evidence rather than independent authorization, and
they do not clear the open same-repository-CI High or grant cloud authority by
themselves. Accepted ADR-0012 now governs the consolidated local implementation boundary and later gate-evidence closeout.

## Historical non-scope of the original local/static scaffold slice

The following constraints describe the original source-only scaffold work. They do not deny the separately approved state/foundation operations now recorded above, and they grant no authority for any current or future cloud action.

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

Beatrice has accepted a durable bootstrap/state control plane separate from disposable `develop` workload teardown. PR #74 is merged through `develop@92b104e`; run `33882394981` completed Gate P publication, signing, attestations, transparency verification, final semantic admission, and approved immutable-reference emission. Gate P is complete and its one-use approval is consumed. No prior-state adoption/import is claimed. Every later Terraform, Secret, database, tester, migration, service, qualification, live-data, public-access, or production action remains separately approved.
