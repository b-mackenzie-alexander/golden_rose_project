# Bootstrap IAM Address Reconciliation Plan

> **For Hermes:** This is a source-only planning packet. Do not initialize a backend, import state, run a Terraform plan/apply, or mutate GCP while preparing or reviewing it.

**Goal:** Make the bootstrap bucket’s temporary `Storage Object Admin` authority representable by exactly one Terraform state address per unique live IAM member, so E2 can later establish state without duplicate ownership.

**Architecture:** Replace the three semantic-role `google_storage_bucket_iam_member` resources with one deduplicated `for_each` resource over the active bootstrap/state/recovery principal set. If the current temporary authorities converge to one principal, Terraform exposes one address; if they later split, each distinct principal receives exactly one address. Policy-role semantics remain in private approval/recovery records and the later retirement gate, not duplicate IAM resource addresses.

**Tech Stack:** Terraform 1.16.0; locked Google provider 6.50.0; Python static validator; pytest; no-cloud source-only validation.

---

## Current evidence and boundary

Private E2 readback found exactly one current `roles/storage.objectAdmin` member while the bootstrap source declares three IAM-member resources. Binding the same principal to all three input variables would require three imports of one live bucket/role/member tuple, which is invalid duplicate Terraform ownership.

This plan changes only source representation and its static contracts. It does not change live bucket IAM, retire bootstrap authority, create new identities, initialize state, import, plan, apply, or advance the workload root.

## Task 1 — Establish the source-level failure contract

**Files:**
- Modify: `tests/unit/test_terraform_hygiene.py:2617-2694`
- Inspect: `infra/gcp/bootstrap/iam.tf:47-64`
- Inspect: `scripts/validate_terraform_static.py:3129-3209`

1. Replace the three-address structural expectation with a test requiring one `google_storage_bucket_iam_member` resource using a deduplicating `for_each` collection.
2. Add a focused negative fixture where the resource loses `toset`/deduplication, or where the active bootstrap operator is omitted from the collection, and assert the validator fails on the exact reviewed contract.
3. Run the focused selector and record the expected RED against the current three-resource source.

**Acceptance:** The test proves that a converged authority set cannot produce duplicate Terraform IAM-member addresses.

## Task 2 — Implement the single-owner IAM representation

**Files:**
- Modify: `infra/gcp/bootstrap/iam.tf:47-64`

1. Define a local active-principal collection containing state authority, recovery authority, and bootstrap operator only when `bootstrap_operator_status == "bootstrap-active"`.
2. Use `toset(...)` to deduplicate that collection.
3. Replace the three bucket IAM-member resources with one `google_storage_bucket_iam_member` resource using `for_each` over the set; bind the bucket, fixed `roles/storage.objectAdmin` role, and `each.value` member.
4. Do not alter service-account/WIF resources, bucket settings, variables, bootstrap-retirement semantics, or any live resource.
5. Re-run the focused test and require GREEN.

**Acceptance:** One live bucket/role/member tuple maps to one Terraform address; distinct future principals remain individually representable.

## Task 3 — Align static validation and verifier contracts

**Files:**
- Modify: `scripts/validate_terraform_static.py:3129-3209`
- Modify: `tests/unit/test_terraform_hygiene.py:2617-2694` and adjacent bootstrap IAM tests
- Inspect: `scripts/verify_gcp_foundation.py:522-529`
- Inspect: `tests/unit/test_verify_gcp_foundation.py:24-67`

1. Replace validator requirements for three named bucket-IAM resources with the exact single-resource/`for_each`/`toset` shape.
2. Preserve strict requirements for the state bucket target, `roles/storage.objectAdmin`, active-only bootstrap inclusion, no broad public members, and no unreviewed bucket-IAM resource.
3. Keep `verify_gcp_foundation.py`’s expected-IAM set semantics unchanged; it already deduplicates members and remains the authoritative live-policy comparison.
4. Add negative fixtures for a non-deduplicated list, wrong role, wrong bucket, and missing active-bootstrap conditional.

**Acceptance:** Static policy rejects source drift while allowing one address per unique member.

## Task 4 — No-cloud validation and living evidence

**Files:**
- Modify: `CURRENT_WORK.md`, `ROADMAP.md`, `NOTES.md`
- Create: `docs/review-handoffs/<UTC-date>-bootstrap-iam-address-reconciliation-review-handoff.md`

1. Run the focused pytest nodes, then the complete Terraform hygiene suite and `env -u PYTHONPATH uv run python scripts/validate_terraform_static.py`.
2. Run `terraform fmt -check -recursive infra/gcp`, backend-free root validation only if the existing local static-validation authority permits it, and `git diff --check`.
3. Record observed RED/GREEN and explicitly state that no backend initialization, import, state operation, plan/apply, or cloud mutation occurred.
4. Independently review the uncommitted source-only surface before any commit/PR.

**Acceptance:** The next E2 command-allowlist step has a reviewable source representation that does not demand duplicate state ownership.

## Material replanning triggers

Stop and revisit this plan if the existing live bucket IAM readback contains more than one intended authority member, if role-specific future authority requires a different resource model, if a Terraform/provider version changes, or if the proposed change affects bootstrap-retirement authority, bucket IAM, backend state, or workload state.
