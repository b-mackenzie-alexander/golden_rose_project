# Receipt scaffolding

This directory holds source-controlled scaffolding for the operator-held receipt artifacts used by the Golden Rose GCP deployment process.

## Purpose
These files are **templates and guidance only**. They are not authority by themselves and must not be mistaken for live approved receipts.

Use them to:
- document the reviewed receipt shapes,
- give later operator workflows a consistent starting point,
- reduce ad hoc formatting drift when the real tester/stage receipt gate opens.

## Boundaries
- Do not place real tester identities, real approval references, live bundle files, or sensitive operator-held values in this directory.
- Do not commit detached Sigstore bundles, real signed receipts, live endpoint details, or production identities here.
- Real receipt JSON and detached bundles stay in operator-held records outside tracked source.

## Contents
- `templates/tester-authority-receipt.example.json` — reviewed tester-authority receipt skeleton matching `scripts/verify_tester_authority_receipt.py`
- `templates/stage-receipt.example.json` — reviewed stage receipt skeleton matching `scripts/verify_stage_receipt.py`
- `templates/migration-success-receipt.example.json` — reviewed migration-success receipt skeleton matching `scripts/write_migration_success_receipt.py` and `scripts/verify_stage_receipt.py`

## Related sources
- `scripts/verify_tester_authority_receipt.py`
- `scripts/verify_stage_receipt.py`
- `deploy/gcp/private-tester-access.md`
- `deploy/gcp/staged-plan-approval.md`
