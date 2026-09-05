# Bootstrap state runbook

This runbook covers the durable bootstrap bucket and the later establishment of new Terraform state lineage for it. It is intentionally value-safe: operator-held project, bucket, location, and principal inputs stay out of tracked source.

Current source status: bootstrap/workload state establishment, A5 disposition, foundation apply/readback, Gate P, the bounded early Gate S synthetic-staff Secret action, and PR #76's local provisioner bridge source are complete. The first approved bootstrap one-create plan was generated but withheld before apply because it also proposed provider-canonical WIF-condition formatting and artifact-verifier description updates. The active source-only correction preserves those observed provider/live representations so a later fresh plan can contain only the intended provisioner operator IAM-member create. No apply, IAM mutation, token mint, migration-plan retry, or downstream action is authorized by this correction.

Before any bootstrap-state establishment/reconciliation request, prove privately that bootstrap and workload roots have distinct state objects/files, backend keys/prefixes, lock scopes, lineages, and recovery paths. Bind each approval to the canonical private backend-config digest plus an opaque resolved backend identity, state object or prefix, and lock scope fingerprint, then require pre-initialization comparison against the reviewed source and operator-held inputs. Establish/read back bootstrap state with the approved existing bootstrap inventory and prove it contains bootstrap addresses only before any workload-root state path or bootstrap-authority retirement.

## Scope

- local bootstrap only
- durable remote state bucket for later approved use
- partial backend configuration in `infra/gcp/bootstrap/backend.tf`
- one operator-held named human principal may receive `roles/iam.serviceAccountTokenCreator` only on the exact provisioner service account so separately approved local Terraform operations can use short-lived impersonation
- no project-level Token Creator, provisioner GitHub WIF, service-account key, or ambient-user Terraform fallback
- no secret payloads in source, state, plans, logs, or ordinary docs
- no Terraform plan/apply against workload resources from this runbook without a later explicit gate

## Ceremony sequence

1. bind the exact existing bootstrap candidate inventory, source/lock/input digests, and private backend/recovery references
2. establish the bootstrap root's new remote Terraform state lineage against the existing durable bucket through a separately approved reconciliation path
3. read back state lineage/serial, backend object or prefix, lock scope, bootstrap-only address set, and recovery access before any workload-state decision
4. bind one operator-held `user:` principal to `roles/iam.serviceAccountTokenCreator` on only the exact provisioner service account through a separately reviewed bootstrap saved plan/apply
5. read back that exact service-account policy and prove short-lived token mint succeeds without output; project-level Token Creator, provisioner GitHub WIF, keys, and ambient-user Terraform remain forbidden
6. retain the reviewed publisher/deployer WIF handoff while keeping provisioner GitHub WIF disabled unless a separately accepted material authority change replaces the local path
7. perform bootstrap authority retirement only through its separate approved transition

### Provisioner operator bootstrap exception

The existing bootstrap operator may run one exact bootstrap-root saved plan/apply under separate approvals solely to make the reviewed provisioner path executable. The sole allowed create is `google_service_account_iam_member.provisioner_operator_token_creator`; every other action must be no-op, with no bucket/state replacement, WIF change, project-level IAM, key, or unrelated control-plane mutation. Immediate readback passes the same private named user to `scripts/verify_gcp_foundation.py --provisioner-operator-principal`, which must reject missing/wrong/extra/WIF/project-wide authority before non-echoing token mint is attempted. After exact policy readback proves short-lived provisioner impersonation, all workload-root Terraform uses that provisioner path. Ambient-user workload Terraform remains forbidden.

The existing provisioner service-account description is intentionally unchanged in this correction so the bootstrap plan can remain exactly one IAM-member create. Its historical GitHub-OIDC wording is not authority and does not describe the current provisioner path; correcting that metadata would require its own reviewed plan action.

The bootstrap WIF provider condition is source-rendered in the provider's canonical single-line representation while preserving the exact reviewed repository/owner/ref/environment/event/workflow Boolean contract. The artifact-verifier service-account description likewise preserves the observed live metadata. These are no-op convergence fields, not authority changes; static validation rejects semantic WIF drift or additive broadening.

## Exact GitHub WIF trust contract

- only `b-mackenzie-alexander/golden_rose_project` may federate
- only `refs/heads/develop` may federate
- only the reviewed `develop` deployment environment may federate
- only `workflow_dispatch` subjects may impersonate bootstrap-reviewed automation identities
- `workflow_ref` must be exactly `b-mackenzie-alexander/golden_rose_project/.github/workflows/build-image.yml@refs/heads/develop` for the image-publisher identity
- `workflow_ref` must be exactly `b-mackenzie-alexander/golden_rose_project/.github/workflows/deploy-develop.yml@refs/heads/develop` for the deployer identity
- wildcard repository, owner, ref, or environment claims are forbidden
- principal-set broadening beyond the exact reviewed workflow ref is forbidden
- provisioner GitHub WIF is disabled; adding it requires a separately accepted material trust/authority change and is not part of the current local path
- provisioner, image-publisher, and deployer identities stay separate
- ordinary GitHub WIF paths do not receive `roles/iam.serviceAccountTokenCreator` unless a later reviewed operation proves it necessary
- service-account keys remain forbidden; the handoff stays keyless

## Required operator-held values

- control-plane project identifier
- state bucket name
- state bucket location
- bootstrap operator principal
- provisioner operator principal: one named `user:` value held privately, passed to the live verifier through `--provisioner-operator-principal`, and bound only at the provisioner service-account level
- backend configuration values supplied at init time rather than committed in source

## Recovery and governance

- preserve remote state versioning and retention posture
- keep emergency recovery documented and operator-approved
- keep state survival explicit across workload teardown and rebuild; the durable control plane is not part of the disposable workload lifecycle
- document state access ownership and client handoff expectations separately from workload teardown
- keep teardown exclusions explicit: the disposable workload root must not destroy the lifecycle-independent state bucket

## Relationship to workload recovery and teardown

- use `deploy/gcp/rollback-forward-recovery-runbook.md` for workload rollback-versus-forward-recovery decisions
- use `deploy/gcp/teardown-rebuild-runbook.md` for disposable workload teardown/rebuild
- keep bootstrap/state survival outside those workload procedures unless an explicit reviewed break-glass change says otherwise

## Boundaries

- no secret payloads in Terraform source or state
- no client or live data
- no workload deployment, image push, migration execution, or service start
- no silent reuse of bootstrap authority after WIF handoff

## Later database-authority gate prerequisites

- apply reviewed database authority migrations only after the separate deployment gate exists
- keep the non-login `golden_rose_schema_owner` authority distinct from the migration and runtime capability roles
- treat runtime access as bounded DML only; no runtime DDL, trigger administration, truncate, or role-management authority
- run `python scripts/verify_database_authority.py` against the reviewed target before treating database authority as qualified
