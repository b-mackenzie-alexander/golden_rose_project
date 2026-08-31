# Bootstrap state runbook

This runbook covers the one-time local bootstrap of the durable Terraform state bucket and the later migration to remote state. It is intentionally value-safe: operator-held project, bucket, location, and principal inputs stay out of tracked source.

Current source status: PR #37 merged the no-cloud deployment-path remediation at `caf96a7`; PR #46 made the evaluated foundation root workload-free and Cloud-SQL-free at `58aed28`; PR #48 aligned the verifier at `5f265d8`; and PR #57 closed A1 live-foundation remediation with zero current-source violations. Private records show separately approved partial foundation work. This runbook remains future operator guidance: after the narrow source amendment merges, separately approved read-only binding/readback and bounded workload-scope delta must complete in the same operator session before either root adoption gate; PR #57's A1 closure is not reopened.

Before any later adoption/import request, prove privately that bootstrap and workload roots have distinct state objects/files, backend keys/prefixes, lock scopes, lineages, and import operations. Bind each approval to the canonical private backend-config digest plus an opaque resolved backend identity, state object or prefix, and lock scope fingerprint, then require pre-initialization comparison against the reviewed source and operator-held inputs. Verify bootstrap-local-state provenance (or record its absence as a blocker), then migrate/read back bootstrap state and prove it contains bootstrap addresses only before any workload-root state initialization/import or bootstrap-authority retirement.

## Scope

- local bootstrap only
- durable remote state bucket for later approved use
- partial backend configuration in `infra/gcp/backend.tf`
- no secret payloads in source, state, plans, logs, or ordinary docs
- no Terraform plan/apply against workload resources from this runbook without a later explicit gate

## Ceremony sequence

1. local bootstrap in `infra/gcp/bootstrap` with operator-held values
2. create the durable remote state bucket with lifecycle protection and recovery controls
3. verify remote state access before any migration
4. migrate the root module from local bootstrap to remote state using the partial backend configuration plus operator-held backend values, after matching the canonical private backend-config digest and the opaque resolved backend identity/state object or prefix/lock scope fingerprint approved for that root
5. complete the later WIF handoff after the reviewed trust contract exists
6. perform bootstrap authority retirement so the one-time bootstrap operator path does not remain standing authority

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
