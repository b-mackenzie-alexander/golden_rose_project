import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

MIGRATION = (
    Path(__file__).resolve().parents[2] / "migrations" / "versions" / "0020_contact_email_fields.py"
)


def migration_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("contact_email_migration", MIGRATION)
    assert spec is not None and spec.loader is not None
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def test_contact_email_migration_sql_patch_helpers_update_every_function_and_fail_closed() -> None:
    migration = migration_module()

    assert migration.replace_function("CREATE FUNCTION a(); CREATE FUNCTION b();") == (
        "CREATE OR REPLACE FUNCTION a(); CREATE OR REPLACE FUNCTION b();"
    )
    assert migration.replace_exact("before target after", "target", "replacement") == (
        "before replacement after"
    )
    with pytest.raises(RuntimeError, match="Expected exactly one"):
        migration.replace_exact("before after", "target", "replacement")
    with pytest.raises(RuntimeError, match="Expected exactly one"):
        migration.replace_exact("target target", "target", "replacement")


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
    assert "replace_exact" in sql
    assert 'sql.replace("CREATE FUNCTION", "CREATE OR REPLACE FUNCTION")' in sql
    assert "reviews.CURRENT_FACTS" in sql
    assert "jsonb_strip_nulls(jsonb_build_object" in sql
    assert "linked.SNAPSHOT" in sql
    assert "contact email data blocks downgrade before DDL" in sql
