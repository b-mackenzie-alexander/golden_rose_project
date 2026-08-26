# Private SQL Foundation and Verifier Reconciliation Implementation Plan

> **For Hermes:** Use the `subagent-driven-development` skill to implement this plan task-by-task.

**Goal:** Reconcile the staged foundation verifier with the actual cloud authority sequence, then prepare a separately approved private-network and Cloud SQL foundation gate without creating an executable workload, database credentials, secret payload, image, migration job, or Cloud Run service.

**Architecture:** Preserve the existing staged model: `foundation` owns durable non-executable lower layers, `migration` adds only the reviewed migration job, and `service` adds the staff-facing Cloud Run service and named-tester ingress. The verified live posture now establishes APIs, identities, state, registry, metadata-only secrets, observability, and budgets, but not private networking or Cloud SQL. The verifier must stop requiring tester authority outside the service stage, while the Cloud SQL expectation remains an explicit lower-layer prerequisite for a later post-network/SQL foundation pass.

**Tech Stack:** Terraform 1.9+/Google provider 6.x source contracts, Python foundation verifier, pytest, gcloud read-only evidence, operator-held GCP inputs and evidence.

---

## Current evidence and hard boundaries

### Observed live posture
- `golden-rose-control` provides the durable state bucket, control-plane identities, and exact GitHub WIF trust.
- `golden-rose-dev` now contains required APIs, runtime/migration identities, Artifact Registry, four metadata-only Secret Manager containers, budget/alert/logging baseline, and no Cloud Run workload.
- The Phase 8 read-only snapshot confirms no Cloud Run service or migration job exists.
- No private VPC, Direct VPC subnet, private-service-access reservation/connection, Cloud SQL instance, application database, secret version/payload, image, migration execution, or service activation exists.

### Verified verifier/plan mismatch
- `scripts/verify_gcp_foundation.py:580-581` requires `develop-postgres` in every mode, including `foundation`.
- `scripts/verify_gcp_foundation.py:1595-1610` unconditionally derives tester authority before it can collect any foundation snapshot.
- The executed mutation plan did not include private-network/Cloud SQL provisioning, so Phase 8 could validate only its snapshot half and could not reach a full verifier pass.
- Tester authority is correctly deferred until the later named-tester/service ceremony; it must not be fabricated merely to run a foundation check.

### Hard stop boundaries
- Do not execute Terraform `plan`, `apply`, import, state commands, or backend migration under this plan.
- Do not create private-network or Cloud SQL resources under this plan. This is planning/source reconciliation only.
- Do not create database users, passwords, secret versions/payloads, Cloud Run jobs/services, images, tester access, or public ingress.
- Do not enable additional APIs or alter the existing live cloud environment.
- Do not put project IDs, billing identifiers, email addresses, credential material, database connection strings, state values, tester details, or receipt/bundle values in tracked source.

---

## Task 1: Freeze the staged verifier semantics in tests

**Objective:** Make the intended authority boundary executable: foundation and migration checks must not require later service-stage tester evidence; service checks must still derive and validate it.

**Files:**
- Modify: `tests/unit/test_verify_gcp_foundation.py`
- Modify: `scripts/verify_gcp_foundation.py`

**Step 1: Write failing CLI argument/staging tests**

Add narrowly scoped tests that invoke the verifier argument parser and `main()` through controlled fakes:
- foundation mode accepts no tester receipt/bundle/certificate CLI inputs;
- migration mode accepts no tester receipt/bundle/certificate CLI inputs;
- service mode rejects absent tester inputs before live service IAM is accepted;
- service mode still derives the tester contract through `derive_tester_authority_contract`.

Keep tests free of real receipt content, private principal values, and real Cosign calls. Use existing temporary-path patterns and fake verifier runners.

**Step 2: Verify RED**

Run:

```bash
env -u PYTHONPATH uv run pytest \
  tests/unit/test_verify_gcp_foundation.py::<new-foundation-mode-test> \
  tests/unit/test_verify_gcp_foundation.py::<new-service-mode-test> -q
```

Expected: foundation/migration argument handling fails because the current parser requires tester inputs and `main()` derives tester authority unconditionally.

**Step 3: Implement the smallest stage-aware CLI contract**

In `scripts/verify_gcp_foundation.py`:
- make tester receipt, bundle, and certificate arguments optional at parse time;
- reject missing tester inputs only when `--mode service` is selected;
- derive tester authority only in service mode;
- build service-only contract keys only after a successful service-stage derivation;
- ensure foundation/migration evaluation does not read `private_invoker_principal` or tester receipt digest.

Do not accept caller-supplied tester principal/digest in any mode.

**Step 4: Verify GREEN**

Run the focused tests from Step 2 and then:

```bash
env -u PYTHONPATH uv run pytest tests/unit/test_verify_gcp_foundation.py -q
```

Expected: all verifier unit tests pass.

---

## Task 2: Preserve Cloud SQL as an explicit lower-layer foundation requirement

**Objective:** Resolve the apparent mismatch without weakening the Cloud SQL private-posture contract or falsely declaring the current partial foundation complete.

**Files:**
- Modify: `tests/unit/test_verify_gcp_foundation.py`
- Modify: `scripts/verify_gcp_foundation.py` only if a test exposes an accidental stage leak
- Modify: `infra/gcp/develop/cloud_sql.tf` only if source/test reconciliation exposes an actual contract defect

**Step 1: Write/adjust a stage-contract regression**

Add a test proving that:
- `foundation` continues to reject an absent `develop-postgres` inventory after tester authority has been decoupled;
- `foundation` continues to reject public-IP or wrong-version Cloud SQL posture;
- `foundation` continues to reject a present Cloud Run service/job.

This distinguishes two facts:
1. current live Phase 8 snapshot is intentionally incomplete, and
2. the next private SQL foundation gate is required before a full foundation verifier pass.

**Step 2: Verify RED or honest GREEN**

Run the focused test. If current behavior already meets the assertion once Task 1 is complete, document it as an honest GREEN regression rather than changing production verifier code.

**Step 3: Minimal implementation only if required**

If the test reveals an accidental stage leak, make the smallest change that preserves:
- Cloud SQL required in foundation/migration/service;
- Cloud Run absent in foundation;
- migration job absent in foundation and service-only tester authority.

Do not alter Cloud SQL parameters, recovery values, or resources in this task.

**Step 4: Verify**

```bash
env -u PYTHONPATH uv run pytest tests/unit/test_verify_gcp_foundation.py -q
```

---

## Task 3: Define the separate private-network and Cloud SQL authority packet

**Objective:** Produce a value-safe, operator-held input checklist and exact gate boundary for the missing lower-layer resources before any future mutation authority is requested.

**Files:**
- Modify: `.hermes/plans/2026-08-25_195726-private-sql-foundation-verifier-reconciliation-plan.md` if implementation discoveries require clarification
- Modify: `deploy/gcp/first-deployment-runbook.md` only after accepted decisions change its operator contract
- Modify: `CURRENT_WORK.md`, `ROADMAP.md`, and `NOTES.md` only after the plan is accepted/merged under the repository workflow

**Required operator-held decisions (do not commit values):**
- an RFC1918 Direct VPC subnet CIDR, validated against live collision evidence;
- private-service-access address-range strategy and collision outcome;
- Cloud SQL backup enablement, UTC window, PITR choice, transaction-log retention, retained backup count, and recovery-policy status;
- non-secret database identifier and non-secret schema/migrator/runtime role identifiers;
- exact confirmation that the accepted non-production cost posture still permits the fixed Cloud SQL component;
- recovery/restore evidence requirements and later restore-test authority;
- explicit decision about whether direct gcloud provisioning remains permitted or Terraform-only plan/apply becomes mandatory for the resources.

**Gate constraints to preserve:**
- network is a dedicated `develop-vpc`, not the default network;
- no firewall, router, NAT, external IP, public IP, or public authorized network;
- private-service-access allocation and connection precede Cloud SQL;
- Cloud SQL remains `POSTGRES_16`, `db-f1-micro`, 10 GiB `PD_SSD`, private IP only, and deletion-protected;
- no `google_sql_user`, no password, and no database credential/secret payload under the infrastructure provisioning gate;
- database and role credentials stay in the later out-of-band secret/database authority ceremony.

**Required read-only preflight evidence for the later gate:**

```bash
gcloud compute networks list --project golden-rose-dev --format=json
gcloud compute networks subnets list --project golden-rose-dev --format=json
gcloud compute addresses list --project golden-rose-dev --global --format=json
gcloud services vpc-peerings list --project golden-rose-dev --network develop-vpc --format=json
gcloud sql instances list --project golden-rose-dev --format=json
```

Use the actual CIDR proposal only in private operator-held evidence; never place it in tracked source until an accepted value-safe procedure authorizes that exposure.

---

## Task 4: Prepare a follow-on Cloud SQL foundation execution plan, but do not execute it

**Objective:** Turn Task 3 decisions into the next separately approved mutation plan.

**Files:**
- Create later: `.hermes/plans/<timestamp>-private-network-cloud-sql-foundation-execution-plan.md`
- Inspect: `infra/gcp/develop/network.tf`
- Inspect: `infra/gcp/develop/cloud_sql.tf`
- Inspect: `infra/gcp/develop/variables.tf`
- Inspect: `deploy/gcp/rollback-forward-recovery-runbook.md`
- Inspect: `deploy/gcp/teardown-rebuild-runbook.md`

The later plan must use this sequencing:
1. rebaseline Git/state and capture read-only network/CIDR collision evidence;
2. freeze non-secret operator-held inputs and recovery decisions;
3. run approved local source tests/static validation only;
4. obtain a distinct cloud mutation approval;
5. provision dedicated VPC, Direct VPC subnet, private-service-access reservation, and service-networking connection using the approved authority path;
6. provision the private Cloud SQL instance and empty application database only after network readiness; no login, schema migration, user creation, or credential injection;
7. read back private-IP/deletion-protection/backup/PITR/retention labels and network association;
8. run `scripts/verify_gcp_foundation.py --mode foundation` with real operator-held foundation inputs but without tester inputs;
9. record a truthful pass/fail result and stop before secrets, database login, image publication, migrations, Cloud Run, or service qualification.

---

## Task 5: Define the later tester-authority evidence ceremony as service-stage-only

**Objective:** Keep named tester authority out of foundation/migration verification while retaining its full service-stage security boundary.

**Files:**
- Inspect/modify later: `scripts/verify_tester_authority_receipt.py`
- Inspect/modify later: `deploy/gcp/private-tester-access.md`
- Inspect/modify later: `deploy/gcp/receipts/README.md`
- Test later: `tests/unit/test_tester_authority_receipt.py`

**Requirements:**
- do not create a real receipt, bundle, certificate identity, named tester binding, or Cloud Run invoker grant in this planning slice;
- retain the exact signed receipt + detached bundle + certificate identity verifier at service stage;
- derive one named tester principal only after verification;
- continue to prohibit `allUsers`, `allAuthenticatedUsers`, project-wide tester access, and shared tester accounts;
- add the real tester evidence only when a private service exists and a separately approved named-tester window opens.

---

## Task 6: Plan review and verification closeout

**Objective:** Keep the current uncommitted cloud-reconciliation source surface reviewable before any commit/PR decision.

**Files:**
- Modify: `tests/unit/test_verify_gcp_foundation.py`
- Modify: `tests/unit/test_terraform_hygiene.py` only if Task 2 source expectations need an update
- Modify: `scripts/verify_gcp_foundation.py`
- Modify: `infra/gcp/develop/observability.tf` only as already required by the Phase 7 corrected metric/resource pairing
- Add: this plan file

**Verification order:**

```bash
env -u PYTHONPATH uv run pytest tests/unit/test_verify_gcp_foundation.py -q
env -u PYTHONPATH uv run pytest tests/unit/test_terraform_hygiene.py -q
env -u PYTHONPATH uv run python scripts/validate_terraform_static.py
git diff --check
```

Before any staging/commit/push/PR decision:
- re-read the exact uncommitted surface;
- run the project’s exact local secret-scanning expectation for the intended range when a commit boundary exists;
- obtain the required focused independent rereview;
- update living docs only after the accepted plan/implementation status is truthful.

---

## Risks and open questions

1. **Cloud SQL cost/recovery gate:** private Cloud SQL is the accepted non-production fixed cost driver. Backup/PITR settings are not placeholders; they must be explicitly frozen and tied to recovery evidence before provisioning.
2. **CIDR collision:** no subnet or private-service-access range can be selected from memory. It must be checked against live networks, subnets, and global address reservations immediately before the later mutation gate.
3. **Source vs live divergence:** manual foundation setup now exists while Terraform has not been applied. The later authority packet must determine the approved reconciliation method before Terraform becomes the source of applied-state authority; do not import or apply under this plan.
4. **Tester evidence:** service-stage tester receipt requirements must remain strict. Making tester inputs optional for foundation/migration must never let service mode accept missing or caller-supplied authority.
5. **Email confirmation:** the Phase 7 notification channel resource exists, but actual email delivery must be confirmed out of band before treating alert routing as qualified.

## Acceptance criteria
- A formal approved plan exists for the verifier stage-boundary fix and a later private-network/Cloud SQL authority gate.
- Foundation/migration verifier modes can be executed without fabricated tester evidence after implementation, while service mode remains receipt-bound.
- The verifier continues to require private Cloud SQL before a full foundation pass.
- No cloud/database/network/tester mutation occurs in this planning slice.
- The plan explicitly identifies every operator-held input, cost/recovery decision, conflict check, and separate approval needed before private-network/Cloud SQL execution.
