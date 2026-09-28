from pathlib import Path

MIGRATION = (
    Path(__file__).resolve().parents[2] / "migrations" / "versions" / "0010_staff_accounts.py"
)
LIFECYCLE_MIGRATION = (
    Path(__file__).resolve().parents[2]
    / "migrations"
    / "versions"
    / "0011_staff_account_lifecycle.py"
)


def test_staff_account_migration_records_account_grants_and_delegations() -> None:
    source = MIGRATION.read_text(encoding="utf-8")

    for fragment in (
        'revision = "0010_staff_accounts"',
        'down_revision = "0009a_canonical_reviews"',
        "CREATE TABLE staff_accounts",
        "CREATE TABLE staff_permission_grants",
        "CREATE TABLE staff_delegations",
        "provider_subject varchar(256) NOT NULL UNIQUE",
        "CHECK((lifecycle_status='active' AND mfa_enrolled) OR lifecycle_status<>'active')",
        "CREATE UNIQUE INDEX uq_staff_permission_grants_active_scope",
        "GRANT SELECT ON {table} TO golden_rose_runtime",
    ):
        assert fragment in source


def test_staff_account_migration_refuses_downgrade_when_identity_data_exists() -> None:
    source = MIGRATION.read_text(encoding="utf-8")

    assert "staff account data blocks downgrade before DDL" in source
    assert "EXISTS(SELECT 1 FROM staff_accounts)" in source


def test_staff_account_lifecycle_migration_adds_evidence_and_narrow_write_grants() -> None:
    source = LIFECYCLE_MIGRATION.read_text(encoding="utf-8")

    for fragment in (
        'revision = "0011_staff_account_lifecycle"',
        'down_revision = "0010_staff_accounts"',
        "CREATE TABLE staff_account_lifecycle_events",
        "staff_account.activated",
        "staff_account.suspended",
        "staff_account.deprovisioned",
        "GRANT UPDATE(lifecycle_status,mfa_enrolled,updated_at,updated_by,version)",
        "staff account lifecycle data blocks downgrade before DDL",
    ):
        assert fragment in source
