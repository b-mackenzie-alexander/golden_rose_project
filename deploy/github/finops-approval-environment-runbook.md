# FinOps approval environment Gate E0

**Status:** Historical superseded procedure. ADR-0016's merged 2026-09-09 human-visible addendum suspends Gate E0 and per-domain signer/envelope/runner machinery for fictional-synthetic `develop`; PR #83 merged the replacement source contract at `develop@9a04b274d9e0132e5a0b409314ba53170b43e303`. Do not execute this runbook for the current target. Reconsider it only for a later production or materially different authority decision.

## Purpose and boundary

Gate E0 configures the single GitHub environment used by `.github/workflows/sign-finops-approval.yml`. It does not dispatch the signer and grants no GCP, IAM, state, plan/apply, import/removal, receipt, migration, service, tester, live-data, or production authority.

The environment ceremony is controlled repository configuration, not an independent-human control. Beatrice remains the sole maintainer and exact private reviewer; `prevent_self_review` is therefore truthfully `false`. ADR-0011/ADR-0012's same-repository/sole-maintainer High remains open and accepted.

## Exact desired contract

- repository: exact current Golden Rose repository, resolved privately and read back before mutation;
- environment name: `finops-approval`;
- wait timer: `0`;
- required reviewers: exactly one `User`, the privately recorded accountable owner ID/login;
- `prevent_self_review`: `false`;
- deployment branch policy: `protected_branches = true`, `custom_branch_policies = false`;
- environment secrets: exactly none;
- environment variables: exactly none;
- admin bypass: disabled when the repository/API exposes a configurable enforcement field; if the platform cannot configure or prove that posture, stop and replan rather than claim it;
- signer source: workflow job requires exact `refs/heads/develop`, and signed envelope `source_sha` must equal that run's exact `GITHUB_SHA`;
- no custom deployment branch/tag policy objects; and
- no second environment may be treated as approval authority.

Protected-branch policy may admit other protected branches at the environment layer, so the workflow's exact job `if`, in-script `GITHUB_REF` check, and envelope `source_sha == GITHUB_SHA` are mandatory additional controls. Environment configuration alone is never signer authority.

## Private inputs

Prepare outside Git and ordinary chat:

- exact repository owner/name;
- exact accountable-owner reviewer numeric ID and login;
- one-use Gate E0 approval record and digest;
- expected pre-change environment status; and
- owner-only evidence destination.

No token, reviewer ID/login, repository API response, or environment object is written into tracked source.

## Ordered Gate E0 ceremony

1. Rebaseline to the exact protected merge of revised PR A and verify all required PR checks passed.
2. Read the environment, deployment policies, environment secrets, and environment variables before mutation. If `finops-approval` exists with unknown or mismatched authority, stop; do not overwrite it from assumptions.
3. Review one exact private request body containing only the desired contract above and bind its SHA-256 to a fresh one-use Gate E0 approval.
4. Authenticate only to GitHub with the minimum repository-environment administration authority required for this one gate. No GCP credentials or cloud environment variables may be present.
5. Create or update only `finops-approval` with the exact reviewed body. Do not create secrets, variables, custom branch/tag policies, deployment keys, repository secrets, or another environment.
6. Read back the complete environment plus separate secrets/variables/custom-policy inventories.
7. Compare the response semantically to the exact contract. Bind the response ETag or equivalent immutable response digest and observation timestamp in private evidence.
8. Mark Gate E0 approval consumed after the mutation attempt regardless of success. If the mutation response or readback is missing, interrupted, ambiguous, or mismatched, signer dispatch remains prohibited and a new read-only recovery approval is required.
9. Remove GitHub administration credentials from the process and verify no run-owned credential file remains before any later signer approval is requested.

## Exact API surfaces for a future approved run

Use the documented GitHub REST environment endpoints for the exact repository:

- `GET /repos/{owner}/{repo}/environments/finops-approval`
- `PUT /repos/{owner}/{repo}/environments/finops-approval`
- `GET /repos/{owner}/{repo}/environments/finops-approval/deployment-branch-policies`
- `GET /repositories/{repository_id}/environments/finops-approval/secrets`
- `GET /repositories/{repository_id}/environments/finops-approval/variables`

Endpoint spelling must be revalidated against current authoritative GitHub documentation immediately before Gate E0. Documentation/version drift is a stop, not permission to improvise. Build request JSON in an owner-only file; do not place reviewer values or tokens on argv or in shell history.

## Required readback checks

Fail unless all are true:

- environment name is exactly `finops-approval`;
- protection rules contain exactly one required-reviewer rule with exactly the private expected user and no team/app reviewer;
- wait timer is exactly zero;
- `prevent_self_review` is exactly false;
- protected branches is exactly true and custom branch policies exactly false;
- custom branch-policy inventory is empty;
- secrets total count and item inventory are empty;
- variables total count and item inventory are empty;
- no unreviewed protection rule or deployment authority exists;
- admin-bypass posture is disabled and proven when configurable; and
- revised PR A's exact signer workflow source/hash/static contract is the merged protected source.

Record only value-safe outcome labels and digests in tracked notes. Keep raw responses and private reviewer/repository values in the approved evidence root.

## Unknown outcome and rollback

An HTTP success without exact readback is unknown. Do not dispatch the signer. Obtain a fresh read-only approval and repeat all readbacks.

If exact readback proves a wrong setting was created, keep signer dispatch blocked and prepare a separately reviewed correction request. Do not delete or broadly reset the environment as an automatic rollback. A correction has its own one-use approval and complete post-write readback.

## First signer-dispatch prerequisite

Before each signer dispatch, read back Gate E0 posture again under that transaction's separately approved preflight. Environment existence, an earlier successful Gate E0, or a workflow success flag is not reusable approval. Any drift blocks signing and all downstream domain transactions.
