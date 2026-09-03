# GCP Terraform scaffold

This directory contains the repo-local Terraform scaffold for the Golden Rose private `develop` environment. PR #24 merged this validate-without-apply, local-validation, and static-policy surface into protected `develop` at `50451b3`.

PR #29 merged semantic static-policy validation, deterministic `uv`, Cloud Run/private-SQL declaration, API ordering, Cloud SQL backup enablement, and managed Artifact Registry image authority into protected `develop` at `08fe305`. PR #33 later merged ADR-0012's consolidated source-controlled pre-deployment implementation; PR #37/PR #42/PR #46/PR #48 closed the ADR-0013 source and verifier blockers; PR #57 closed A1; and PR #62/PR #64 completed bootstrap-IAM and foundation-evaluation corrections. WP-2/WP-3, A2, E2/E3 state establishment/readback, A5, ownership alignment, exact replacement-free foundation apply, and post-apply verification are complete. The verified foundation contains 41 managed addresses plus one expected data source and no executable Cloud Run service/job. The first post-PR71 Gate P dispatch built/pushed an immutable image but stopped before attestation at the invalid unprefixed Syft tag. Complete local preflight expanded the correction through real SPDX semantics, cloud-blind final-image scanning, schema-correct SLSA v1, raw Cosign evidence admission, and exact application-SBOM binding; the disposable local chain passes. Complete candidate review, protected merge, exact-tip rebind, fresh retry approval, and final keyless/transparency verification remain required. The accepted outcome plan predeclares later Secret-version, migration, service, tester, and qualification gates without collapsing their separate approvals. `foundation` remains Cloud-SQL-free; later stages retain fail-closed private Cloud SQL posture checks. Same-repository-CI remains an open accepted residual risk.

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
- Foundation cost and observability controls are now present and verified: `infra/gcp/develop/budgets.tf` fixes the reviewed $50/$75/$100 thresholds, routes alerts only through operator-held notification inputs, and keeps alerts explicitly non-cap. `infra/gcp/develop/observability.tf` retains reviewed notification-channel, alert-policy, log-retention, and value-safe viewer/access contracts without creating an export sink or logging request bodies/SQL values.
- Workload startup is intentionally gated on reviewed cost/observability resources: `infra/gcp/develop/cloud_run.tf` and `infra/gcp/develop/migration_job.tf` both depend on the reviewed budget/alert/log-retention contract so later deployment work cannot claim readiness before those prerequisites exist.
- Task 9 immutable-build authority is source-controlled and Gate P remains incomplete: `.github/workflows/build-image.yml` keeps pull requests cloud-blind, reserves WIF-backed publication for the named `develop` environment, captures the immutable Artifact Registry digest, and uses a commit-pinned Syft action for the image SBOM. The first post-PR71 exact-head dispatch built/pushed an image but stopped before attestation because the configured `1.37.0` release tag does not exist; upstream publishes `v1.37.0`. Complete local preflight now covers the corrected installer, actual Syft SPDX `DESCRIBES` semantics, PR final-image scanning, schema-correct SLSA v1 generation via `slsaprovenance1`, raw Cosign evidence admission, and exact application-SBOM checksum binding. Protected merge, exact-tip rebind, fresh retry approval, and final keyless/transparency proof remain required. `scripts/verify_image_provenance.py` continues to fail closed on missing digest, reviewed base-image pins, absent provenance, or missing SBOM evidence.
- Task 10 deploy authority is source-controlled and still no-cloud only: `.github/workflows/deploy-develop.yml` accepts only an immutable digest input, requires the exact protected `develop` ref plus named `develop` environment, uses only the reviewed deployer WIF path, serializes `run-migrations` before `staff-tracer` rollout under workflow concurrency, and emits only value-safe forward-only compatibility/readiness evidence while leaving synthetic qualification to a later separate tool/gate.
- Task 11 live-foundation qualification tooling remains read-only and separately gated by stage: `scripts/verify_gcp_foundation.py` completed the current workload-free, Cloud-SQL-free foundation verification for labels, APIs, absence of executable workload/service-account keys, exact IAM, state recovery controls, budget/alert routing, and bounded logging posture. Later verifier stages remain responsible for private invoker and private Cloud SQL checks when those resources enter scope. `deploy/gcp/evidence-template.md` records the value-safe evidence shape.
- Task 12 private-synthetic deployment qualification tooling is source-controlled but still separate from deployment itself: `scripts/qualify_develop_deployment.py` requires authenticated private access, keeps `/health` and `/readiness` as non-mutating probes, exercises only bounded Employer and EmployerContact create/read/search/revision/replay flows with newly generated fictional values, emits minimized evidence that redacts submitted identifiers/cursors/tokens/DSNs/raw bodies, and records cleanup as teardown/rebuild disposition rather than inventing delete semantics.
- Task 13 operator procedures are source-controlled but still no-cloud only: `deploy/gcp/first-deployment-runbook.md` defines the out-of-band secret custody/injection ceremony and `deploy/gcp/private-tester-access.md` defines named private tester access while synthetic auth remains. Both procedures keep payloads, tester identities, and private endpoints out of Terraform, chat, repo artifacts, and ordinary docs.
- Secret metadata and IAM may be modeled later, but No secret payloads belong in Terraform source, state, plans, logs, artifacts, containers, or ordinary docs.
- Private tester access must remain named and service-level only; `allUsers`, `allAuthenticatedUsers`, and project-wide convenience bindings are forbidden.
- Project IDs, billing IDs, domains, user emails, credentials, and cloud-specific input values must stay in ignored/operator-held inputs, not tracked source.
- The approved state and foundation ceremony is complete through: manually established durable bootstrap bucket → E2 new-lineage bootstrap state → E3 workload-state import/readback → A5 verified-existing artifact authority → canonical-parent ownership alignment → replacement-free saved foundation plan → exact approved foundation apply → workload-free post-apply verification. The final foundation contains 41 managed addresses plus one expected data source; no state repair or destructive replacement occurred. The first post-PR71 Gate P dispatch built/pushed an immutable image but stopped before attestation on the invalid unprefixed Syft tag. Complete local preflight now proves the expanded source correction and disposable signature/SLSA-v1/SPDX/application-SBOM verification chain. Publication remains incomplete pending full candidate review, protected merge, exact-tip rebind, fresh retry approval, and final keyless/transparency verification. Out-of-band Secret-version, migration, service, tester, qualification, state recovery/handoff, and teardown gates remain separately approved and value-safe.

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
read-only verification entrypoint. It has completed the current foundation-mode
verification; later migration/service stages must reuse the reviewed tool and
stage-specific contract rather than ad-hoc cloud inspection notes.
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

Beatrice has accepted a durable bootstrap/state control plane separate from disposable `develop` workload teardown. PR #57 closed A1; PR #62 completed bootstrap IAM reconciliation; PR #64 closed the readiness-local correction; E2/E3 state readbacks, A5, ownership alignment, exact foundation apply, and post-apply verification are complete. The verified foundation contains 41 managed addresses plus one expected data source and no executable workload. The first post-PR71 Gate P dispatch built/pushed an immutable image but stopped before attestation at the invalid unprefixed Syft tag. Complete local preflight proves the expanded source correction and disposable verification chain; Gate P remains open pending full candidate review, protected merge, exact-tip rebind, fresh retry approval, and final keyless/transparency verification. No prior-state adoption/import is claimed. Each later Terraform plan/apply, out-of-band Secret preparation, database authority, image-publication retry, named private tester access, migration execution, service activation, qualification, real identity, live/client data, public access, and production action remains a separate evidence and approval gate.
