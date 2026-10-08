from pathlib import Path

MIGRATION = (
    Path(__file__).resolve().parents[2] / "migrations" / "versions" / "0016_staff_google_email.py"
)


def test_staff_account_google_email_binding_migration_extends_onboarding_identity() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")

    assert 'revision = "0016_staff_google_email"' in sql
    assert len("0016_staff_google_email") <= 32
    assert 'down_revision = "0015_staff_account_corrections"' in sql
    assert "ADD COLUMN provider_email varchar(320)" in sql
    assert "uq_staff_accounts_provider_email" in sql
    assert "ck_staff_accounts_provider_email_shape" in sql
