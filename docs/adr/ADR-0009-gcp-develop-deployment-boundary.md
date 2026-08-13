# ADR-0009 — GCP develop deployment boundary

**Status:** Accepted
**Date:** 2026-08-13

## Context and evidence posture

PR #20 merged the EmployerContact authority foundation into protected `develop` at `6eb05d5`. The repository now has a technically qualified local/synthetic Employer and EmployerContact tracer, a React staff workspace for Employer operations, PostgreSQL migrations, and strong application-quality CI. It does not have a deployable container contract, runtime health/readiness boundary, infrastructure as code, cloud identity, cloud database role separation, backup/restore evidence, or a shared environment for the human browser/accessibility/fluent-language checks deferred by ADR-0006.

Beatrice has reported a facilitator need for more visible progress and has confirmed that the immediate deployment target is `develop`/testing rather than production. This creates a legitimate need for an isolated shared non-production environment, but not permission to collapse the existing security, data, billing, identity, or production gates.

The following claims are classified separately:

- **Observed:** GCP is already the selected platform direction; Cloud Run and Cloud SQL are the accepted managed-container/database baseline in `TECHNOLOGY_DECISIONS.md`.
- **Observed:** the current application supports only `auth_mode = "synthetic"`, rejects synthetic authentication in `production`, and grants a configuration-owned synthetic principal all currently implemented permissions.
- **Observed:** the frontend uses relative same-origin staff API paths and has no approved independent hosting or cross-origin identity/token design.
- **Observed:** the current database migrations use application-level triggers and constraints, but the local/test database owner can bypass them through owner-level DDL, trigger changes, or `TRUNCATE`; runtime-role immutability therefore remains unqualified.
- **Reported by Beatrice:** the facilitator is requesting greater visibility into progress.
- **Accepted direction:** begin a safe GCP non-production deployment program using fictional synthetic data only.
- **Not validated:** region, cost, project/billing topology, Terraform state ownership, named cloud administrators, identity-provider configuration, Cloud SQL sizing/recovery, and first provisioning inputs.

## Decision

Adopt a staged, develop-only GCP deployment boundary with these decisions.

### 1. Environment and data boundary

Create no production environment under this ADR. The only authorized target after separate provisioning approval is one isolated GCP non-production project for `develop` testing.

The environment admits only wholly fictional synthetic data. Client/live records, transformed or de-identified client data, legacy imports, and production backups are prohibited. The application and evidence must identify the environment as non-production and synthetic-only.

Planning, implementation, cloud provisioning, first deployment, and later production promotion are separate approval events. Accepting or merging this ADR authorizes none of the latter actions by itself.

### 2. First deployable boundary

Use one same-origin staff-app Cloud Run service for the initial deployed tracer. The container contains the built React/Vite assets and the FastAPI staff API so the existing relative `/api/staff/v1/...` browser contract remains same-origin.

This is a deployment-unit decision, not a collapse of trust planes. It contains only the current staff-plane tracer. Future public worker/employer surfaces require separate identity audiences, credentials, endpoints, deployments, and data access and trigger a revisit of this ADR.

A separate API and static-host deployment was considered but deferred until a reviewed cross-origin/session/token and independent-promotion requirement exists. A gateway/load balancer/CDN is not introduced merely to simulate future architecture.

### 3. Access while synthetic authentication remains

The Cloud Run service must grant neither `allUsers` nor `allAuthenticatedUsers` invocation while the application uses a synthetic principal. Service-level `roles/run.invoker` is limited to the approved group or named managed principals. Qualification must inspect effective IAM, including inherited policy, rather than trusting Terraform declarations alone. Named approved test operators access it through Cloud Run IAM and an approved authenticated access method.

Cloud Run IAM is an outer develop-test perimeter only. It does not implement the accepted Owner/Manager/Operations Staff/Platform Administrator business authorization contract, individual staff accounts, MFA, or production session behavior. Those remain separate implementation and qualification gates.

The service cannot be described as staff-authenticated, identity-qualified, live-data-ready, or production-ready while synthetic application authentication remains active.

### 4. Managed GCP services

Use the existing accepted direction:

- Artifact Registry for immutable OCI images;
- Cloud Run for the private staff application;
- a separately invoked Cloud Run Job or equivalently bounded one-shot job for Alembic migrations;
- Cloud SQL for PostgreSQL 16;
- Secret Manager for runtime secret versions;
- Cloud Logging and Monitoring for value-safe operational evidence;
- GitHub Actions with GCP Workload Identity Federation for build/deploy identity;
- Terraform for reviewable infrastructure definitions.

Do not add GKE, Compute Engine, public Cloud Storage hosting, load balancing/CDN, Cloud Tasks/Scheduler, Maps/geocoding, documents, messaging, or other vendors without a concrete approved need.

### 5. Immutable artifact and migration boundary

Build once, scan/attest, push once, and deploy by immutable image digest. Tags may assist discovery but never constitute deployment authority.

Do not run Alembic automatically in every web process startup. A serialized migration job uses the exact approved application image and a separate migration identity/database role. Serialization must exist at the database boundary, not only in CI: the migration runner acquires one reviewed PostgreSQL advisory lock for the entire migration, fails closed when the lock is unavailable, and runs one task per job execution. Invoker IAM is narrowly bounded; workflow concurrency is defense in depth. Service deployment proceeds only after the migration result and compatibility evidence are known.

Each migration must declare and prove its image/schema compatibility window. Expansion must remain compatible with the currently serving image before migration; readiness uses a compatibility capability/range rather than requiring exact head in a way that makes the old revision unavailable. Both old and candidate images are checked after migration. Image rollback is permitted only while the resulting schema remains in the old image's proven range; otherwise forward recovery is mandatory.

### 6. Runtime, migration, deployment, and human authority separation

Use separate GCP identities for at least:

- application runtime;
- migration execution;
- deployment/provisioning automation;
- named human cloud administration and emergency access.

Use an explicit PostgreSQL role lifecycle: a non-login schema-owner role owns the application schema, Alembic objects, tables, sequences, functions, and triggers; the separately authenticated migration role may assume only that schema-owner role for reviewed migrations; and the runtime login role receives only explicit DML/sequence/function privileges required by the application. Bootstrap authority, ownership transfer, revocations, grants for existing objects, schema-owner default privileges for future objects, and `alembic_version` access must be declared and tested after every migration. The runtime role must not own the schema or have routine DDL, `TRUNCATE`, trigger-management, role-management, schema-owner assumption, or append-only authority update/delete capability. Tests must cover current and newly created objects and fail on grant drift before the environment is qualified.

Platform Administrator cloud access remains distinct from business-role access to operational records. No routine cloud role silently grants staff business authority or raw database access.

### 7. Health, readiness, and qualification

Provide three distinct contracts:

- cheap process liveness that does not depend on the database;
- bounded readiness that verifies required configuration plus authoritative database/schema availability without mutating business data;
- a separate qualification workflow that exercises the approved synthetic Employer/EmployerContact path.

Neither liveness nor readiness may create records, replay commands, or act as a full workflow acceptance test.

### 8. Infrastructure, state, CI/CD, and secrets

Terraform is the accepted IaC direction, but no Terraform apply occurs until region, cost, account/billing, IAM, recovery, state ownership, and resource inputs are reviewed and Beatrice gives explicit scoped provisioning approval.

Terraform state location, access, backup, and transfer ownership must be decided before apply. Secrets do not enter Terraform source, state by design, Git, chat, GitHub artifacts, container layers, or ordinary logs.

GitHub deployment uses OIDC/WIF rather than long-lived service-account keys. Pull-request workflows do not receive deploy authority. Protected GitHub environments, immutable action pins, concurrency control, digest deployment, and value-safe evidence are mandatory. CI concurrency does not replace database-level migration serialization.

Cloud Run platform request logs require an explicit minimization contract because exact-detail routes contain entity UUIDs in URL paths. Before deployment, the reviewed configuration must either exclude/disable those request logs where supported or strictly restrict access and sinks with an accepted retention/minimization rationale. Qualification inspects generated platform request logs and every configured sink; application-log tests alone are insufficient. Route redesign remains an alternative requiring its own reviewed product/API change.

### 9. Cost, recovery, logging, and teardown gates

Before provisioning, accept a non-production cost estimate, monthly budget/alert posture, maximum first-run exposure, named alert recipients, Cloud SQL sizing, backup/PITR and restore expectations, develop RTO/RPO targets, log retention/redaction behavior, and teardown/rebuild plan.

Budget alerts are alerts, not hard spending caps. Cloud SQL is expected to be the fixed baseline cost even if Cloud Run scales to zero.

The first environment is not qualified until budget routing, migration/rollback or forward recovery, log redaction, backup/restore or teardown/rebuild, and intentional shutdown/scale-down behavior are evidenced.

### 10. Evidence and facilitator visibility

Produce a value-safe visibility packet for the facilitator containing scope/non-scope, architecture, current stage, protected source commit, immutable image digest when available, migration/readiness/qualification outcome, manual browser/accessibility/language result, cost posture, recovery result, findings, and remaining gates.

Do not expose credentials, tokens, database URLs, synthetic names, precise request values, command IDs, cursors, raw logs, raw traces, or screenshots containing sensitive-looking data merely to demonstrate progress.

## Consequences and constraints

### Positive

- The engagement gains a real shared testing target without falsely declaring production readiness.
- Human browser, accessibility, and fluent-language qualification can proceed against a controlled deployed `develop` target.
- Same-origin deployment preserves the existing privacy-conscious frontend/API contract and avoids premature cross-origin identity complexity.
- Terraform, WIF, digest promotion, separate migration execution, and runtime database-role qualification reduce future operational debt.
- Distinct planning, implementation, provisioning, deployment, and production gates prevent cloud momentum from silently widening scope.

### Costs and limitations

- Private Cloud Run access adds tester onboarding friction while synthetic application auth remains.
- Cloud SQL introduces a recurring fixed cost even for a small develop environment.
- The same-origin single deployable may later be split when public/staff planes, independent scaling, or release ownership justify it.
- The environment will demonstrate deployment and current tracer behavior, not completion of the full Phase 1 employer-demand workflow.
- Real staff authentication, MFA, role administration, live-data admission, production recovery, and client production acceptance remain open.

## Alternatives considered

### Expose the synthetic application publicly for easy facilitator access

Rejected. Anyone reaching the service would receive the configured synthetic principal's permissions, so public invocation would convert a test convenience into an unreviewed authorization bypass.

### Block all deployment until real identity and the full Phase 1 workflow are complete

Rejected. A private synthetic shared target provides useful deployment, accessibility, language, runtime, and facilitator evidence without claiming production readiness. Waiting would preserve several known qualification gaps and reduce delivery visibility.

### Deploy frontend and API as separate public services immediately

Deferred. It would introduce CORS, independent endpoint discovery, token/session crossing, and multi-artifact promotion before the identity and public/staff deployment contracts are accepted. Same-origin is the safer minimal boundary for the current tracer.

### Serve static frontend assets from a public object bucket/CDN

Deferred. Public asset hosting is unnecessary for the private first target and would add caching, CSP, routing, origin, and release-coordination decisions. Revisit if measured delivery needs justify it.

### Run database migrations during web startup

Rejected. Concurrent instance startup and rollout failure would make schema authority nondeterministic. Use a separately controlled one-shot migration job.

### Give the runtime database user schema-owner privileges

Rejected. It would undermine the append-only and typed-authority assurances by allowing routine runtime credentials to change triggers/constraints or truncate protected tables.

### Use service-account JSON keys in GitHub Actions

Rejected. Workload Identity Federation is required to avoid long-lived cloud credentials.

### Use GKE or Compute Engine

Rejected for this stage. They add cluster/VM patching, network, supervision, and operational burden without an evidenced need.

### Provision manually first and codify later

Rejected for routine resources. A narrowly documented bootstrap exception may be necessary for project/billing/state/WIF setup, but the deployable foundation must be reviewable and reproducible before it is treated as qualified.

## Approval, owner, and revisit trigger

Beatrice is the technical decision owner. Independent architecture/security, database/recovery, GCP/IAM/cost, CI/supply-chain, and documentation reviews cleared the exact remediated packet with no remaining Blocker, High, or Medium findings, and Beatrice explicitly accepted the decision on 2026-08-13. This ADR is **Accepted** as the planning boundary; it is not implemented or provisioned.

Even after acceptance and merge, separate explicit approvals remain required for:

1. runtime/container implementation;
2. Terraform/IaC implementation;
3. GCP project/billing/API/resource/service-identity provisioning;
4. secret configuration and first migration/deployment;
5. any real identity/provider integration;
6. live/client-data admission;
7. production project creation or production promotion.

Revisit this ADR before:

- granting unauthenticated/public invocation;
- admitting any client/live-derived data;
- integrating real staff identity, MFA, sessions, or role administration;
- creating a public worker/employer plane;
- splitting frontend/API deployables or adding a gateway/CDN;
- enabling uploads, mapping/geocoding, messaging, payments, signatures, screening, or async workers;
- selecting production topology, HA, SLOs, production RTO/RPO, or production retention;
- transferring GCP account/billing/state/support ownership to the client;
- changing the runtime/migration database authority model.

The exact implementation slices, evidence, and hard stops are controlled by `.hermes/plans/2026-08-13_145234-gcp-develop-deployment-foundation-plan.md`.
