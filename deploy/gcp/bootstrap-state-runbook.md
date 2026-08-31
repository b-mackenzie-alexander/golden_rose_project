# Bootstrap state runbook

This runbook covers the durable bootstrap bucket and the later establishment of new Terraform state lineage for it. It is intentionally value-safe: operator-held project, bucket, location, and principal inputs stay out of tracked source.

Current source status: PR #57 closed A1; PR #58/PR #59 and separately approved WP-2/WP-3 completed the workload binding/scope-delta sequence without mutation. A2 is complete: the bucket was manually established before Terraform state, so empty state and absent local state retire prior-state adoption/import. This runbook remains future operator guidance pending a separately approved bootstrap-state establishment/reconciliation decision with new lineage; PR #57's A1 closure is not reopened.

Before any bootstrap-state establishment/reconciliation request, prove privately that bootstrap and workload roots have distinct state objects/files, backend keys/prefixes, lock scopes, lineages, and recovery paths. Bind each approval to the canonical private backend-config digest plus an opaque resolved backend identity, state object or prefix, and lock scope fingerprint, then require pre-initialization comparison against the reviewed source and operator-held inputs. Establish/read back bootstrap state with the approved existing bootstrap inventory and prove it contains bootstrap addresses only before any workload-root state path or bootstrap-authority retirement.

## Scope

- local bootstrap only
- durable remote state bucket for later approved use
- partial backend configuration in `infra/gcp/backend.tf`
- no secret payloads in source, state, plans, logs, or ordinary docs
- no Terraform plan/apply against workload resources from this runbook without a later explicit gate

## Ceremony sequence

1. bind the exact existing bootstrap candidate inventory, source/lock/input digests, and private backend/recovery references
2. establish the bootstrap root's new remote Terraform state lineage against the existing durable bucket through a separately approved reconciliation path
3. read back state lineage/serial, backend object or prefix, lock scope, bootstrap-only address set, and recovery access before any workload-state decision
4. complete the later WIF handoff after the reviewed trust contract exists
5. perform bootstrap authority retirement only through its separate approved transition

## Exact GitHub WIF trust contract

- only `b-mackenzie-alexander/golden_rose_project` may federate
- only `refs/heads/develop` may federate
- only the reviewed `develop` deployment environment may federate
- only `workflow_dispatch` subjects may impersonate bootstrap-reviewed automation identities
- `workflow_ref` must be exactly `b-mackenzie-alexander/golden_rose_project/.github/workflows/build-image.yml@refs/heads/develop` for the image-publisher identity
- `workflow_ref` must be exactly `b-mackenzie-alexander/golden_rose_project/.github/workflows/deploy-develop.yml@refs/heads/develop` for the deployer identity
- wildcard repository, owner, ref, or environment claims are forbidden
- principal-set broadening beyond the exact reviewed workflow ref is forbidden
- provisioner GitHub WIF remains disabled until a separately accepted Terraform-apply workflow exists
- provisioner, image-publisher, and deployer identities stay separate
- ordinary GitHub WIF paths do not receive `roles/iam.serviceAccountTokenCreator` unless a later reviewed operation proves it necessary
- service-account keys remain forbidden; the handoff stays keyless

## Required operator-held values

- control-plane project identifier
- state bucket name
- state bucket location
- bootstrap operator principal
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
