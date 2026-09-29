from pathlib import Path

MIGRATION = (
    Path(__file__).resolve().parents[2]
    / "migrations"
    / "versions"
    / "0013_shift_need_foundation.py"
)


def test_shift_need_migration_adds_draft_child_and_evidence_tables():
    sql = MIGRATION.read_text()

    assert 'revision = "0013_shift_need_foundation"' in sql
    assert 'down_revision = "0012_staff_account_evidence"' in sql
    assert "CREATE TABLE shift_needs" in sql
    assert "CHECK(shift_status = 'draft')" in sql
    assert "CREATE TABLE shift_need_events" in sql
    assert "CHECK(event_type = 'shift_need.created')" in sql
    assert "deny_mutation_shift_need_events" in sql
    assert (
        "GRANT SELECT, INSERT ON TABLE shift_needs, shift_need_events TO golden_rose_runtime" in sql
    )
