# Gate P Cosign signature-subject remediation review handoff

## Objective

Review the bounded correction after approved run `33878561528` completed signing and attestation but failed final repository admission. Align signature admission with actual Cosign v3 verification semantics without weakening immutable digest, certificate, transparency, provenance, or SBOM authority.

## Exact boundary

- Base: protected `develop@0da1aeb3fd9143a7d14149a84b856319e90ef997`
- Branch: `fix/gate-p-cosign-signature-subject`
- Failed run: `33878561528`
- Failure: `signature subject does not match the immutable OCI image`
- Retry authority: consumed; no retry is authorized
- Private evidence: raw logs, immutable reference, and all seven artifacts remain operator-held

## Observed run result

The protected run completed:

- immutable `linux/amd64` build and push;
- pinned Syft image scan;
- one keyless Cosign signature;
- SLSA v1, SPDX, and embedded application-SBOM attestations;
- four certificate-identity, GitHub OIDC issuer, and transparency-log verification blocks;
- uploads for backend/frontend SBOM, image metadata, signature verification, provenance verification, SPDX verification, and application-SBOM verification.

It failed only when `verify_deploy_image_authority.py` required repository-only `critical.identity.docker-reference`. Every actual Cosign v3 verification record instead carries canonical `repository@sha256:...`, while separately retaining the same `docker-manifest-digest`. The workflow did not emit `published-image.txt` because final admission failed.

## RED → GREEN correction

Tests now model the four actual Cosign verification record types:

- `https://sigstore.dev/cosign/sign/v1`
- `https://slsa.dev/provenance/v1`
- `https://spdx.dev/Document`
- `https://golden-rose.nousresearch.com/attestations/application-sbom-checksums/v1`

Admission now requires, for every record:

- canonical `repository@digest` identity equal to the requested immutable image;
- exact `docker-manifest-digest` equality;
- a type in the reviewed four-type set;
- the complete reviewed type set across the output.

Negative regressions reject repository-only identity, unknown types, and a missing primary `sign/v1` record. The complete actual seven-artifact run evidence passes the corrected repository verifier locally.

## Candidate file inventory

1. `AGENTS.md`
2. `ARCHITECTURE.md`
3. `CURRENT_WORK.md`
4. `NOTES.md`
5. `README.md`
6. `ROADMAP.md`
7. `SECURITY.md`
8. `TECHNICAL_REQUIREMENTS.md`
9. `deploy/gcp/first-deployment-runbook.md`
10. `docs/review-handoffs/2026-09-04-gate-p-cosign-signature-subject-review-handoff.md`
11. `infra/gcp/README.md`
12. `scripts/verify_deploy_image_authority.py`
13. `tests/unit/test_deploy_image_authority.py`

## Local verification

- Full unit suite: `632 passed, 1 warning`.
- Focused Gate P generator/deployment/image/workflow suite: `341 passed`.
- Frontend: `116 passed`; coverage thresholds and production build passed.
- `uv lock --check`, Ruff format/check, strict mypy, Bandit, and pip-audit: passed.
- Terraform static validation and recursive formatting: passed.
- Working-tree Gitleaks: no leaks across approximately 16.06 MB.
- Diff hygiene: passed.
- Complete actual seven-artifact run evidence through corrected repository admission: passed.

## Review focus

1. Does canonical signature identity bind exactly to the requested repository and digest?
2. Does the manifest digest remain independently equal for every record?
3. Is the accepted signature type set exact and complete rather than open-ended?
4. Are repository-only, unknown-type, and missing-primary-signature cases rejected?
5. Does actual run evidence pass without synthesizing or rewriting provider output?
6. Do active docs preserve run failure, consumed approval, missing workflow-approved reference, and exact-tip fresh-approval boundary?
7. Is private cloud/image/credential material absent from tracked changes?

## Independent review result

Fresh security review found no Blocker, High, or Medium. It accepted the canonical four-record set and rejected 16/16 subject, digest, type, and missing-type mutations; focused modified-file checks passed. Fresh documentation/privacy review found no Blocker, High, or Medium; the 13-file inventory, current totals, failed-run boundary, missing workflow-approved reference, consumed approval, and private-evidence handling are consistent.

## Stop boundary

This is source-only remediation. It authorizes no publication retry, Secret version, database/migration, service activation, tester access, qualification, live/client data, or production action. After clean review and protected merge, a new exact-tip binding and explicit one-dispatch approval are required.
