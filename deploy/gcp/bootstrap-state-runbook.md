# Bootstrap state runbook

This runbook covers the durable bootstrap bucket and the later establishment of new Terraform state lineage for it. It is intentionally value-safe: operator-held project, bucket, location, and principal inputs stay out of tracked source.

Current source status: PR #88 merged at `develop@4b678d1c2b6b5eb13c1031bd2cd4be16a2da5302`. The successor packet passed exact quota-role/binding readback and then stopped read-only on managed-IAM verifier modeling. Its approval is consumed; no backend/state/plan or later action occurred. Bounded source correction is active; a fresh final-tip packet and approval are required.

Before any bootstrap-state establishment/reconciliation request, prove privately that bootstrap and workload roots have distinct state objects/files, backend keys/prefixes, lock scopes, lineages, and recovery paths. Bind each approval to the canonical private backend-config digest plus an opaque resolved backend identity, state object or prefix, and lock scope fingerprint, then require pre-initialization comparison against the reviewed source and operator-held inputs. Establish/read back bootstrap state with the approved existing bootstrap inventory and prove it contains bootstrap addresses only before any workload-root state path or bootstrap-authority retirement.

## Scope

- local bootstrap only
- durable remote state bucket for later approved use
- partial backend configuration in `infra/gcp/bootstrap/backend.tf`
- one operator-held named human principal may receive `roles/iam.serviceAccountTokenCreator` only on the exact provisioner service account so separately approved local Terraform operations can use short-lived impersonation
- the existing provisioner service account receives `roles/storage.objectAdmin` only on the exact Terraform state bucket so those short-lived credentials can use the reviewed bootstrap and workload state objects
- no project-level Token Creator, provisioner GitHub WIF, service-account key, or ambient-user Terraform fallback
- no secret payloads in source, state, plans, logs, or ordinary docs
- no Terraform plan/apply against workload resources from this runbook without a later explicit gate

## Ceremony sequence

1. bind the exact existing bootstrap candidate inventory, source/lock/input digests, and private backend/recovery references
2. establish the bootstrap root's new remote Terraform state lineage against the existing durable bucket through a separately approved reconciliation path
3. read back state lineage/serial, backend object or prefix, lock scope, bootstrap-only address set, and recovery access before any workload-state decision
4. bind one operator-held `user:` principal to `roles/iam.serviceAccountTokenCreator` on only the exact provisioner service account through a separately reviewed bootstrap saved plan/apply
5. bind that provisioner service account to `roles/storage.objectAdmin` only on the exact state bucket through a separately reviewed bootstrap saved plan/apply
6. read back both exact policies, reject project-wide storage or impersonation authority, prove short-lived token mint without output, and prove the provisioner can initialize/read the reviewed backend before migration planning
7. retain the reviewed publisher/deployer WIF handoff while keeping provisioner GitHub WIF disabled unless a separately accepted material authority change replaces the local path
8. perform bootstrap authority retirement only through its separate approved transition

### Provisioner operator bootstrap exception — completed

The bounded named-human bootstrap operator executed the separately approved Token Creator and bucket Object Admin transitions. The existing bootstrap operator remained the bounded executor for each exact bootstrap-root saved plan. In the final PR #78 transition, the sole allowed create was the exact provisioner bucket member; exact policy/state readback and short-lived provisioner impersonation backend proof passed, and both approvals are consumed. Ambient-user workload Terraform, provisioner GitHub WIF, keys, and every project-level provisioner role remain forbidden.

ADR-0015 accepts a different future bootstrap-owned FinOps state bucket and exact authoritative bucket policy. ADR-0016's merged human-visible addendum defers that split and suspends Gate E0/signed per-domain transactions for fictional-synthetic `develop`; do not execute this future sequence before production/handoff or a concrete billing-ownership trigger and a fresh accepted decision.

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
- provider operator principal: one exact named `user:` value held privately and passed separately through `--provider-operator-principal`; an existing direct `roles/owner` binding is accepted only when its complete membership equals that principal, and it never substitutes for backend-only provisioner impersonation
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
