from pathlib import Path

MIGRATION = (
    Path(__file__).resolve().parents[2]
    / "migrations"
    / "versions"
    / "0018_staff_account_correction_authority.py"
)


def test_staff_account_correction_authority_migration_grants_runtime_update_columns() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")

    assert 'revision = "0018_staff_acct_corr_auth"' in sql
    assert len("0018_staff_acct_corr_auth") <= 32
    assert 'down_revision = "0017_staff_signin_email_mgmt"' in sql
    assert "GRANT UPDATE(provider_subject,provider_email,display_name,role_name)" in sql
    assert "ON staff_accounts TO golden_rose_runtime" in sql
    assert "REVOKE UPDATE(provider_subject,provider_email,display_name,role_name)" in sql
    assert "ON staff_accounts FROM golden_rose_runtime" in sql
