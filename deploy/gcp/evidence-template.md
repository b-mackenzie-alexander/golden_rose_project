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

## Foundation checks
- Project labels and inventory match the reviewed develop posture.
- Only approved APIs are enabled.
- Cloud Run invoker access remains private and named.
- Cloud SQL remains private-path only.
- No service-account keys exist.
- Project/service-account IAM matches the reviewed effective-authority contract.
- State bucket versioning/access/recovery posture is intact.
- Budget, alert route, and logging posture are present.

## Violations
- [REDACTED or none]

## Qualification result
- Employer create/read/search/revision/replay: [passed|failed]
- EmployerContact create/query/read: [passed|failed]
- Cleanup/rebuild disposition: [REDACTED]

## Value-safety notes
- Redact project IDs, principals, emails, URLs, tokens, exception payloads, and raw policy blobs.
- Keep only minimized evidence needed to prove pass/fail posture.
