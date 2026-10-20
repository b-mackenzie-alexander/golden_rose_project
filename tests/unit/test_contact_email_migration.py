from pathlib import Path

MIGRATION = (
    Path(__file__).resolve().parents[2] / "migrations" / "versions" / "0020_contact_email_fields.py"
)


def test_contact_email_migration_preserves_contact_correction_and_review_boundaries() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")

    assert 'revision = "0020_contact_email_fields"' in sql
    assert len("0020_contact_email_fields") <= 32
    assert 'down_revision = "0019_ext_calendar_imports"' in sql
    assert 'sa.Column("email", sa.String(320), nullable=True)' in sql
    assert "ck_worker_contacts_email_shape" in sql
    assert "ck_employer_contact_details_email_shape" in sql
    assert "GRANT UPDATE(phone,email,version,updated_at,updated_by)" in sql
    assert "GRANT UPDATE(representative_name,phone,email,version,updated_at,updated_by)" in sql
    assert "canonical_correction_section" in sql
    assert "reviews.CURRENT_FACTS" in sql
    assert "contact email data blocks downgrade before DDL" in sql
