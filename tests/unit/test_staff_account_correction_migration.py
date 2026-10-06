from pathlib import Path

MIGRATION = (
    Path(__file__).resolve().parents[2]
    / "migrations"
    / "versions"
    / "0015_staff_account_corrections.py"
)


def test_staff_account_correction_migration_updates_lifecycle_event_contract() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")

    assert 'revision = "0015_staff_account_corrections"' in sql
    assert len("0015_staff_account_corrections") <= 32
    assert 'down_revision = "0014_request_shift_review"' in sql
    assert "'staff_account.corrected'" in sql
    assert "new_version=previous_version+1" in sql
    assert "staff account correction data blocks downgrade" in sql
