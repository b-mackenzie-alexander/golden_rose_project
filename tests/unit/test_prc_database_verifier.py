from scripts.verify_database_authority import (
    EXPECTED_INTAKE_CONSTRAINTS,
    EXPECTED_INTAKE_TRIGGERS,
    EXPECTED_RUNTIME_FUNCTION_PRIVILEGES,
    EXPECTED_RUNTIME_TABLE_PRIVILEGES,
    EXPECTED_RUNTIME_UPDATE_COLUMNS,
    EXPECTED_SCHEMA_OWNER_OBJECTS,
)

CANONICAL_TABLES = {
    "workers",
    "worker_contacts",
    "worker_residences",
    "worker_preferences",
    "worker_interest_selections",
    "intake_finalizations",
    "employer_contact_details",
    "employer_addresses",
    "worksites",
    "staffing_requests",
}


def test_prc_tables_are_owned_append_only_and_have_no_runtime_update() -> None:
    for table in CANONICAL_TABLES:
        assert table in EXPECTED_SCHEMA_OWNER_OBJECTS
        assert EXPECTED_RUNTIME_TABLE_PRIVILEGES[table] == {"INSERT", "SELECT"}
        assert EXPECTED_RUNTIME_UPDATE_COLUMNS[table] == set()
        assert f"{table}.deny_mutation_{table}" in EXPECTED_INTAKE_TRIGGERS


def test_prc_links_and_finalization_replace_closed_predecessor_gate() -> None:
    assert "intakes.ck_intakes_links_not_available" not in EXPECTED_INTAKE_CONSTRAINTS
    assert "intake_links.ck_intake_links_not_available" not in EXPECTED_INTAKE_CONSTRAINTS
    assert "intake_finalizations.ck_finalization_reuse_shape" in EXPECTED_INTAKE_CONSTRAINTS
    assert {
        "worker_id",
        "worker_version",
        "employer_id",
        "employer_version",
        "lifecycle_status",
    } <= EXPECTED_RUNTIME_UPDATE_COLUMNS["intakes"]
    assert "employer_contact_version" in EXPECTED_RUNTIME_UPDATE_COLUMNS["intake_links"]
    assert "audit_events.guard_intake_link_event" in EXPECTED_INTAKE_TRIGGERS
    assert "command_results.guard_finalization_results" in EXPECTED_INTAKE_TRIGGERS


def test_only_explicit_snapshot_functions_have_runtime_execute() -> None:
    for function in ("intake_canonical_record", "intake_link_refs", "intake_effective_snapshot"):
        assert EXPECTED_RUNTIME_FUNCTION_PRIVILEGES[function] == {"EXECUTE"}
    for function in ("guard_intake_links", "guard_intake_link_event", "guard_finalization_results"):
        assert EXPECTED_RUNTIME_FUNCTION_PRIVILEGES[function] == set()
