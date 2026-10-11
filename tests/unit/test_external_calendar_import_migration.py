from pathlib import Path

MIGRATION = (
    Path(__file__).resolve().parents[2]
    / "migrations"
    / "versions"
    / "0019_external_calendar_import_candidates.py"
)


def test_external_calendar_import_migration_adds_candidate_tables_and_runtime_grants() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")

    assert 'revision = "0019_ext_calendar_imports"' in sql
    assert len("0019_ext_calendar_imports") <= 32
    assert 'down_revision = "0018_staff_acct_corr_auth"' in sql
    assert "CREATE TABLE staff_calendar_connections" in sql
    assert "CREATE TABLE external_calendar_imports" in sql
    assert "CREATE TABLE external_calendar_import_events" in sql
    assert "provider_name varchar(40) NOT NULL CHECK(provider_name='google_calendar')" in sql
    assert "UNIQUE(connection_id,provider_event_uid)" in sql
    assert "deny_mutation_external_calendar_import_events" in sql
    assert "GRANT SELECT, INSERT ON TABLE staff_calendar_connections" in sql
    assert "GRANT UPDATE(calendar_alias,token_material_ref,granted_scopes" in sql
    assert "GRANT UPDATE(import_status,linked_entity_type,linked_entity_id" in sql
    assert "SELECT EXISTS(SELECT 1 FROM external_calendar_imports)" in sql
