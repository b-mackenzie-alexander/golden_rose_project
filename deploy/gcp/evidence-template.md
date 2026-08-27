# GCP deployment evidence template

Status: [passed|failed]
Mode: [read-only|qualification]
Date: [YYYY-MM-DD]
Operator: [REDACTED]
Project: [REDACTED]
Region: us-east4

## Expected operator-held inputs
- State bucket name: [REDACTED]
- Private invoker principal: [REDACTED]
- Artifact Registry writer member: [REDACTED]
- Deployer principal: [REDACTED]
- Observability viewer principal: [REDACTED]
- Recovery policy review status: [REDACTED]
- Billing account: [REDACTED]

## Read-only command posture
- No mutation mode is approved in this task.
- No cloud apply, deploy, image push, secret injection, or IAM write occurs here.
- Any future mutation path requires separate approval and a separately reviewed tool/runbook.

## Qualification posture
- Qualification must use approved authenticated private access only.
- `/health` and `/readiness` remain non-mutating probes and are not substitutes for bounded workflow qualification.
- Qualification uses newly generated fictional values only.
- Evidence must not include submitted names, UUIDs, command IDs, cursors, raw bodies, DSNs, tokens, or exception payloads.
- Cleanup must state teardown/rebuild disposition without inventing product delete semantics.

## Image provenance posture
- Deploy evidence must bind to one immutable `sha256:` image digest; tags alone are not acceptable proof.
- Record whether signature, provenance, image SBOM, and application SBOM attestation verification all matched the exact reviewed digest.
- Record the reviewed GitHub Actions certificate identity and OIDC issuer without copying raw certificate bundles or Rekor payloads.
- Do not claim publication or attestation verification occurred unless the reviewed workflow emitted those exact evidence artifacts.

## Foundation checks
- Stage mode is recorded as foundation, migration, or service and the expected workload absence/presence is evaluated accordingly.
- Project labels and inventory match the reviewed develop posture.
- Only approved APIs are enabled.
- Budget evidence preserves raw notification-channel resource names and compares them separately from human display names.
- Cloud Run invoker access remains private and named only when a later stage brings the service into scope.
- Authenticated `/readiness` uptime evidence exists only in service and uses the reviewed monitoring service-agent path.
- In `foundation`, Cloud SQL is absent and out of scope for the reviewed lower-layer contract.
- In `migration` and `service`, Cloud SQL remains private-path only.
- No service-account keys exist.
- Project/service-account IAM matches the reviewed effective-authority contract.
- State bucket versioning/access/recovery posture is intact.
- Budget, alert route, and logging posture are present.
- Availability alerts are provisional develop review triggers, not SLOs or client commitments.

## Violations
- [REDACTED or none]

## Qualification result
- Employer create/read/search/revision/replay: [passed|failed]
- EmployerContact create/query/read: [passed|failed]
- Cleanup/rebuild disposition: [REDACTED]

## Value-safety notes
- Redact project IDs, principals, emails, URLs, tokens, exception payloads, and raw policy blobs.
- Keep only minimized evidence needed to prove pass/fail posture.
