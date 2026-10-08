from pathlib import Path

MIGRATION = (
    Path(__file__).resolve().parents[2]
    / "migrations"
    / "versions"
    / "0017_staff_signin_email_mgmt.py"
)


def test_staff_account_signin_email_management_migration_adds_event_type() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")

    assert 'revision = "0017_staff_signin_email_mgmt"' in sql
    assert len("0017_staff_signin_email_mgmt") <= 32
    assert 'down_revision = "0016_staff_google_email"' in sql
    assert "'staff_account.signin_email_updated'" in sql
    assert "new_version=previous_version+1" in sql
    assert "staff account sign-in email data blocks downgrade" in sql
