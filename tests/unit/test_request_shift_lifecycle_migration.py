from pathlib import Path

MIGRATION = (
    Path(__file__).resolve().parents[2] / "migrations" / "versions" / "0014_request_shift_review.py"
)


def test_request_shift_lifecycle_migration_adds_review_evidence_and_authority():
    sql = MIGRATION.read_text()

    assert 'revision = "0014_request_shift_review"' in sql
    assert len("0014_request_shift_review") <= 32
    assert 'down_revision = "0013_shift_need_foundation"' in sql
    assert "request_status IN ('draft', 'pending_review')" in sql
    assert "shift_need.submitted_for_review" in sql
    assert "CREATE TABLE staffing_request_events" in sql
    assert "staffing_request.submitted_for_review" in sql
    assert "deny_mutation_staffing_request_events" in sql
    assert (
        "GRANT UPDATE(request_status, version, updated_at, updated_by) ON TABLE staffing_requests"
        in sql
    )
    assert "GRANT UPDATE(shift_status, version, updated_at, updated_by) ON TABLE shift_needs" in sql
    assert "staffing request evidence blocks downgrade before DDL" in sql
