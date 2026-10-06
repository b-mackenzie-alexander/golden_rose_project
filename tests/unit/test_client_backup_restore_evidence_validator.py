import json
from pathlib import Path
from typing import Any

import pytest

from scripts.validate_client_backup_restore_evidence import (
    EXPECTED_VALIDATOR_COMMAND,
    BackupRestoreEvidenceValidationError,
    validate_backup_restore_evidence,
)


def _valid_backup_restore_evidence() -> dict[str, Any]:
    return {
        "evidence_type": "client-production-backup-restore-rehearsal-not-activation",
        "validator_command": EXPECTED_VALIDATOR_COMMAND,
        "authority_boundary": {
            "cloud_execution": "separate-approval-required",
            "production_deployment": "separate-approval-required",
            "live_data_admission": "separate-approval-required",
            "destructive_recovery": "separate-approval-required",
        },
        "source": {
            "source_commit": "a" * 40,
            "migration_revision": "0015_staff_account_corrections",
        },
        "rehearsal": {
            "backup_rehearsal_status": "passed",
            "restore_rehearsal_status": "passed",
            "restore_target": "isolated-nonproduction-or-approved-production-shaped",
            "live_data_in_source": "not-included",
            "destructive_recovery": "not-executed-without-separate-approval",
        },
        "evidence": {
            "backup_receipt": "Backup receipt recorded by operator",
            "restore_receipt": "Restore receipt recorded by operator",
            "integrity_check": "Integrity check passed with expected counts",
            "database_authority_receipt": "Database authority receipt recorded",
            "rollback_or_forward_recovery_note": "Forward recovery note recorded",
            "backup_restore_owner": "Private owner record",
        },
    }


def _write_evidence(tmp_path: Path, document: dict[str, Any]) -> Path:
    path = tmp_path / "backup-restore.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    return path


def test_backup_restore_evidence_accepts_value_safe_rehearsal(tmp_path: Path) -> None:
    checked = validate_backup_restore_evidence(
        _write_evidence(tmp_path, _valid_backup_restore_evidence())
    )

    assert checked == [
        "authority_boundary",
        "source",
        "rehearsal",
        "evidence",
    ]


def test_backup_restore_evidence_rejects_wrong_type(tmp_path: Path) -> None:
    document = _valid_backup_restore_evidence()
    document["evidence_type"] = "production-activation"

    with pytest.raises(BackupRestoreEvidenceValidationError, match="evidence_type"):
        validate_backup_restore_evidence(_write_evidence(tmp_path, document))


def test_backup_restore_evidence_rejects_short_commit(tmp_path: Path) -> None:
    document = _valid_backup_restore_evidence()
    document["source"]["source_commit"] = "abc123"

    with pytest.raises(BackupRestoreEvidenceValidationError, match="40-character SHA"):
        validate_backup_restore_evidence(_write_evidence(tmp_path, document))


def test_backup_restore_evidence_rejects_blocked_backup(tmp_path: Path) -> None:
    document = _valid_backup_restore_evidence()
    document["rehearsal"]["backup_rehearsal_status"] = "blocked"

    with pytest.raises(BackupRestoreEvidenceValidationError, match="backup_rehearsal_status"):
        validate_backup_restore_evidence(_write_evidence(tmp_path, document))


def test_backup_restore_evidence_rejects_unapproved_restore_target(tmp_path: Path) -> None:
    document = _valid_backup_restore_evidence()
    document["rehearsal"]["restore_target"] = "production-database"

    with pytest.raises(BackupRestoreEvidenceValidationError, match="restore_target"):
        validate_backup_restore_evidence(_write_evidence(tmp_path, document))


def test_backup_restore_evidence_rejects_live_data_claim(tmp_path: Path) -> None:
    document = _valid_backup_restore_evidence()
    document["rehearsal"]["live_data_in_source"] = "live client data copied"

    with pytest.raises(BackupRestoreEvidenceValidationError, match="live client data"):
        validate_backup_restore_evidence(_write_evidence(tmp_path, document))


def test_backup_restore_evidence_rejects_placeholder_evidence(tmp_path: Path) -> None:
    document = _valid_backup_restore_evidence()
    document["evidence"]["backup_receipt"] = "<value-safe-backup-receipt-record>"

    with pytest.raises(BackupRestoreEvidenceValidationError, match="backup_receipt"):
        validate_backup_restore_evidence(_write_evidence(tmp_path, document))


def test_backup_restore_evidence_rejects_concrete_url(tmp_path: Path) -> None:
    document = _valid_backup_restore_evidence()
    document["evidence"]["restore_receipt"] = "see https://private.invalid/restore"

    with pytest.raises(BackupRestoreEvidenceValidationError, match="concrete URL"):
        validate_backup_restore_evidence(_write_evidence(tmp_path, document))


def test_backup_restore_evidence_rejects_email_like_owner(tmp_path: Path) -> None:
    document = _valid_backup_restore_evidence()
    document["evidence"]["backup_restore_owner"] = "owner@example.invalid"

    with pytest.raises(BackupRestoreEvidenceValidationError, match="email-like"):
        validate_backup_restore_evidence(_write_evidence(tmp_path, document))


def test_backup_restore_evidence_rejects_cloud_command(tmp_path: Path) -> None:
    document = _valid_backup_restore_evidence()
    document["evidence"]["database_authority_receipt"] = "gcloud sql backups restore"

    with pytest.raises(BackupRestoreEvidenceValidationError, match="gcloud"):
        validate_backup_restore_evidence(_write_evidence(tmp_path, document))
